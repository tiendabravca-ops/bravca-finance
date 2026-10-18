import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
from datetime import datetime, timedelta
import os

def obtener_metas_desde_obligaciones(anio, mes_nombre):
    """Consulta la base de datos de obligaciones para sumar dinámicamente las metas ideales de cada sobre."""
    db_path = "data/sistema_financiero.db"
    
    metas = {
        'reserva': 1000000.0,
        'salarios': 0.0,
        'alquiler': 0.0,
        'tarjeta': 0.0,
        'proveedores': 0.0
    }
    
    obligaciones_lista = []

    if os.path.exists(db_path):
        try:
            conn = sqlite3.connect(db_path)
            query = "SELECT id, categoria, descripcion, monto, fecha_pago, tienda, pagado FROM obligaciones WHERE anio = ? AND LOWER(mes) = ?"
            df_obs = pd.read_sql_query(query, conn, params=(anio, mes_nombre.lower()))
            conn.close()

            if not df_obs.empty:
                for _, row in df_obs.iterrows():
                    cat = str(row['categoria']).lower()
                    monto = float(row['monto']) if row['monto'] else 0.0
                    
                    if 'planilla' in cat or 'salario' in cat:
                        metas['salarios'] += monto
                    elif 'alquiler' in cat:
                        metas['alquiler'] += monto
                    elif 'tarjeta' in cat or 'prestamo' in cat or 'financiamiento' in cat or 'impuesto' in cat or 'contabilidad' in cat:
                        metas['tarjeta'] += monto
                    elif 'proveedor' in cat or 'mercaderia' in cat or 'insumo' in cat:
                        metas['proveedores'] += monto
                    else:
                        metas['reserva'] += monto
                        
                obligaciones_lista = df_obs.to_dict('records')
        except Exception:
            pass

    # Asegurar valores mínimos si aún no hay registros
    if metas['salarios'] == 0: metas['salarios'] = 1500000.0
    if metas['alquiler'] == 0: metas['alquiler'] = 860000.0
    if metas['tarjeta'] == 0: metas['tarjeta'] = 500000.0
    if metas['proveedores'] == 0: metas['proveedores'] = 1500000.0

    return metas, obligaciones_lista

