import sqlite3
import pandas as pd
import streamlit as st
from datetime import datetime

def obtener_ventas_reales_desde_db():
    """Consulta la base de datos de cierres para extraer los totales reales agrupados por mes y tienda."""
    conn = sqlite3.connect("db_cierres.db")
    query = "SELECT fecha, negocio, colones FROM cierres"
    df_db = pd.read_sql_query(query, conn)
    conn.close()

    se_dict = {m: 0.0 for m in ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']}
    me_dict = {m: 0.0 for m in ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']}
    
    mapping_meses = {
        '01': 'enero', '02': 'febrero', '03': 'marzo', '04': 'abril',
        '05': 'mayo', '06': 'junio', '07': 'julio', '08': 'agosto',
        '09': 'septiembre', '10': 'octubre', '11': 'noviembre', '12': 'diciembre'
    }

    if not df_db.empty:
        df_db['fecha_dt'] = pd.to_datetime(df_db['fecha'], errors='coerce')
        df_db['mes_num'] = df_db['fecha_dt'].dt.strftime('%m')
        df_db['anio'] = df_db['fecha_dt'].dt.strftime('%Y')
        
        # Filtramos estrictamente el año 2026
        df_2026 = df_db[df_db['anio'] == '2026']

        for _, row in df_2026.iterrows():
            m_num = row['mes_num']
            if m_num in mapping_meses:
                nombre_mes = mapping_meses[m_num]
                tienda = str(row['negocio']).strip().lower()
                monto = float(row['colones']) if pd.notnull(row['colones']) else 0.0

                # Bravca Souvenir = Santa Elena | Bravca Extremo = Monteverde Extremo
                if 'souvenir' in tienda or 'santa elena' in tienda:
                    se_dict[nombre_mes] += monto
                elif 'extremo' in tienda:
                    me_dict[nombre_mes] += monto

    return se_dict, me_dict

def run():
    # Estilos CSS originales recuperados para las tarjetas corporativas
    st.markdown("""
        <style>
            .brabca-card {
                background-color: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-left: 4px solid #1B365D;
                padding: 16px;
                border-radius: 8px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.05);
            }
            .card-label {
                font-size: 11px;
                font-weight: 700;
                color: #6E7C77;
                letter-spacing: 0.5px;
                margin-bottom: 4px;
            }
            .card-value {
                font-size: 20px;
                font-weight: 700;
                color: #1B365D;
            }
            .card-value-gold {
                font-size: 20px;
                font-weight: 700;
                color: #C5A059;
            }
            .card-value-alert {
                font-size: 20px;
                font-weight: 700;
                color: #D9534F;
            }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("##### 📈 COMPARATIVO DE VENTAS VS. PROYECCIÓN 2026")
    
    col_v1, col_v2 = st.columns(2)
    with col_v1:
        tienda_filtro = st.selectbox(
            "Punto de Venta / Vista",
            ["Consolidado (Ambas Tiendas)", "Santa Elena", "Monteverde Extremo"],
            key="proy_2026_tienda"
        )
    with col_v2:
        porcentaje_crecimiento = st.number_input(
            "Crecimiento Esperado vs. 2025 (%)", 
            min_value=0.0, 
            max_value=100.0, 
            value=10.0, 
            step=1.0,
            help="Ajusta el porcentaje para recalcular la meta proyectada en tiempo real."
        )

    st.markdown("###### 📅 Selección de Período (Rango de Meses)")
    
    b1, b2, b3, b4 = st.columns(4)
    with b1:
        if st.button("⚡ Enero a la fecha (Octubre)", use_container_width=True):
            st.session_state['mes_inicio'] = 'enero'
            st.session_state['mes_fin'] = 'diciembre'
    with b2:
        if st.button("⚡ Primer Semestre (Ene - Jun)", use_container_width=True):
            st.session_state['mes_inicio'] = 'enero'
            st.session_state['mes_fin'] = 'junio'
    with b3:
        if st.button("⚡ Q1 (Ene - Mar)", use_container_width=True):
            st.session_state['mes_inicio'] = 'enero'
            st.session_state['mes_fin'] = 'marzo'
    with b4:
        if st.button("⚡ Todo el Año", use_container_width=True):
            st.session_state['mes_inicio'] = 'enero'
            st.session_state['mes_fin'] = 'diciembre'

    orden_meses = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']

    col_m1, col_m2 = st.columns(2)
    with col_m1:
        mes_inicio = st.selectbox(
            "Desde Mes:", orden_meses,
            index=orden_meses.index(st.session_state.get('mes_inicio', 'enero')),
            key="mes_inicio_sel"
        )
    with col_m2:
        mes_fin = st.selectbox(
            "Hasta Mes:", orden_meses,
            index=orden_meses.index(st.session_state.get('mes_fin', 'diciembre')),
            key="mes_fin_sel"
        )

    # Datos base 2025 completos
    se_2025 = {'enero': 5609058.0, 'febrero': 5858674.0, 'marzo': 6563325.0, 'abril': 5030208.0, 'mayo': 3051706.0, 'junio': 4533249.0, 'julio': 6181795.0, 'agosto': 5707678.0, 'septiembre': 2240840.0, 'octubre': 2068705.0, 'noviembre': 4995976.0, 'diciembre': 6451352.0}
    me_2025 = {'enero': 3996723.0, 'febrero': 3849065.0, 'marzo': 3948468.0, 'abril': 3902629.0, 'mayo': 2604663.0, 'junio': 3305065.0, 'julio': 5166749.0, 'agosto': 4805683.0, 'septiembre': 2902578.0, 'octubre': 2914149.0, 'noviembre': 4123608.0, 'diciembre': 5747824.0}

    # Ventas 2026 conectadas automáticamente a la base de datos de cierres reales
    se_2026, me_2026 = obtener_ventas_reales_desde_db()

    idx_start = orden_meses.index(mes_inicio)
    idx_end = orden_meses.index(mes_fin)
    
    if idx_start > idx_end:
        st.warning("El mes de inicio no puede ser posterior al mes de fin.")
        return

    meses_seleccionados = orden_meses[idx_start:idx_end+1]
    factor_crecimiento = 1.0 + (porcentaje_crecimiento / 100.0)

    filas = []
    for m in meses_seleccionados:
        v25_se, v26_se = se_2025[m], se_2026[m]
        v25_me, v26_me = me_2025[m], me_2026[m]

        if tienda_filtro == "Santa Elena":
            v_2025 = v25_se
            v_2026 = v26_se
        elif tienda_filtro == "Monteverde Extremo":
            v_2025 = v25_me
            v_2026 = v26_me
        else:
            v_2025 = v25_se + v25_me
            v_2026 = v26_se + v26_me

        meta_2026 = v_2025 * factor_crecimiento
        brecha = v_2026 - meta_2026 if v_2026 > 0 else -meta_2026
        pct_cumplimiento = (v_2026 / meta_2026 * 100) if meta_2026 > 0 and v_2026 > 0 else 0.0

        filas.append({
            'mes': m.capitalize(),
            'Base 2025 (₡)': v_2025,
            'Meta Proyectada (₡)': meta_2026,
            'Venta Real 2026 (₡)': v_2026,
            'brecha': brecha,
            'pct_cumplimiento': pct_cumplimiento
        })

    df = pd.DataFrame(filas)

    total_real = df['Venta Real 2026 (₡)'].sum()
    total_meta = df['Meta Proyectada (₡)'].sum()
    brecha_total = total_real - total_meta
    pct_total = (total_real / total_meta * 100) if total_meta > 0 else 0

    st.markdown("<br>", unsafe_allow_html=True)

    # Tarjetas de totales con diseño corporativo
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f'''
            <div class="brabca-card">
                <div class="card-label">VENTAS REALES 2026</div>
                <div class="card-value">₡ {total_real:,.2f}</div>
                <small style="color: #6E7C77;">{tienda_filtro}</small>
            </div>
        ''', unsafe_allow_html=True)
    with c2:
        st.markdown(f'''
            <div class="brabca-card">
                <div class="card-label">META PROYECTADA</div>
                <div class="card-value-gold">₡ {total_meta:,.2f}</div>
                <small style="color: #6E7C77;">Base 2025 + {porcentaje_crecimiento:.0f}%</small>
            </div>
        ''', unsafe_allow_html=True)
    with c3:
        clase_b = "card-value" if brecha_total >= 0 else "card-value-alert"
        st.markdown(f'''
            <div class="brabca-card">
                <div class="card-label">BRECHA / ALCANZADO</div>
                <div class="{clase_b}">₡ {brecha_total:,.2f}</div>
                <small style="color: #6E7C77;">Diferencia en colones</small>
            </div>
        ''', unsafe_allow_html=True)
    with c4:
        st.markdown(f'''
            <div class="brabca-card">
                <div class="card-label">% CUMPLIMIENTO</div>
                <div class="card-value">{pct_total:.2f}%</div>
                <small style="color: #6E7C77;">Período seleccionado</small>
            </div>
        ''', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Tabla Desglosada
    st.dataframe(
        df[['mes', 'Base 2025 (₡)', 'Meta Proyectada (₡)', 'Venta Real 2026 (₡)', 'brecha', 'pct_cumplimiento']],
        column_config={
            "mes": "Mes",
            "Base 2025 (₡)": st.column_config.NumberColumn("Base 2025 (₡)", format="₡ %,.2f"),
            "Meta Proyectada (₡)": st.column_config.NumberColumn("Meta Proyectada (₡)", format="₡ %,.2f"),
            "Venta Real 2026 (₡)": st.column_config.NumberColumn("Venta Real 2026 (₡)", format="₡ %,.2f"),
            "brecha": st.column_config.NumberColumn("Brecha (₡)", format="₡ %,.2f"),
            "pct_cumplimiento": st.column_config.NumberColumn("% Cumplimiento", format="%.2f %%")
        },
        use_container_width=True,
        hide_index=True
    )

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("##### 📊 GRÁFICO COMPARATIVO DEL PERÍODO SELECCIONADO (AÑO VS AÑO)")
    
    df_chart = df.set_index('mes')[['Base 2025 (₡)', 'Meta Proyectada (₡)', 'Venta Real 2026 (₡)']]
    st.bar_chart(df_chart)
