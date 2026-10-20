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
                # Leer el Excel y limpiar espacios en los títulos de las columnas
                df = pd.read_excel(archivo_subido)
                df.columns = df.columns.astype(str).str.strip()
                
                st.success(f"✅ Archivo leído con éxito. Se detectaron {len(df)} registros.")
                
                # Identificación exacta de columnas clave de Simplifica2
                col_fecha = next((c for c in df.columns if "fecha" in c.lower()), df.columns[0])
                col_tienda = next((c for c in df.columns if "tienda" in c.lower()), (df.columns[2] if len(df.columns) > 2 else "Bravca"))
                
                # Columnas en Colones exactas (por nombre o por posición segura de tu reporte)
                col_ef_c = next((c for c in df.columns if "efectivo" in c.lower() and "₡" in c), (df.columns[11] if len(df.columns) > 11 else None))
                col_tj_c = next((c for c in df.columns if "tarjeta" in c.lower() and "₡" in c), (df.columns[12] if len(df.columns) > 12 else None))
                col_vend_c = next((c for c in df.columns if "vendido" in c.lower() and "₡" in c), (df.columns[16] if len(df.columns) > 16 else None))

                # Forzar conversión numérica limpia para evitar errores de tipo de dato
                df[col_ef_c] = pd.to_numeric(df[col_ef_c], errors='coerce').fillna(0)
                df[col_tj_c] = pd.to_numeric(df[col_tj_c], errors='coerce').fillna(0)
                df[col_vend_c] = pd.to_numeric(df[col_vend_c], errors='coerce').fillna(0)

                # Calcular sumas reales exactas del archivo
                tot_ef = df[col_ef_c].sum()
                tot_tj = df[col_tj_c].sum()
                tot_vend = df[col_vend_c].sum()

                st.markdown("### 📋 Resumen Real del Archivo")
                c1, c2, c3 = st.columns(3)
                c1.metric("Efectivo ₡", f"₡{tot_ef:,.2f}")
                c2.metric("Tarjeta ₡", f"₡{tot_tj:,.2f}")
                c3.metric("Total Vendido ₡", f"₡{tot_vend:,.2f}")
                
                st.markdown("---")
                st.dataframe(df, use_container_width=True)
                
                if st.button("💾 Confirmar y Guardar en Base de Datos", type="primary"):
                    conn = sqlite3.connect("db_cierres.db")
                    cursor = conn.cursor()
                    
                    # Tabla estructurada para almacenar cada tienda de forma independiente
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS cierres (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            negocio TEXT,
                            fecha TEXT,
                            efectivo REAL,
                            tarjeta REAL,
                            vendido REAL
                        )
                    """)
                    
                    # Insertar cada fila del Excel asegurando integridad de datos
                    for idx, row in df.iterrows():
                        negocio = str(row[col_tienda]) if col_tienda in df.columns and pd.notnull(row[col_tienda]) else "Bravca"
                        fecha = str(row[col_fecha]) if col_fecha in df.columns and pd.notnull(row[col_fecha]) else f"Cierre {idx+1}"
                        ef = float(row[col_ef_c])
                        tj = float(row[col_tj_c])
                        vend = float(row[col_vend_c])
                        
                        cursor.execute("""
                            INSERT INTO cierres (negocio, fecha, efectivo, tarjeta, vendido)
                            VALUES (?, ?, ?, ?, ?)
                        """, (negocio, fecha, ef, tj, vend))
                    
                    conn.commit()
                    conn.close()
                    st.success("¡Datos guardados y acumulados correctamente en la base de datos sin sobrescribir otras tiendas!")
                    
            except Exception as e:
                st.error(f"Error crítico al procesar el archivo: {e}")

    with tab1:
        st.subheader("📊 Historial de Cierres Registrados")
        
        # Botón para limpiar datos anteriores si arrastran errores de pruebas pasadas
        if st.button("🗑️ Reiniciar / Borrar Base de Datos Actual"):
            try:
                conn = sqlite3.connect("db_cierres.db")
                cursor = conn.cursor()
                cursor.execute("DROP TABLE IF EXISTS cierres")
                conn.commit()
                conn.close()
                st.success("Base de datos limpiada correctamente.")
                st.rerun()
            except Exception as e:
                st.error(f"Error al limpiar: {e}")

        try:
            conn = sqlite3.connect("db_cierres.db")
            df_db = pd.read_sql_query("SELECT * FROM cierres", conn)
            conn.close()
            
            if not df_db.empty:
                # Selector de tiendas para ver reportes separados o consolidados
                tiendas = ["Todas las tiendas"] + list(df_db["negocio"].unique())
                tienda_sel = st.selectbox("Filtrar por Tienda:", tiendas)
                
                if tienda_sel != "Todas las tiendas":
                    df_fil = df_db[df_db["negocio"] == tienda_sel]
                else:
                    df_fil = df_db
                
                t_ef = df_fil["efectivo"].sum()
                t_tj = df_fil["tarjeta"].sum()
                t_vend = df_fil["vendido"].sum() if "vendido" in df_fil.columns else (t_ef + t_tj)
                
                col1, col2, col3 = st.columns(3)
                col1.metric("💵 Total Efectivo", f"₡{t_ef:,.2f}")
                col2.metric("💳 Total Tarjeta", f"₡{t_tj:,.2f}")
                col3.metric("💰 Total Vendido", f"₡{t_vend:,.2f}")
                
                st.markdown("---")
                st.dataframe(df_fil, use_container_width=True)
            else:
                st.info("No hay registros guardados en la base de datos.")
        except Exception:
            st.info("La base de datos se está inicializando o está vacía.")
