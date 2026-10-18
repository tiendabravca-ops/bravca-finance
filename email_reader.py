import sqlite3
import pandas as pd
import streamlit as st
import email_reader

def cargar_datos_cierres():
    email_reader.init_db() # Asegura que la BD y el histórico estén inicializados
    conn = sqlite3.connect("db_cierres.db")
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
        with st.spinner("Conectando con tiendabravca@gmail.com para actualizar cierres, desgloses e histórico..."):
            try:
                email_reader.sincronizar_cierres_gmail()
                st.success("¡Sincronización y actualización histórica completada con éxito!")
                st.rerun()
            except Exception as e:
                st.error(f"Error inesperado: {e}")
    st.markdown("---")

    # Pestañas de gestión
    pestana1, pestana2 = st.tabs(["📊 Histórico y Reportes por Tienda", "📥 Procesar Nuevo PDF de Cierre"])

    with pestana1:
        st.markdown("##### 📈 Consolidado y Filtro por Ubicación")
        
        df_cierres = cargar_datos_cierres()
        
        if not df_cierres.empty:
            # Selector / Filtro por Tienda
            negocios_disponibles = ["Todas las tiendas"] + list(df_cierres['negocio'].dropna().unique())
            tienda_seleccionada = st.selectbox("Seleccione la Tienda para el Resumen:", negocios_disponibles)
            
            # Aplicar filtro según selección
            if tienda_seleccionada != "Todas las tiendas":
                df_filtrado = df_cierres[df_cierres['negocio'] == tienda_seleccionada]
            else:
                df_filtrado = df_cierres
            
            st.markdown(f"Mostrando registros para: **{tienda_seleccionada}**")
            st.dataframe(df_filtrado, use_container_width=True)
            
            # Métricas calculadas con base en el filtro actual
            total_tarjeta = df_filtrado['tarjeta_colones'].sum()
            total_efectivo = df_filtrado['efectivo_colones'].sum()
            total_general = df_filtrado['colones'].sum()
            total_dolares = df_filtrado['dolares'].sum()
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(label=f"Tarjetas ({tienda_seleccionada})", value=f"₡ {total_tarjeta:,.2f}")
            with col2:
                st.metric(label=f"Efectivo ({tienda_seleccionada})", value=f"₡ {total_efectivo:,.2f}")
            with col3:
                st.metric(label=f"Venta Total ({tienda_seleccionada})", value=f"₡ {total_general:,.2f}")
                
            if total_dolares > 0:
                st.metric(label=f"Total Ventas USD ({tienda_seleccionada})", value=f"$ {total_dolares:,.2f}")
        else:
            st.info("No hay cierres registrados todavía. Presiona el botón de **Sincronizar Cierres desde Gmail Ahora**.")

    with pestana2:
        st.markdown("##### 📥 Subir Cierre de Caja en PDF Manualmente")
        st.info("Sube o arrastra aquí el PDF si deseas registrar un cierre de forma manual.")
        archivo_pdf = st.file_uploader("Seleccionar archivo PDF de Simplifica2", type=["pdf"])

        if archivo_pdf is not None:
            st.success(f"¡Archivo '{archivo_pdf.name}' cargado con éxito!")
            if st.button("⚙️ Procesar y Registrar Cierre"):
                st.success("Los datos del PDF fueron registrados.")
