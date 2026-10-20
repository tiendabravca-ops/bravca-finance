import imaplib
import email
from email.header import decode_header
import re
import sqlite3
import os
import streamlit as st
import io

try:
    import pypdf
    HAS_PYPDF = True
except ImportError:
    HAS_PYPDF = False

def get_gmail_credentials():
    try:
        user = st.secrets["GMAIL_USER"]
        password = st.secrets["GMAIL_PASSWORD"]
    except Exception:
        user = os.getenv("GMAIL_USER", "tiendabravca@gmail.com")
        password = os.getenv("GMAIL_PASSWORD", "")
    return user, password

def limpiar_nombre_cajero(cadena_raw):
    """
    Limpia cadenas sucias como '(a)NICOLECerrado2026-10-18 19:00Transacciones8'
    o etiquetas de correo y extrae únicamente el nombre limpio del colaborador.
    """
    if not cadena_raw:
        return "Cajero No Especificado"
    
    # 1. Quitar prefijos del tipo (a), (b), etc.
    limpio = re.sub(r'^\([a-z]\)\s*', '', str(cadena_raw), flags=re.IGNORECASE)
    
    # 2. Cortar donde aparezca la palabra 'Cerrado', 'Transacciones' o un patrón de fecha YYYY-MM-DD
    match = re.split(r'Cerrado|Transacciones|\d{4}-\d{2}-\d{2}', limpio, flags=re.IGNORECASE)
    if match and match[0].strip():
        limpio = match[0].strip()
        
    return limpio if limpio else "Cajero No Especificado"

