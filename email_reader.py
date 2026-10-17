import email
from email.header import decode_header
import imaplib
import re
import sqlite3


def conectar_gmail(correo, contraseña_app):
  # Conexión IMAP a Gmail
  mail = imaplib.IMAP4_SSL("imap.gmail.com")
  mail.login(correo, contraseña_app)
  return mail


def extraer_datos_tiquete(cuerpo_texto):
  """Función de extracción (Regex) optimizada para el tiquete de cierres."""
  datos = {}

  # Extraer tipo de cambio
  tc_match = re.search(r"Tipo de cambio.*?(\d+\.\d+|\d+)", cuerpo_texto)
  datos["tipo_cambio"] = float(tc_match.group(1)) if tc_match else 0.0

  # Extraer cobro en tarjeta y efectivo
  tarjeta_match = re.search(r"Tarjeta.*?₡\s*([\d,]+\.?\d*)", cuerpo_texto)
  efectivo_match = re.search(r"Efectivo cobrado.*?₡\s*([\d,]+\.?\d*)", cuerpo_texto)

  datos["tarjeta_colones"] = (
      float(tarjeta_match.group(1).replace(",", "")) if tarjeta_match else 0.0
  )
  datos["efectivo_colones"] = (
      float(efectivo_match.group(1).replace(",", "")) if efectivo_match else 0.0
  )

  return datos


def sincronizar_cierres_correo(correo, contraseña_app):
  mail = conectar_gmail(correo, contraseña_app)
  mail.select("inbox")

  # Buscar todos los correos en la bandeja de entrada
  status, messages = mail.search(None, "ALL")

  conexion = sqlite3.connect("db_cierres.db")
  cursor = conexion.cursor()

  # Crear la tabla de cierres si no existe
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS cierres (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT,
            tipo_cambio REAL,
            tarjeta_colones REAL,
            efectivo_colones REAL
        )
    """)

  # Tomar los últimos 15 correos para procesar
  id_list = messages[0].split()
  ultimos = id_list[-15:] if len(id_list) >= 15 else id_list

  for num in ultimos:
    res, msg_data = mail.fetch(num, "(RFC822)")
    for response_part in msg_data:
      if isinstance(response_part, tuple):
        msg = email.message_from_bytes(response_part[1])
        cuerpo = ""
        if msg.is_multipart():
          for part in msg.walk():
            if part.get_content_type() == "text/plain":
              cuerpo = part.get_payload(decode=True).decode(
                  "utf-8", errors="ignore"
              )
        else:
          cuerpo = msg.get_payload(decode=True).decode("utf-8", errors="ignore")

        # Extraer los datos mediante la expresión regular
        datos = extraer_datos_tiquete(cuerpo)

        # Si encontró montos válidos, los guarda en la base de datos
        if datos.get("tarjeta_colones", 0) > 0 or datos.get(
            "efectivo_colones", 0
        ) > 0:
          cursor.execute(
              """
                    INSERT INTO cierres (fecha, tipo_cambio, tarjeta_colones, efectivo_colones)
                    VALUES (datetime('now'), ?, ?, ?)
                """,
              (
                  datos.get("tipo_cambio", 0.0),
                  datos.get("tarjeta_colones", 0.0),
                  datos.get("efectivo_colones", 0.0),
              ),
          )

  conexion.commit()
  conexion.close()
  mail.logout()
