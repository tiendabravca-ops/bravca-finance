import streamlit as st
import pandas as pd
import sqlite3

def run():
    st.header("📥 Gestión y Sincronización de Cierres de Caja")
    
    # Menú de opciones principal (siempre visible arriba)
    opcion = st.radio(
        "Selecciona una acción:", 
        ["Ver Cierres y Totales", "Subir Reporte Excel (Simplifica2)"],
        horizontal=True
    )
    
    st.markdown("---")
    
    if opcion == "Subir Reporte Excel (Simplifica2)":
        st.subheader("Cargar archivo de Simplifica2")
        archivo_subido = st.file_uploader("Sube el archivo Excel de Simplifica2", type=["xlsx", "xls"])
        
        if archivo_subido is not None:
            try:
                # Leer el archivo Excel completo con openpyxl
                df = pd.read_excel(archivo_subido)
                st.write(f"✅ Vista previa de los datos detectados ({len(df)} registros):")
                st.dataframe(df, use_container_width=True)
                
                if st.button("Confirmar y Guardar en Base de Datos", type="primary"):
                    conn = sqlite3.connect("db_cierres.db")
                    cursor = conn.cursor()
                    
                    # Crear la tabla si no existe
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS cierres (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            negocio TEXT,
                            fecha TEXT,
                            efectivo REAL,
                            tarjeta REAL
                        )
                    """)
                    
                    # Insertar cada fila del Excel adaptado a las columnas reales
                    for index, row in df.iterrows():
                        negocio = str(row.get("Negocio", "Bravca"))
                        fecha = str(row.get("Fecha", row.get("Fecha / Turno", f"Cierre {index+1}")))
                        efectivo = float(row.get("Efectivo $", row.get("Efectivo", 0)))
                        tarjeta = float(row.get("Tarjeta $", row.get("Tarjeta", 0)))
                        
                        cursor.execute("""
                            INSERT INTO cierres (negocio, fecha, efectivo, tarjeta)
                            VALUES (?, ?, ?, ?)
                        """, (negocio, fecha, efectivo, tarjeta))
                    
                    conn.commit()
                    conn.close()
                    st.success("¡Cierres guardados exitosamente en la base de datos!")
                    st.balloons()
                    
            except Exception as e:
                st.error(f"Ocurrió un error al procesar el archivo: {e}")
                
    else:
        st.subheader("📊 Resumen General y Cierres Registrados")
        
        try:
            conn = sqlite3.connect("db_cierres.db")
            df_guardados = pd.read_sql_query("SELECT * FROM cierres", conn)
            conn.close()
            
            if not df_guardados.empty:
                # Calcular totales para las tarjetas de resumen superior
                total_efectivo = df_guardados["efectivo"].sum()
                total_tarjeta = df_guardados["tarjeta"].sum()
                total_general = total_efectivo + total_tarjeta
                
                # Mostrar tarjetas con los totales (Métricas)
                col1, col2, col3 = st.columns(3)
                col1.metric("💵 Total Efectivo", f"₡{total_efectivo:,.2f}")
                col2.metric("💳 Total Tarjeta", f"₡{total_tarjeta:,.2f}")
                col3.metric("💰 Total General", f"₡{total_general:,.2f}")
                
                st.markdown("### Historial detallado en la Base de Datos")
                st.dataframe(df_guardados, use_container_width=True)
            else:
                st.info("No hay registros guardados todavía. Selecciona 'Subir Reporte Excel' para cargar tu primer archivo.")
                
        except Exception as e:
            st.info("Aún no se ha inicializado la base de datos. Sube un archivo primero en la otra opción.")
