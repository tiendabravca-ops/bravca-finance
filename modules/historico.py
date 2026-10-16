import streamlit as st
import pandas as pd
import sqlite3
import os

def run():
    st.markdown("##### 📅 VENTAS REALES 2025 (BASE HISTÓRICA)")
    
    tienda_hist_filtro = st.selectbox(
        "Seleccionar Tienda / Vista Histórica", 
        ["Consolidado (Ambas Tiendas)", "Santa Elena", "Monteverde Extremo"],
        key="hist_tienda_sel"
    )
    
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "bravca.db")
    df_2025 = pd.DataFrame()

    # Intentamos leer de la base de datos las ventas reales puras
    if os.path.exists(db_path):
        conn = sqlite3.connect(db_path, timeout=10.0)
        try:
            if tienda_hist_filtro == "Consolidado (Ambas Tiendas)":
                query = """
                    SELECT mes, SUM(ventas_2025) as ventas_2025 
                    FROM historico_2025 GROUP BY mes
                """
            else:
                query = f"""
                    SELECT mes, ventas_2025 
                    FROM historico_2025 WHERE tienda = '{tienda_hist_filtro}'
                """
            df_2025 = pd.read_sql_query(query, conn)
        except Exception as e:
            st.error(f"Error al leer la base de datos: {e}")
        finally:
            conn.close()

    # Si la base de datos está vacía, usamos los datos reales oficiales de respaldo garantizados
    if df_2025.empty or len(df_2025) < 12:
        se_data = {
            'enero': 5609058.0, 'febrero': 5858674.0, 'marzo': 6563325.0, 'abril': 5030208.0,
            'mayo': 3051706.0, 'junio': 4533249.0, 'julio': 6181795.0, 'agosto': 5707678.0,
            'setiembre': 2240840.0, 'octubre': 2068705.0, 'noviembre': 4995976.0, 'diciembre': 6451352.0
        }
        me_data = {
            'enero': 3996723.0, 'febrero': 3849065.0, 'marzo': 3948468.0, 'abril': 3902629.0,
            'mayo': 2604663.0, 'junio': 3305065.0, 'julio': 5166749.0, 'agosto': 4805683.0,
            'setiembre': 2902578.0, 'octubre': 2914149.0, 'noviembre': 4123608.0, 'diciembre': 5747824.0
        }
        orden_meses = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'setiembre', 'octubre', 'noviembre', 'diciembre']
        
        filas = []
        for m in orden_meses:
            v_se = se_data[m]
            v_me = me_data[m]
            if tienda_hist_filtro == "Santa Elena":
                v = v_se
            elif tienda_hist_filtro == "Monteverde Extremo":
                v = v_me
            else:
                v = v_se + v_me
            filas.append({'mes': m, 'ventas_2025': v})
        df_2025 = pd.DataFrame(filas)

    # Orden cronológico estricto
    orden_meses = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'setiembre', 'octubre', 'noviembre', 'diciembre']
    df_2025['mes'] = df_2025['mes'].astype(str).str.lower()
    df_2025['mes'] = pd.Categorical(df_2025['mes'], categories=orden_meses, ordered=True)
    df_2025 = df_2025.sort_values('mes').reset_index(drop=True)

    if tienda_hist_filtro == "Santa Elena":
        label_venta = "Ventas Reales 2025 - Santa Elena (₡)"
    elif tienda_hist_filtro == "Monteverde Extremo":
        label_venta = "Ventas Reales 2025 - Monteverde Extremo (₡)"
    else:
        label_venta = "Ventas Reales 2025 Consolidado (₡)"

    total_v_2025 = df_2025['ventas_2025'].sum()

    # Tarjeta superior limpia con el total real
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown(f'''
            <div class="brabca-card">
                <div class="card-label">Total Ventas Reales 2025</div>
                <div class="card-value">₡ {total_v_2025:,.2f}</div>
                <small style="color: #6E7C77;">Base de referencia para proyecciones ({tienda_hist_filtro})</small>
            </div>
        ''', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Tabla limpia y directa solo con las ventas reales por mes
    st.dataframe(
        df_2025,
        column_config={
            "mes": "Mes",
            "ventas_2025": st.column_config.NumberColumn(label_venta, format="₡ %,.2f")
        },
        use_container_width=True,
        hide_index=True
    )
