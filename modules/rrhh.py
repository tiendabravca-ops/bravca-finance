import streamlit as st
import pandas as pd
import sqlite3
import os
from datetime import datetime
from PIL import Image

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
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS entrevistas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            candidato TEXT NOT NULL,
            tienda TEXT NOT NULL,
            puesto TEXT NOT NULL,
            fecha TEXT NOT NULL,
            calificacion INTEGER,
            estado TEXT DEFAULT 'En Evaluación',
            notas TEXT
        )
    ''')
    conn.commit()

def run():
    st.markdown('<div class="brand-title">Gestión de Recursos Humanos</div>', unsafe_allow_html=True)
    st.markdown('<div class="brand-sub">CONTROL DE PERSONAL, PLANILLA, RECLUTAMIENTO Y COSTOS • BRÁVCA</div>', unsafe_allow_html=True)

    conn = sqlite3.connect('bravca.db')
    crear_tablas_rrhh_si_no_existen(conn)

    # Crear carpetas locales para almacenamiento de archivos
    os.makedirs("archivos_rrhh/folletos", exist_ok=True)
    os.makedirs("archivos_rrhh/manuales", exist_ok=True)

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "👥 Colaboradores", 
        "💸 Adelantos y Planilla", 
        "📊 Análisis & Gráficos",
        "📢 Reclutamiento & Folletos", 
        "📋 Manuales de Puesto", 
        "🗣️ Entrevistas"
    ])

    # ---------------------------------------------------------
    # TAB 1: COLABORADORES
    # ---------------------------------------------------------
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
            
            # Botón para exportar a Excel / CSV
            csv = df_col.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Exportar Lista a CSV", csv, "personal_bravca.csv", "text/csv")
        else:
            st.info("No hay colaboradores registrados todavía.")

    # ---------------------------------------------------------
    # TAB 2: ADELANTOS Y PLANILLA
    # ---------------------------------------------------------
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
            st.warning("Debe registrar al menos un colaborador en la pestaña de Colaboradores.")

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

    # ---------------------------------------------------------
    # TAB 3: ANÁLISIS & GRÁFICOS DE COSTOS
    # ---------------------------------------------------------
    with tab3:
        st.markdown("### 📊 Distribución Visual de Costos de Planilla")
        
        df_costos = pd.read_sql("""
            SELECT tienda, COUNT(id) as total_empleados, SUM(salario_base) as total_planilla 
            FROM colaboradores WHERE estado='Activo' GROUP BY tienda
        """, conn)

        if not df_costos.empty:
            # Tarjetas ejecutivas superiores
            c1, c2 = st.columns(2)
            total_general = df_costos['total_planilla'].sum()
            total_empleados = df_costos['total_empleados'].sum()

            with c1:
                st.markdown(f"""
                    <div class="brabca-card">
                        <div class="card-label">Planilla Mensual Consolidada</div>
                        <div class="card-value">₡ {total_general:,.2f}</div>
                    </div>
                """, unsafe_allow_html=True)
            with c2:
                st.markdown(f"""
                    <div class="brabca-card">
                        <div class="card-label">Total de Colaboradores Activos</div>
                        <div class="card-value-gold">{total_empleados} Personas</div>
                    </div>
                """, unsafe_allow_html=True)

            st.markdown("---")
            col_chart1, col_chart2 = st.columns(2)
            
            with col_chart1:
                st.markdown("##### **Costo de Planilla por Tienda (₡)**")
                df_bar = df_costos.set_index('tienda')[['total_planilla']]
                st.bar_chart(df_bar)

            with col_chart2:
                st.markdown("##### **Distribución de Personal por Tienda**")
                df_emp = df_costos.set_index('tienda')[['total_empleados']]
                st.bar_chart(df_emp)

        else:
            st.info("Aún no hay suficiente información para generar los gráficos de costos.")

    # ---------------------------------------------------------
    # TAB 4: RECLUTAMIENTO & FOLLETOS (IMÁGENES)
    # ---------------------------------------------------------
    with tab4:
        st.markdown("### 📢 Banco de Afiches y Folletos de Contratación")
        
        with st.expander("📤 Subir Nuevo Folleto de Reclutamiento"):
            folleto_file = st.file_uploader("Selecciona la imagen promocional (PNG/JPG)", type=["png", "jpg", "jpeg"])
            nombre_folleto = st.text_input("Nombre / Referencia del Folleto (Ej: Busqueda_Cajero_SantaElena)")
            
            if st.button("Guardar Folleto") and folleto_file and nombre_folleto:
                path = os.path.join("archivos_rrhh/folletos", f"{nombre_folleto}.png")
                image = Image.open(folleto_file)
                image.save(path)
                st.success("¡Folleto guardado correctamente!")
                st.rerun()

        st.markdown("---")
        st.markdown("### Folletos Disponibles")
        folletos_existentes = os.listdir("archivos_rrhh/folletos")
        
        if folletos_existentes:
            cols = st.columns(3)
            for idx, file in enumerate(folletos_existentes):
                with cols[idx % 3]:
                    file_path = os.path.join("archivos_rrhh/folletos", file)
                    st.image(file_path, caption=file.replace(".png", ""), use_container_width=True)
                    with open(file_path, "rb") as f:
                        st.download_button(f"📥 Descargar {file}", f, file_name=file, key=f"btn_folleto_{idx}")
        else:
            st.info("Aún no se han subido folletos de contratación.")

    # ---------------------------------------------------------
    # TAB 5: MANUALES DE PUESTO (DOCUMENTOS)
    # ---------------------------------------------------------
    with tab5:
        st.markdown("### 📋 Manuales de Puesto y Políticas de Tienda")
        
        with st.expander("📤 Cargar Nuevo Manual / Documento (PDF/Word)"):
            doc_file = st.file_uploader("Selecciona el archivo PDF o Word", type=["pdf", "docx"])
            titulo_doc = st.text_input("Título del Puesto / Documento (Ej: Manual_Vendedor_Monteverde)")
            
            if st.button("Guardar Documento") and doc_file and titulo_doc:
                ext = doc_file.name.split(".")[-1]
                path = os.path.join("archivos_rrhh/manuales", f"{titulo_doc}.{ext}")
                with open(path, "wb") as f:
                    f.write(doc_file.getbuffer())
                st.success("¡Documento guardado con éxito!")
                st.rerun()

        st.markdown("---")
        st.markdown("### Biblioteca de Manuales")
        manuales_existentes = os.listdir("archivos_rrhh/manuales")
        
        if manuales_existentes:
            for file in manuales_existentes:
                file_path = os.path.join("archivos_rrhh/manuales", file)
                col_name, col_btn = st.columns([3, 1])
                with col_name:
                    st.markdown(f"📄 **{file}**")
                with col_btn:
                    with open(file_path, "rb") as f:
                        st.download_button("📥 Descargar", f, file_name=file, key=f"btn_man_{file}")
        else:
            st.info("No hay manuales cargados en la biblioteca.")

    # ---------------------------------------------------------
    # TAB 6: ENTREVISTAS Y CANDIDATOS
    # ---------------------------------------------------------
    with tab6:
        st.markdown("### 🗣️ Registro y Control de Entrevistas")
        
        with st.form("form_entrevista", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                candidato = st.text_input("Nombre del Candidato")
                tienda_ent = st.selectbox("Tienda Destino", ["Santa Elena", "Monteverde Extremo"])
                puesto_ent = st.text_input("Puesto al que Aplica")
            with c2:
                fecha_ent = st.date_input("Fecha de Entrevista", value=datetime.today())
                calificacion = st.slider("Calificación (1 al 10)", 1, 10, 7)
                estado_ent = st.selectbox("Estado", ["En Evaluación", "Contratado", "Descartado"])
            
            notas_ent = st.text_area("Notas / Impresiones de la Entrevista")
            
            if st.form_submit_button("Guardar Entrevista") and candidato:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO entrevistas (candidato, tienda, puesto, fecha, calificacion, estado, notas)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (candidato, tienda_ent, puesto_ent, str(fecha_ent), calificacion, estado_ent, notas_ent))
                conn.commit()
                st.success(f"Entrevista de {candidato} registrada con éxito.")
                st.rerun()

        st.markdown("---")
        st.markdown("### Historial de Candidatos Entrevistados")
        df_ent = pd.read_sql("SELECT fecha, candidato, tienda, puesto, calificacion, estado, notas FROM entrevistas ORDER BY fecha DESC", conn)
        if not df_ent.empty:
            st.dataframe(df_ent, use_container_width=True)
        else:
            st.info("No hay entrevistas registradas.")

    conn.close()
