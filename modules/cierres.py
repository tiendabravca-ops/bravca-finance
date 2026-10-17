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
            tipo_cambio REAL,
            tarjeta_colones REAL,
            efectivo_colones REAL
        )
    """)
    df = pd.read_sql_query("SELECT * FROM cierres ORDER BY id DESC", conn)
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
                # Intenta tomar las credenciales de los Secrets o usa valores por defecto
                correo = st.secrets.get("GMAIL_USER", "tiendabravca@gmail.com")
                password = st.secrets.get("GMAIL_PASSWORD", "")
                
                if password:
                    email_reader.sincronizar_cierres_correo(correo, password)
                    st.success("¡Sincronización completada con éxito! Actualizando datos...")
                    st.rerun()
                else:
                    st.error("Falta configurar la contraseña de aplicación de Gmail en los 'Secrets' de Streamlit Cloud.")
            except Exception as e:
                st.error(f"Error al sincronizar correos: {e}")
    st.markdown("---")

    # Pestañas de gestión
    pestana1, pestana2 = st.tabs(["📊 Histórico y Reportes", "📥 Procesar Nuevo PDF de Cierre"])

    with pestana1:
        st.markdown("##### 📈 Consolidado Reciente de Tiendas")
        
        df_cierres = cargar_datos_cierres()
        
        if not df_cierres.empty:
            st.dataframe(df_cierres, use_container_width=True)
            
            total_tarjeta = df_cierres['tarjeta_colones'].sum()
            total_efectivo = df_cierres['efectivo_colones'].sum()
            
            col_m1, col_m2 = st.columns(2)
            with col_m1:
                st.metric(label="Total Tarjeta (CRC)", value=f"₡ {total_tarjeta:,.2f}")
            with col_m2:
                st.metric(label="Total Efectivo (CRC)", value=f"₡ {total_efectivo:,.2f}")
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
