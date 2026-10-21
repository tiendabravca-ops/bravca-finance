import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import sqlite3
import os

def obtener_ventas_reales_desde_db(se_base_2026, me_base_2026):
    """Suma directamente el total vendido de la BD agrupado por mes de forma segura, conservando el historial."""
    db_path = "db_cierres.db"
    se_dict = se_base_2026.copy()
    me_dict = me_base_2026.copy()
    
    if not os.path.exists(db_path):
        return se_dict, me_dict

    try:
        conn = sqlite3.connect(db_path)
        try:
            query = "SELECT fecha, negocio, vendido FROM cierres"
            df_db = pd.read_sql_query(query, conn)
        except Exception:
            # Fallback por si la estructura anterior usa efectivo + tarjeta
            query = "SELECT fecha, negocio, efectivo + tarjeta AS vendido FROM cierres"
            df_db = pd.read_sql_query(query, conn)
        conn.close()

        mapping_meses = {
            '01': 'enero', '02': 'febrero', '03': 'marzo', '04': 'abril',
            '05': 'mayo', '06': 'junio', '07': 'julio', '08': 'agosto',
            '09': 'septiembre', '10': 'octubre', '11': 'noviembre', '12': 'diciembre'
        }

        if not df_db.empty and 'vendido' in df_db.columns:
            df_db['fecha_clean'] = df_db['fecha'].astype(str).str.strip()
            df_db['anio'] = df_db['fecha_clean'].str.slice(0, 4)
            df_db['mes_num'] = df_db['fecha_clean'].str.slice(5, 7)
            
            # Filtrar únicamente los registros del año 2026
            df_2026 = df_db[df_db['anio'] == '2026']

            meses_con_datos = df_2026['mes_num'].dropna().unique()
            for m_num in meses_con_datos:
                if m_num in mapping_meses:
                    nombre_mes = mapping_meses[m_num]
                    df_mes = df_2026[df_2026['mes_num'] == m_num]
                    
                    # Clasificación flexible por nombre de tienda
                    suma_se = df_mes[~df_mes['negocio'].str.lower().str.contains('extremo|monteverde', na=False)]['vendido'].sum()
                    suma_me = df_mes[df_mes['negocio'].str.lower().str.contains('extremo|monteverde', na=False)]['vendido'].sum()

                    if suma_se > 0:
                        se_dict[nombre_mes] = float(suma_se)
                    if suma_me > 0:
                        me_dict[nombre_mes] = float(suma_me)
    except Exception:
        pass

    return se_dict, me_dict

def obtener_obligaciones_db():
    """Lee las obligaciones/gastos mensuales de la base de datos de SQLite o retorna defaults si no existe."""
    db_path = "data/sistema_financiero.db"
    
    obligaciones_def = {
        'enero': 4200000.0, 'febrero': 4100000.0, 'marzo': 4500000.0, 
        'abril': 3800000.0, 'mayo': 3200000.0, 'junio': 3100000.0, 
        'julio': 4000000.0, 'agosto': 4100000.0, 'septiembre': 2800000.0,
        'octubre': 3500000.0, 'noviembre': 0.0, 'diciembre': 0.0
    }
    
    if not os.path.exists(db_path):
        return obligaciones_def
        
    try:
        conn = sqlite3.connect(db_path)
        query = "SELECT mes, SUM(monto) as total_obligaciones FROM obligaciones WHERE anio = 2026 GROUP BY mes"
        df_obs = pd.read_sql_query(query, conn)
        conn.close()
        
        if not df_obs.empty:
            for _, row in df_obs.iterrows():
                m_str = str(row['mes']).lower()
                if m_str in obligaciones_def:
                    obligaciones_def[m_str] = float(row['total_obligaciones'])
    except Exception:
        pass
        
    return obligaciones_def