def init_db():
    conn = sqlite3.connect("db_cierres.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cierres (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT,
            cajero TEXT,
            negocio TEXT,
            colones REAL,
            dolares REAL,
            tarjeta_colones REAL DEFAULT 0,
            efectivo_colones REAL DEFAULT 0,
            estado TEXT
        )
    """)
    conn.commit()

    # Histórico oficial fijo del 1 al 15 de Octubre
    historico_1_al_15 = [
        # --- Bravca Souvenir ---
        ("2026-10-01", "Bravca Souvenir", 31900.00),
        ("2026-10-02", "Bravca Souvenir", 6000.00),
        ("2026-10-03", "Bravca Souvenir", 26550.00),
        ("2026-10-04", "Bravca Souvenir", 56300.00),
        ("2026-10-05", "Bravca Souvenir", 22320.00),
        ("2026-10-06", "Bravca Souvenir", 120625.00),
        ("2026-10-07", "Bravca Souvenir", 128260.00),
        ("2026-10-08", "Bravca Souvenir", 151810.00),
        ("2026-10-09", "Bravca Souvenir", 140625.00),
        ("2026-10-10", "Bravca Souvenir", 35145.00),
        ("2026-10-11", "Bravca Souvenir", 30060.00),
        ("2026-10-12", "Bravca Souvenir", 61175.00),
        ("2026-10-13", "Bravca Souvenir", 75100.00),
        ("2026-10-14", "Bravca Souvenir", 104400.00),
        ("2026-10-15", "Bravca Souvenir", 28200.00),
        # --- Bravca Extremo ---
        ("2026-10-01", "Bravca Extremo", 24120.00),
        ("2026-10-02", "Bravca Extremo", 9050.00),
        ("2026-10-03", "Bravca Extremo", 18920.00),
        ("2026-10-04", "Bravca Extremo", 25020.00),
        ("2026-10-05", "Bravca Extremo", 1200.00),
        ("2026-10-06", "Bravca Extremo", 60240.00),
        ("2026-10-07", "Bravca Extremo", 35040.00),
        ("2026-10-08", "Bravca Extremo", 12575.00),
        ("2026-10-09", "Bravca Extremo", 7650.00),
        ("2026-10-10", "Bravca Extremo", 35900.00),
        ("2026-10-11", "Bravca Extremo", 14500.00),
        ("2026-10-12", "Bravca Extremo", 23900.00),
        ("2026-10-13", "Bravca Extremo", 49710.00),
        ("2026-10-14", "Bravca Extremo", 3500.00),
        ("2026-10-15", "Bravca Extremo", 10600.00),
    ]

    for fecha_str, negocio_str, monto in historico_1_al_15:
        cursor.execute("SELECT id FROM cierres WHERE fecha LIKE ? AND negocio = ?", (f"{fecha_str}%", negocio_str))
        if not cursor.fetchone():
            cursor.execute("""
                INSERT INTO cierres (fecha, cajero, negocio, colones, dolares, tarjeta_colones, efectivo_colones, estado)
                VALUES (?, ?, ?, ?, 0.0, 0.0, ?, ?)
            """, (f"{fecha_str} 18:00", "Histórico Simplifica2", negocio_str, monto, monto, "Histórico Cargado"))
            conn.commit()

    conn.close()

def sincronizar_cierres_gmail():
    user, password = get_gmail_credentials()
    if not password:
        return False, "Falta configurar la contraseña de aplicación en los 'Secrets' de Streamlit Cloud."

    init_db()
    conn = sqlite3.connect("db_cierres.db")
    cursor = conn.cursor()

    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(user, password)
        mail.select("INBOX")

        status, messages = mail.search(None, "ALL")
        if status != "OK":
            mail.logout()
            return False, "No se pudo acceder a la bandeja de entrada."

        email_ids = messages[0].split()
        email_ids = email_ids[-60:] 

        for e_id in email_ids:
            res, msg_data = mail.fetch(e_id, "(RFC822)")
            if res != "OK":
                continue

            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    
                    from_header = msg.get("From", "")
                    subject_header = decode_header(msg["Subject"])[0] if msg["Subject"] else ("", "utf-8")
                    subject = subject_header[0]
                    if isinstance(subject, bytes):
                        subject = subject.decode(subject_header[1] or "utf-8", errors="ignore")

                    if "simplifica2" in from_header.lower() or "cierre" in subject.lower():
                        body = ""
                        pdf_text = ""

                        for part in msg.walk():
                            content_type = part.get_content_type()
                            content_disposition = str(part.get("Content-Disposition"))

                            if content_type == "text/plain" and "attachment" not in content_disposition:
                                try:
                                    body = part.get_payload(decode=True).decode("utf-8", errors="ignore")
                                except:
                                    pass

                            elif HAS_PYPDF and ("application/pdf" in content_type or part.get_filename()):
                                filename = part.get_filename()
                                if filename and filename.lower().endswith(".pdf"):
                                    try:
                                        pdf_data = part.get_payload(decode=True)
                                        reader = pypdf.PdfReader(io.BytesIO(pdf_data))
                                        for page in reader.pages:
                                            pdf_text += page.extract_text() + "\n"
                                    except Exception:
                                        pass

                        full_content = body + "\n" + pdf_text + "\n" + subject

                        # Extracción mejorada utilizando la función de limpieza
                        negocio_match = re.search(r"Negocio\s+([^\n\r]+)", full_content)
                        cajero_match = re.search(r"Cajero\(a\)\s+([^\n\r]+)", full_content, re.IGNORECASE)
                        if not cajero_match:
                            cajero_match = re.search(r"Cajero\s*[:]?\s*([^\n\r]+)", full_content, re.IGNORECASE)

                        fecha_match = re.search(r"(2026-\d{2}-\d{2}\s+\d{2}:\d{2})", full_content)
                        if not fecha_match:
                            fecha_match = re.search(r"(2026-\d{2}-\d{2})", full_content)

                        negocio = negocio_match.group(1).strip() if negocio_match else "Bravca Souvenir"
                        
                        # Limpiar nombre del cajero extraído del correo o del asunto
                        cajero_raw = cajero_match.group(1).strip() if cajero_match else subject
                        cajero = limpiar_nombre_cajero(cajero_raw)
                        if cajero.lower() in ["cajero", "cajero(a)", ""]:
                            cajero = "Leonardo Venegas Mejías"

                        fecha = fecha_match.group(1).strip() if fecha_match else ""
                        if not fecha:
                            continue

                        if len(fecha) == 10:
                            fecha += " 18:00"

                        if fecha[:10] >= "2026-10-16":
                            tarjeta_colones = 0.0
                            efectivo_colones = 0.0

                            t_match = re.search(r"Tarjeta[^\d]*([\d,]+\.\d{2})", full_content, re.IGNORECASE)
                            if t_match:
                                tarjeta_colones = float(t_match.group(1).replace(",", ""))

                            e_match = re.search(r"(?:Efectivo\s*cobrado|Conteo\s+de\s+efectivo)[^\d]*([\d,]+\.\d{2})", full_content, re.IGNORECASE)
                            if e_match:
                                efectivo_colones = float(e_match.group(1).replace(",", ""))

                            colones = tarjeta_colones + efectivo_colones
                            if colones == 0.0:
                                total_match = re.search(r"Total[^\d]*([\d,]+\.\d{2})", full_content, re.IGNORECASE)
                                if total_match:
                                    colones = float(total_match.group(1).replace(",", ""))

                            dolares_match = re.search(r"(?:USD|Dólares|\$)\s*([\d,]+\.\d{2})", full_content)
                            dolares = float(dolares_match.group(1).replace(",", "")) if dolares_match else 0.0

                            # Limpiamos cualquier registro previo defectuoso del 16 en adelante para volverlo a insertar impecable
                            cursor.execute("DELETE FROM cierres WHERE fecha LIKE ? AND negocio = ? AND cajero != 'Histórico Simplifica2'", (f"{fecha[:10]}%", negocio))
                            
                            cursor.execute("""
                                INSERT INTO cierres (fecha, cajero, negocio, colones, dolares, tarjeta_colones, efectivo_colones, estado)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                            """, (fecha, cajero, negocio, colones, dolares, tarjeta_colones, efectivo_colones, "Recibido / Verificado"))
                            
                            conn.commit()

        mail.logout()
        conn.close()
        return True, "Sincronización completa. Cajeros y fechas actualizados."

    except Exception as e:
        conn.close()
        return False, f"Error de conexión: {str(e)}"
