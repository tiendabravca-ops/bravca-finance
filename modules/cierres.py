import streamlit as st
import pandas as pd
import sqlite3
import os

def render_importar_excel_simplifica2():
    st.subheader("📥 Importar Cierre de Caja desde Excel (Simplifica2)")
    
    # Widget para subir el archivo Excel
    archivo_subido = st.file_uploader("Sube el archivo Excel de Simplifica2", type=["xlsx", "xls"])
    
    if archivo_subido is not None:
        try:
            # Leer el archivo Excel
            df = pd.read_excel(archivo_subido)
            
            st.write("Vista previa de los datos detectados:")
            st.dataframe(df.head())
            
            # Botón para procesar e insertar en la base de datos
            if st.button("Confirmar y Guardar en Base de Datos"):
                conn = sqlite3.connect("db_cierres.db")
                cursor = conn.cursor()
                
                # Asegurar que la tabla existe
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS cierres (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        negocio TEXT,
                        fecha TEXT,
                        efectivo REAL,
                        tarjeta REAL
                    )
                """)
                
                # Iterar sobre las filas del Excel e insertarlas (ajusta los nombres de columnas según tu Excel)
                for index, row in df.iterrows():
                    # Suponiendo columnas estándar; puedes adaptarlas si tienen otro nombre en Simplifica2
                    negocio = str(row.get("Negocio", "Bravca"))
                    fecha = str(row.get("Fecha", ""))
                    efectivo = float(row.get("Efectivo", 0))
                    tarjeta = float(row.get("Tarjeta", 0))
                    
                    cursor.execute("""
                        INSERT INTO cierres (negocio, fecha, efectivo, tarjeta)
                        VALUES (?, ?, ?, ?)
                    """, (negocio, fecha, efectivo, tarjeta))
                
                conn.commit()
                conn.close()
                st.success("¡Cierres sincronizados y guardados exitosamente en `db_cierres.db`!")
                
        except Exception as e:
            st.error(f"Ocurrió un error al procesar el archivo: {e}")