def run():
    st.markdown("##### 🏦 CONSOLIDADO DE FONDOS, RESERVAS Y CRONOGRAMA OPERATIVO")
    
    db_path_cierres = "db_cierres.db"
    hoy = datetime.now()
    anio_curr = hoy.year
    mes_num_curr = hoy.month
    
    mapping_meses = {
        1: 'enero', 2: 'febrero', 3: 'marzo', 4: 'abril',
        5: 'mayo', 6: 'junio', 7: 'julio', 8: 'agosto',
        9: 'septiembre', 10: 'octubre', 11: 'noviembre', 12: 'diciembre'
    }
    mes_nombre_curr = mapping_meses.get(mes_num_curr, 'octubre')

    # Lectura de ventas reales desde db_cierres.db
    df_ventas = pd.DataFrame()
    if os.path.exists(db_path_cierres):
        try:
            conn = sqlite3.connect(db_path_cierres, timeout=10.0)
            df_ventas = pd.read_sql_query("SELECT negocio as tienda, fecha as fecha_cierre, colones as efectivo_cobrado FROM cierres", conn)
            conn.close()
        except Exception:
            pass
    
    v_1_10, v_11_20, v_21_31, total_mes = 0.0, 0.0, 0.0, 0.0
    
    if not df_ventas.empty:
        df_ventas['monto'] = pd.to_numeric(df_ventas['efectivo_cobrado'], errors='coerce').fillna(0)
        df_ventas['fecha_dt'] = pd.to_datetime(df_ventas['fecha_cierre'], errors='coerce')
        
        df_mes_actual = df_ventas[(df_ventas['fecha_dt'].dt.year == anio_curr) & (df_ventas['fecha_dt'].dt.month == mes_num_curr)].copy()
        
        if not df_mes_actual.empty:
            total_mes = df_mes_actual['monto'].sum()
            df_mes_actual['dia'] = df_mes_actual['fecha_dt'].dt.day
            
            v_1_10 = df_mes_actual[(df_mes_actual['dia'] >= 1) & (df_mes_actual['dia'] <= 10)]['monto'].sum()
            v_11_20 = df_mes_actual[(df_mes_actual['dia'] >= 11) & (df_mes_actual['dia'] <= 20)]['monto'].sum()
            v_21_31 = df_mes_actual[(df_mes_actual['dia'] >= 21)]['monto'].sum()

    # Consolidación dinámica con la base de datos de Obligaciones
    metas_dinamicas, lista_obs = obtener_metas_desde_obligaciones(anio_curr, mes_nombre_curr)

    tab_sobres, tab_gantt = st.tabs(["📦 Asignación Automática por Sobres", "📊 Cronograma Operativo (Flujo de Caja)"])
    
    with tab_sobres:
        st.markdown(f"###### **Distribución Automática por Bloques Operativos — {mes_nombre_curr.capitalize()} {anio_curr}**")
        st.caption("Los montos de Meta Ideal se recalculan automáticamente con base en las obligaciones registradas.")
        
        datos_sobres = [
            {"nombre_fondo": "FONDO DE EMERGENCIA (Días 1-10)", "monto_meta_colones": metas_dinamicas['reserva'], "monto_logrado_colones": v_1_10, "prioridad": 1},
            {"nombre_fondo": "ROTATIVO DE COMPRAS + SALARIOS", "monto_meta_colones": metas_dinamicas['salarios'], "monto_logrado_colones": v_11_20 * 0.5, "prioridad": 2},
            {"nombre_fondo": "ALQUILER TIENDAS (Santa Elena & Extremo)", "monto_meta_colones": metas_dinamicas['alquiler'], "monto_logrado_colones": v_11_20 * 0.5, "prioridad": 3},
            {"nombre_fondo": "PAGO TARJETA / IMPUESTOS / PROFESIONALES", "monto_meta_colones": metas_dinamicas['tarjeta'], "monto_logrado_colones": v_21_31 * 0.4, "prioridad": 4},
            {"nombre_fondo": "FACTURAS CRÉDITO + PROVEEDORES", "monto_meta_colones": metas_dinamicas['proveedores'], "monto_logrado_colones": v_21_31 * 0.6, "prioridad": 5}
        ]
        
        df_display = pd.DataFrame(datos_sobres)
        total_meta = df_display["monto_meta_colones"].sum()
        total_logrado = df_display["monto_logrado_colones"].sum()
        cumplimiento = (total_logrado / total_meta * 100) if total_meta > 0 else 0
        
        # Tarjetas de Resumen Global
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("META GLOBAL SOBRES", f"₡ {total_meta:,.0f}")
        with col2:
            st.metric("TOTAL LOGRADO REAL", f"₡ {total_logrado:,.0f}")
        with col3:
            st.metric("% CUMPLIMIENTO", f"{cumplimiento:.1f}%")
        with col4:
            st.metric("VENTAS TIENDAS (TOTAL)", f"₡ {total_mes:,.0f}")

        st.markdown("<br>", unsafe_allow_html=True)

        fila_total = pd.DataFrame([{
            "nombre_fondo": "📌 TOTALES GENERALES",
            "monto_meta_colones": total_meta,
            "monto_logrado_colones": total_logrado,
            "prioridad": 0
        }])
        
        df_display = pd.concat([df_display, fila_total], ignore_index=True)
        
        st.dataframe(
            df_display,
            column_config={
                "nombre_fondo": st.column_config.TextColumn("Nombre del Sobre / Fondo"),
                "monto_meta_colones": st.column_config.NumberColumn("Meta Ideal (₡)", format="₡ %,.2f"),
                "monto_logrado_colones": st.column_config.NumberColumn("Monto Logrado Real (Ambas Tiendas ₡)", format="₡ %,.2f"),
                "prioridad": st.column_config.NumberColumn("Prioridad", format="%d")
            },
            use_container_width=True,
            hide_index=True
        )

    with tab_gantt:
        st.markdown("###### **Cronograma de Flujo de Efectivo (Sincronizado con Obligaciones)**")
        
        datos_ciclo = []
        if lista_obs:
            for obs in lista_obs:
                f_pago_str = obs.get('fecha_pago')
                if not f_pago_str:
                    f_pago_str = f"{anio_curr}-{mes_num_curr:02d}-15"
                
                try:
                    dt_inicio = datetime.strptime(f_pago_str, "%Y-%m-%d")
                except Exception:
                    dt_inicio = datetime(anio_curr, mes_num_curr, 15)

                # Se define una duración de al menos 2 días para que la barra horizontal sea claramente visible en Gantt
                dt_fin = dt_inicio + timedelta(days=2)
                
                desc = obs.get('descripcion') if obs.get('descripcion') else obs.get('categoria')
                estado = "✅ Pagado" if obs.get('pagado') == 1 else "⏳ Pendiente"
                
                datos_ciclo.append({
                    "Actividad": f"{desc} ({obs['tienda']})",
                    "Inicio": dt_inicio.strftime("%Y-%m-%d"),
                    "Fin": dt_fin.strftime("%Y-%m-%d"),
                    "Bloque": obs['categoria'],
                    "Monto": obs['monto'],
                    "Estado": estado
                })
        
        if not datos_ciclo:
            datos_ciclo = [
                {"Actividad": "Fondo de Emergencia (Intocable)", "Inicio": f"{anio_curr}-{mes_num_curr:02d}-01", "Fin": f"{anio_curr}-{mes_num_curr:02d}-10", "Bloque": "Reserva", "Monto": v_1_10, "Estado": "Pendiente"},
                {"Actividad": "Salarios 1ra Quincena", "Inicio": f"{anio_curr}-{mes_num_curr:02d}-11", "Fin": f"{anio_curr}-{mes_num_curr:02d}-13", "Bloque": "Planilla", "Monto": v_11_20 * 0.3, "Estado": "Pendiente"},
                {"Actividad": "Alquiler Santa Elena", "Inicio": f"{anio_curr}-{mes_num_curr:02d}-14", "Fin": f"{anio_curr}-{mes_num_curr:02d}-17", "Bloque": "Alquileres", "Monto": v_11_20 * 0.3, "Estado": "Pendiente"}
            ]
        
        df_gantt = pd.DataFrame(datos_ciclo)

        fig = px.timeline(
            df_gantt,
            x_start="Inicio",
            x_end="Fin",
            y="Actividad",
            color="Bloque",
            hover_data=["Monto", "Estado"],
            labels={"Actividad": "Compromiso Operativo", "Inicio": "Fecha de Pago"}
        )
        
        fig.update_yaxes(autorange="reversed")
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#1C2826', family='Inter'),
            legend=dict(title=None, orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=20, r=20, t=40, b=20)
        )
        
        st.plotly_chart(fig, use_container_width=True)
