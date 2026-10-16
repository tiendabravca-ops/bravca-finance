import sqlite3
import os
from datetime import datetime

def obtener_conexion(nombre_db):
    os.makedirs("databases", exist_ok=True)
    return sqlite3.connect(f"databases/{nombre_db}", timeout=10.0)

def sincronizar_estado_financiero_en_tiempo_real():
    """
    Motor central que recalcula saldos, cruza ingresos de cierres con obligaciones
    y actualiza los fondos de reserva de manera continua.
    """
    # 1. Obtener total de ingresos reales de los cierres de caja
    conn_cierres = obtener_conexion("db_cierres.db")
    cursor_c = conn_cierres.cursor()
    try:
        cursor_c.execute("SELECT SUM(efectivo_cobrado) FROM cierres_caja")
        res_ingresos = cursor_c.fetchone()
        total_ingresos = res_ingresos[0] if res_ingresos and res_ingresos[0] is not None else 0.0
    except Exception:
        total_ingresos = 0.0
    conn_cierres.close()

    # 2. Obtener total de obligaciones pagadas y pendientes
    conn_obs = obtener_conexion("db_obligaciones.db")
    cursor_o = conn_obs.cursor()
    try:
        cursor_o.execute("SELECT SUM(monto_colones) FROM obligaciones WHERE estado = 'PAGADO'")
        res_pagados = cursor_o.fetchone()
        total_pagado = res_pagados[0] if res_pagados and res_pagados[0] is not None else 0.0

        cursor_o.execute("SELECT SUM(monto_colones) FROM obligaciones WHERE estado = 'PENDIENTE'")
        res_pendientes = cursor_o.fetchone()
        total_pendiente = res_pendientes[0] if res_pendientes and res_pendientes[0] is not None else 0.0
    except Exception:
        total_pagado = 0.0
        total_pendiente = 0.0
    conn_obs.close()

    # 3. Actualizar la salud financiera y liquidez neta en el Dashboard (`db_dashboard.db`)
    conn_dash = obtener_conexion("db_dashboard.db")
    cursor_d = conn_dash.cursor()
    cursor_d.execute('''
        CREATE TABLE IF NOT EXISTS kpis_financieros (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            metrica TEXT UNIQUE,
            valor REAL
        )
    ''')
    
    liquidez_neta = total_ingresos - total_pagado
    
    cursor_d.execute("INSERT OR REPLACE INTO kpis_financieros (metrica, valor) VALUES ('total_ingresos', ?)", (total_ingresos,))
    cursor_d.execute("INSERT OR REPLACE INTO kpis_financieros (metrica, valor) VALUES ('total_pagado', ?)", (total_pagado,))
    cursor_d.execute("INSERT OR REPLACE INTO kpis_financieros (metrica, valor) VALUES ('total_pendiente', ?)", (total_pendiente,))
    cursor_d.execute("INSERT OR REPLACE INTO kpis_financieros (metrica, valor) VALUES ('liquidez_neta', ?)", (liquidez_neta,))
    
    conn_dash.commit()
    conn_dash.close()

    return {
        "ingresos": total_ingresos,
        "pagado": total_pagado,
        "pendiente": total_pendiente,
        "liquidez_neta": liquidez_neta
    }