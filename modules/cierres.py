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
                df.columns = df.columns.astype(str).str.strip()
                
                st.success(f"✅ Archivo leído con éxito. Se detectaron {len(df)} registros.")
                
                # Identificar columnas clave de forma segura
                col_fecha = next((c for c in df.columns if "fecha" in c.lower()), None)
                col_tienda = next((c for c in df.columns if "tienda" in c.lower()), None)
                
                col_ef_c = next((c for c in df.columns if "efectivo" in c.lower() and "₡" in c), None)
                col_tj_c = next((c for c in df.columns if "tarjeta" in c.lower() and "₡" in c), None)
                col_vend_c = next((c for c in df.columns if "vendido" in c.lower() and "₡" in c), None)
                
                if not col_ef_c:
                    col_ef_c = next((c for c in df.columns if c.lower() == "efectivo"), None)
                if not col_tj_c:
                    col_tj_c = next((c for c in df.columns if c.lower() == "tarjeta"), None)
                if not col_vend_c:
                    col_vend_c = next((c for c in df.columns if c.lower() == "vendido"), None)

                # Calcular sumas del archivo actual
                tot_ef_c = pd.to_numeric(df[col_ef_c], errors='coerce').sum() if col_ef_c else 0.0
                tot_tj_c = pd.to_numeric(df[col_tj_c], errors='coerce').sum() if col_tj_c else 0.0
                tot_vend_c = pd.to_numeric(df[col_vend_c], errors='coerce').sum() if col_vend_c else 0.0

                st.markdown("### 📋 Resumen del Archivo Cargado")
                c1, c2, c3 = st.columns(3)
                c1.metric("Efectivo ₡", f"₡{tot_ef_c:,.2f}")
                c2.metric("Tarjeta ₡", f"₡{tot_tj_c:,.2f}")
                c3.metric("Total Vendido ₡", f"₡{tot_vend_c:,.2f}")
                
                st.markdown("---")
                st.dataframe(df, use_container_width=True)
                
                if st.button("💾 Confirmar y Agregar a la Base de Datos", type="primary"):
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
                    
                    # Insertar cada fila conservando la tienda correspondiente sin borrar las demás
                    for idx, row in df.iterrows():
                        negocio = str(row[col_tienda]) if col_tienda and pd.notnull(row[col_tienda]) else "Tienda Principal"
                        fecha = str(row[col_fecha]) if col_fecha and pd.notnull(row[col_fecha]) else f"Cierre {idx+1}"
                        ef = float(row[col_ef_c]) if col_ef_c and pd.notnull(row[col_ef_c]) else 0.0
                        tj = float(row[col_tj_c]) if col_tj_c and pd.notnull(row[col_tj_c]) else 0.0
                        
                        cursor.execute("""
                            INSERT INTO cierres (negocio, fecha, efectivo, tarjeta)
                            VALUES (?, ?, ?, ?)
                        """, (negocio, fecha, ef, tj))
                    
                    conn.commit()
                    conn.close()
                    st.success("¡Datos guardados y acumulados correctamente sin afectar la otra tienda!")
                    
            except Exception as e:
                st.error(f"Error al procesar el archivo: {e}")

    with tab1:
        st.subheader("📊 Historial de Cierres por Tienda")
        try:
            conn = sqlite3.connect("db_cierres.db")
            df_db = pd.read_sql_query("SELECT * FROM cierres", conn)
            conn.close()
            
            if not df_db.empty:
                # Selector para filtrar por tienda o ver ambas
                tiendas_disponibles = ["Todas las tiendas"] + list(df_db["negocio"].unique())
                tienda_seleccionada = st.selectbox("Filtrar por Tienda:", tiendas_disponibles)
                
                if tienda_seleccionada != "Todas las tiendas":
                    df_filtrado = df_db[df_db["negocio"] == tienda_seleccionada]
                else:
                    df_filtrado = df_db
                
                tot_ef = df_filtrado["efectivo"].sum()
                tot_tj = df_filtrado["tarjeta"].sum()
                
                col1, col2, col3 = st.columns(3)
                col1.metric("💵 Total Efectivo", f"₡{tot_ef:,.2f}")
                col2.metric("💳 Total Tarjeta", f"₡{tot_tj:,.2f}")
                col3.metric("💰 Total General", f"₡{tot_ef + tot_tj:,.2f}")
                
                st.markdown("---")
                st.dataframe(df_filtrado, use_container_width=True)
            else:
                st.info("No hay cierres guardados aún en la base de datos.")
        except Exception:
            st.info("La base de datos está vacía.")
