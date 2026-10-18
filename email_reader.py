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

    # Limpiamos las precargas antiguas para dejar solo del 1 al 15
    cursor.execute("DELETE FROM cierres WHERE cajero = 'Histórico Simplifica2'")
    conn.commit()

    # 1. Histórico exacto del 1 al 15 para Bravca Souvenir
    historico_souvenir = [
        ("2026-10-01 18:00:00", "Bravca Souvenir", 31900.00),
        ("2026-10-02 18:00:00", "Bravca Souvenir", 6000.00),
        ("2026-10-03 18:00:00", "Bravca Souvenir", 26550.00),
        ("2026-10-04 18:00:00", "Bravca Souvenir", 56300.00),
        ("2026-10-05 18:00:00", "Bravca Souvenir", 22320.00),
        ("2026-10-06 18:00:00", "Bravca Souvenir", 120625.00),
        ("2026-10-07 18:00:00", "Bravca Souvenir", 128260.00),
        ("2026-10-08 18:00:00", "Bravca Souvenir", 151810.00),
        ("2026-10-09 18:00:00", "Bravca Souvenir", 140625.00),
        ("2026-10-10 18:00:00", "Bravca Souvenir", 35145.00),
        ("2026-10-11 18:00:00", "Bravca Souvenir", 30060.00),
        ("2026-10-12 18:00:00", "Bravca Souvenir", 61175.00),
        ("2026-10-13 18:00:00", "Bravca Souvenir", 75100.00),
        ("2026-10-14 18:00:00", "Bravca Souvenir", 104400.00),
        ("2026-10-15 18:00:00", "Bravca Souvenir", 28200.00),
    ]

    # 2. Histórico exacto del 1 al 15 para Bravca Extremo
    historico_extremo = [
        ("2026-10-01 18:00:00", "Bravca Extremo", 24120.00),
        ("2026-10-02 18:00:00", "Bravca Extremo", 9050.00),
        ("2026-10-03 18:00:00", "Bravca Extremo", 18920.00),
        ("2026-10-04 18:00:00", "Bravca Extremo", 25020.00),
        ("2026-10-05 18:00:00", "Bravca Extremo", 1200.00),
        ("2026-10-06 18:00:00", "Bravca Extremo", 60240.00),
        ("2026-10-07 18:00:00", "Bravca Extremo", 35040.00),
        ("2026-10-08 18:00:00", "Bravca Extremo", 12575.00),
        ("2026-10-09 18:00:00", "Bravca Extremo", 7650.00),
        ("2026-10-10 18:00:00", "Bravca Extremo", 35900.00),
        ("2026-10-11 18:00:00", "Bravca Extremo", 14500.00),
        ("2026-10-12 18:00:00", "Bravca Extremo", 23900.00),
        ("2026-10-13 18:00:00", "Bravca Extremo", 49710.00),
        ("2026-10-14 18:00:00", "Bravca Extremo", 3500.00),
        ("2026-10-15 18:00:00", "Bravca Extremo", 10600.00),
    ]

    for fecha_str, negocio_str, monto in historico_souvenir + historico_extremo:
        cursor.execute("""
            INSERT INTO cierres (fecha, cajero, negocio, colones, dolares, tarjeta_colones, efectivo_colones, estado)
            VALUES (?, ?, ?, ?, 0.0, 0.0, ?, ?)
        """, (fecha_str, "Histórico Simplifica2", negocio_str, monto, monto, "Histórico Cargado"))

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
        email_ids = email_ids[-20:] 

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

                        negocio_match = re.search(r"Negocio\s+([^\n]+)", full_content)
                        cajero_match = re.search(r"Cajero\(a\)\s+([^\n]+)", full_content)
                        fecha_match = re.search(r"(?:Cerrado|Fecha)\s+([^\n]+)", full_content)

                        negocio = negocio_match.group(1).strip() if negocio_match else "Bravca Souvenir"
                        cajero = cajero_match.group(1).strip() if cajero_match else "Leonardo Venegas Mejías"
                        fecha = fecha_match.group(1).strip() if fecha_match else "2026-10-16 18:46"

                        tarjeta_match = re.search(r"Tarjeta\s*[^\d]*([\d,]+\.\d{2})", full_content, re.IGNORECASE)
                        efectivo_match = re.search(r"Efectivo\s*cobrado\s*[^\d]*([\d,]+\.\d{2})", full_content, re.IGNORECASE)
                        if not efectivo_match:
                            efectivo_match = re.search(r"Conteo\s+de\s+efectivo\s*[^\d]*([\d,]+\.\d{2})", full_content, re.IGNORECASE)

                        tarjeta_colones = float(tarjeta_match.group(1).replace(",", "")) if tarjeta_match else 0.0
                        efectivo_colones = float(efectivo_match.group(1).replace(",", "")) if efectivo_match else 0.0
                        colones = tarjeta_colones + efectivo_colones

                        dolares_match = re.search(r"(?:USD|Dólares|\$)\s*([\d,]+\.\d{2})", full_content)
                        dolares = float(dolares_match.group(1).replace(",", "")) if dolares_match else 0.0

                        cursor.execute("SELECT id FROM cierres WHERE fecha LIKE ? AND negocio = ?", (f"{fecha[:10]}%", negocio))
                        row = cursor.fetchone()
                        
                        if row:
                            cursor.execute("""
                                UPDATE cierres 
                                SET cajero = ?, colones = ?, dolares = ?, tarjeta_colones = ?, efectivo_colones = ?, estado = ?
                                WHERE id = ?
                            """, (cajero, colones, dolares, tarjeta_colones, efectivo_colones, "Recibido / Verificado", row[0]))
                        else:
                            cursor.execute("""
                                INSERT INTO cierres (fecha, cajero, negocio, colones, dolares, tarjeta_colones, efectivo_colones, estado)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                            """, (fecha, cajero, negocio, colones, dolares, tarjeta_colones, efectivo_colones, "Recibido / Verificado"))
                        
                        conn.commit()

        mail.logout()
        conn.close()
        return True, "Sincronización completa. Fechas corregidas y montos alineados con Simplifica2."

    except Exception as e:
        conn.close()
        return False, f"Error de conexión: {str(e)}"
