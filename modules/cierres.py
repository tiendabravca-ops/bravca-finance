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
                df = pd.read_excel(archivo_subido)
                df.columns = df.columns.str.strip()
                
                st.success(f"✅ Archivo leído con éxito. Se detectaron {len(df)} registros.")
                
                # Identificar columnas de Colones y Dólares
                col_ef_colones = "Efectivo ₡" if "Efectivo ₡" in df.columns else "Efectivo"
                col_tj_colones = "Tarjeta ₡" if "Tarjeta ₡" in df.columns else "Tarjeta"
                
                col_ef_dolares = "Efectivo $" if "Efectivo $" in df.columns else None
                col_tj_dolares = "Tarjeta $" if "Tarjeta $" in df.columns else None
                
                # Sumas en Colones
                tot_ef_c = pd.to_numeric(df[col_ef_colones], errors='coerce').sum() if col_ef_colones in df.columns else 0
                tot_tj_c = pd.to_numeric(df[col_tj_colones], errors='coerce').sum() if col_tj_colones in df.columns else 0
                
                # Sumas en Dólares
                tot_ef_d = pd.to_numeric(df[col_ef_dolares], errors='coerce').sum() if col_ef_dolares and col_ef_dolares in df.columns else 0
                tot_tj_d = pd.to_numeric(df[col_tj_dolares], errors='coerce').sum() if col_tj_dolares and col_tj_dolares in df.columns else 0
                
                st.markdown("### 📋 Resumen Calculado del Archivo Actual")
                
                # Mostrar métricas separadas por moneda y método de pago
                st.write("**Moneda: Colones (₡)**")
                c1, c2, c3 = st.columns(3)
                c1.metric("Efectivo (₡)", f"₡{tot_ef_c:,.2f}")
                c2.metric("Tarjeta (₡)", f"₡{tot_tj_c:,.2f}")
                c3.metric("Total Colones", f"₡{(tot_ef_c + tot_tj_c):,.2f}")
                
                st.write("**Moneda: Dólares ($)**")
                d1, d2, d3 = st.columns(3)
                d1.metric("Efectivo ($)", f"${tot_ef_d:,.2f}")
                d2.metric("Tarjeta ($)", f"${tot_tj_d:,.2f}")
                d3.metric("Total Dólares", f"${(tot_ef_d + tot_tj_d):,.2f}")
                
                st.markdown("---")
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
                        negocio = str(row.get("Tienda", "Bravca"))
                        fecha = str(row["Fecha"]) if "Fecha" in df.columns and pd.notnull(row["Fecha"]) else f"Cierre {idx+1}"
                        
                        # Guardamos por defecto los valores en colones (o el total general unificado que prefieras)
                        ef = float(row[col_ef_colones]) if col_ef_colones in df.columns and pd.notnull(row[col_ef_colones]) else 0.0
                        tj = float(row[col_tj_colones]) if col_tj_colones in df.columns and pd.notnull(row[col_tj_colones]) else 0.0
                        
                        cursor.execute("""
                            INSERT INTO cierres (negocio, fecha, efectivo, tarjeta)
                            VALUES (?, ?, ?, ?)
                        """, (negocio, fecha, ef, tj))
                    
                    conn.commit()
                    conn.close()
                    st.success("¡Datos guardados correctamente en la base de datos sin animaciones!")
                    
            except Exception as e:
                st.error(f"Error al procesar el archivo: {e}")

    with tab1:
        st.subheader("📊 Historial General en Base de Datos")
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
                st.info("No hay cierres guardados aún.")
        except Exception:
            st.info("La base de datos está vacía.")
