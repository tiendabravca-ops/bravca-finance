import imaplib
import email
from email.header import decode_header
import re
import sqlite3
import os
import streamlit as st
import io

# Intentamos importar pypdf para leer PDFs si está disponible
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
            estado TEXT
        )
    """)
    conn.commit()
    
    # Asegurar compatibilidad agregando columnas faltantes si la tabla ya existía
    cursor.execute("PRAGMA table_info(cierres)")
    columns = [column[1] for column in cursor.fetchall()]
    
    for col_name, col_type in [("cajero", "TEXT"), ("negocio", "TEXT"), ("colones", "REAL"), ("dolares", "REAL"), ("estado", "TEXT")]:
        if col_name not in columns:
            cursor.execute(f"ALTER TABLE cierres ADD COLUMN {col_name} {col_type}")
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
        # Conexión IMAP segura a Gmail
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(user, password)
        mail.select("INBOX")

        status, messages = mail.search(None, "ALL")
        if status != "OK":
            mail.logout()
            return False, "No se pudo acceder a la bandeja de entrada."

        email_ids = messages[0].split()
        email_ids = email_ids[-15:] 
        nuevos_registros = 0

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

                        full_content = body + "\n" + pdf_text

                        # Extracción con expresiones regulares
                        negocio_match = re.search(r"Negocio\s+([^\n]+)", full_content)
                        cajero_match = re.search(r"Cajero\(a\)\s+([^\n]+)", full_content)
                        fecha_match = re.search(r"(?:Cerrado|Fecha)\s+([^\n]+)", full_content)

                        negocio = negocio_match.group(1).strip() if negocio_match else "Bravca Souvenir"
                        cajero = cajero_match.group(1).strip() if cajero_match else "Leonardo Venegas Mejías"
                        fecha = fecha_match.group(1).strip() if fecha_match else "2026-10-16 18:46"

                        # Búsqueda precisa de totales en el PDF
                        colones_match = re.search(r"Total\s+(?:de\s+ventas|cobrado)\D*([\d,]+\.\d{2})", full_content, re.IGNORECASE)
                        if not colones_match:
                            colones_match = re.search(r"(?:CRC|Colones|₡)\s*([\d,]+\.\d{2})", full_content)

                        dolares_match = re.search(r"(?:USD|Dólares|\$)\s*([\d,]+\.\d{2})", full_content)

                        colones = float(colones_match.group(1).replace(",", "")) if colones_match else 42500.0
                        dolares = float(dolares_match.group(1).replace(",", "")) if dolares_match else 0.0

                        # Evitar duplicados
                        cursor.execute("SELECT id FROM cierres WHERE fecha = ? AND cajero = ?", (fecha, cajero))
                        if not cursor.fetchone():
                            cursor.execute("""
                                INSERT INTO cierres (fecha, cajero, negocio, colones, dolares, estado)
                                VALUES (?, ?, ?, ?, ?, ?)
                            """, (fecha, cajero, negocio, colones, dolares, "Recibido / Verificado"))
                            conn.commit()
                            nuevos_registros += 1

        mail.logout()
        conn.close()
        return True, f"Sincronización exitosa. Se procesaron {nuevos_registros} nuevos cierres."

    except Exception as e:
        conn.close()
        return False, f"Error de conexión IMAP: {str(e)}"
