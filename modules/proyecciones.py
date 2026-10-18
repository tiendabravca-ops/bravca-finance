import sqlite3
import pandas as pd
import streamlit as st
from datetime import datetime

def obtener_ventas_reales_desde_db(se_base_2026, me_base_2026):
    """Toma las ventas base de 2026 y sobreescribe dinámicamente cualquier mes que tenga cierres registrados en la base de datos."""
    conn = sqlite3.connect("db_cierres.db")
    query = "SELECT fecha, negocio, colones FROM cierres"
    df_db = pd.read_sql_query(query, conn)
    conn.close()

    # Panel de depuración visual para verificar los datos exactos que vienen de la BD
    st.info("🔍 Depuración: Registros leídos de `db_cierres.db`")
    st.dataframe(df_db, use_container_width=True)

    se_dict = se_base_2026.copy()
    me_dict = me_base_2026.copy()
    
    mapping_meses = {
        '01': 'enero', '02': 'febrero', '03': 'marzo', '04': 'abril',
        '05': 'mayo', '06': 'junio', '07': 'julio', '08': 'agosto',
        '09': 'septiembre', '10': 'octubre', '11': 'noviembre', '12': 'diciembre'
    }

    if not df_db.empty:
        df_db['fecha_dt'] = pd.to_datetime(df_db['fecha'], errors='coerce')
        df_db['mes_num'] = df_db['fecha_dt'].dt.strftime('%m')
        df_db['anio'] = df_db['fecha_dt'].dt.strftime('%Y')
        
        df_2026 = df_db[df_db['anio'] == '2026']

        for mes_num, grupo_mes in df_2026.groupby('mes_num'):
            if mes_num in mapping_meses:
                nombre_mes = mapping_meses[mes_num]
                
                suma_se = 0.0
                suma_me = 0.0
                
                for _, row in grupo_mes.iterrows():
                    tienda = str(row['negocio']).strip().lower()
                    monto = float(row['colones']) if pd.notnull(row['colones']) else 0.0
                    
                    if 'extremo' in tienda or 'monteverde' in tienda:
                        suma_me += monto
                    else:
                        suma_se += monto

                if suma_se > 0:
                    se_dict[nombre_mes] = suma_se
                if suma_me > 0:
                    me_dict[nombre_mes] = suma_me

    return se_dict, me_dict

def run():
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
    se_2025 = {'enero': 5609058.0, 'febrero': 5858674.0, 'marzo': 6563325.0, 'abril': 503
