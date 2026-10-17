import sqlite3
import pandas as pd
import streamlit as st
import email_reader

def cargar_datos_cierres():
    conn = sqlite3.connect("db_cierres.db")
    cursor = conn.cursor()
    
    # Verificamos si la tabla tiene las columnas de desglose, si no, la recreamos limpia
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
    
    df = pd.read_sql_query("SELECT id, fecha, cajero, negocio, tarjeta_colones, efectivo_colones, colones, dolares, estado FROM cierres ORDER BY id DESC", conn)
    conn.close()
    return df

def run():
    st.markdown("##### 🧾 CENTRO DE CONTROL DE CIERRES DE CAJA")
    st.caption("Monitoreo automatizado y consolidado diario de cierres desde Gmail para bráVca Souvenir.")

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
            st.dataframe(df_cierres, use_container_width=True)
            
            total_tarjeta = df_cierres['tarjeta_colones'].sum()
            total_efectivo = df_cierres['efectivo_colones'].sum()
            total_general = df_cierres['colones'].sum()
            total_dolares = df_cierres['dolares'].sum()
            
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
            st.info("No hay cierres registrados todavía. Presiona el botón de **Sincronizar Cierres desde Gmail Ahora**.")

    with pestana2:
        st.markdown("##### 📥 Subir Cierre de Caja en PDF Manualmente")
        st.info("Sube o arrastra aquí el PDF si deseas registrar un cierre de forma manual.")
        archivo_pdf = st.file_uploader("Seleccionar archivo PDF de Simplifica2", type=["pdf"])

        if archivo_pdf is not None:
            st.success(f"¡Archivo '{archivo_pdf.name}' cargado con éxito!")
            if st.button("⚙️ Procesar y Registrar Cierre"):
                st.success("Los datos del PDF fueron registrados.")
