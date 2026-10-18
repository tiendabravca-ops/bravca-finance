def obtener_ventas_reales_desde_db(se_base_2026, me_base_2026):
    """Toma las ventas base de 2026 y sobreescribe dinámicamente cualquier mes que tenga cierres registrados en la base de datos."""
    conn = sqlite3.connect("db_cierres.db")
    query = "SELECT fecha, negocio, colones FROM cierres"
    df_db = pd.read_sql_query(query, conn)
    conn.close()

    # DIAGNÓSTICO TEMPORAL EN PANTALLA: Esto te mostrará qué hay guardado exactamente en la BD
    st.info("🔍 Depuración de Cierres leídos de la BD:")
    st.dataframe(df_db)

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
