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
    Limpia cadenas sucias como '(a)Karol Villegas PorrasCerrado2026-10-20 15:12Transacciones1'
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
        email_ids = email_ids[-80:] # Ampliamos el rango para asegurar lectura de ambos negocios

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

                    if "simplifica2" in from_header.lower() or "cierre" in subject.lower() or "transacciones" in subject.lower():
                        body = ""
                        pdf_text = ""
                        nombres_adjuntos = ""

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
                                if filename:
                                    nombres_adjuntos += " " + filename
                                if filename and filename.lower().endswith(".pdf"):
                                    try:
                                        pdf_data = part.get_payload(decode=True)
                                        reader = pypdf.PdfReader(io.BytesIO(pdf_data))
                                        for page in reader.pages:
                                            pdf_text += page.extract_text() + "\n"
                                    except Exception:
                                        pass

                        full_content = body + "\n" + pdf_text + "\n" + subject + "\n" + nombres_adjuntos

                        # Detección inteligente de Tienda (Souvenir vs Extremo)
                        content_lower = full_content.lower()
                        if "extremo" in content_lower:
                            negocio = "Bravca Extremo"
                        else:
                            negocio = "Bravca Souvenir"

                        # Extracción y limpieza del cajero
                        cajero_match = re.search(r"Cajero\(a\)\s+([^\n\r]+)", full_content, re.IGNORECASE)
                        if not cajero_match:
                            cajero_match = re.search(r"Cajero\s*[:]?\s*([^\n\r]+)", full_content, re.IGNORECASE)

                        cajero_raw = cajero_match.group(1).strip() if cajero_match else subject
                        cajero = limpiar_nombre_cajero(cajero_raw)
                        if cajero.lower() in ["cajero", "cajero(a)", ""] or len(cajero) < 3:
                            cajero = "Colaborador BráVca"

                        fecha_match = re.search(r"(2026-\d{2}-\d{2}\s+\d{2}:\d{2})", full_content)
                        if not fecha_match:
                            fecha_match = re.search(r"(2026-\d{2}-\d{2})", full_content)

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

                            # Limpiar duplicados exactos por fecha y negocio para reinsertar limpio
                            cursor.execute("DELETE FROM cierres WHERE fecha LIKE ? AND negocio = ? AND cajero != 'Histórico Simplifica2'", (f"{fecha[:10]}%", negocio))
                            
                            cursor.execute("""
                                INSERT INTO cierres (fecha, cajero, negocio, colones, dolares, tarjeta_colones, efectivo_colones, estado)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                            """, (fecha, cajero, negocio, colones, dolares, tarjeta_colones, efectivo_colones, "Recibido / Verificado"))
                            
                            conn.commit()

        mail.logout()
        conn.close()
        return True, "Sincronización completa. Nombres y tiendas actualizados correctamente."

    except Exception as e:
        conn.close()
        return False, f"Error de conexión: {str(e)}"
