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
        "ALTER TABLE obligaciones ADD COLUMN periodicidad TEXT DEFAULT 'Mensual'",
        "ALTER TABLE obligaciones ADD COLUMN pagado INTEGER DEFAULT 0"
    ]
    
    for mig in migraciones:
        try:
            cursor.execute(mig)
        except Exception:
            pass

    conn.commit()
    conn.close()

def mapear_icono_categoria(cat):
    """Agrega badges visuales a las categorías para distinguirlas claramente."""
    cat_str = str(cat)
    if "Planilla" in cat_str or "Salario" in cat_str:
        return "💼 " + cat_str
    elif "Alquiler" in cat_str:
        return "🏢 " + cat_str
    elif "Impuesto" in cat_str or "Patente" in cat_str:
        return "🏛️ " + cat_str
    elif "Contabilidad" in cat_str or "Profesionales" in cat_str:
        return "📊 " + cat_str
    elif "Servicios" in cat_str:
        return "💡 " + cat_str
    elif "Préstamo" in cat_str or "Financiamiento" in cat_str:
        return "🏦 " + cat_str
    elif "Mercadería" in cat_str or "Proveedor" in cat_str:
        return "📦 " + cat_str
    elif "Mantenimiento" in cat_str or "Reparaciones" in cat_str:
        return "🛠️ " + cat_str
    elif "Insumos" in cat_str:
        return "🏷️ " + cat_str
    else:
        return "📌 " + cat_str

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
                    "Planilla / Salarios", 
                    "Alquileres", 
                    "Impuestos Municipales / Patente", 
                    "Contabilidad / Servicios Profesionales", 
                    "Servicios Públicos", 
                    "Préstamos / Financiamiento", 
                    "Otros Fijos"
                ], key="fijo_cat")
                periodicidad = st.selectbox("Periodicidad de Pago", [
                    "Quincenal",
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
                        "INSERT INTO obligaciones (anio, mes, tienda, tipo_gasto, categoria, descripcion, monto, fecha_pago, periodicidad, pagado) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0)",
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
                    "Quincenal",
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
                        "INSERT INTO obligaciones (anio, mes, tienda, tipo_gasto, categoria, descripcion, monto, fecha_pago, periodicidad, pagado) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0)",
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
        "SELECT id, pagado as Pagado, fecha_pago as 'Fecha Pago', periodicidad as Periodicidad, mes as Mes, tienda as Tienda, tipo_gasto as Tipo, categoria as Categoria, descripcion as Descripcion, monto as Monto FROM obligaciones WHERE anio = 2026 ORDER BY fecha_pago DESC", 
        conn
    )
    conn.close()

    if not df_registros.empty:
        # Normalizar estado booleano para el Data Editor
        df_registros['Pagado'] = df_registros['Pagado'].apply(lambda x: True if x == 1 or x is True else False)

        # Aplicar el filtro según la tienda seleccionada
        if filtro_tienda != "Consolidado (Ambas Tiendas)":
            df_filtrado = df_registros[df_registros['Tienda'].isin([filtro_tienda, "Consolidado (Ambas Tiendas)"])].copy()
        else:
            df_filtrado = df_registros.copy()

        # Cálculo de totales dinámicos
        total_programado = df_filtrado['Monto'].sum()
        total_pagado = df_filtrado[df_filtrado['Pagado'] == True]['Monto'].sum()
        saldo_pendiente = total_programado - total_pagado

        # Tarjetas KPI de resumen
        k1, k2, k3 = st.columns(3)
        with k1:
            st.metric("🔴 TOTAL PROGRAMADO", f"₡ {total_programado:,.2f}", delta=filtro_tienda, delta_color="inverse")
        with k2:
            st.metric("✅ TOTAL PAGADO", f"₡ {total_pagado:,.2f}")
        with k3:
            st.metric("⏳ SALDO PENDIENTE POR PAGAR", f"₡ {saldo_pendiente:,.2f}", delta=f"-₡ {total_pagado:,.2f} Pagados", delta_color="normal")

        st.markdown("<br>", unsafe_allow_html=True)

        # Aplicar formato de categorías e íconos para la vista
        df_filtrado['Categoria_Display'] = df_filtrado['Categoria'].apply(mapear_icono_categoria)
        df_filtrado['Tipo_Display'] = df_filtrado['Tipo'].apply(lambda x: "🔴 Fijo" if x == "Fijo" else "⚡ Variable")

        st.caption("💡 Marca la casilla **'☑️ Pagado'** para registrar un egreso como saldado. El saldo pendiente se actualizará al guardar los cambios.")

        # Data Editor interactivo con Checkbox
        edited_df = st.data_editor(
            df_filtrado[['id', 'Pagado', 'Fecha Pago', 'Periodicidad', 'Mes', 'Tienda', 'Tipo_Display', 'Categoria_Display', 'Descripcion', 'Monto']],
            column_config={
                "id": st.column_config.NumberColumn("ID", format="%d", disabled=True),
                "Pagado": st.column_config.CheckboxColumn("☑️ Pagado?", help="Marcar si el pago ya fue realizado"),
                "Monto": st.column_config.NumberColumn("Monto (₡)", format="₡ %,.2f", disabled=True),
                "Fecha Pago": st.column_config.DateColumn("Fecha Correspondiente", format="YYYY-MM-DD", disabled=True),
                "Periodicidad": st.column_config.TextColumn("Frecuencia", disabled=True),
                "Tipo_Display": st.column_config.TextColumn("Tipo Gasto", disabled=True),
                "Categoria_Display": st.column_config.TextColumn("Categoría", disabled=True),
                "Descripcion": st.column_config.TextColumn("Descripción", disabled=True),
                "Tienda": st.column_config.TextColumn("Tienda", disabled=True),
                "Mes": st.column_config.TextColumn("Mes", disabled=True)
            },
            use_container_width=True,
            hide_index=True,
            key="editor_pagos_obligaciones"
        )

        # Guardar cambios en el estado de 'Pagado'
        if st.button("💾 Guardar Estado de Pagos", use_container_width=True):
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            for _, row in edited_df.iterrows():
                p_val = 1 if row['Pagado'] else 0
                r_id = row['id']
                cursor.execute("UPDATE obligaciones SET pagado = ? WHERE id = ?", (p_val, r_id))
            conn.commit()
            conn.close()
            st.success("¡Estado de pagos actualizado correctamente!")
            st.rerun()

        st.markdown("---")

        # --- SECCIÓN DE EDICIÓN Y ELIMINACIÓN DE REGISTROS ---
        e1, e2 = st.columns([1, 1])

        with e1:
            st.markdown("###### ✏️ Editar Registro Existente")
            id_a_editar = st.number_input("ID de registro a editar", min_value=0, step=1, value=0, key="id_edit_input")

            if id_a_editar > 0:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT id, tienda, tipo_gasto, categoria, descripcion, monto, fecha_pago, periodicidad, pagado FROM obligaciones WHERE id = ?", (id_a_editar,))
                row_edit = cursor.fetchone()
                conn.close()

                if row_edit:
                    _, curr_tienda, curr_tipo, curr_cat, curr_desc, curr_monto, curr_fecha, curr_period, curr_pagado = row_edit
                    
                    try:
                        fecha_val = datetime.strptime(curr_fecha, "%Y-%m-%d").date() if curr_fecha else datetime.now().date()
                    except Exception:
                        fecha_val = datetime.now().date()

                    with st.form(f"form_edit_{id_a_editar}"):
                        st.caption(f"Modificando Registro ID #{id_a_editar}")
                        new_fecha = st.date_input("Fecha Correspondiente", value=fecha_val, key="edit_fecha")
                        new_tienda = st.selectbox("Tienda", ["Consolidado (Ambas Tiendas)", "Santa Elena", "Monteverde Extremo"], index=["Consolidado (Ambas Tiendas)", "Santa Elena", "Monteverde Extremo"].index(curr_tienda) if curr_tienda in ["Consolidado (Ambas Tiendas)", "Santa Elena", "Monteverde Extremo"] else 0, key="edit_tienda")
                        new_tipo = st.selectbox("Tipo de Gasto", ["Fijo", "Variable"], index=0 if curr_tipo == "Fijo" else 1, key="edit_tipo")
                        new_cat = st.text_input("Categoría", value=curr_cat, key="edit_cat")
                        new_period = st.selectbox("Periodicidad", ["Quincenal", "Mensual", "Trimestral (Q1 / Q2 / Q3 / Q4)", "Semestral", "Anual", "Pago Único"], index=["Quincenal", "Mensual", "Trimestral (Q1 / Q2 / Q3 / Q4)", "Semestral", "Anual", "Pago Único"].index(curr_period) if curr_period in ["Quincenal", "Mensual", "Trimestral (Q1 / Q2 / Q3 / Q4)", "Semestral", "Anual", "Pago Único"] else 1, key="edit_period")
                        new_desc = st.text_input("Descripción / Proveedor", value=curr_desc, key="edit_desc")
                        new_monto = st.number_input("Monto (₡)", min_value=0.0, value=float(curr_monto), step=5000.0, key="edit_monto")
                        new_pagado_bool = st.checkbox("¿Marcado como Pagado?", value=True if curr_pagado == 1 else False, key="edit_pagado_cb")

                        submitted_update = st.form_submit_button("🔄 Actualizar Registro", use_container_width=True)

                        if submitted_update:
                            new_anio = new_fecha.year
                            new_mes = mapping_meses.get(new_fecha.month, 'enero')
                            new_fecha_str = new_fecha.strftime("%Y-%m-%d")
                            new_pagado_val = 1 if new_pagado_bool else 0

                            conn = sqlite3.connect(db_path)
                            cursor = conn.cursor()
                            cursor.execute("""
                                UPDATE obligaciones 
                                SET anio = ?, mes = ?, tienda = ?, tipo_gasto = ?, categoria = ?, descripcion = ?, monto = ?, fecha_pago = ?, periodicidad = ?, pagado = ?
                                WHERE id = ?
                            """, (new_anio, new_mes, new_tienda, new_tipo, new_cat, new_desc, new_monto, new_fecha_str, new_period, new_pagado_val, id_a_editar))
                            conn.commit()
                            conn.close()

                            st.success(f"¡Registro #{id_a_editar} actualizado correctamente!")
                            st.rerun()
                else:
                    st.warning(f"No se encontró ningún registro con el ID #{id_a_editar}.")

        with e2:
            st.markdown("###### 🗑️ Eliminar Registro")
            id_a_borrar = st.number_input("ID de registro a eliminar", min_value=0, step=1, value=0, key="id_del_input")
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🗑️ Eliminar Registro Seleccionado", use_container_width=True):
                if id_a_borrar > 0:
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM obligaciones WHERE id = ?", (id_a_borrar,))
                    conn.commit()
                    conn.close()
                    st.success(f"Registro con ID #{id_a_borrar} eliminado correctamente.")
                    st.rerun()
                else:
                    st.error("Por favor ingrese un ID válido a eliminar.")
    else:
        st.info("Aún no hay egresos registrados en la base de datos para 2026. Utiliza los formularios superiores para programar tus pagos fijos, quincenales, trimestrales y variables.")
