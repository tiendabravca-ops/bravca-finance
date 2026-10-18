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
            tienda TEXT,
            tipo_gasto TEXT,
            categoria TEXT,
            descripcion TEXT,
            monto REAL
        )
    ''')
    conn.commit()
    conn.close()

def run():
    st.markdown("##### 📑 CONTROL DE OBLIGACIONES, GASTOS FIJOS Y VARIABLES")
    inicializar_bd()

    db_path = "data/sistema_financiero.db"

    # Pestañas para separar la gestión
    tab_fijos, tab_variables = st.tabs(["📌 Gastos Fijos (Alquileres, Planilla, etc.)", "⚡ Gastos Variables (Insumos, Extras, etc.)"])

    with tab_fijos:
        with st.form("form_gasto_fijo", clear_on_submit=True):
            st.markdown("###### Registrar Gasto Fijo / Obligación Operativa")
            c1, c2, c3 = st.columns(3)
            with c1:
                anio = st.selectbox("Año", [2026, 2025], key="fijo_anio")
                mes = st.selectbox("Mes", ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'], key="fijo_mes")
            with c2:
                tienda = st.selectbox("Tienda / Destino", ["Consolidado (Ambas Tiendas)", "Santa Elena", "Monteverde Extremo"], key="fijo_tienda")
                categoria = st.selectbox("Categoría", ["Alquileres", "Planilla", "Servicios Públicos", "Préstamos / Financiamiento", "Otros Fijos"], key="fijo_cat")
            with c3:
                monto = st.number_input("Monto en Colones (₡)", min_value=0.0, step=10000.0, key="fijo_monto")
                descripcion = st.text_input("Descripción / Proveedor", key="fijo_desc")
            
            submitted_fijo = st.form_submit_button("💾 Guardar Gasto Fijo")

            if submitted_fijo:
                if monto > 0:
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()
                    cursor.execute(
                        "INSERT INTO obligaciones (anio, mes, tienda, tipo_gasto, categoria, descripcion, monto) VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (anio, mes, tienda, "Fijo", categoria, descripcion, monto)
                    )
                    conn.commit()
                    conn.close()
                    st.success(f"¡Gasto fijo de ₡ {monto:,.2f} registrado con éxito!")
                    st.rerun()
                else:
                    st.error("Por favor ingrese un monto válido mayor a cero.")

    with tab_variables:
        with st.form("form_gasto_variable", clear_on_submit=True):
            st.markdown("###### Registrar Gasto Variable / Operativo Diario")
            c1, c2, c3 = st.columns(3)
            with c1:
                anio_v = st.selectbox("Año", [2026, 2025], key="var_anio")
                mes_v = st.selectbox("Mes", ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'], key="var_mes")
            with c2:
                tienda_v = st.selectbox("Tienda / Destino", ["Consolidado (Ambas Tiendas)", "Santa Elena", "Monteverde Extremo"], key="var_tienda")
                categoria_v = st.selectbox("Categoría", ["Proveedores / Mercadería", "Mantenimiento & Reparaciones", "Insumos de Tienda", "Comisiones / Extras", "Otros Variables"], key="var_cat")
            with c3:
                monto_v = st.number_input("Monto en Colones (₡)", min_value=0.0, step=5000.0, key="var_monto")
                descripcion_v = st.text_input("Descripción / Proveedor", key="var_desc")
            
            submitted_var = st.form_submit_button("💾 Guardar Gasto Variable")

            if submitted_var:
                if monto_v > 0:
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()
                    cursor.execute(
                        "INSERT INTO obligaciones (anio, mes, tienda, tipo_gasto, categoria, descripcion, monto) VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (anio_v, mes_v, tienda_v, "Variable", categoria_v, descripcion_v, monto_v)
                    )
                    conn.commit()
                    conn.close()
                    st.success(f"¡Gasto variable de ₡ {monto_v:,.2f} registrado con éxito!")
                    st.rerun()
                else:
                    st.error("Por favor ingrese un monto válido mayor a cero.")

    st.markdown("---")
    st.markdown("###### 📋 Registro Consolidado de Egresos (2026)")

    # Mostrar tabla unificada de obligaciones y gastos variables
    conn = sqlite3.connect(db_path)
    df_registros = pd.read_sql_query("SELECT id, mes, tienda, tipo_gasto, categoria, descripcion, monto FROM obligaciones WHERE anio = 2026", conn)
    conn.close()

    if not df_registros.empty:
        st.dataframe(df_registros, use_container_width=True)
        
        # Opción para borrar registros si fuera necesario
        st.markdown("---")
        c_del1, c_del2 = st.columns([2, 1])
        with c_del1:
            id_a_borrar = st.number_input("ID de registro a eliminar", min_value=0, step=1, value=0)
        with c_del2:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🗑️ Eliminar Registro Seleccionado", use_container_width=True):
                if id_a_borrar > 0:
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM obligaciones WHERE id = ?", (id_a_borrar,))
                    conn.commit()
                    conn.close()
                    st.success(f"Registro con ID {id_a_borrar} eliminado correctamente.")
                    st.rerun()
    else:
        st.info("Aún no hay egresos registrados en la base de datos para 2026. Utiliza los formularios superiores para registrar tus gastos fijos y variables por tienda.")
