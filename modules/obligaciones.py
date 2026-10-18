import streamlit as st
import pandas as pd
import sqlite3
import os
from datetime import datetime

def inicializar_bd():
    db_path = "data/sistema_financiero.db"
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Tabla base para obligaciones y egresos
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
    
    # Migraciones automáticas para columnas dinámicas
    migraciones = [
        "ALTER TABLE obligaciones ADD COLUMN tienda TEXT DEFAULT 'Consolidado (Ambas Tiendas)'",
        "ALTER TABLE obligaciones ADD COLUMN tipo_gasto TEXT DEFAULT 'Fijo'",
        "ALTER TABLE obligaciones ADD COLUMN fecha_pago TEXT DEFAULT ''",
        "ALTER TABLE obligaciones ADD COLUMN periodicidad TEXT DEFAULT 'Mensual'"
    ]
    
    for mig in migraciones:
        try:
            cursor.execute(mig)
        except Exception:
            pass

    conn.commit()
    conn.close()

def run():
    st.markdown("##### 📑 CONTROL DE OBLIGACIONES, GASTOS FIJOS Y VARIABLES")
    inicializar_bd()

    db_path = "data/sistema_financiero.db"
    mapping_meses = {
        1: 'enero', 2: 'febrero', 3: 'marzo', 4: 'abril',
        5: 'mayo', 6: 'junio', 7: 'julio', 8: 'agosto',
        9: 'septiembre', 10: 'octubre', 11: 'noviembre', 12: 'diciembre'
    }

    # Pestañas para separar la gestión por tipo de gasto
    tab_fijos, tab_variables = st.tabs([
        "📌 Gastos Fijos (Alquileres, Planilla, Impuestos, etc.)", 
        "⚡ Gastos Variables (Insumos, Extras, etc.)"
    ])

    with tab_fijos:
        with st.form("form_gasto_fijo", clear_on_submit=True):
            st.markdown("###### Registrar Gasto Fijo / Obligación Operativa")
            c1, c2, c3, c4 = st.columns([1.5, 1.5, 1.5, 1.5])
            with c1:
                fecha_pago_dt = st.date_input("Fecha Correspondiente / Límite", value=datetime.now(), key="fijo_fecha_pago")
                tienda = st.selectbox("Tienda / Destino", ["Consolidado (Ambas Tiendas)", "Santa Elena", "Monteverde Extremo"], key="fijo_tienda")
            with c2:
                categoria = st.selectbox("Categoría", [
                    "Alquileres", 
                    "Planilla", 
                    "Impuestos Municipales / Patente", 
                    "Contabilidad / Servicios Profesionales", 
                    "Servicios Públicos", 
                    "Préstamos / Financiamiento", 
                    "Otros Fijos"
                ], key="fijo_cat")
                periodicidad = st.selectbox("Periodicidad de Pago", [
                    "Mensual", 
                    "Trimestral (Q1 / Q2 / Q3 / Q4)", 
                    "Semestral", 
                    "Anual", 
                    "Pago Único"
                ], key="fijo_period")
            with c3:
                monto = st.number_input("Monto en Colones (₡)", min_value=0.0, step=10000.0, key="fijo_monto")
                descripcion = st.text_input("Descripción / Proveedor", key="fijo_desc")
            with c4:
                st.markdown("<br>", unsafe_allow_html=True)
                submitted_fijo = st.form_submit_button("💾 Guardar Gasto Fijo", use_container_width=True)

            if submitted_fijo:
                if monto > 0:
                    anio = fecha_pago_dt.year
                    mes = mapping_meses.get(fecha_pago_dt.month, 'enero')
                    fecha_pago_str = fecha_pago_dt.strftime("%Y-%m-%d")

                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()
                    cursor.execute(
                        "INSERT INTO obligaciones (anio, mes, tienda, tipo_gasto, categoria, descripcion, monto, fecha_pago, periodicidad) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        (anio, mes, tienda, "Fijo", categoria, descripcion, monto, fecha_pago_str, periodicidad)
                    )
                    conn.commit()
                    conn.close()
                    st.success(f"¡Gasto fijo ({periodicidad}) de ₡ {monto:,.2f} programado para {fecha_pago_str} registrado con éxito!")
                    st.rerun()
                else:
                    st.error("Por favor ingrese un monto válido mayor a cero.")

    with tab_variables:
        with st.form("form_gasto_variable", clear_on_submit=True):
            st.markdown("###### Registrar Gasto Variable / Operativo Diario")
            c1, c2, c3, c4 = st.columns([1.5, 1.5, 1.5, 1.5])
            with c1:
                fecha_pago_var_dt = st.date_input("Fecha Correspondiente / Pago", value=datetime.now(), key="var_fecha_pago")
                tienda_v = st.selectbox("Tienda / Destino", ["Consolidado (Ambas Tiendas)", "Santa Elena", "Monteverde Extremo"], key="var_tienda")
            with c2:
                categoria_v = st.selectbox("Categoría", [
                    "Proveedores / Mercadería", 
                    "Mantenimiento & Reparaciones", 
                    "Insumos de Tienda", 
                    "Comisiones / Extras", 
                    "Otros Variables"
                ], key="var_cat")
                periodicidad_v = st.selectbox("Periodicidad de Pago", [
                    "Pago Único", 
                    "Mensual", 
                    "Trimestral (Q1 / Q2 / Q3 / Q4)"
                ], key="var_period")
            with c3:
                monto_v = st.number_input("Monto en Colones (₡)", min_value=0.0, step=5000.0, key="var_monto")
                descripcion_v = st.text_input("Descripción / Proveedor", key="var_desc")
            with c4:
                st.markdown("<br>", unsafe_allow_html=True)
                submitted_var = st.form_submit_button("💾 Guardar Gasto Variable", use_container_width=True)

            if submitted_var:
                if monto_v > 0:
                    anio_v = fecha_pago_var_dt.year
                    mes_v = mapping_meses.get(fecha_pago_var_dt.month, 'enero')
                    fecha_pago_var_str = fecha_pago_var_dt.strftime("%Y-%m-%d")

                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()
                    cursor.execute(
                        "INSERT INTO obligaciones (anio, mes, tienda, tipo_gasto, categoria, descripcion, monto, fecha_pago, periodicidad) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        (anio_v, mes_v, tienda_v, "Variable", categoria_v, descripcion_v, monto_v, fecha_pago_var_str, periodicidad_v)
                    )
                    conn.commit()
                    conn.close()
                    st.success(f"¡Gasto variable de ₡ {monto_v:,.2f} con fecha {fecha_pago_var_str} registrado con éxito!")
                    st.rerun()
                else:
                    st.error("Por favor ingrese un monto válido mayor a cero.")

    st.markdown("---")
    
    # Controles de Filtro por Tienda y Visualización
    col_filtro, col_vacio = st.columns([2, 2])
    with col_filtro:
        filtro_tienda = st.selectbox(
            "🔍 Filtrar Egresos por Tienda", 
            ["Consolidado (Ambas Tiendas)", "Santa Elena", "Monteverde Extremo"],
            key="filtro_tienda_egresos"
        )

    # Consulta de registros desde la base de datos
    conn = sqlite3.connect(db_path)
    df_registros = pd.read_sql_query(
        "SELECT id, fecha_pago as 'Fecha Pago', periodicidad as Periodicidad, mes as Mes, tienda as Tienda, tipo_gasto as Tipo, categoria as Categoria, descripcion as Descripcion, monto as Monto FROM obligaciones WHERE anio = 2026 ORDER BY fecha_pago DESC", 
        conn
    )
    conn.close()

    if not df_registros.empty:
        # Aplicar el filtro según la tienda seleccionada
        if filtro_tienda != "Consolidado (Ambas Tiendas)":
            df_filtrado = df_registros[df_registros['Tienda'].isin([filtro_tienda, "Consolidado (Ambas Tiendas)"])].copy()
        else:
            df_filtrado = df_registros.copy()

        # Cálculo de totales
        total_egresos = df_filtrado['Monto'].sum()
        total_fijos = df_filtrado[df_filtrado['Tipo'] == 'Fijo']['Monto'].sum()
        total_variables = df_filtrado[df_filtrado['Tipo'] == 'Variable']['Monto'].sum()

        # Tarjetas KPI de resumen
        k1, k2, k3 = st.columns(3)
        with k1:
            st.metric("🔴 TOTAL EGRESOS PROGRAMADOS", f"₡ {total_egresos:,.2f}", delta=filtro_tienda, delta_color="inverse")
        with k2:
            st.metric("📌 GASTOS FIJOS / OBLIGACIONES", f"₡ {total_fijos:,.2f}")
        with k3:
            st.metric("⚡ GASTOS VARIABLES / OPERATIVOS", f"₡ {total_variables:,.2f}")

        st.markdown("<br>", unsafe_allow_html=True)

        # Mostrar Tabla de Resultados
        st.dataframe(
            df_filtrado,
            column_config={
                "Monto": st.column_config.NumberColumn("Monto (₡)", format="₡ %,.2f"),
                "Fecha Pago": st.column_config.DateColumn("Fecha Correspondiente", format="YYYY-MM-DD"),
                "Periodicidad": st.column_config.TextColumn("Frecuencia")
            },
            use_container_width=True,
            hide_index=True
        )
        
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
        st.info("Aún no hay egresos registrados en la base de datos para 2026. Utiliza los formularios superiores para programar tus pagos fijos, trimestrales y variables.")
