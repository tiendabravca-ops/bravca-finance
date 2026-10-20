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
                # Leer el archivo Excel
                df = pd.read_excel(archivo_subido)
                
                # Limpiamos los nombres de las columnas eliminando espacios adelante/atrás
                df.columns = df.columns.astype(str).str.strip()
                
                st.success(f"✅ Archivo leído con éxito. Se detectaron {len(df)} registros.")
                
                # Buscamos de forma exacta y segura las columnas de tu reporte
                # Si no encuentra alguna, lo notifica en pantalla en lugar de fallar a la fuerza
                col_fecha = next((c for c in df.columns if "fecha" in c.lower()), None)
                col_tienda = next((c for c in df.columns if "tienda" in c.lower()), None)
                
                # Buscamos explícitamente las columnas de Colones
                col_ef_c = next((c for c in df.columns if "efectivo" in c.lower() and "₡" in c), None)
                col_tj_c = next((c for c in df.columns if "tarjeta" in c.lower() and "₡" in c), None)
                col_vend_c = next((c for c in df.columns if "vendido" in c.lower() and "₡" in c), None)
                
                # Si no encuentra con símbolo, buscamos por nombre base limpio
                if not col_ef_c:
                    col_ef_c = next((c for c in df.columns if c.lower() == "efectivo"), None)
                if not col_tj_c:
                    col_tj_c = next((c for c in df.columns if c.lower() == "tarjeta"), None)
                if not col_vend_c:
                    col_vend_c = next((c for c in df.columns if c.lower() == "vendido"), None)

                # Calcular sumas reales convirtiendo a numérico de forma segura
                tot_ef_c = pd.to_numeric(df[col_ef_c], errors='coerce').sum() if col_ef_c else 0.0
                tot_tj_c = pd.to_numeric(df[col_tj_c], errors='coerce').sum() if col_tj_c else 0.0
                tot_vend_c = pd.to_numeric(df[col_vend_c], errors='coerce').sum() if col_vend_c else 0.0

                st.markdown("### 📋 Resumen Calculado del Excel")
                c1, c2, c3 = st.columns(3)
                c1.metric("Efectivo ₡", f"₡{tot_ef_c:,.2f}")
                c2.metric("Tarjeta ₡", f"₡{tot_tj_c:,.2f}")
                c3.metric("Total Vendido ₡", f"₡{tot_vend_c:,.2f}")
                
                st.markdown("---")
                st.write("Vista previa de los datos exactos del archivo:")
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
                        negocio = str(row[col_tienda]) if col_tienda and pd.notnull(row[col_tienda]) else "Bravca"
                        fecha = str(row[col_fecha]) if col_fecha and pd.notnull(row[col_fecha]) else f"Cierre {idx+1}"
                        ef = float(row[col_ef_c]) if col_ef_c and pd.notnull(row[col_ef_c]) else 0.0
                        tj = float(row[col_tj_c]) if col_tj_c and pd.notnull(row[col_tj_c]) else 0.0
                        
                        cursor.execute("""
                            INSERT INTO cierres (negocio, fecha, efectivo, tarjeta)
                            VALUES (?, ?, ?, ?)
                        """, (negocio, fecha, ef, tj))
                    
                    conn.commit()
                    conn.close()
                    st.success("¡Datos guardados de forma segura en la base de datos!")
                    
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
