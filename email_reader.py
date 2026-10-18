import sqlite3
import pandas as pd
import streamlit as st
import email_reader

def run():
    st.markdown("##### 🧾 CENTRO DE CONTROL DE CIERRES DE CAJA")
    st.caption("Consolidado diario por fechas con desglose de tarjetas, efectivo y filtro por tienda.")

    # Botón de Sincronización
    st.markdown("---")
    if st.button("📥 Sincronizar Cierres desde Gmail Ahora"):
        with st.spinner("Conectando con Gmail para actualizar cierres e histórico..."):
            try:
                email_reader.sincronizar_cierres_gmail()
                st.success("¡Sincronización completada con éxito!")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")
    st.markdown("---")

    # Conexión y consulta agrupada por fecha y negocio para ver el desglose limpio
    conn = sqlite3.connect("db_cierres.db")
    df = pd.read_sql_query("""
        SELECT 
            DATE(fecha) as Fecha,
            negocio as Tienda,
            SUM(tarjeta_colones) as Tarjetas_CRC,
            SUM(efectivo_colones) as Efectivo_CRC,
            SUM(colones) as Total_CRC,
            SUM(dolares) as Total_USD
        FROM cierres 
        GROUP BY DATE(fecha), negocio
        ORDER BY Fecha DESC
    """, conn)
    conn.close()

    if not df.empty:
        # --- FILTRO POR TIENDAS ---
        tiendas_disponibles = ["Todas las tiendas"] + list(df['Tienda'].dropna().unique())
        tienda_seleccionada = st.selectbox("🏬 Filtrar por Tienda:", tiendas_disponibles)

        # Aplicar filtro en la vista
        if tienda_seleccionada != "Todas las tiendas":
            df_filtrado = df[df['Tienda'] == tienda_seleccionada]
        else:
            df_filtrado = df

        st.markdown(f"##### 📊 Reporte Consolidado por Fechas ({tienda_seleccionada})")
        st.dataframe(df_filtrado, use_container_width=True)

        # --- MÉTRICAS TOTALES DINÁMICAS ---
        t_tarjetas = df_filtrado['Tarjetas_CRC'].sum()
        t_efectivo = df_filtrado['Efectivo_CRC'].sum()
        t_general = df_filtrado['Total_CRC'].sum()

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Tarjetas (CRC)", f"₡ {t_tarjetas:,.2f}")
        with col2:
            st.metric("Total Efectivo (CRC)", f"₡ {t_efectivo:,.2f}")
        with col3:
            st.metric("Venta General (CRC)", f"₡ {t_general:,.2f}")
            
    else:
        st.info("No hay registros en la base de datos todavía. Presiona sincronizar para cargar el histórico y los correos.")
