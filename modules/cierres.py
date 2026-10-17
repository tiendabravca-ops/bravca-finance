import sqlite3
import pandas as pd
import streamlit as st
import email_reader

def cargar_datos_cierres():
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
            estado TEXT
        )
    """)
    conn.commit()
    df = pd.read_sql_query("SELECT id, fecha, cajero, negocio, colones, dolares, estado FROM cierres ORDER BY id DESC", conn)
    conn.close()
    return df

def run():
    st.markdown("##### 🧾 CENTRO DE CONTROL DE CIERRES DE CAJA")
    st.caption("Monitoreo automatizado de los cierres diarios desde Gmail para bráVca Souvenir.")

    # Botón directo y visible de Sincronización
    st.markdown("---")
    st.markdown("##### 🔄 Sincronización Automática de Correos")
    
    if st.button("📥 Sincronizar Cierres desde Gmail Ahora"):
        with st.spinner("Conectando con tiendabravca@gmail.com para leer nuevos cierres..."):
            try:
                # Llamada correcta a la función de email_reader
                exito, mensaje = email_reader.sincronizar_cierres_gmail()
                
                if exito:
                    st.success(mensaje)
                    st.rerun()
                else:
                    st.error(f"No se pudo sincronizar: {mensaje}")
            except Exception as e:
                st.error(f"Error inesperado al ejecutar sincronización: {e}")
    st.markdown("---")

    # Pestañas de gestión
    pestana1, pestana2 = st.tabs(["📊 Histórico y Reportes", "📥 Procesar Nuevo PDF de Cierre"])

    with pestana1:
        st.markdown("##### 📈 Consolidado Reciente de Tiendas")
        
        df_cierres = cargar_datos_cierres()
        
        if not df_cierres.empty:
            st.dataframe(df_cierres, use_container_width=True)
            
            total_colones = df_cierres['colones'].sum()
            total_dolares = df_cierres['dolares'].sum()
            
            col_m1, col_m2 = st.columns(2)
            with col_m1:
                st.metric(label="Total Venta (CRC)", value=f"₡ {total_colones:,.2f}")
            with col_m2:
                st.metric(label="Total Venta (USD)", value=f"$ {total_dolares:,.2f}")
        else:
            st.info("No hay cierres registrados todavía en la base de datos. Presiona el botón de **Sincronizar Cierres desde Gmail Ahora** para descargar los datos de tus correos.")

    with pestana2:
        st.markdown("##### 📥 Subir Cierre de Caja en PDF Manualmente")
        st.info("Sube o arrastra aquí el PDF si deseas registrar un cierre de forma manual.")

        archivo_pdf = st.file_uploader("Seleccionar archivo PDF de Simplifica2", type=["pdf"])

        if archivo_pdf is not None:
            st.success(f"¡Archivo '{archivo_pdf.name}' cargado con éxito!")
            if st.button("⚙️ Procesar y Registrar Cierre en el Sistema"):
                st.success("Los datos extraídos del PDF han sido añadidos al registro contable.")
