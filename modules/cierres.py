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
                
                # Mapeo exacto por posición y nombre seguro basado en tu reporte real
                col_fecha = df.columns[0] if len(df.columns) > 0 else "Fecha"
                col_tienda = "Tienda" if "Tienda" in df.columns else (df.columns[2] if len(df.columns) > 2 else None)
                
                # Posiciones exactas confirmadas en tu Excel: Columna L (11) = Efectivo ₡, Columna M (12) = Tarjeta ₡
                col_ef_c = df.columns[11] if len(df.columns) > 11 else "Efectivo ₡"
                col_tj_c = df.columns[12] if len(df.columns) > 12 else "Tarjeta ₡"
                
                # Calcular sumas reales del archivo
                tot_ef_c = pd.to_numeric(df[col_ef_c], errors='coerce').sum()
                tot_tj_c = pd.to_numeric(df[col_tj_c], errors='coerce').sum()
                tot_vend_c = tot_ef_c + tot_tj_c

                st.markdown("### 📋 Resumen Exacto del Excel Subido")
                c1, c2, c3 = st.columns(3)
                c1.metric("Efectivo ₡", f"₡{tot_ef_c:,.2f}")
                c2.metric("Tarjeta ₡", f"₡{tot_tj_c:,.2f}")
                c3.metric("Total General ₡", f"₡{tot_vend_c:,.2f}")
                
                st.markdown("---")
                st.dataframe(df, use_container_width=True)
                
                if st.button("💾 Confirmar y Guardar en Base de Datos", type="primary"):
                    conn = sqlite3.connect("db_cierres.db")
                    cursor = conn.cursor()
                    
                    # Creamos la tabla limpia
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS cierres (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            negocio TEXT,
                            fecha TEXT,
                            efectivo REAL,
                            tarjeta REAL
                        )
                    """)
                    
                    # Insertar cada fila extrayendo los valores reales
                    for idx, row in df.iterrows():
                        negocio = str(row[col_tienda]) if col_tienda and pd.notnull(row[col_tienda]) else "Bravca"
                        fecha = str(row[col_fecha]) if pd.notnull(row[col_fecha]) else f"Cierre {idx+1}"
                        
                        ef = float(pd.to_numeric(row[col_ef_c], errors='raise')) if pd.notnull(row[col_ef_c]) else 0.0
                        tj = float(pd.to_numeric(row[col_tj_c], errors='raise')) if pd.notnull(row[col_tj_c]) else 0.0
                        
                        cursor.execute("""
                            INSERT INTO cierres (negocio, fecha, efectivo, tarjeta)
                            VALUES (?, ?, ?, ?)
                        """, (negocio, fecha, ef, tj))
                    
                    conn.commit()
                    conn.close()
                    st.success("¡Datos guardados correctamente en la base de datos con sus montos reales!")
                    
            except Exception as e:
                st.error(f"Error al procesar el archivo: {e}")

    with tab1:
        st.subheader("📊 Historial de Cierres por Tienda")
        
        # Botón de emergencia para limpiar datos con ceros anteriores
        if st.button("🗑️ Reiniciar / Borrar Base de Datos Actual"):
            try:
                conn = sqlite3.connect("db_cierres.db")
                cursor = conn.cursor()
                cursor.execute("DROP TABLE IF EXISTS cierres")
                conn.commit()
                conn.close()
                st.success("Base de datos reiniciada. Vuelve a subir tus Excel.")
                st.rerun()
            except Exception as e:
                st.error(f"Error al reiniciar: {e}")

        try:
            conn = sqlite3.connect("db_cierres.db")
            df_db = pd.read_sql_query("SELECT * FROM cierres", conn)
            conn.close()
            
            if not df_db.empty:
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
                st.info("No hay cierres guardados aún. Sube un archivo en la otra pestaña.")
        except Exception:
            st.info("La base de datos está vacía.")
