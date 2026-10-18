import sqlite3
import os

def init_db():
    db_path = 'bravca.db'
    
    # Si la base de datos ya existe, se mantiene o elimina según flujo
    conn = sqlite3.connect(db_path, timeout=10.0)
    cursor = conn.cursor()

    # Creación de tablas de la arquitectura unificada
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS historico_2025 (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tienda TEXT,
            mes TEXT,
            ventas_2025 REAL DEFAULT 0,
            proyeccion_2025 REAL DEFAULT 0,
            fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(tienda, mes)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS dashboard_cierres (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tienda TEXT,
            fecha_cierre TEXT,
            ventas_contado REAL DEFAULT 0,
            total_ventas REAL DEFAULT 0,
            tarjeta_cobrado REAL DEFAULT 0,
            efectivo_cobrado REAL DEFAULT 0,
            total_cobrado REAL DEFAULT 0,
            cierre_tarjetas REAL DEFAULT 0,
            conteo_efectivo REAL DEFAULT 0,
            total_dinero_fisico REAL DEFAULT 0,
            diferencia_caja REAL DEFAULT 0,
            estado_caja TEXT DEFAULT 'Cuadra',
            raw_text TEXT,
            fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS proyecciones_ventas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mes TEXT UNIQUE,
            ventas_bravca REAL DEFAULT 0,
            ventas_extremo REAL DEFAULT 0,
            ventas_reales REAL DEFAULT 0,
            proyeccion REAL DEFAULT 0,
            fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS fondos_reserva (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre_fondo TEXT UNIQUE,
            dias_ingreso_asociados INTEGER DEFAULT 0,
            monto_meta_colones REAL,
            monto_logrado_colones REAL DEFAULT 0,
            prioridad INTEGER DEFAULT 1,
            fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS obligaciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tienda TEXT,
            proveedor_concepto TEXT,
            monto_colones REAL,
            fecha_vencimiento TEXT,
            asociado_fondo TEXT,
            estado TEXT DEFAULT 'PENDIENTE',
            fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS gastos_fijos_config (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tienda TEXT,
            proveedor_concepto TEXT,
            monto_colones REAL,
            dia_vencimiento INTEGER,
            asociado_fondo TEXT,
            frecuencia TEXT DEFAULT 'MENSUAL',
            mes_inicio INTEGER DEFAULT 1,
            fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # --- TABLAS DE RECURSOS HUMANOS ---
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

    # Datos oficiales completos del año 2025 para ambas tiendas
    datos_oficiales_2025 = [
        # --- SANTA ELENA ---
        ("Santa Elena", "enero", 5609058.0, 6402917.0),
        ("Santa Elena", "febrero", 5858674.0, 6249901.0),
        ("Santa Elena", "marzo", 6563325.0, 7219657.0),
        ("Santa Elena", "abril", 5030208.0, 5533228.0),
        ("Santa Elena", "mayo", 3051706.0, 3356876.0),
        ("Santa Elena", "junio", 4533249.0, 4986573.0),
        ("Santa Elena", "julio", 6181795.0, 6799974.0),
        ("Santa Elena", "agosto", 5707678.0, 6278445.0),
        ("Santa Elena", "setiembre", 2240840.0, 2464924.0),
        ("Santa Elena", "octubre", 2068705.0, 2275575.0),
        ("Santa Elena", "noviembre", 4995976.0, 5495573.0),
        ("Santa Elena", "diciembre", 6451352.0, 7096487.0),
        
        # --- MONTEVERDE EXTREMO ---
        ("Monteverde Extremo", "enero", 3996723.0, 4396395.0),
        ("Monteverde Extremo", "febrero", 3849065.0, 4233971.0),
        ("Monteverde Extremo", "marzo", 3948468.0, 4343314.0),
        ("Monteverde Extremo", "abril", 3902629.0, 4292891.0),
        ("Monteverde Extremo", "mayo", 2604663.0, 2865129.0),
        ("Monteverde Extremo", "junio", 3305065.0, 3635571.0),
        ("Monteverde Extremo", "julio", 5166749.0, 5683423.0),
        ("Monteverde Extremo", "agosto", 4805683.0, 5286251.0),
        ("Monteverde Extremo", "setiembre", 2902578.0, 3192835.0),
        ("Monteverde Extremo", "octubre", 2914149.0, 3205563.0),
        ("Monteverde Extremo", "noviembre", 4123608.0, 4535968.0),
        ("Monteverde Extremo", "diciembre", 5747824.0, 6322606.0)
    ]

    for tienda, mes, venta, proyeccion in datos_oficiales_2025:
        cursor.execute('''
            INSERT OR REPLACE INTO historico_2025 (tienda, mes, ventas_2025, proyeccion_2025)
            VALUES (?, ?, ?, ?)
        ''', (tienda, mes, venta, proyeccion))

    conn.commit()
    conn.close()

def cargar_ventas_octubre_simplifica2():
    pass

def auto_generar_gastos_fijos():
    pass

if __name__ == "__main__":
    init_db()