def run():
    st.markdown("##### 📊 DASHBOARD FINANCIERO CONSOLIDADO & WALL STREET RATING")

    # Controles superiores
    col_f1, col_f2 = st.columns([2, 1])
    with col_f1:
        tienda_filtro = st.selectbox(
            "Punto de Venta / Vista General",
            ["Consolidado (Ambas Tiendas)", "Santa Elena", "Monteverde Extremo"],
            key="dash_tienda_sel"
        )
    with col_f2:
        porcentaje_crecimiento = st.number_input(
            "Meta Crecimiento Global (%)",
            min_value=0.0,
            max_value=100.0,
            value=10.0,
            step=1.0,
            key="dash_growth_input"
        )

    orden_meses = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']

    # Bases Reales 2025
    se_2025 = {'enero': 5609058.0, 'febrero': 5858674.0, 'marzo': 6563325.0, 'abril': 5030208.0, 'mayo': 3051706.0, 'junio': 4533249.0, 'julio': 6181795.0, 'agosto': 5707678.0, 'septiembre': 2240840.0, 'octubre': 2068705.0, 'noviembre': 4995976.0, 'diciembre': 6451352.0}
    me_2025 = {'enero': 3996723.0, 'febrero': 3849065.0, 'marzo': 3948468.0, 'abril': 3902629.0, 'mayo': 2604663.0, 'junio': 3305065.0, 'julio': 5166749.0, 'agosto': 4805683.0, 'septiembre': 2902578.0, 'octubre': 2914149.0, 'noviembre': 4123608.0, 'diciembre': 5747824.0}

    # Ventas Reales 2026 Base (preservando enero a septiembre)
    se_2026_base = {'enero': 6505637.0, 'febrero': 6428153.0, 'marzo': 6568137.0, 'abril': 3404128.0, 'mayo': 2436870.0, 'junio': 2492625.0, 'julio': 3659071.0, 'agosto': 4591962.0, 'septiembre': 2076047.0, 'octubre': 0.0, 'noviembre': 0.0, 'diciembre': 0.0}
    me_2026_base = {'enero': 5217268.0, 'febrero': 3745984.0, 'marzo': 4792605.0, 'abril': 3885728.0, 'mayo': 3427314.0, 'junio': 2571164.0, 'julio': 4780260.0, 'agosto': 4339610.0, 'septiembre': 1287905.0, 'octubre': 0.0, 'noviembre': 0.0, 'diciembre': 0.0}

    # Integramos la base de datos de cierres para actualizar dinámicamente cualquier mes con registros
    se_2026, me_2026 = obtener_ventas_reales_desde_db(se_2026_base, me_2026_base)

    # Determinamos de forma dinámica los meses activos que ya tienen ventas reales registradas (> 0)
    meses_activos = [m for m in orden_meses if (se_2026[m] > 0 or me_2026[m] > 0)]

    # Obligaciones desde base de datos / archivo
    obligaciones_2026 = obtener_obligaciones_db()
    factor = 1.0 + (porcentaje_crecimiento / 100.0)

    filas = []
    alertas_rojas = []
    alertas_verdes = []

    for m in orden_meses:
        v25_se, v26_se = se_2025[m], se_2026[m]
        v25_me, v26_me = me_2025[m], me_2026[m]

        if tienda_filtro == "Santa Elena":
            v25, v26 = v25_se, v26_se
        elif tienda_filtro == "Monteverde Extremo":
            v25, v26 = v25_me, v26_me
        else:
            v25 = v25_se + v25_me
            v26 = v26_se + v26_me

        meta = v25 * factor
        brecha = v26 - meta
        pct = (v26 / meta * 100) if meta > 0 else 0.0

        if m in meses_activos and v26 > 0:
            if pct < 85.0:
                alertas_rojas.append(f"**{m.capitalize()}**: Cumplimiento del **{pct:.1f}%** (Déficit vs. Meta: ₡ {abs(brecha):,.2f})")
            elif pct >= 100.0:
                alertas_verdes.append(f"**{m.capitalize()}**: ¡Meta superada! **{pct:.1f}%** (Superávit vs. Meta: ₡ {brecha:,.2f})")

        filas.append({
            'mes': m.capitalize(),
            'Base 2025': v25,
            'Meta 2026': meta,
            'Venta Real 2026': v26,
            'Brecha': brecha,
            'Cumplimiento': pct
        })

    df = pd.DataFrame(filas)
    df_activos = df[df['mes'].str.lower().isin(meses_activos)]

    tot_real = df_activos['Venta Real 2026'].sum()
    tot_meta = df_activos['Meta 2026'].sum()
    brecha_global = tot_real - tot_meta
    pct_global = (tot_real / tot_meta * 100) if tot_meta > 0 else 0.0

    # Texto dinámico del período activo
    texto_periodo = f"{meses_activos[0].capitalize()} - {meses_activos[-1].capitalize()}" if meses_activos else "2026"

    # ALERTAS Y DIAGNÓSTICO
    st.markdown("###### 🚨 ALERTAS Y DIAGNÓSTICO FINANCIERO AUTOMÁTICO")
    if pct_global < 90.0:
        st.error(f"⚠️ **Alerta Global de Rendimiento:** El cumplimiento acumulado del período a la fecha es del **{pct_global:.2f}%**. Brecha total vs. Meta: ₡ {brecha_global:,.2f}.")
    else:
        st.success(f"✅ **Estado Financiero Saludable:** El cumplimiento acumulado general se mantiene en **{pct_global:.2f}%**.")

    col_a1, col_a2 = st.columns(2)
    with col_a1:
        if alertas_rojas:
            with st.expander("🔻 Meses por debajo del umbral objetivo (<85%)", expanded=True):
                for a in alertas_rojas:
                    st.write(f"- {a}")
        else:
            st.info("No hay meses con desviaciones críticas inferiores al 85%.")

    with col_a2:
        if alertas_verdes:
            with st.expander("🟢 Meses destacados (>100% de cumplimiento)", expanded=True):
                for a in alertas_verdes:
                    st.write(f"- {a}")
        else:
            st.warning("No hay meses que hayan superado la meta proyectada al 100%.")

    st.markdown("<br>", unsafe_allow_html=True)

    # TARJETAS DE KPIS PRINCIPALES
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(f'''
            <div class="brabca-card">
                <div class="card-label">VENTA ACUMULADA 2026</div>
                <div class="card-value">₡ {tot_real:,.2f}</div>
                <small style="color: #6E7C77;">{tienda_filtro} ({texto_periodo})</small>
            </div>
        ''', unsafe_allow_html=True)
    with k2:
        st.markdown(f'''
            <div class="brabca-card">
                <div class="card-label">META ACUMULADA 2026</div>
                <div class="card-value-gold">₡ {tot_meta:,.2f}</div>
                <small style="color: #6E7C77;">Base 2025 + {porcentaje_crecimiento:.0f}%</small>
            </div>
        ''', unsafe_allow_html=True)
    with k3:
        clase_b = "card-value" if brecha_global >= 0 else "card-value-alert"
        st.markdown(f'''
            <div class="brabca-card">
                <div class="card-label">BRECHA / BALANCE</div>
                <div class="{clase_b}">₡ {brecha_global:,.2f}</div>
                <small style="color: #6E7C77;">Diferencia acumulada</small>
            </div>
        ''', unsafe_allow_html=True)
    with k4:
        st.markdown(f'''
            <div class="brabca-card">
                <div class="card-label">% CUMPLIMIENTO GLOBAL</div>
                <div class="card-value">{pct_global:.2f}%</div>
                <small style="color: #6E7C77;">{texto_periodo} 2026</small>
            </div>
        ''', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # --- SECCIÓN BOLSAS DE VALORES / VELAS JAPONESAS (WALL STREET) ---
    st.markdown("---")
    st.markdown("### 🕯️ COMPORTAMIENTO DEL MERCADO & FLUJO DE CAJA (WALL STREET STYLE)")

    open_vals, close_vals, high_vals, low_vals, labels = [], [], [], [], []
    tot_egresos = 0.0

    for m in meses_activos:
        v_real = se_2026[m] + me_2026[m] if tienda_filtro == "Consolidado (Ambas Tiendas)" else (se_2026[m] if tienda_filtro == "Santa Elena" else me_2026[m])
        v_base = se_2025[m] + me_2025[m] if tienda_filtro == "Consolidado (Ambas Tiendas)" else (se_2025[m] if tienda_filtro == "Santa Elena" else me_2025[m])
        
        meta = v_base * factor
        egreso = obligaciones_2026[m]
        tot_egresos += egreso
        flujo_libre = v_real - egreso

        labels.append(m.capitalize())
        open_vals.append(meta)
        close_vals.append(v_real)
        high_vals.append(max(v_real, meta))
        low_vals.append(flujo_libre)

    # Métricas Ticker
    neto_acumulado = tot_real - tot_egresos
    margen_neto_pct = (neto_acumulado / tot_real * 100) if tot_real > 0 else 0.0

    t1, t2, t3 = st.columns(3)
    with t1:
        st.metric("🟢 INGRESOS TOTALES (VENTAS)", f"₡ {tot_real:,.2f}", delta=f"{tienda_filtro}")
    with t2:
        st.metric("🔴 OBLIGACIONES & GASTOS", f"₡ {tot_egresos:,.2f}", delta="-Egresos acumulados", delta_color="inverse")
    with t3:
        st.metric("📊 MARGEN NETO LIBRE", f"₡ {neto_acumulado:,.2f}", delta=f"Rendimiento: {margen_neto_pct:.1f}%")

    st.markdown("<br>", unsafe_allow_html=True)

    # Construcción de la Gráfica de Velas Japonesas en Plotly
    fig = go.Figure(data=[go.Candlestick(
        x=labels,
        open=open_vals,
        high=high_vals,
        low=low_vals,
        close=close_vals,
        increasing_line_color='#2ECC71',  # Verde cuando Venta Real >= Meta
        decreasing_line_color='#E74C3C', # Rojo cuando Venta Real < Meta
        name="Rendimiento Mensual"
    )])

    fig.update_layout(
        title="<b>Comportamiento del Mercado 2026:</b> Meta (Apertura), Venta Real (Cierre) y Flujo Neto (Mínimo)",
        yaxis_title="Monto en Colones (₡)",
        xaxis_title="Meses del Año",
        template="plotly_dark",
        height=520,
        margin=dict(l=40, r=40, t=60, b=40)
    )

    st.plotly_chart(fig, use_container_width=True)
