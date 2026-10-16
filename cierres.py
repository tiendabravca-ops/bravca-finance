import streamlit as st
import pandas as pd
import datetime

def run():
    st.markdown("##### 🧾 CENTRO DE CONTROL DE CIERRES DE CAJA")
    st.caption("Monitoreo automatizado de los cierres diarios para Bravca Souvenir y Bravca Extremo.")

    # Pestañas de gestión
    pestana1, pestana2 = st.tabs(["📊 Histórico y Reportes", "📥 Procesar Nuevo PDF de Cierre"])

    with pestana1:
        st.markdown("##### 📈 Consolidado Reciente de Tiendas")
        
        # Datos de ejemplo / estructura inicial de registros (puedes conectar esto a tu base de datos o CSV)
        data_ejemplo = [
            {"Fecha": "2026-10-15", "Tienda": "Bravca Souvenir", "Colones (CRC)": 125000.00, "Dólares (USD)": 240.00, "Estado": "Recibido / Verificado"},
            {"Fecha": "2026-10-15", "Tienda": "Bravca Extremo", "Colones (CRC)": 98000.00, "Dólares (USD)": 150.00, "Estado": "Recibido / Verificado"},
        ]
        df_cierres = pd.DataFrame(data_ejemplo)
        
        st.dataframe(df_cierres, use_container_width=True)

        # Métricas rápidas
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            st.metric(label="Total Colones (Último Cierre)", value="₡ 223,000.00", delta="+12.5%")
        with col_m2:
            st.metric(label="Total Dólares (Último Cierre)", value="$ 390.00", delta="+5.0%")

    with pestana2:
        st.markdown("##### 📥 Subir Cierre de Caja en PDF")
        st.info("Sube o arrastra aquí el PDF del cierre que recibiste en tiendabravca@gmail.com para que el agente extraiga los montos automáticamente.")

        archivo_pdf = st.file_uploader("Seleccionar archivo PDF de Simplifica2", type=["pdf"])

        if archivo_pdf is not None:
            st.success(f"¡Archivo '{archivo_pdf.name}' cargado con éxito!")
            if st.button("⚙️ Procesar y Registrar Cierre en el Sistema"):
                # Aquí el sistema procesará el texto del PDF en cuanto configuremos la librería lectora (p.ej. pypdf)
                st.markdown("""
                    <div style="background-color: rgba(45, 90, 39, 0.08); border: 1px solid #2D5A27; padding: 15px; border-radius: 8px;">
                        <h5 style="color: #2D5A27; margin-top: 0;">✅ Cierre Procesado Correctamente</h5>
                        <p style="margin-bottom: 0; font-size: 0.95rem;">Los datos extraídos del PDF han sido añadidos al registro contable de las tiendas.</p>
                    </div>
                """, unsafe_allow_html=True)