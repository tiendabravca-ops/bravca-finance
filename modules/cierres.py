import sqlite3
import pandas as pd
import streamlit as st
import email_reader
from pypdf import PdfReader
import re
from datetime import datetime

def guardar_cierre_manual(datos):
    """Inserta o actualiza un cierre procesado manualmente en la base de datos db_cierres.db"""
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
    
    # Verificar si ya existe un registro para esa fecha y negocio
    cursor.execute("SELECT id FROM cierres WHERE fecha = ? AND negocio = ?", (datos['fecha'], datos['negocio']))
    existente = cursor.fetchone()
    
    if existente:
        cursor.execute("""
            UPDATE cierres 
            SET cajero = ?, colones = ?, dolares = ?, tarjeta_colones = ?, efectivo_colones = ?, estado = ?
            WHERE id = ?
        """, (datos['cajero'], datos['colones'], datos['dolares'], datos['tarjeta_colones'], datos['efectivo_colones'], datos['estado'], existente[0]))
    else:
        cursor.execute("""
            INSERT INTO cierres (fecha, cajero, negocio, colones, dolares, tarjeta_colones, efectivo_colones, estado)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (datos['fecha'], datos['cajero'], datos['negocio'], datos['colones'], datos['dolares'], datos['tarjeta_colones'], datos['efectivo_colones'], datos['estado']))
        
    conn.commit()
    conn.close()

def procesar_pdf_manual(archivo_subido, tienda_seleccionada_manual):
    """Extrae los campos clave del PDF usando pypdf"""
    texto = ""
    try:
        lector = PdfReader(archivo_subido)
        for pagina in lector.pages:
            t = pagina.extract_text()
            if t:
                texto += t + "\n"
    except Exception as e:
        return False, f"Error al leer el PDF: {e}"

    if not texto.strip():
        return False, "El archivo PDF está vacío o no se pudo extraer texto."

    negocio = tienda_seleccionada_manual

    # Extraer Fecha Operativa (Ej: 2026-10-17)
    match_fecha = re.search(r"Día operativo\s*[:\-]?\s*(\d{4}-\d{2}-\d{2})", texto)
    fecha_str = match_fecha.group(1) if match_fecha else datetime.now().strftime("%Y-%m-%d")

    # Extraer Cajero
    match_cajero = re.search(r"Cajero\s*[:\-]?\s*([^\n]+)", texto)
    cajero = match_cajero.group(1).strip() if match_cajero else "Desconocido"

    def extraer_monto(patron):
        m = re.search(patron, texto)
        if m:
            val_str = m.group(1).replace(",", "").strip()
            try:
                return float(val_str)
            except ValueError:
                return 0.0
        return 0.0

    # Capturar rubros exactos del PDF
    total_ventas = extraer_monto(r"Total de ventas\s*[₡]?\s*([\d,]+\.\d{2})")
    if total_ventas == 0.0:
        total_ventas = extraer_monto(r"Total dinero físico\s*[₡]?\s*([\d,]+\.\d{2})")

    tarjeta_colones = extraer_monto(r"Tarjeta\s*[₡]?\s*([\d,]+\.\d{2})")
    if tarjeta_colones == 0.0:
        tarjeta_colones = extraer_monto(r"Cierre de tarjetas[^\d]*([\d,]+\.\d{2})")

    efectivo_colones = extraer_monto(r"Efectivo cobrado\s*[₡]?\s*([\d,]+\.\d{2})")
    if efectivo_colones == 0.0:
        efectivo_colones = extraer_monto(r"Conteo de efectivo[^\d]*([\d,]+\.\d{2})")

    datos_registro = {
        "fecha": fecha_str,
        "cajero": cajero,
        "negocio": negocio,
        "colones": total_ventas,
        "dolares": 0.0,
        "tarjeta_colones": tarjeta_colones,
        "efectivo_colones": efectivo_colones,
        "estado": "Registrado Manual"
    }

    guardar_cierre_manual(datos_registro)
    return True, f"Cierre de '{negocio}' para el día {fecha_str} procesado y guardado con éxito (Total: ₡ {total_ventas:,.2f})."

def cargar_datos_cierres():
    conn = sqlite3.connect("db_cierres.db")
    cursor = conn.cursor()
    
    cursor.execute("PRAGMA table_info(cierres)")
    columns = [column[1] for column in cursor.fetchall()]
    
    if "tarjeta_colones" not in columns or "efectivo_colones" not in columns:
        cursor.execute("DROP TABLE IF EXISTS cierres")
        conn.commit()

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
    
    df = pd.read_sql_query("SELECT id, fecha, cajero, negocio, tarjeta_colones, efectivo_colones, colones, dolares, estado FROM cierres ORDER BY fecha DESC", conn)
    conn.close()
    return df

def run():
    st.markdown("##### 🧾 CENTRO DE CONTROL DE CIERRES DE CAJA")
    st.caption("Monitoreo automatizado y consolidado diario de cierres desde Gmail para bráVca Souvenir y Extremo.")

    # Botón de Sincronización
    st.markdown("---")
    st.markdown("##### 🔄 Sincronización Automática de Correos")
    
    if st.button("📥 Sincronizar Cierres desde Gmail Ahora"):
        with st.spinner("Conectando con tiendabravca@gmail.com para actualizar cierres y desgloses..."):
            try:
                exito, mensaje = email_reader.sincronizar_cierres_gmail()
                if exito:
                    st.success(mensaje)
                    st.rerun()
                else:
                    st.error(f"No se pudo sincronizar: {mensaje}")
            except Exception as e:
                st.error(f"Error inesperado: {e}")
    st.markdown("---")

    # Pestañas de gestión
    pestana1, pestana2 = st.tabs(["📊 Histórico y Reportes", "📥 Procesar Nuevo PDF de Cierre"])

    with pestana1:
        st.markdown("##### 📈 Consolidado Reciente por Día")
        
        df_cierres = cargar_datos_cierres()
        
        if not df_cierres.empty:
            df_cierres['fecha_dt'] = pd.to_datetime(df_cierres['fecha'], errors='coerce').dt.date

            col_f1, col_f2 = st.columns(2)
            
            with col_f1:
                tiendas_disponibles = ["Todas las tiendas"] + list(df_cierres['negocio'].dropna().unique())
                tienda_seleccionada = st.selectbox("🏬 Filtrar por Tienda:", tiendas_disponibles)

            with col_f2:
                tipo_filtro_fecha = st.radio("📅 Filtrar por Fechas:", ["Todo el histórico", "Rango específico"], horizontal=True)

            df_filtrado = df_cierres.copy()

            if tienda_seleccionada != "Todas las tiendas":
                df_filtrado = df_filtrado[df_filtrado['negocio'] == tienda_seleccionada]

            if tipo_filtro_fecha == "Rango específico":
                fechas_validas = df_cierres['fecha_dt'].dropna()
                if not fechas_validas.empty:
                    min_f = fechas_validas.min()
                    max_f = fechas_validas.max()
                else:
                    min_f = datetime.now().date()
                    max_f = datetime.now().date()
                
                rango_fechas = st.date_input(
                    "Selecciona el tramo de fechas:",
                    value=(min_f, max_f),
                    min_value=min_f,
                    max_value=max_f
                )
                
                if isinstance(rango_fechas, tuple) and len(rango_fechas) == 2:
                    f_inicio, f_fin = rango_fechas
                    df_filtrado = df_filtrado[(df_filtrado['fecha_dt'] >= f_inicio) & (df_filtrado['fecha_dt'] <= f_fin)]

            df_mostrar = df_filtrado.drop(columns=['fecha_dt'])

            st.dataframe(df_mostrar, use_container_width=True)
            
            total_tarjeta = df_filtrado['tarjeta_colones'].sum()
            total_efectivo = df_filtrado['efectivo_colones'].sum()
            total_general = df_filtrado['colones'].sum()
            total_dolares = df_filtrado['dolares'].sum()
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(label="Total Tarjetas (CRC)", value=f"₡ {total_tarjeta:,.2f}")
            with col2:
                st.metric(label="Total Efectivo (CRC)", value=f"₡ {total_efectivo:,.2f}")
            with col3:
                st.metric(label="Venta Total (CRC)", value=f"₡ {total_general:,.2f}")
                
            if total_dolares > 0:
                st.metric(label="Total Ventas (USD)", value=f"$ {total_dolares:,.2f}")
        else:
            st.info("No hay cierres registrados todavía. Presiona el botón de **Sincronizar Cierres desde Gmail Ahora** o sube un PDF en la pestaña contigua.")

    with pestana2:
        st.markdown("##### 📥 Subir Cierre de Caja en PDF Manualmente")
        st.info("Selecciona la tienda correspondiente, sube tu archivo PDF de Simplifica2 y el sistema registrará los datos al instante.")
        
        tienda_manual = st.selectbox("🏬 Seleccionar Tienda Correspondiente:", ["Bravca Souvenir", "Bravca Extremo", "Santa Elena"])
        archivo_pdf = st.file_uploader("Seleccionar archivo PDF de Simplifica2", type=["pdf"])

        if archivo_pdf is not None:
            st.success(f"¡Archivo '{archivo_pdf.name}' cargado con éxito!")
            if st.button("⚙️ Procesar y Registrar Cierre"):
                with st.spinner("Leyendo y extrayendo datos del PDF..."):
                    exito, mensaje = procesar_pdf_manual(archivo_pdf, tienda_manual)
                    if exito:
                        st.success(mensaje)
                        st.rerun()
                    else:
                        st.error(f"Error procesando el PDF: {mensaje}")
