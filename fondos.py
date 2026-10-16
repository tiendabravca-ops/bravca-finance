import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
from datetime import datetime
import os

def run():
    st.markdown("##### 🏦 CONSOLIDADO DE FONDOS, RESERVAS Y CRONOGRAMA")
    
    # Asegurar que la carpeta 'databases' exista
    os.makedirs('databases', exist_ok=True)
    
    # Conexión a la base de datos
    conn = sqlite3.connect('databases/db_cierres.db', timeout=10.0)
    cursor = conn.cursor()
    
    # Crear la tabla si no existe
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cierres_caja (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tienda TEXT,
            fecha_cierre TEXT,
            efectivo_cobrado REAL
        )
    ''')
    conn.commit()
    
    # Verificar si existen datos del mes actual (octubre 2026)
    cursor.execute("SELECT COUNT(*) FROM cierres_caja WHERE fecha_cierre LIKE '2026-10-__'")
    count = cursor.fetchone()[0]
    
    if count < 5:
        datos_diarios = [
            ("Santa Elena", "2026-10-01", 31900.0),
            ("Santa Elena", "2026-10-02", 24120.0),
            ("Santa Elena", "2026-10-03", 26550.0),
            ("Santa Elena", "2026-10-04", 56300.0),
            ("Santa Elena", "2026-10-05", 22320.0),
            ("Santa Elena", "2026-10-06", 120625.0),
            ("Santa Elena", "2026-10-07", 128260.0),
            ("Santa Elena", "2026-10-08", 151810.0),
            ("Santa Elena", "2026-10-09", 140625.0),
            ("Santa Elena", "2026-10-10", 35145.0),
            ("Santa Elena", "2026-10-11", 30060.0),
            ("Santa Elena", "2026-10-12", 59199.12),
            ("Santa Elena", "2026-10-13", 75100.0),
            ("Santa Elena", "2026-10-14", 104400.0),
            ("Santa Elena", "2026-10-15", 10700.0),
            # Datos de Monteverde Extremo
            ("Monteverde Extremo", "2026-10-01", 15000.0),
            ("Monteverde Extremo", "2026-10-05", 20000.0),
            ("Monteverde Extremo", "2026-10-10", 45000.0),
            ("Monteverde Extremo", "2026-10-12", 30000.0),
            ("Monteverde Extremo", "2026-10-15", 221925.0)
        ]
        for tienda, fecha, monto in datos_diarios:
            try:
                cursor.execute("""
                    INSERT INTO cierres_caja (tienda, fecha_cierre, efectivo_cobrado)
                    VALUES (?, ?, ?)
                """, (tienda, fecha, monto))
            except Exception:
                pass
        conn.commit()

    try:
        df_ventas = pd.read_sql_query("SELECT tienda, fecha_cierre, efectivo_cobrado FROM cierres_caja", conn)
    except Exception:
        df_ventas = pd.DataFrame()
    conn.close()
    
    v_1_10, v_11_20, v_21_31, total_mes = 0.0, 0.0, 0.0, 0.0
    
    if not df_ventas.empty:
        df_ventas['monto'] = pd.to_numeric(df_ventas['efectivo_cobrado'], errors='coerce').fillna(0)
        total_mes = df_ventas['monto'].sum()
        
        df_ventas['fecha_dt'] = pd.to_datetime(df_ventas['fecha_cierre'], errors='coerce')
        validas = df_ventas[df_ventas['fecha_dt'].notna()].copy()
        
        if not validas.empty:
            validas['dia'] = validas['fecha_dt'].dt.day
            v_1_10 = validas[(validas['dia'] >= 1) & (validas['dia'] <= 10)]['monto'].sum()
            v_11_20 = validas[(validas['dia'] >= 11) & (validas['dia'] <= 20)]['monto'].sum()
            v_21_31 = validas[(validas['dia'] >= 21)]['monto'].sum()
        else:
            v_1_10 = total_mes * 0.40
            v_11_20 = total_mes * 0.35
            v_21_31 = total_mes * 0.25

    tab_sobres, tab_gantt = st.tabs(["📦 Asignación Automática por Sobres", "📊 Cronograma Operativo (Flujo de Caja)"])
    
    with tab_sobres:
        st.markdown("###### **Distribución Automática por Bloques Operativos (Ambas Tiendas)**")
        st.caption("Los montos logrados suman las ventas combinadas de Santa Elena y Monteverde Extremo.")
        
        datos_sobres = [
            {"nombre_fondo": "FONDO DE EMERGENCIA (Días 1-10)", "monto_meta_colones": 1000000.0, "monto_logrado_colones": v_1_10, "prioridad": 1},
            {"nombre_fondo": "ROTATIVO DE COMPRAS + SALARIOS", "monto_meta_colones": 1500000.0, "monto_logrado_colones": v_11_20 * 0.5, "prioridad": 2},
            {"nombre_fondo": "ALQUILER TIENDA 1 (Santa Elena)", "monto_meta_colones": 600000.0, "monto_logrado_colones": v_11_20 * 0.5, "prioridad": 3},
            {"nombre_fondo": "PAGO TARJETA CORPORATIVA", "monto_meta_colones": 500000.0, "monto_logrado_colones": v_21_31 * 0.4, "prioridad": 4},
            {"nombre_fondo": "FACTURAS CRÉDITO + PROVEEDORES", "monto_meta_colones": 2000000.0, "monto_logrado_colones": v_21_31 * 0.6, "prioridad": 5}
        ]
        
        df_display = pd.DataFrame(datos_sobres)
        
        total_meta = df_display["monto_meta_colones"].sum()
        total_logrado = df_display["monto_logrado_colones"].sum()
        cumplimiento = (total_logrado / total_meta * 100) if total_meta > 0 else 0
        
        # --- TARJETAS PRO ESTILO FINTECH ---
        st.markdown("""
            <style>
            .pro-card {
                background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
                border-left: 5px solid #2C5E3B;
                padding: 15px 20px;
                border-radius: 8px;
                box-shadow: 0 2px 6px rgba(0,0,0,0.05);
                margin-bottom: 15px;
            }
            .pro-card-title {
                font-size: 0.85rem;
                text-transform: uppercase;
                color: #6c757d;
                font-weight: 700;
                letter-spacing: 0.5px;
            }
            .pro-card-value {
                font-size: 1.5rem;
                font-weight: 800;
                color: #1c2826;
                margin-top: 5px;
            }
            </style>
        """, unsafe_allow_html=True)

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(f"""
                <div class="pro-card" style="border-left-color: #3b82f6;">
                    <div class="pro-card-title">Meta Global Sobres</div>
                    <div class="pro-card-value">₡ {total_meta:,.0f}</div>
                </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
                <div class="pro-card" style="border-left-color: #10b981;">
                    <div class="pro-card-title">Total Logrado Real</div>
                    <div class="pro-card-value">₡ {total_logrado:,.0f}</div>
                </div>
            """, unsafe_allow_html=True)
        with col3:
            st.markdown(f"""
                <div class="pro-card" style="border-left-color: #f59e0b;">
                    <div class="pro-card-title">% Cumplimiento</div>
                    <div class="pro-card-value">{cumplimiento:.1f}%</div>
                </div>
            """, unsafe_allow_html=True)
        with col4:
            st.markdown(f"""
                <div class="pro-card" style="border-left-color: #8b5cf6;">
                    <div class="pro-card-title">Ventas Tiendas (Total)</div>
                    <div class="pro-card-value">₡ {total_mes:,.0f}</div>
                </div>
            """, unsafe_allow_html=True)

        # Fila de totales en la tabla
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
        st.markdown("###### **Cronograma de Flujo de Efectivo (Ciclo Operativo del Mes)**")
        st.caption("Distribución cronológica basada en los bloques operativos reales.")
        
        hoy = datetime.now()
        anio, mes = hoy.year, hoy.month
        
        datos_ciclo = [
            {"Actividad": "Fondo de Emergencia (Intocable)", "Inicio": f"{anio}-{mes:02d}-01", "Fin": f"{anio}-{mes:02d}-10", "Bloque": "1. Días 1-10 (Reserva)", "Monto": v_1_10},
            {"Actividad": "Salarios 1ra Quincena", "Inicio": f"{anio}-{mes:02d}-11", "Fin": f"{anio}-{mes:02d}-13", "Bloque": "2. Días 11-13 (Salarios)", "Monto": v_11_20 * 0.3},
            {"Actividad": "Alquiler Tienda Santa Elena", "Inicio": f"{anio}-{mes:02d}-14", "Fin": f"{anio}-{mes:02d}-17", "Bloque": "3. Días 14-17 (Alquiler)", "Monto": v_11_20 * 0.3},
            {"Actividad": "Pago Tarjeta de Crédito", "Inicio": f"{anio}-{mes:02d}-18", "Fin": f"{anio}-{mes:02d}-20", "Bloque": "4. Días 18-20 (Tarjeta)", "Monto": v_21_31 * 0.4},
            {"Actividad": "Proveedores / Facturas Crédito", "Inicio": f"{anio}-{mes:02d}-21", "Fin": f"{anio}-{mes:02d}-30", "Bloque": "5. Días 21-30 (Proveedores)", "Monto": v_21_31 * 0.6}
        ]
        
        df_gantt = pd.DataFrame(datos_ciclo)

        fig = px.timeline(
            df_gantt,
            x_start="Inicio",
            x_end="Fin",
            y="Actividad",
            color="Bloque",
            hover_data=["Monto"],
            labels={
                "Actividad": "Fase Operativa", 
                "Inicio": "Fecha",
                "Bloque": "Bloque de Pago"
            }
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