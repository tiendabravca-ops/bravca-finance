import streamlit as st
import pandas as pd
import sqlite3
import os

def inicializar_bd():
    db_path = "data/sistema_financiero.db"
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS obligaciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            anio INTEGER,
            mes TEXT,
            categoria TEXT,
            descripcion TEXT,
            monto REAL
        )
    ''')
    conn.commit()
    conn.close()

def run():
    st.markdown("##### 📑 CONTROL DE OBLIGACIONES Y GASTOS OPERATIVOS")
    inicializar_bd()

    db_path = "data/sistema_financiero.db"
    
    # Formulario de registro de nuevo gasto u obligación
    with st.form("form_obligacion", clear_on_submit=True):
        st.markdown("###### Registrar Nuevo Egreso / Gasto Fijo")
        c1, c2, c3 = st.columns(3)
        with c1:
            anio = st.selectbox("Año", [2026, 2025], key="obs_anio")
            mes = st.selectbox("Mes", ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'], key="obs_mes")
        with c2:
            categoria = st.selectbox("Categoría", ["Alquileres", "Planilla", "Proveedores / Mercadería", "Servicios Públicos", "Otros Gastos"], key="obs_cat")
            monto = st.number_input("Monto en Colones (₡)", min_value=0.0, step=10000.0, key="obs_monto")
        with c3:
            descripcion = st.text_input("Descripción / Proveedor", key="obs_desc")
            st.markdown("<br>", unsafe_allow_html=True)
            submitted = st.form_submit_button("💾 Guardar Obligación")

        if submitted:
            if monto > 0:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO obligaciones (anio, mes, categoria, descripcion, monto) VALUES (?, ?, ?, ?, ?)",
                    (anio, mes, categoria, descripcion, monto)
                )
                conn.commit()
                conn.close()
                st.success(f"¡Obligación de ₡ {monto:,.2f} registrada correctamente!")
                st.rerun()
            else:
                st.error("Por favor ingrese un monto válido mayor a cero.")

    st.markdown("---")
    st.markdown("###### 📋 Registro Actual de Obligaciones (2026)")

    # Mostrar tabla de obligaciones registradas
    conn = sqlite3.connect(db_path)
    df_registros = pd.read_sql_query("SELECT id, mes, categoria, descripcion, monto FROM obligaciones WHERE anio = 2026", conn)
    conn.close()

    if not df_registros.empty:
        st.dataframe(df_registros, use_container_width=True)
        
        # Opción para borrar registros si fuera necesario
        st.markdown("---")
        id_a_borrar = st.number_input("ID de obligación a eliminar (opcional)", min_value=0, step=1, value=0)
        if st.button("🗑️ Eliminar Registro Seleccionado"):
            if id_a_borrar > 0:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("DELETE FROM obligaciones WHERE id = ?", (id_a_borrar,))
                conn.commit()
                conn.close()
                st.success(f"Registro con ID {id_a_borrar} eliminado.")
                st.rerun()
    else:
        st.info("Aún no hay obligaciones registradas en la base de datos para 2026. Utiliza el formulario superior para agregar los gastos de alquileres, planillas y proveedores.")