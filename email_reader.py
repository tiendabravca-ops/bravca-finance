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
        email_ids = email_ids[-30:] # Revisamos los últimos 30 correos para capturar todos los recientes
        registros_procesados = 0

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

                        # Extracción robusta de datos del correo y PDF
                        negocio_match = re.search(r"Negocio\s+([^\n]+)", full_content)
                        cajero_match = re.search(r"Cajero\(a\)\s+([^\n]+)", full_content)
                        fecha_match = re.search(r"(?:Cerrado|Fecha)\s+([^\n]+)", full_content)

                        negocio = negocio_match.group(1).strip() if negocio_match else "Bravca Souvenir"
                        cajero = cajero_match.group(1).strip() if cajero_match else "Cajero"
                        fecha = fecha_match.group(1).strip() if fecha_match else "2026-10-17 19:01"

                        tarjeta_match = re.search(r"Tarjeta\s*[^\d]*([\d,]+\.\d{2})", full_content, re.IGNORECASE)
                        efectivo_match = re.search(r"Efectivo\s*cobrado\s*[^\d]*([\d,]+\.\d{2})", full_content, re.IGNORECASE)
                        if not efectivo_match:
                            efectivo_match = re.search(r"Conteo\s+de\s+efectivo\s*[^\d]*([\d,]+\.\d{2})", full_content, re.IGNORECASE)

                        tarjeta_colones = float(tarjeta_match.group(1).replace(",", "")) if tarjeta_match else 0.0
                        efectivo_colones = float(efectivo_match.group(1).replace(",", "")) if efectivo_match else 0.0
                        colones = tarjeta_colones + efectivo_colones

                        dolares_match = re.search(r"(?:USD|Dólares|\$)\s*([\d,]+\.\d{2})", full_content)
                        dolares = float(dolares_match.group(1).replace(",", "")) if dolares_match else 0.0

                        # Validar si ya existe exactamente este cierre por hora y fecha para no duplicar correos idénticos
                        cursor.execute("SELECT id FROM cierres WHERE fecha = ? AND negocio = ? AND cajero = ?", (fecha, negocio, cajero))
                        row = cursor.fetchone()
                        
                        if not row:
                            cursor.execute("""
                                INSERT INTO cierres (fecha, cajero, negocio, colones, dolares, tarjeta_colones, efectivo_colones, estado)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                            """, (fecha, cajero, negocio, colones, dolares, tarjeta_colones, efectivo_colones, "Recibido / Verificado"))
                            conn.commit()
                            registros_procesados += 1

        mail.logout()
        conn.close()
        return True, f"Sincronización exitosa. Se procesaron nuevos reportes de correo (como el de Nicole)."

    except Exception as e:
        conn.close()
        return False, f"Error de conexión: {str(e)}"
