import sqlite3
import pandas as pd
import streamlit as st
import datetime

def run():
    st.markdown("##### 🧾 CENTRO DE CONTROL DE CIERRES DE CAJA")
    st.caption("Consolidado y filtrado avanzado por tienda y tramos de fechas.")

    # Botón de Sincronización interna
    st.markdown("---")
    if st.button("📥 Sincronizar y Actualizar Base de Datos"):
        with st.spinner("Actualizando registros y base de datos..."):
            try:
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
                st.success("¡Base de datos sincronizada correctamente!")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")
    st.markdown("---")

    conn = sqlite3.connect("db_cierres.db")
    
    # Asegurar tabla por seguridad
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

    df = pd.read_sql_query("""
        SELECT 
            id,
            fecha,
            cajero,
            negocio,
            tarjeta_colones,
            efectivo_colones,
            colones,
            dolares,
            estado
        FROM cierres 
        ORDER BY fecha DESC
    """, conn)
    conn.close()

    if not df.empty:
        # Convertir campo de fecha para permitir filtrado por tramo
        df['fecha_dt'] = pd.to_datetime(df['fecha'], errors='coerce').dt.date

        # --- SECCIÓN DE FILTROS ---
        col_f1, col_f2 = st.columns(2)
        
        with col_f1:
            tiendas_disponibles = ["Todas las tiendas"] + list(df['negocio'].dropna().unique())
            tienda_seleccionada = st.selectbox("🏬 Filtrar por Tienda:", tiendas_disponibles)

        with col_f2:
            tipo_filtro_fecha = st.radio("📅 Filtrar por Fechas:", ["Todo el histórico", "Rango de fechas específico"], horizontal=True)

        df_filtrado = df.copy()

        # Aplicar filtro por Tienda
        if tienda_seleccionada != "Todas las tiendas":
            df_filtrado = df_filtrado[df_filtrado['negocio'] == tienda_seleccionada]

        # Aplicar filtro por Rango/Tramo de Fechas
        if tipo_filtro_fecha == "Rango de fechas específico":
            min_f = df['fecha_dt'].min()
            max_f = df['fecha_dt'].max()
            if pd.isna(min_f):
                min_f = datetime.date.today()
            if pd.isna(max_f):
                max_f = datetime.date.today()
            
            rango_fechas = st.date_input(
                "Selecciona el tramo de fechas:",
                value=(min_f, max_f),
                min_value=min_f,
                max_value=max_f
            )
            
            if isinstance(rango_fechas, tuple) and len(rango_fechas) == 2:
                f_inicio, f_fin = rango_fechas
                df_filtrado = df_filtrado[(df_filtrado['fecha_dt'] >= f_inicio) & (df_filtrado['fecha_dt'] <= f_fin)]

        # Eliminar columna temporal de la vista
        df_mostrar = df_filtrado.drop(columns=['fecha_dt'])

        st.markdown(f"##### 📊 Resumen para: **{tienda_seleccionada}**")
        st.dataframe(df_mostrar, use_container_width=True)

        # --- MÉTRICAS RECALCULADAS ---
        t_tarjetas = df_filtrado['tarjeta_colones'].sum()
        t_efectivo = df_filtrado['efectivo_colones'].sum()
        t_general = df_filtrado['colones'].sum()

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Tarjetas (CRC)", f"₡ {t_tarjetas:,.2f}")
        with col2:
            st.metric("Total Efectivo (CRC)", f"₡ {t_efectivo:,.2f}")
        with col3:
            st.metric("Venta General (CRC)", f"₡ {t_general:,.2f}")

    else:
        st.info("No hay cierres registrados todavía.")
