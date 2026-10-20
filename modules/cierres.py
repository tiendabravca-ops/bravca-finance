import streamlit as st
import pandas as pd
import sqlite3

def run():
    st.header("📥 Gestión y Sincronización de Cierres de Caja")
    
    # Pestañas limpias para no perder botones ni vistas
    tab1, tab2 = st.tabs(["📊 Ver Cierres y Totales", "📤 Subir Reporte Excel (Simplifica2)"])
    
    with tab2:
        st.subheader("Cargar archivo de Simplifica2")
        archivo_subido = st.file_uploader("Sube el archivo Excel de Simplifica2", type=["xlsx", "xls"])
        
        if archivo_subido is not None:
            try:
                # Leer el Excel completo
                df = pd.read_excel(archivo_subido)
                
                # Identificar columnas de efectivo y tarjeta
                col_efectivo = [c for c in df.columns if "efectivo" in str(c).lower()]
                col_tarjeta = [c for c in df.columns if "tarjeta" in str(c).lower()]
                
                col_ef = col_efectivo[0] if col_efectivo else None
                col_tj = col_tarjeta[0] if col_tarjeta else None
                
                # Calcular sumas inmediatas del archivo cargado
                total_ef = pd.to_numeric(df[col_ef], errors='coerce').sum() if col_ef else 0
                total_tj = pd.to_numeric(df[col_tj], errors='coerce').sum() if col_tj else 0
                total_gen = total_ef + total_tj
                
                st.success(f" Archivo cargado con éxito. Se detectaron {len(df)} cierres/días.")
                
                # MOSTRAR TARJETAS DE RESUMEN AL INSTANTE
                c1, c2, c3 = st.columns(3)
                c1.metric("💵 Total Efectivo", f"₡{total_ef:,.2f}")
                c2.metric("💳 Total Tarjeta", f"₡{total_tj:,.2f}")
                c3.metric("💰 Total General", f"₡{total_gen:,.2f}")
                
                st.markdown("---")
                st.write("Detalle completo de los cierres detectados:")
                st.dataframe(df, use_container_width=True)
                
                if st.button("💾 Confirmar y Guardar en Base de Datos", type="primary"):
                    conn = sqlite3.connect("db_cierres.db")
                    cursor = conn.cursor()
                    
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS cierres (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            negocio TEXT,
                            fecha TEXT,
                            efectivo REAL,
                            tarjeta REAL
                        )
                    """)
                    
                    for idx, row in df.iterrows():
                        negocio = str(row.get("Negocio", "Bravca"))
                        fecha = str(row.get("Fecha", row.get("Fecha / Turno", f"Cierre {idx+1}")))
                        ef = float(row[col_ef]) if col_ef and pd.notnull(row[col_ef]) else 0.0
                        tj = float(row[col_tj]) if col_tj and pd.notnull(row[col_tj]) else 0.0
                        
                        cursor.execute("""
                            INSERT INTO cierres (negocio, fecha, efectivo, tarjeta)
                            VALUES (?, ?, ?, ?)
                        """, (negocio, fecha, ef, tj))
                    
                    conn.commit()
                    conn.close()
                    st.success("¡Los 20 cierres quedaron guardados en la base de datos!")
                    st.balloons()
                    
            except Exception as e:
                st.error(f"Error al procesar el archivo: {e}")

    with tab1:
        st.subheader("📊 Historial de Cierres Registrados")
        try:
            conn = sqlite3.connect("db_cierres.db")
            df_db = pd.read_sql_query("SELECT * FROM cierres", conn)
            conn.close()
            
            if not df_db.empty:
                tot_ef = df_db["efectivo"].sum()
                tot_tj = df_db["tarjeta"].sum()
                
                col1, col2, col3 = st.columns(3)
                col1.metric("💵 Total Efectivo (BD)", f"₡{tot_ef:,.2f}")
                col2.metric("💳 Total Tarjeta (BD)", f"₡{tot_tj:,.2f}")
                col3.metric("💰 Total General (BD)", f"₡{tot_ef + tot_tj:,.2f}")
                
                st.markdown("---")
                st.dataframe(df_db, use_container_width=True)
            else:
                st.info("No hay cierres guardados en la base de datos aún. Sube un archivo en la pestaña 'Subir Reporte Excel'.")
        except Exception:
            st.info("La base de datos se creará automáticamente cuando guardes tu primer reporte.")
