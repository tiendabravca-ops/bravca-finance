import sqlite3
import pandas as pd
import streamlit as st
import email_reader
from datetime import datetime, date

def run():
    st.markdown("##### 🧾 CENTRO DE CONTROL DE CIERRES DE CAJA")
    st.caption("Consolidado y filtrado avanzado por tienda y tramos de fechas.")

    # Botón de Sincronización
    st.markdown("---")
    if st.button("📥 Sincronizar Cierres desde Gmail Ahora"):
        with st.spinner("Actualizando cierres..."):
            try:
                email_reader.sincronizar_cierres_gmail()
                st.success("¡Sincronización completada!")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")
    st.markdown("---")

    conn = sqlite3.connect("db_cierres.db")
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
        # Convertir fecha a tipo datetime para los filtros de tramos
        df['fecha_dt'] = pd.to_datetime(df['fecha']).dt.date

        # --- FILTROS EN COLUMNAS ---
        col_f1, col_f2 = st.columns(2)
        
        with col_f1:
            # 1. Filtro por Tienda
            tiendas_disponibles = ["Todas las tiendas"] + list(df['negocio'].dropna().unique())
            tienda_seleccionada = st.selectbox("🏬 Filtrar por Tienda:", tiendas_disponibles)

        with col_f2:
            # 2. Filtro por tramo de fechas
            tipo_filtro_fecha = st.radio("📅 Ver por:", ["Todo el histórico", "Rango de fechas específico"], horizontal=True)

        df_filtrado = df.copy()

        # Aplicar filtro de tienda
        if tienda_seleccionada != "Todas las tiendas":
            df_filtrado = df_filtrado[df_filtrado['negocio'] == tienda_seleccionada]

        # Aplicar filtro de tramo de fechas
        if tipo_filtro_fecha == "Rango de fechas específico":
            min_f = df['fecha_dt'].min()
            max_f = df['fecha_dt'].max()
            
            rango_fechas = st.date_input(
                "Selecciona el tramo de fechas:",
                value=(min_f, max_f),
                min_value=min_f,
                max_value=max_f
            )
            
            if isinstance(rango_fechas, tuple) and len(rango_fechas) == 2:
                f_inicio, f_fin = rango_fechas
                df_filtrado = df_filtrado[(df_filtrado['fecha_dt'] >= f_inicio) & (df_filtrado['fecha_dt'] <= f_fin)]

        # Limpiar columna temporal para la vista
        df_mostrar = df_filtrado.drop(columns=['fecha_dt'])

        st.markdown(f"##### 📊 Resultados para: **{tienda_seleccionada}**")
        st.dataframe(df_mostrar, use_container_width=True)

        # --- MÉTRICAS SEGÚN EL FILTRADO ---
        t_tarjeta = df_filtrado['tarjeta_colones'].sum()
        t_efectivo = df_filtrado['efectivo_colones'].sum()
        t_general = df_filtrado['colones'].sum()

        m1, m2, m3 = st.columns(3)
        with m1:
            st.metric("Total Tarjetas (CRC)", f"₡ {t_tarjeta:,.2f}")
        with m2:
            st.metric("Total Efectivo (CRC)", f"₡ {t_efectivo:,.2f}")
        with m3:
            st.metric("Venta Total (CRC)", f"₡ {t_general:,.2f}")

    else:
        st.info("No hay registros en la base de datos todavía.")
