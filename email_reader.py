import imaplib
import email
from email.header import decode_header
import re
import sqlite3

def conectar_gmail(correo, contraseña_app):
    # Conexión IMAP a Gmail
    mail = imaplib.IMAP4_SSL("imap.gmail.com")
    mail.login(correo, contraseña_app)
    return mail

def extraer_datos_tiquete(cuerpo_texto):
    """
    Función de extracción (Regex) optimizada para la pantalla/tiquete de Simplifica2.
    """
    datos = {}
    
    # Extraer tipo de cambio
    tc_match = re.search(r'Tipo de cambio.*?(\d+\.\d+|\d+)', cuerpo_texto)
    datos['tipo_cambio'] = float(tc_match.group(1)) if tc_match else 0.0

    # Extraer cobro en tarjeta y efectivo
    tarjeta_match = re.search(r'Tarjeta.*?₡\s*([\d,]+\.?\d*)', cuerpo_texto)
    efectivo_match = re.search(r'Efectivo cobrado.*?₡\s*([\d,]+\.?\d*)', cuerpo_texto)
    
    datos['tarjeta_colones'] = float(tarjeta_match.group(1).replace(',', '')) if tarjeta_match else 0.0
    datos['efectivo_colones'] = float(efectivo_match.group(1).replace(',', '')) if efectivo_match else 0.0

    return datos

# Para probar la lectura manualmente