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
    """Limpia nombres de cajeros eliminando fechas y textos pegados."""
    if not cadena_raw:
        return "Colaborador BráVca"
    limpio = re.sub(r'^\([a-z]\)\s*', '', str(cadena_raw), flags=re.IGNORECASE)
    match = re.split(r'Cerrado|Transacciones|\d{4}-\d{2}-\d{2}', limpio, flags=re.IGNORECASE)
    if match and match[0].strip():
        limpio = match[0].strip()
    return limpio if limpio else "Colaborador BráVca"

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

        status, messages = mail.search(None, '(UNSEEN)') # Opcional: busca no leídos, o usa 'ALL' si prefieres revisar histórico
        if status != "OK":
            status, messages = mail.search(None, "ALL")

        email_ids = messages[0].split()
        email_ids = email_ids[-40:] # Analizamos los últimos correos más relevantes

        cierres_procesados = 0

        for e_id in email_ids:
            res, msg_data = mail.fetch(e_id, "(RFC822)")
            if res != "OK":
                continue

            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    
                    subject_header = decode_header(msg["Subject"])[0] if msg["Subject"] else ("", "utf-8")
                    subject = subject_header[0]
                    if isinstance(subject, bytes):
                        subject = subject.decode(subject_header[1] or "utf-8", errors="ignore")

                    pdf_text = ""
                    tiene_pdf = False

                    for part in msg.walk():
                        content_disposition = str(part.get("Content-Disposition"))
                        if HAS_PYPDF and "attachment" in content_disposition:
                            filename = part.get_filename()
                            if filename and filename.lower().endswith(".pdf"):
                                try:
                                    pdf_data = part.get_payload(decode=True)
                                    reader = pypdf.PdfReader(io.BytesIO(pdf_data))
                                    for page in reader.pages:
                                        t = page.extract_text()
                                        if t:
                                            pdf_text += t + "\n"
                                    tiene_pdf = True
                                except Exception:
                                    pass

                    # Si el correo contiene un PDF adjunto de cierre
                    if tiene_pdf and pdf_text.strip():
                        full_content = pdf_text + "\n" + subject

                        # Determinar Tienda de forma estricta
                        content_lower = full_content.lower()
                        if "extremo" in content_lower or "monteverde extremo" in content_lower:
                            negocio = "Bravca Extremo"
                        else:
                            negocio = "Bravca Souvenir"

                        # Extraer Fecha Operativa exacta del PDF
                        match_fecha = re.search(r"Día operativo\s*[:\-]?\s*(\d{4}-\d{2}-\d{2})", full_content)
                        if not match_fecha:
                            match_fecha = re.search(r"(2026-\d{2}-\d{2})", full_content)
                        
                        fecha_str = match_fecha.group(1) if match_fecha else None
                        if not fecha_str:
                            continue

                        fecha_completa = f"{fecha_str} 18:00"

                        # Extraer Cajero limpio
                        match_cajero = re.search(r"Cajero\s*[:\-]?\s*([^\n]+)", full_content)
                        cajero_raw = match_cajero.group(1).strip() if match_cajero else subject
                        cajero = limpiar_nombre_cajero(cajero_raw)

                        # Extracción precisa de montos desde las líneas estructuradas del PDF
                        def extraer_monto_pdf(patron):
                            m = re.search(patron, full_content, re.IGNORECASE)
                            if m:
                                val_str = m.group(1).replace(",", "").strip()
                                try:
                                    return float(val_str)
                                except ValueError:
                                    return 0.0
                            return 0.0

                        total_ventas = extraer_monto_pdf(r"Total de ventas\s*[₡]?\s*([\d,]+\.\d{2})")
                        if total_ventas == 0.0:
                            total_ventas = extraer_monto_pdf(r"Total dinero físico\s*[₡]?\s*([\d,]+\.\d{2})")

                        tarjeta_colones = extraer_monto_pdf(r"Tarjeta\s*[₡]?\s*([\d,]+\.\d{2})")
                        if tarjeta_colones == 0.0:
                            tarjeta_colones = extraer_monto_pdf(r"Cierre de tarjetas[^\d]*([\d,]+\.\d{2})")

                        efectivo_colones = extraer_monto_pdf(r"Efectivo cobrado\s*[₡]?\s*([\d,]+\.\d{2})")
                        if efectivo_colones == 0.0:
                            efectivo_colones = extraer_monto_pdf(r"Conteo de efectivo[^\d]*([\d,]+\.\d{2})")

                        # Si los subtotales no vinieron desglosados pero sí el total
                        if total_ventas > 0.0 and tarjeta_colones == 0.0 and efectivo_colones == 0.0:
                            efectivo_colones = total_ventas

                        colones_final = tarjeta_colones + efectivo_colones
                        if colones_final == 0.0:
                            colones_final = total_ventas

                        # Evitar duplicados: Borrar cualquier registro previo para esa misma fecha y tienda antes de insertar el correcto
                        cursor.execute("DELETE FROM cierres WHERE fecha LIKE ? AND negocio = ? AND cajero != 'Histórico Simplifica2'", (f"{fecha_str}%", negocio))
                        
                        cursor.execute("""
                            INSERT INTO cierres (fecha, cajero, negocio, colones, dolares, tarjeta_colones, efectivo_colones, estado)
                            VALUES (?, ?, ?, ?, 0.0, ?, ?, ?)
                        """, (fecha_completa, cajero, negocio, colones_final, tarjeta_colones, efectivo_colones, "Sincronizado PDF Gmail"))
                        
                        conn.commit()
                        cierres_procesados += 1

        mail.logout()
        conn.close()
        return True, f"Sincronización automática exitosa. Se procesaron {cierres_procesados} cierres por PDF desde Gmail."

    except Exception as e:
        conn.close()
        return False, f"Error de conexión IMAP: {str(e)}"
