import sqlite3
import pandas as pd
import streamlit as st
from datetime import datetime

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

def guardar_cierre_api(datos):
    """Guarda o actualiza cierres que provienen directamente de la pantalla de Simplifica2"""
    init_db()
    conn = sqlite3.connect("db_cierres.db")
    cursor = conn.cursor()
    
    fecha_base = datos['fecha'][:10]
    cursor.execute("SELECT id FROM cierres WHERE fecha LIKE ? AND negocio = ?", (f"{fecha_base}%", datos['negocio']))
    existente = cursor.fetchone()
    
    if existente:
        cursor.execute("""
            UPDATE cierres 
            SET cajero = ?, colones = ?, dolares = ?, tarjeta_colones = ?, efectivo_colones = ?, estado = ?
            WHERE id = ?
        """, (datos['cajero'], datos['colones'], datos['dolares'], datos['tarjeta_colones'], datos['efectivo_colones'], "Sincronizado Simplifica2", existente[0]))
    else:
        cursor.execute("""
            INSERT INTO cierres (fecha, cajero, negocio, colones, dolares, tarjeta_colones, efectivo_colones, estado)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (datos['fecha'], datos['cajero'], datos['negocio'], datos['colones'], datos['dolares'], datos['tarjeta_colones'], datos['efectivo_colones'], "Sincronizado Simplifica2"))
        
    conn.commit()
    conn.close()

def cargar_datos_cierres():
    init_db()
    conn = sqlite3.connect("db_cierres.db")
    df = pd.read_sql_query("SELECT id, fecha, cajero, negocio, tarjeta_colones, efectivo_colones, colones, dolares, estado FROM cierres ORDER BY fecha DESC", conn)
    conn.close()
    return df

def run():
    st.markdown("##### 🧾 CENTRO DE CONTROL DE CIERRES DE CAJA")
    st.caption("Monitoreo en tiempo real sincronizado desde Simplifica2 • BRÁVCA")

    # Detección de sincronización entrante desde el navegador
    query_params = st.query_params
    if "action" in query_params and query_params["action"] == "sync":
        try:
            negocio = query_params.get("negocio", "Bravca Souvenir")
            fecha = query_params.get("fecha", datetime.now().strftime("%Y-%m-%d 18:00"))
            cajero = query_params.get("cajero", "Karol Villegas Porras")
            tarjeta = float(query_params.get("tarjeta", 0.0))
            efectivo = float(query_params.get("efectivo", 0.0))
            total = float(query_params.get("total", tarjeta + efectivo))

            guardar_cierre_api({
                "fecha": fecha,
                "cajero": cajero,
                "negocio": negocio,
                "colones": total,
                "dolares": 0.0,
                "tarjeta_colones": tarjeta,
                "efectivo_colones": efectivo
            })
            st.success(f"¡Cierre de '{negocio}' para el día {fecha[:10]} recibido y sincronizado con éxito!")
            st.query_params.clear()
            st.rerun()
        except Exception as e:
            st.error(f"Error procesando sincronización: {e}")

    # Visualización de métricas y tabla
    st.markdown("---")
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
            min_f = fechas_validas.min() if not fechas_validas.empty else datetime.now().date()
            max_f = fechas_validas.max() if not fechas_validas.empty else datetime.now().date()
            
            rango_fechas = st.date_input("Selecciona el tramo de fechas:", value=(min_f, max_f), min_value=min_f, max_value=max_f)
            if isinstance(rango_fechas, tuple) and len(rango_fechas) == 2:
                f_inicio, f_fin = rango_fechas
                df_filtrado = df_filtrado[(df_filtrado['fecha_dt'] >= f_inicio) & (df_filtrado['fecha_dt'] <= f_fin)]

        df_mostrar = df_filtrado.drop(columns=['fecha_dt'])
        st.dataframe(df_mostrar, use_container_width=True)
        
        total_tarjeta = df_filtrado['tarjeta_colones'].sum()
        total_efectivo = df_filtrado['efectivo_colones'].sum()
        total_general = df_filtrado['colones'].sum()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(label="Total Tarjetas (CRC)", value=f"₡ {total_tarjeta:,.2f}")
        with col2:
            st.metric(label="Total Efectivo (CRC)", value=f"₡ {total_efectivo:,.2f}")
        with col3:
            st.metric(label="Venta Total (CRC)", value=f"₡ {total_general:,.2f}")
    else:
        st.info("No hay cierres registrados aún.")
