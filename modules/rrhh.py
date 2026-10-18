import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

def crear_tablas_rrhh_si_no_existen(conn):
    """Garantiza la existencia de las tablas de RRHH en la base de datos"""
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS colaboradores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            tienda TEXT NOT NULL,
            puesto TEXT NOT NULL,
            salario_base REAL NOT NULL,
            fecha_ingreso TEXT NOT NULL,
            estado TEXT DEFAULT 'Activo'
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS movimientos_rrhh (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            colaborador_id INTEGER,
            tipo TEXT NOT NULL,
            monto REAL NOT NULL,
            fecha TEXT NOT NULL,
            nota TEXT,
            FOREIGN KEY (colaborador_id) REFERENCES colaboradores (id)
        )
    ''')
    conn.commit()

def run():
    st.markdown('<div class="brand-title">Gestión de Recursos Humanos</div>', unsafe_allow_html=True)
    st.markdown('<div class="brand-sub">CONTROL DE PERSONAL, PLANILLA Y ADELANTOS • BRÁVCA</div>', unsafe_allow_html=True)

    conn = sqlite3.connect('bravca.db')
    
    # Crear tablas automáticamente si aún no existen
    crear_tablas_rrhh_si_no_existen(conn)

    tab1, tab2, tab3 = st.tabs(["👥 Colaboradores", "💸 Adelantos y Planilla", "📊 Resumen de Costos"])

    with tab1:
        st.markdown("### Registro de Nuevo Colaborador")
        with st.form("form_colaborador", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                nombre = st.text_input("Nombre Completo")
                tienda = st.selectbox("Tienda", ["Santa Elena", "Monteverde Extremo"])
                puesto = st.text_input("Puesto / Rol")
            with col2:
                salario_base = st.number_input("Salario Base (₡)", min_value=0.0, step=10000.0)
                fecha_ingreso = st.date_input("Fecha de Ingreso", value=datetime.today())
            
            submitted = st.form_submit_button("Guardar Colaborador")
            if submitted and nombre:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO colaboradores (nombre, tienda, puesto, salario_base, fecha_ingreso) VALUES (?, ?, ?, ?, ?)",
                    (nombre, tienda, puesto, salario_base, str(fecha_ingreso))
                )
                conn.commit()
                st.success(f"¡Colaborador {nombre} registrado con éxito!")
                st.rerun()

        st.markdown("---")
        st.markdown("### Listado de Personal Activo")
        df_col = pd.read_sql("SELECT id, nombre, tienda, puesto, salario_base, fecha_ingreso FROM colaboradores WHERE estado='Activo'", conn)
        if not df_col.empty:
            st.dataframe(df_col, use_container_width=True)
        else:
            st.info("No hay colaboradores registrados todavía.")

    with tab2:
        st.markdown("### Registro de Adelantos o Movimientos")
        df_colab_list = pd.read_sql("SELECT id, nombre FROM colaboradores WHERE estado='Activo'", conn)
        
        if not df_colab_list.empty:
            colab_dict = dict(zip(df_colab_list['nombre'], df_colab_list['id']))
            
            with st.form("form_movimiento", clear_on_submit=True):
                c1, c2, c3 = st.columns(3)
                with c1:
                    sel_colab = st.selectbox("Colaborador", list(colab_dict.keys()))
                with c2:
                    tipo_mov = st.selectbox("Tipo de Movimiento", ["Adelanto de Salario", "Bono / Incentivo", "Deducción Extraordinaria"])
                with c3:
                    monto = st.number_input("Monto (₡)", min_value=0.0, step=5000.0)
                
                nota = st.text_input("Observación / Motivo")
                sub_mov = st.form_submit_button("Registrar Movimiento")
                
                if sub_mov and monto > 0:
                    cursor = conn.cursor()
                    cursor.execute(
                        "INSERT INTO movimientos_rrhh (colaborador_id, tipo, monto, fecha, nota) VALUES (?, ?, ?, ?, ?)",
                        (colab_dict[sel_colab], tipo_mov, monto, str(datetime.today().date()), nota)
                    )
                    conn.commit()
                    st.success("Movimiento registrado correctamente.")
                    st.rerun()
        else:
            st.warning("Debe registrar al menos un colaborador en la pestaña anterior.")

        st.markdown("### Historial de Movimientos Recientes")
        df_mov = pd.read_sql("""
            SELECT m.fecha, c.nombre, m.tipo, m.monto, m.nota 
            FROM movimientos_rrhh m 
            JOIN colaboradores c ON m.colaborador_id = c.id 
            ORDER BY m.fecha DESC LIMIT 20
        """, conn)
        if not df_mov.empty:
            st.dataframe(df_mov, use_container_width=True)
        else:
            st.info("No hay movimientos registrados.")

    with tab3:
        st.markdown("### Análisis de Impacto en Planilla")
        df_resumen = pd.read_sql("""
            SELECT tienda, COUNT(id) as total_empleados, SUM(salario_base) as planilla_total 
            FROM colaboradores WHERE estado='Activo' GROUP BY tienda
        """, conn)
        
        if not df_resumen.empty:
            st.dataframe(df_resumen, use_container_width=True)
            total_general = df_resumen['planilla_total'].sum()
            st.markdown(f"""
                <div class="brabca-card">
                    <div class="card-label">Planilla Base Mensual Consolidada</div>
                    <div class="card-value">₡ {total_general:,.2f}</div>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.info("Sin datos para calcular el resumen.")

    conn.close()
