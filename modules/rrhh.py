import streamlit as st
import pandas as pd
import sqlite3
import os
from datetime import datetime, timedelta
from PIL import Image

def crear_tablas_rrhh_si_no_existen(conn):
    """Garantiza la existencia de las tablas de RRHH y migra columnas sin perder datos"""
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS colaboradores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            tienda TEXT NOT NULL,
            puesto TEXT NOT NULL,
            tipo_pago TEXT DEFAULT 'Salario Fijo Mensual',
            salario_base REAL DEFAULT 0,
            tarifa_hora REAL DEFAULT 0,
            fecha_ingreso TEXT NOT NULL,
            estado TEXT DEFAULT 'Activo'
        )
    ''')
    
    # Migraciones defensivas para mantener compatibilidad
    try:
        cursor.execute("ALTER TABLE colaboradores ADD COLUMN tipo_pago TEXT DEFAULT 'Salario Fijo Mensual'")
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute("ALTER TABLE colaboradores ADD COLUMN tarifa_hora REAL DEFAULT 0")
    except sqlite3.OperationalError:
        pass

    # Asegura que ningún registro previo quede sin estado Activo
    cursor.execute("UPDATE colaboradores SET estado = 'Activo' WHERE estado IS NULL OR estado = ''")

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
        CREATE TABLE IF NOT EXISTS coberturas_libres (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            colaborador_id INTEGER,
            fecha TEXT NOT NULL,
            horas_trabajadas REAL NOT NULL,
            tarifa_hora REAL NOT NULL,
            monto_total REAL NOT NULL,
            motivo_cobertura TEXT,
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
    st.markdown('<div class="brand-title">Gestión de Recursos Humanos & Nómina</div>', unsafe_allow_html=True)
    st.markdown('<div class="brand-sub">CONTROL DE PERSONAL, PLANILLA POR HORAS/CCSS, COBERTURA Y COSTOS • BRÁVCA</div>', unsafe_allow_html=True)

    conn = sqlite3.connect('bravca.db')
    crear_tablas_rrhh_si_no_existen(conn)

    # Carpetas para archivos
    os.makedirs("archivos_rrhh/folletos", exist_ok=True)
    os.makedirs("archivos_rrhh/manuales", exist_ok=True)

    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "👥 Colaboradores", 
        "🧮 Planilla Neto & CCSS",
        "💸 Adelantos & Horas Libres", 
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
        
        col_tipo, _ = st.columns([2, 2])
        with col_tipo:
            tipo_pago = st.selectbox(
                "Modalidad de Pago", 
                ["Salario Fijo Mensual", "Por Horas / Fin de Semana"]
            )

        with st.form("form_colaborador", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                nombre = st.text_input("Nombre Completo (Ej: Nicole Corrales)")
                tienda = st.selectbox("Tienda Destino", ["Santa Elena", "Monteverde Extremo"])
                puesto = st.text_input("Puesto / Rol (Ej: Cubre Libres Fin de Semana)")
            with col2:
                if tipo_pago == "Salario Fijo Mensual":
                    salario_base = st.number_input("Salario Base Mensual (₡)", min_value=0.0, step=10000.0)
                    tarifa_hora = 0.0
                else:
                    salario_base = 0.0
                    tarifa_hora = st.number_input("Tarifa Base por Hora (₡)", min_value=1000.0, value=2000.0, step=250.0)
                    st.caption("ℹ️ Registra las horas trabajadas en la pestaña 'Adelantos & Horas Libres'.")

                fecha_ingreso = st.date_input("Fecha de Ingreso a la Empresa", value=datetime.today())
            
            submitted = st.form_submit_button("Guardar Colaborador")
            if submitted and nombre:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO colaboradores (nombre, tienda, puesto, tipo_pago, salario_base, tarifa_hora, fecha_ingreso, estado) VALUES (?, ?, ?, ?, ?, ?, ?, 'Activo')",
                    (nombre, tienda, puesto, tipo_pago, salario_base, tarifa_hora, str(fecha_ingreso))
                )
                conn.commit()
                st.success(f"¡Colaborador {nombre} registrado con éxito!")
                st.rerun()

        st.markdown("---")
        st.markdown("### Listado de Personal Activo")
        df_col = pd.read_sql("SELECT id, nombre, tienda, puesto, COALESCE(tipo_pago, 'Salario Fijo Mensual') as tipo_pago, salario_base, COALESCE(tarifa_hora, 0) as tarifa_hora, fecha_ingreso FROM colaboradores", conn)
        if not df_col.empty:
            st.dataframe(df_col, use_container_width=True)
            csv = df_col.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Exportar Lista a CSV", csv, "personal_bravca.csv", "text/csv")
        else:
            st.info("No hay colaboradores registrados todavía.")

    # ---------------------------------------------------------
    # TAB 2: CÁLCULO DE PLANILLA NETO & CCSS + SUMATORIA TOTAL + RECIBOS
    # ---------------------------------------------------------
    with tab2:
        st.markdown("### 🧮 Cálculo de Nómina Quincenal / Mensual con CCSS")
        st.caption("Combina colaboradores de salario fijo con colaboradores de pago variable por horas.")

        c_periodo, _ = st.columns([2, 2])
        with c_periodo:
            periodo = st.radio(
                "Selecciona el Periodo de Pago:", 
                ["1era Quincena (50%)", "2da Quincena (50%)", "Mensual Completo (100%)"], 
                horizontal=True
            )

        factor_periodo = 0.5 if "Quincena" in periodo else 1.0

        df_activos = pd.read_sql("SELECT id, nombre, tienda, puesto, COALESCE(tipo_pago, 'Salario Fijo Mensual') as tipo_pago, salario_base, COALESCE(tarifa_hora, 0) as tarifa_hora FROM colaboradores", conn)

        if not df_activos.empty:
            lista_planilla = []
            for _, emp in df_activos.iterrows():
                emp_id = emp['id']
                
                df_cob = pd.read_sql(f"SELECT SUM(monto_total) as total, SUM(horas_trabajadas) as horas FROM coberturas_libres WHERE colaborador_id={emp_id}", conn)
                total_coberturas = df_cob['total'].iloc[0] if df_cob['total'].iloc[0] else 0.0
                horas_totales = df_cob['horas'].iloc[0] if df_cob['horas'].iloc[0] else 0.0

                if emp['tipo_pago'] == "Salario Fijo Mensual":
                    salario_periodo = emp['salario_base'] * factor_periodo
                    salario_bruto = salario_periodo + total_coberturas
                else:
                    salario_periodo = 0.0
                    salario_bruto = total_coberturas

                df_ad = pd.read_sql(f"SELECT SUM(monto) as total FROM movimientos_rrhh WHERE colaborador_id={emp_id} AND tipo LIKE '%Adelanto%'", conn)
                total_adelantos = df_ad['total'].iloc[0] if df_ad['total'].iloc[0] else 0.0

                ccss_obrero = salario_bruto * 0.1067
                ccss_patronal = salario_bruto * 0.2667
                pago_neto = salario_bruto - ccss_obrero - total_adelantos

                lista_planilla.append({
                    "ID": emp['id'],
                    "Colaborador": emp['nombre'],
                    "Modalidad": emp['tipo_pago'],
                    "Tienda": emp['tienda'],
                    "Puesto": emp['puesto'],
                    f"Salario Base ({periodo.split(' ')[0]})": salario_periodo,
                    "Horas Trabajadas": horas_totales,
                    "Total Pago por Horas (+)": total_coberturas,
                    "Salario Bruto": salario_bruto,
                    "CCSS Obrero (10.67%) (-)": ccss_obrero,
                    "Adelantos (-)": total_adelantos,
                    "Pago Neto Liquido": pago_neto,
                    "Costo Patronal CCSS (26.67%)": ccss_patronal
                })

            df_planilla_final = pd.DataFrame(lista_planilla)
            col_sal_periodo = f"Salario Base ({periodo.split(' ')[0]})"
            
            st.dataframe(df_planilla_final.drop(columns=["ID"]).style.format({
                col_sal_periodo: "₡{:,.2f}",
                "Total Pago por Horas (+)": "₡{:,.2f}",
                "Salario Bruto": "₡{:,.2f}",
                "CCSS Obrero (10.67%) (-)": "₡{:,.2f}",
                "Adelantos (-)": "₡{:,.2f}",
                "Pago Neto Liquido": "₡{:,.2f}",
                "Costo Patronal CCSS (26.67%)": "₡{:,.2f}"
            }), use_container_width=True)

            st.markdown("#### 📊 Consolidado Financiero de la Planilla")
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.metric("Total Salario Bruto", f"₡ {df_planilla_final['Salario Bruto'].sum():,.2f}")
            with c2:
                st.metric("Total Neto a Pagar", f"₡ {df_planilla_final['Pago Neto Liquido'].sum():,.2f}")
            with c3:
                st.metric("CCSS Obrero (10.67%)", f"₡ {df_planilla_final['CCSS Obrero (10.67%) (-)'].sum():,.2f}")
            with c4:
                st.metric("CCSS Patronal (26.67%)", f"₡ {df_planilla_final['Costo Patronal CCSS (26.67%)'].sum():,.2f}")

            csv_plan = df_planilla_final.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Exportar Reporte Completo a CSV", csv_plan, "planilla_completa_bravca.csv", "text/csv")

            st.markdown("---")
            st.markdown("### 📄 Generar Comprobante / Recibo de Pago Individual")
            
            emp_seleccionado = st.selectbox("Selecciona un colaborador para ver su boleta de pago:", df_planilla_final['Colaborador'].tolist())

            if emp_seleccionado:
                datos_emp = df_planilla_final[df_planilla_final['Colaborador'] == emp_seleccionado].iloc[0]

                html_recibo = f"""
                <div style="background-color: #ffffff; border: 2px solid #102A43; padding: 25px; border-radius: 10px; font-family: 'Inter', sans-serif; color: #102A43;">
                    <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #D9E2EC; padding-bottom: 10px;">
                        <div>
                            <h2 style="margin:0; color: #102A43; font-weight: 800;">bráVca</h2>
                            <span style="font-size: 12px; color: #627D98;">SOUVENIR & EXTREMO • MONTEVERDE</span>
                        </div>
                        <div style="text-align: right;">
                            <h3 style="margin:0; color: #102A43;">COMPROBANTE DE PAGO</h3>
                            <span style="font-size: 13px; color: #627D98;">{periodo} • {datetime.today().strftime('%d/%m/%Y')}</span>
                        </div>
                    </div>
                    
                    <div style="margin-top: 15px; font-size: 14px;">
                        <p style="margin: 4px 0;"><b>Colaborador:</b> {datos_emp['Colaborador']}</p>
                        <p style="margin: 4px 0;"><b>Tienda:</b> {datos_emp['Tienda']} | <b>Puesto:</b> {datos_emp['Puesto']}</p>
                        <p style="margin: 4px 0;"><b>Modalidad:</b> {datos_emp['Modalidad']}</p>
                    </div>

                    <table style="width: 100%; border-collapse: collapse; margin-top: 15px; font-size: 14px;">
                        <thead>
                            <tr style="background-color: #F4F6F9; border-bottom: 1px solid #D9E2EC; text-align: left;">
                                <th style="padding: 8px;">Concepto</th>
                                <th style="padding: 8px; text-align: right;">Detalle / Horas</th>
                                <th style="padding: 8px; text-align: right;">Monto (₡)</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td style="padding: 8px;">Salario Base Periodo</td>
                                <td style="padding: 8px; text-align: right;">-</td>
                                <td style="padding: 8px; text-align: right;">₡ {datos_emp[col_sal_periodo]:,.2f}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px;">Horas Trabajadas / Libres (+):</td>
                                <td style="padding: 8px; text-align: right;">{datos_emp['Horas Trabajadas']} hrs</td>
                                <td style="padding: 8px; text-align: right;">₡ {datos_emp['Total Pago por Horas (+)']:,.2f}</td>
                            </tr>
                            <tr style="background-color: #F9FAFC;">
                                <td style="padding: 8px;"><b>SALARIO BRUTO TOTAL</b></td>
                                <td style="padding: 8px; text-align: right;">-</td>
                                <td style="padding: 8px; text-align: right;"><b>₡ {datos_emp['Salario Bruto']:,.2f}</b></td>
                            </tr>
                            <tr>
                                <td style="padding: 8px; color: #C53030;">CCSS Obrero (10.67%) (-)</td>
                                <td style="padding: 8px; text-align: right; color: #C53030;">Deducción de Ley</td>
                                <td style="padding: 8px; text-align: right; color: #C53030;">- ₡ {datos_emp['CCSS Obrero (10.67%) (-)']:,.2f}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px; color: #C53030;">Adelantos / Deducciones (-)</td>
                                <td style="padding: 8px; text-align: right; color: #C53030;">Anticipos</td>
                                <td style="padding: 8px; text-align: right; color: #C53030;">- ₡ {datos_emp['Adelantos (-)']:,.2f}</td>
                            </tr>
                            <tr style="border-top: 2px solid #102A43; background-color: #E0FC3E; font-size: 16px;">
                                <td style="padding: 10px; color: #102A43;"><b>PAGO NETO LÍQUIDO A TRANSFERIR</b></td>
                                <td style="padding: 10px; text-align: right;">-</td>
                                <td style="padding: 10px; text-align: right; color: #102A43;"><b>₡ {datos_emp['Pago Neto Liquido']:,.2f}</b></td>
                            </tr>
                        </tbody>
                    </table>

                    <div style="margin-top: 30px; display: flex; justify-content: space-between; text-align: center; font-size: 12px; color: #627D98;">
                        <div style="border-top: 1px solid #9FB3C8; width: 40%; padding-top: 5px;">Firma Patrono / Gerencia</div>
                        <div style="border-top: 1px solid #9FB3C8; width: 40%; padding-top: 5px;">Firma Conforme Colaborador</div>
                    </div>
                </div>
                """

                st.markdown(html_recibo, unsafe_allow_html=True)

        else:
            st.info("No hay colaboradores para procesar en este momento.")

    # ---------------------------------------------------------
    # TAB 3: REGISTRO DE HORAS DIRECTO
    # ---------------------------------------------------------
    with tab3:
        st.markdown("### Registro de Horas Trabajadas y Movimientos")
        df_colab_list = pd.read_sql("SELECT id, nombre, COALESCE(tarifa_hora, 2000) as tarifa_hora FROM colaboradores", conn)
        
        if not df_colab_list.empty:
            colab_dict = dict(zip(df_colab_list['nombre'], df_colab_list['id']))
            tarifa_dict = dict(zip(df_colab_list['id'], df_colab_list['tarifa_hora']))

            col_a, col_b = st.columns(2)

            with col_a:
                st.markdown("##### ⏳ Registrar Horas Trabajadas (Suma Directa)")
                with st.form("form_cobertura_directa", clear_on_submit=True):
                    sel_colab_cob = st.selectbox("Colaborador", list(colab_dict.keys()), key="cob_colab")
                    c_id = colab_dict[sel_colab_cob]
                    tarifa_sugerida = tarifa_dict[c_id] if tarifa_dict[c_id] > 0 else 2000.0

                    fecha_turno = st.date_input("Fecha o Día del Turno", value=datetime.today())
                    total_horas = st.number_input("Cantidad Total de Horas Trabajadas (Ej: 8, 12, 16 hrs)", min_value=0.5, max_value=100.0, value=8.0, step=0.5)
                    tarifa = st.number_input("Tarifa por Hora (₡)", min_value=1000.0, value=float(tarifa_sugerida), step=250.0)
                    motivo = st.text_input("Motivo / Tienda (Ej: Cobertura Sábado y Domingo Santa Elena)")
                    
                    monto_tot = total_horas * tarifa
                    st.info(f"💰 **Total a Pagar por estas horas:** ₡ {monto_tot:,.2f} ({total_horas} hrs x ₡{tarifa:,.0f})")

                    if st.form_submit_button("Registrar Horas"):
                        cursor = conn.cursor()
                        cursor.execute(
                            "INSERT INTO coberturas_libres (colaborador_id, fecha, horas_trabajadas, tarifa_hora, monto_total, motivo_cobertura) VALUES (?, ?, ?, ?, ?, ?)",
                            (c_id, str(fecha_turno), total_horas, tarifa, monto_tot, motivo)
                        )
                        conn.commit()
                        st.success("¡Horas registradas exitosamente!")
                        st.rerun()

            with col_b:
                st.markdown("##### 💸 Registrar Adelanto / Deducción")
                with st.form("form_movimiento", clear_on_submit=True):
                    sel_colab = st.selectbox("Colaborador", list(colab_dict.keys()), key="mov_colab")
                    tipo_mov = st.selectbox("Tipo", ["Adelanto de Salario", "Deducción Extraordinaria", "Bono / Incentivo"])
                    monto = st.number_input("Monto (₡)", min_value=0.0, step=5000.0)
                    nota = st.text_input("Observación / Motivo")
                    if st.form_submit_button("Registrar Movimiento") and monto > 0:
                        cursor = conn.cursor()
                        cursor.execute(
                            "INSERT INTO movimientos_rrhh (colaborador_id, tipo, monto, fecha, nota) VALUES (?, ?, ?, ?, ?)",
                            (colab_dict[sel_colab], tipo_mov, monto, str(datetime.today().date()), nota)
                        )
                        conn.commit()
                        st.success("Registrado correctamente.")
                        st.rerun()

        st.markdown("---")
        st.markdown("### Historial Reciente de Horas Registradas")
        df_cob_rec = pd.read_sql("""
            SELECT cl.fecha as 'Fecha', c.nombre, cl.horas_trabajadas as 'Horas', cl.tarifa_hora as 'Tarifa/Hr', cl.monto_total as 'Monto Total', cl.motivo_cobertura as 'Notas'
            FROM coberturas_libres cl 
            JOIN colaboradores c ON cl.colaborador_id = c.id 
            ORDER BY cl.id DESC LIMIT 15
        """, conn)
        if not df_cob_rec.empty:
            st.dataframe(df_cob_rec, use_container_width=True)

    # ---------------------------------------------------------
    # TAB 4: ANÁLISIS & GRÁFICOS
    # ---------------------------------------------------------
    with tab4:
        st.markdown("### 📊 Distribución Visual de Costos de Planilla")
        df_costos = pd.read_sql("""
            SELECT tienda, COUNT(id) as total_empleados, SUM(salario_base) as total_planilla 
            FROM colaboradores GROUP BY tienda
        """, conn)

        if not df_costos.empty:
            c1, c2 = st.columns(2)
            total_general = df_costos['total_planilla'].sum()
            total_empleados = df_costos['total_empleados'].sum()

            with c1:
                st.markdown(f"""
                    <div class="brabca-card">
                        <div class="card-label">Planilla Fija Mensual Consolidada</div>
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
                st.markdown("##### **Costo Fijo por Tienda (₡)**")
                st.bar_chart(df_costos.set_index('tienda')[['total_planilla']])
            with col_chart2:
                st.markdown("##### **Distribución de Personal por Tienda**")
                st.bar_chart(df_costos.set_index('tienda')[['total_empleados']])

    # ---------------------------------------------------------
    # TAB 5: RECLUTAMIENTO & FOLLETOS
    # ---------------------------------------------------------
    with tab5:
        st.markdown("### 📢 Banco de Afiches y Folletos de Contratación")
        with st.expander("📤 Subir Nuevo Folleto de Reclutamiento"):
            folleto_file = st.file_uploader("Selecciona la imagen promocional (PNG/JPG)", type=["png", "jpg", "jpeg"])
            nombre_folleto = st.text_input("Nombre / Referencia del Folleto")
            if st.button("Guardar Folleto") and folleto_file and nombre_folleto:
                path = os.path.join("archivos_rrhh/folletos", f"{nombre_folleto}.png")
                image = Image.open(folleto_file)
                image.save(path)
                st.success("¡Folleto guardado correctamente!")
                st.rerun()

        folletos_existentes = os.listdir("archivos_rrhh/folletos")
        if folletos_existentes:
            cols = st.columns(3)
            for idx, file in enumerate(folletos_existentes):
                with cols[idx % 3]:
                    file_path = os.path.join("archivos_rrhh/folletos", file)
                    st.image(file_path, caption=file.replace(".png", ""), use_container_width=True)

    # ---------------------------------------------------------
    # TAB 6: MANUALES DE PUESTO
    # ---------------------------------------------------------
    with tab6:
        st.markdown("### 📋 Manuales de Puesto y Políticas de Tienda")
        with st.expander("📤 Cargar Nuevo Manual / Documento (PDF/Word)"):
            doc_file = st.file_uploader("Selecciona el archivo PDF o Word", type=["pdf", "docx"])
            titulo_doc = st.text_input("Título del Puesto / Documento")
            if st.button("Guardar Documento") and doc_file and titulo_doc:
                ext = doc_file.name.split(".")[-1]
                path = os.path.join("archivos_rrhh/manuales", f"{titulo_doc}.{ext}")
                with open(path, "wb") as f:
                    f.write(doc_file.getbuffer())
                st.success("¡Documento guardado con éxito!")
                st.rerun()

        manuales_existentes = os.listdir("archivos_rrhh/manuales")
        if manuales_existentes:
            for file in manuales_existentes:
                st.markdown(f"📄 **{file}**")

    # ---------------------------------------------------------
    # TAB 7: ENTREVISTAS Y CANDIDATOS
    # ---------------------------------------------------------
    with tab7:
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
            
            notas_ent = st.text_area("Notas / Impresiones")
            if st.form_submit_button("Guardar Entrevista") and candidato:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO entrevistas (candidato, tienda, puesto, fecha, calificacion, estado, notas)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (candidato, tienda_ent, puesto_ent, str(fecha_ent), calificacion, estado_ent, notas_ent))
                conn.commit()
                st.success("Entrevista registrada correctamente.")
                st.rerun()

        df_ent = pd.read_sql("SELECT fecha, candidato, tienda, puesto, calificacion, estado, notas FROM entrevistas ORDER BY fecha DESC", conn)
        if not df_ent.empty:
            st.dataframe(df_ent, use_container_width=True)

    conn.close()
