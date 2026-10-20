import streamlit as st
import pandas as pd
import sqlite3

def run():
    st.header("📥 Gestión y Sincronización de Cierres de Caja")
    
    tab1, tab2 = st.tabs(["📊 Ver Cierres y Totales", "📤 Subir Reporte Excel (Simplifica2)"])
    
    with tab2:
        st.subheader("Cargar archivo de Simplifica2")
        archivo_subido = st.file_uploader("Sube el archivo Excel de Simplifica2", type=["xlsx", "xls"])
        
        if archivo_subido is not None:
            try:
                # Leer el Excel completo
                df = pd.read_excel(archivo_subido)
                
                st.success(f"✅ Archivo leído. Se detectaron {len(df)} filas.")
                
                # Mostrar las columnas exactas que detectó para validarlas en pantalla
                st.write("Columnas detectadas en tu Excel:", list(df.columns))
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
                    
                    # Limpiamos nombres de columnas por si tienen espacios extras
                    df.columns = df.columns.str.strip()
                    
                    # Buscamos columnas de efectivo y tarjeta de forma flexible
                    col_ef = next((c for c in df.columns if "efectivo" in c.lower()), None)
                    col_tj = next((c for c in df.columns if "tarjeta" in c.lower()), None)
                    col_fe = next((c for c in df.columns if "fecha" in c.lower()), None)
                    
                    for idx, row in df.iterrows():
                        negocio = "Bravca"
                        fecha = str(row[col_fe]) if col_fe and pd.notnull(row[col_fe]) else f"Cierre {idx+1}"
                        ef = float(row[col_ef]) if col_ef and pd.notnull(row[col_ef]) else 0.0
                        tj = float(row[col_tj]) if col_tj and pd.notnull(row[col_tj]) else 0.0
                        
                        cursor.execute("""
                            INSERT INTO cierres (negocio, fecha, efectivo, tarjeta)
                            VALUES (?, ?, ?, ?)
                        """, (negocio, fecha, ef, tj))
                    
                    conn.commit()
                    conn.close()
                    st.success("¡Datos guardados correctamente en la base de datos!")
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
                col1.metric("💵 Total Efectivo", f"₡{tot_ef:,.2f}")
                col2.metric("💳 Total Tarjeta", f"₡{tot_tj:,.2f}")
                col3.metric("💰 Total General", f"₡{tot_ef + tot_tj:,.2f}")
                
                st.markdown("---")
                st.dataframe(df_db, use_container_width=True)
            else:
                st.info("No hay cierres guardados aún.")
        except Exception:
            st.info("La base de datos está vacía o pendiente de inicializar.")
