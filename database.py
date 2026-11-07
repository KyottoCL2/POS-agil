import sqlite3
from datetime import datetime
#import urllib.request
#import json

DB_NAME = "punto_agil.db"

def get_connection():
    return sqlite3.connect(DB_NAME)

def calcular_ean13(code_base):
    """Calcula el código de barras EAN-13 completo agregando el dígito verificador estándar (Módulo 10)."""
    code12 = str(code_base).strip()[:12].zfill(12)
    s = sum(int(d) * (1 if i % 2 == 0 else 3) for i, d in enumerate(code12))
    check = (10 - (s % 10)) % 10
    return code12 + str(check)

def validar_ean13(code):
    """Comprueba si un código de barras de 13 dígitos cumple matemáticamente con el estándar EAN-13 (Módulo 10)."""
    code_str = str(code).strip()
    if len(code_str) != 13 or not code_str.isdigit():
        return False
    code12 = code_str[:12]
    s = sum(int(d) * (1 if i % 2 == 0 else 3) for i, d in enumerate(code12))
    check = (10 - (s % 10)) % 10
    return int(code_str[12]) == check

def init_db():
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # Tabla de Productos de la Tienda (Inventario Activo)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS productos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo_barras TEXT UNIQUE NOT NULL,
                nombre TEXT NOT NULL,
                precio_costo REAL NOT NULL DEFAULT 0,
                precio REAL NOT NULL,
                stock INTEGER NOT NULL
            )
        """)

        # Tabla de Cajeros con Contraseña
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cajeros (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL DEFAULT ''
            )
        """)

        try:
            cursor.execute("ALTER TABLE cajeros ADD COLUMN password TEXT NOT NULL DEFAULT ''")
        except sqlite3.OperationalError:
            pass

        # Tabla de Ventas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ventas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha TEXT NOT NULL,
                total REAL NOT NULL,
                medio_pago TEXT NOT NULL DEFAULT 'Efectivo',
                cajero_nombre TEXT NOT NULL DEFAULT 'Cajero',
                monto_pagado REAL DEFAULT 0,
                vuelto REAL DEFAULT 0,
                estado TEXT NOT NULL DEFAULT 'Completada',
                caja_sesion_id INTEGER
            )
        """)

        try:
            cursor.execute("ALTER TABLE ventas ADD COLUMN monto_pagado REAL DEFAULT 0")
        except sqlite3.OperationalError:
            pass

        try:
            cursor.execute("ALTER TABLE ventas ADD COLUMN vuelto REAL DEFAULT 0")
        except sqlite3.OperationalError:
            pass

        try:
            cursor.execute("ALTER TABLE ventas ADD COLUMN estado TEXT NOT NULL DEFAULT 'Completada'")
        except sqlite3.OperationalError:
            pass

        try:
            cursor.execute("ALTER TABLE ventas ADD COLUMN caja_sesion_id INTEGER")
        except sqlite3.OperationalError:
            pass

        # Tabla de Detalle de Ventas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS detalle_ventas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                venta_id INTEGER NOT NULL,
                producto_id INTEGER,
                nombre_item TEXT NOT NULL DEFAULT '',
                cantidad INTEGER NOT NULL,
                precio_costo_unitario REAL NOT NULL DEFAULT 0,
                precio_unitario REAL NOT NULL,
                subtotal REAL NOT NULL,
                FOREIGN KEY (venta_id) REFERENCES ventas (id),
                FOREIGN KEY (producto_id) REFERENCES productos (id)
            )
        """)

        # Migración de detalle_ventas si producto_id es NOT NULL
        cursor.execute("PRAGMA table_info(detalle_ventas)")
        columns = cursor.fetchall()
        for col in columns:
            if col[1] == 'producto_id' and col[3] == 1:
                cursor.execute("""
                    CREATE TABLE detalle_ventas_temp (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        venta_id INTEGER NOT NULL,
                        producto_id INTEGER,
                        nombre_item TEXT NOT NULL DEFAULT '',
                        cantidad INTEGER NOT NULL,
                        precio_costo_unitario REAL NOT NULL DEFAULT 0,
                        precio_unitario REAL NOT NULL,
                        subtotal REAL NOT NULL,
                        FOREIGN KEY (venta_id) REFERENCES ventas (id),
                        FOREIGN KEY (producto_id) REFERENCES productos (id)
                    )
                """)
                cursor.execute("""
                    INSERT INTO detalle_ventas_temp (id, venta_id, producto_id, nombre_item, cantidad, precio_costo_unitario, precio_unitario, subtotal)
                    SELECT id, venta_id, producto_id, COALESCE(nombre_item, ''), cantidad, precio_costo_unitario, precio_unitario, subtotal
                    FROM detalle_ventas
                """)
                cursor.execute("DROP TABLE detalle_ventas")
                cursor.execute("ALTER TABLE detalle_ventas_temp RENAME TO detalle_ventas")
                break

        # Tabla de Historial de Carga de Stock (Kardex de Entradas)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS historial_stock (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                producto_id INTEGER NOT NULL,
                cantidad_agregada INTEGER NOT NULL,
                precio_costo_unitario REAL NOT NULL DEFAULT 0,
                fecha_hora TEXT NOT NULL,
                usuario_id TEXT NOT NULL,
                motivo TEXT DEFAULT 'Reabastecimiento',
                FOREIGN KEY (producto_id) REFERENCES productos (id)
            )
        """)

        # Tabla de Sesiones de Caja (Aperturas y Cierres)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS caja_sesiones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_apertura TEXT NOT NULL,
                fecha_apertura TEXT NOT NULL,
                monto_inicial REAL NOT NULL DEFAULT 0,
                usuario_cierre TEXT,
                fecha_cierre TEXT,
                monto_esperado_efectivo REAL DEFAULT 0,
                monto_real_efectivo REAL DEFAULT 0,
                diferencia REAL DEFAULT 0,
                observaciones TEXT DEFAULT '',
                estado TEXT NOT NULL DEFAULT 'Abierta'
            )
        """)

        # Tabla de Movimientos de Caja (Entradas y Salidas de Caja Chica)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS caja_movimientos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sesion_id INTEGER NOT NULL,
                tipo TEXT NOT NULL,
                monto REAL NOT NULL,
                motivo TEXT NOT NULL,
                fecha_hora TEXT NOT NULL,
                usuario TEXT NOT NULL,
                FOREIGN KEY (sesion_id) REFERENCES caja_sesiones (id)
            )
        """)

        # Tabla de Catálogo Maestro (Chile) — Solo referencia para auto-completar al escanear (OCULTO)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS catalogo_maestro (
                codigo_barras TEXT PRIMARY KEY,
                nombre TEXT NOT NULL,
                marca TEXT DEFAULT '',
                categoria TEXT DEFAULT ''
            )
        """)

        # Migración: Quitar columna imagen_url si existía previamente
        cursor.execute("PRAGMA table_info(catalogo_maestro)")
        cols_maestro = [c[1] for c in cursor.fetchall()]
        if 'imagen_url' in cols_maestro:
            cursor.execute("""
                CREATE TABLE catalogo_maestro_tmp (
                    codigo_barras TEXT PRIMARY KEY,
                    nombre TEXT NOT NULL,
                    marca TEXT DEFAULT '',
                    categoria TEXT DEFAULT ''
                )
            """)
            cursor.execute("""
                INSERT INTO catalogo_maestro_tmp (codigo_barras, nombre, marca, categoria)
                SELECT codigo_barras, nombre, marca, categoria FROM catalogo_maestro
            """)
            cursor.execute("DROP TABLE catalogo_maestro")
            cursor.execute("ALTER TABLE catalogo_maestro_tmp RENAME TO catalogo_maestro")

        # Depurar cualquier código previo con dígito verificador inválido
        cursor.execute("SELECT codigo_barras FROM catalogo_maestro")
        rows = cursor.fetchall()
        for r in rows:
            if not validar_ean13(r[0]):
                cursor.execute("DELETE FROM catalogo_maestro WHERE codigo_barras = ?", (r[0],))

        conn.commit()

    poblar_catalogo_maestro_chile()

# --- CATÁLOGO MAESTRO CHILE (Más de 200 productos más vendidos en almacenes) ---
# Totalmente oculto en UI de inventario/POS; solo provee sugerencias al escanear código de barras.
def poblar_catalogo_maestro_chile():
    productos_chile = [
        ("7801610001011", "Coca-Cola Original 1.5 L", "Coca-Cola", "Bebidas"),
        ("7801610001028", "Coca-Cola Original 2.5 L", "Coca-Cola", "Bebidas"),
        ("7801610001035", "Coca-Cola Original 3 L", "Coca-Cola", "Bebidas"),
        ("7801610001042", "Coca-Cola Original Lata 350 ml", "Coca-Cola", "Bebidas"),
        ("7801610001059", "Coca-Cola Sin Azúcar 1.5 L", "Coca-Cola", "Bebidas"),
        ("7801610001066", "Coca-Cola Sin Azúcar 2.5 L", "Coca-Cola", "Bebidas"),
        ("7801610001073", "Coca-Cola Sin Azúcar 3 L", "Coca-Cola", "Bebidas"),
        ("7801610001080", "Coca-Cola Sin Azúcar Lata 350 ml", "Coca-Cola", "Bebidas"),
        ("7801610001097", "Coca-Cola Light 1.5 L", "Coca-Cola", "Bebidas"),
        ("7801610001103", "Coca-Cola Original 591 ml", "Coca-Cola", "Bebidas"),
        ("7801610001110", "Fanta Naranja 1.5 L", "Fanta", "Bebidas"),
        ("7801610001127", "Fanta Naranja 2.5 L", "Fanta", "Bebidas"),
        ("7801610001134", "Fanta Naranja 3 L", "Fanta", "Bebidas"),
        ("7801610001141", "Fanta Naranja Lata 350 ml", "Fanta", "Bebidas"),
        ("7801610001158", "Fanta Frutilla 1.5 L", "Fanta", "Bebidas"),
        ("7801610001165", "Fanta Pomelo 1.5 L", "Fanta", "Bebidas"),
        ("7801610001172", "Sprite 1.5 L", "Sprite", "Bebidas"),
        ("7801610001189", "Sprite 2.5 L", "Sprite", "Bebidas"),
        ("7801610001196", "Sprite 3 L", "Sprite", "Bebidas"),
        ("7801610001202", "Sprite Lata 350 ml", "Sprite", "Bebidas"),
        ("7801610001219", "Sprite Zero 1.5 L", "Sprite", "Bebidas"),
        ("7801610001226", "Sprite Zero 2.5 L", "Sprite", "Bebidas"),
        ("7801620000011", "Bilz 1.5 L", "CCU", "Bebidas"),
        ("7801620000028", "Bilz 2.5 L", "CCU", "Bebidas"),
        ("7801620000035", "Bilz 3 L", "CCU", "Bebidas"),
        ("7801620000042", "Bilz Lata 350 ml", "CCU", "Bebidas"),
        ("7801620000059", "Bilz Zero 1.5 L", "CCU", "Bebidas"),
        ("7801620000066", "Pap 1.5 L", "CCU", "Bebidas"),
        ("7801620000073", "Pap 2.5 L", "CCU", "Bebidas"),
        ("7801620000080", "Pap 3 L", "CCU", "Bebidas"),
        ("7801620000097", "Crush Piña 1.5 L", "Crush", "Bebidas"),
        ("7801620000103", "Crush Naranja 1.5 L", "Crush", "Bebidas"),
        ("7801620000110", "Pepsi Cola 1.5 L", "Pepsi", "Bebidas"),
        ("7801620000127", "Pepsi Cola 2.5 L", "Pepsi", "Bebidas"),
        ("7801620000134", "Pepsi Cola 3 L", "Pepsi", "Bebidas"),
        ("7801620000141", "Pepsi Cola Lata 350 ml", "Pepsi", "Bebidas"),
        ("7801620000158", "Pepsi Zero 1.5 L", "Pepsi", "Bebidas"),
        ("7801620000165", "Kem Piña 1.5 L", "CCU", "Bebidas"),
        ("7801620000172", "Kem Piña 2.5 L", "CCU", "Bebidas"),
        ("7801620000189", "Kem Piña Zero 1.5 L", "CCU", "Bebidas"),
        ("7801620000196", "Kem Extreme 1.5 L", "CCU", "Bebidas"),
        ("7801620000202", "Kem Zero 2.5 L", "CCU", "Bebidas"),
        ("7801620000219", "Squiz Manzana 1.5 L", "CCU", "Bebidas"),
        ("7801620000226", "7UP Limón 1.5 L", "7UP", "Bebidas"),
        ("7801620000233", "7UP Limón 2.5 L", "7UP", "Bebidas"),
        ("7801620000240", "Mirinda Naranja 1.5 L", "Mirinda", "Bebidas"),
        ("7801620000257", "Canada Dry Ginger Ale 1.5 L", "CCU", "Bebidas"),
        ("7801620000264", "Canada Dry Ginger Ale 2.5 L", "CCU", "Bebidas"),
        ("7801620000271", "Canada Dry Agua Tónica 1.5 L", "CCU", "Bebidas"),
        ("7801620000288", "Nordic Mist Ginger Ale 1.5 L", "Nordic", "Bebidas"),
        ("7801620010010", "Agua Mineral Cachantun Con Gas 1.5 L", "Cachantun", "Aguas"),
        ("7801620010027", "Agua Mineral Cachantun Sin Gas 1.5 L", "Cachantun", "Aguas"),
        ("7801620010034", "Agua Mineral Cachantun Con Gas 500 ml", "Cachantun", "Aguas"),
        ("7801620010041", "Agua Mineral Cachantun Sin Gas 500 ml", "Cachantun", "Aguas"),
        ("7801620010058", "Agua Vital Sin Gas 1.5 L", "Vital", "Aguas"),
        ("7801620010065", "Agua Vital Sin Gas 500 ml", "Vital", "Aguas"),
        ("7801620010072", "Agua Vital Con Gas 1.5 L", "Vital", "Aguas"),
        ("7801620010089", "Agua Benedictino Sin Gas 1.5 L", "Benedictino", "Aguas"),
        ("7801620010096", "Agua Benedictino Sin Gas 500 ml", "Benedictino", "Aguas"),
        ("7801620010102", "Agua Cachantun Sabor Limón 1.5 L", "Cachantun", "Aguas"),
        ("7801620010119", "Agua Cachantun Sabor Manzana 1.5 L", "Cachantun", "Aguas"),
        ("7801620010126", "Agua Mas Manzana 1.5 L", "CCU", "Aguas"),
        ("7801620020019", "Red Bull Energy Drink 250 ml", "Red Bull", "Bebidas Energéticas"),
        ("7801620020026", "Red Bull Sugarfree 250 ml", "Red Bull", "Bebidas Energéticas"),
        ("7801620020033", "Monster Energy Original 473 ml", "Monster", "Bebidas Energéticas"),
        ("7801620020040", "Monster Energy Ultra Zero 473 ml", "Monster", "Bebidas Energéticas"),
        ("7801620020057", "Monster Mango Loco 473 ml", "Monster", "Bebidas Energéticas"),
        ("7801620020064", "Score Energy Drink Original 500 ml", "Score", "Bebidas Energéticas"),
        ("7801620020071", "Gatorade Cool Blue 500 ml", "Gatorade", "Bebidas Deportivas"),
        ("7801620020088", "Gatorade Limón 500 ml", "Gatorade", "Bebidas Deportivas"),
        ("7801620020095", "Gatorade Naranja 500 ml", "Gatorade", "Bebidas Deportivas"),
        ("7801620020101", "Powerade Ion4 Mountain Blast 500 ml", "Powerade", "Bebidas Deportivas"),
        ("7801620020118", "Powerade Ion4 Naranja 500 ml", "Powerade", "Bebidas Deportivas"),
        ("7802800000012", "Jugo Watts Naranja 1.5 L", "Watts", "Jugos"),
        ("7802800000029", "Jugo Watts Durazno 1.5 L", "Watts", "Jugos"),
        ("7802800000036", "Jugo Watts Manzana 1.5 L", "Watts", "Jugos"),
        ("7802800000043", "Jugo Watts Pera 1.5 L", "Watts", "Jugos"),
        ("7802800000050", "Jugo Watts Piña 1.5 L", "Watts", "Jugos"),
        ("7802800000067", "Jugo Watts Frutilla 1.5 L", "Watts", "Jugos"),
        ("7802800000074", "Jugo Watts Naranja Caja 200 ml", "Watts", "Jugos"),
        ("7802800000081", "Jugo Watts Durazno Caja 200 ml", "Watts", "Jugos"),
        ("7802800000098", "Néctar Andina Del Valle Naranja 1.5 L", "Andina", "Jugos"),
        ("7802800000104", "Néctar Andina Del Valle Durazno 1.5 L", "Andina", "Jugos"),
        ("7802800000111", "Néctar Andina Del Valle Manzana 1.5 L", "Andina", "Jugos"),
        ("7802800000128", "Jugo Yuz Naranja 1.5 L", "Yuz", "Jugos"),
        ("7802800000135", "Jugo Yuz Durazno 1.5 L", "Yuz", "Jugos"),
        ("7802800000142", "Néctar Coo-Kee Durazno 1.5 L", "Coo-Kee", "Jugos"),
        ("7802800000159", "Jugo en Polvo Livean Piña Sobre 7 g", "Livean", "Jugos"),
        ("7802800000166", "Jugo en Polvo Zuko Naranja Sobre 13 g", "Zuko", "Jugos"),
        ("7802920001012", "Leche Colun Entera 1 L", "Colun", "Lácteos"),
        ("7802920001029", "Leche Colun Semidescremada 1 L", "Colun", "Lácteos"),
        ("7802920001036", "Leche Colun Descremada 1 L", "Colun", "Lácteos"),
        ("7802920001043", "Leche Colun Sin Lactosa Semidescremada 1 L", "Colun", "Lácteos"),
        ("7802920001050", "Leche Colun Chocolate 200 ml", "Colun", "Lácteos"),
        ("7802920001067", "Leche Colun Frutilla 200 ml", "Colun", "Lácteos"),
        ("7802920001074", "Manjar Colun Bolsa 400 g", "Colun", "Dulces"),
        ("7802920001081", "Manjar Colun Pote 500 g", "Colun", "Dulces"),
        ("7802920001098", "Mantequilla Colun Con Sal Pan 250 g", "Colun", "Lácteos"),
        ("7802920001104", "Mantequilla Colun Sin Sal Pan 250 g", "Colun", "Lácteos"),
        ("7802920001111", "Queso Gauda Colun Laminado 250 g", "Colun", "Fiambrería"),
        ("7802920001128", "Queso Chanco Colun Laminado 250 g", "Colun", "Fiambrería"),
        ("7802920001135", "Quesillo Colun 320 g", "Colun", "Lácteos"),
        ("7802920001142", "Crema de Leche Colun Caja 200 ml", "Colun", "Lácteos"),
        ("7802900000011", "Leche Soprole Entera 1 L", "Soprole", "Lácteos"),
        ("7802900000028", "Leche Soprole Semidescremada 1 L", "Soprole", "Lácteos"),
        ("7802900000035", "Leche Soprole Descremada 1 L", "Soprole", "Lácteos"),
        ("7802900000042", "Leche Soprole Sin Lactosa 1 L", "Soprole", "Lácteos"),
        ("7802900000059", "Leche Soprole Chocolate 200 ml", "Soprole", "Lácteos"),
        ("7802900000066", "Yogurt Soprole Batido Frutilla 120 g", "Soprole", "Lácteos"),
        ("7802900000073", "Yogurt Soprole Batido Vainilla 120 g", "Soprole", "Lácteos"),
        ("7802900000080", "Yogurt Soprole Batido Damasco 120 g", "Soprole", "Lácteos"),
        ("7802900000097", "Yogurt Soprole Trozos Durazno 140 g", "Soprole", "Lácteos"),
        ("7802900000103", "Yogurt Soprole 1+1 Hojuelas 140 g", "Soprole", "Lácteos"),
        ("7802900000110", "Crema de Leche Soprole Caja 200 ml", "Soprole", "Lácteos"),
        ("7802900000127", "Postre Manjarate Soprole 130 g", "Soprole", "Lácteos"),
        ("7802900000134", "Leche Loncoleche Entera 1 L", "Loncoleche", "Lácteos"),
        ("7802900000141", "Leche Loncoleche Semidescremada 1 L", "Loncoleche", "Lácteos"),
        ("7802900000158", "Leche Nido Instantánea Tarro 400 g", "Nestlé", "Lácteos"),
        ("7802900000165", "Leche Nido Instantánea Tarro 800 g", "Nestlé", "Lácteos"),
        ("7802900000172", "Leche Condensada Nestlé Lata 397 g", "Nestlé", "Lácteos"),
        ("7802900000189", "Crema Nestlé Lata 157 g", "Nestlé", "Lácteos"),
        ("7802900000196", "Queso Crema Philadelphia 210 g", "Philadelphia", "Lácteos"),
        ("7803010000014", "Huevos Medianos Blancos Bandeja x12", "Ariztía", "Huevos"),
        ("7803010000021", "Huevos Grandes Color Bandeja x12", "Ariztía", "Huevos"),
        ("7803010000038", "Huevos Extra Grandes Color Bandeja x12", "Super Pollo", "Huevos"),
        ("7803010000045", "Huevos Color Bandeja x30", "Santa Marta", "Huevos"),
        ("7803010000052", "Huevos Blancos Bandeja x6", "Ariztía", "Huevos"),
        ("7802500000015", "Fideos Spaghetti N°5 Carozzi 400 g", "Carozzi", "Pastas"),
        ("7802500000022", "Fideos Tallarines N°77 Carozzi 400 g", "Carozzi", "Pastas"),
        ("7802500000039", "Fideos Espirales Carozzi 400 g", "Carozzi", "Pastas"),
        ("7802500000046", "Fideos Corbatitas Carozzi 400 g", "Carozzi", "Pastas"),
        ("7802500000053", "Fideos Cabellos de Angel Carozzi 400 g", "Carozzi", "Pastas"),
        ("7802500000060", "Fideos Caracoles Carozzi 400 g", "Carozzi", "Pastas"),
        ("7802500000077", "Fideos Rigatoni Carozzi 400 g", "Carozzi", "Pastas"),
        ("7802500000084", "Salsa de Tomate Pomarola Carozzi Doypack 200 g", "Carozzi", "Salsas"),
        ("7802500000091", "Salsa de Tomate Italiana Carozzi Doypack 200 g", "Carozzi", "Salsas"),
        ("7802500000107", "Salsa de Tomate Carne Carozzi Doypack 200 g", "Carozzi", "Salsas"),
        ("7802500000114", "Salsa Pomarola Tradicional Tarro 400 g", "Carozzi", "Salsas"),
        ("7802510000012", "Fideos Spaghetti N°5 Lucchetti 400 g", "Lucchetti", "Pastas"),
        ("7802510000029", "Fideos Tallarines N°77 Lucchetti 400 g", "Lucchetti", "Pastas"),
        ("7802510000036", "Fideos Espirales Lucchetti 400 g", "Lucchetti", "Pastas"),
        ("7802510000043", "Fideos Corbatas Lucchetti 400 g", "Lucchetti", "Pastas"),
        ("7802510000050", "Salsa de Tomate Tuco de Carne Lucchetti 200 g", "Lucchetti", "Salsas"),
        ("7802100000019", "Arroz Grado 2 Tucapel Bolsa 1 kg", "Tucapel", "Arroz"),
        ("7802100000026", "Arroz Grado 1 Tucapel Bolsa 1 kg", "Tucapel", "Arroz"),
        ("7802100000033", "Arroz Grado 2 Tucapel Bolsa 2 kg", "Tucapel", "Arroz"),
        ("7802100000040", "Arroz Pregraneado Tucapel 1 kg", "Tucapel", "Arroz"),
        ("7802200000018", "Arroz Grado 2 Miraflores Bolsa 1 kg", "Miraflores", "Arroz"),
        ("7802200000025", "Arroz Grado 1 Miraflores Bolsa 1 kg", "Miraflores", "Arroz"),
        ("7802200000032", "Lentejas Grado 1 Tucapel 1 kg", "Tucapel", "Legumbres"),
        ("7802200000049", "Lentejas 6mm Miraflores 1 kg", "Miraflores", "Legumbres"),
        ("7802200000056", "Porotos Hallados Tucapel 1 kg", "Tucapel", "Legumbres"),
        ("7802200000063", "Garbanzos Grado 1 Tucapel 1 kg", "Tucapel", "Legumbres"),
        ("7802300000017", "Aceite Vegetal Belmont Botella 900 ml", "Belmont", "Aceites"),
        ("7802300000024", "Aceite Maravilla Miraflores Botella 900 ml", "Miraflores", "Aceites"),
        ("7802300000031", "Aceite Chef Maravilla Botella 900 ml", "Chef", "Aceites"),
        ("7802300000048", "Aceite Vegetal Natura 900 ml", "Natura", "Aceites"),
        ("7802300000055", "Aceite de Oliva Extra Virgen Alonso 500 ml", "Alonso", "Aceites"),
        ("7802300000062", "Vinagre de Manzana Traverso 500 ml", "Traverso", "Condimentos"),
        ("7802300000079", "Vinagre de Vino Blanco Traverso 500 ml", "Traverso", "Condimentos"),
        ("7802300000086", "Salsa de Soya Traverso 200 ml", "Traverso", "Condimentos"),
        ("7802300000093", "Mayonesa Hellmanns Regular Doypack 472 g", "Hellmanns", "Salsas"),
        ("7802300000109", "Mayonesa Kraft Mayo Doypack 400 g", "Kraft", "Salsas"),
        ("7802300000116", "Ketchup JB Doypack 250 g", "JB", "Salsas"),
        ("7802300000123", "Ketchup Hellmanns Doypack 390 g", "Hellmanns", "Salsas"),
        ("7802300000130", "Mostaza JB Doypack 250 g", "JB", "Salsas"),
        ("7802300000147", "Mostaza Traverso Pote 200 g", "Traverso", "Salsas"),
        ("7803100000016", "Azúcar Blanca Iansa Bolsa 1 kg", "Iansa", "Abarrotes"),
        ("7803100000023", "Azúcar Blanca Iansa Bolsa 2 kg", "Iansa", "Abarrotes"),
        ("7803100000030", "Azúcar Rubia Iansa Bolsa 1 kg", "Iansa", "Abarrotes"),
        ("7803200000015", "Sal Lobos Fina Bolsa 1 kg", "Lobos", "Abarrotes"),
        ("7803200000022", "Sal Lobos Parrillera Bolsa 1 kg", "Lobos", "Abarrotes"),
        ("7803200000039", "Sal Lobos Salero 125 g", "Lobos", "Abarrotes"),
        ("7803300000014", "Harina Selecta Sin Polvos de Hornear 1 kg", "Selecta", "Harinas"),
        ("7803300000021", "Harina Selecta Con Polvos de Hornear 1 kg", "Selecta", "Harinas"),
        ("7803300000038", "Harina Pizca de Sal Sin Polvos 1 kg", "Pizca de Sal", "Harinas"),
        ("7803300000045", "Levadura Fresca Levapan 50 g", "Levapan", "Abarrotes"),
        ("7803300000052", "Polvos de Hornear Royal Sobre 100 g", "Royal", "Abarrotes"),
        ("7803400000013", "Atún Lomitos en Aceite San José 160 g", "San José", "Conservas"),
        ("7803400000020", "Atún Lomitos en Agua San José 160 g", "San José", "Conservas"),
        ("7803400000037", "Atún Lomitos en Aceite Fleury Michon 170 g", "Fleury Michon", "Conservas"),
        ("7803400000044", "Atún Lomitos en Agua Fleury Michon 170 g", "Fleury Michon", "Conservas"),
        ("7803400000051", "Atún Lomitos San Remo en Aceite 160 g", "San Remo", "Conservas"),
        ("7803400000068", "Jurel Tipo Salmón Único Lata 425 g", "Único", "Conservas"),
        ("7803400000075", "Choritos al Natural Robinson Crusoe 190 g", "Robinson Crusoe", "Conservas"),
        ("7803400000082", "Duraznos en Mitades Dos Caballos Tarro 590 g", "Dos Caballos", "Conservas"),
        ("7803400000099", "Choclo Dulce Wasil Tarro 400 g", "Wasil", "Conservas"),
        ("7803400000105", "Arvejas Wasil Tarro 400 g", "Wasil", "Conservas"),
        ("7803400000112", "Surtido de Mariscos San José Lata 190 g", "San José", "Conservas"),
        ("7804100000013", "Café Nescafé Tradición Frasco 100 g", "Nescafé", "Cafetería"),
        ("7804100000020", "Café Nescafé Tradición Frasco 170 g", "Nescafé", "Cafetería"),
        ("7804100000037", "Café Nescafé Tradición Doypack 50 g", "Nescafé", "Cafetería"),
        ("7804100000044", "Café Nescafé Dolca Frasco 100 g", "Nescafé", "Cafetería"),
        ("7804100000051", "Café Nescafé Gold Frasco 100 g", "Nescafé", "Cafetería"),
        ("7804200000012", "Té Supremo Ceilán Caja 100 Bolsitas", "Supremo", "Té"),
        ("7804200000029", "Té Supremo Ceilán Caja 20 Bolsitas", "Supremo", "Té"),
        ("7804200000036", "Té Club Ceilán Caja 100 Bolsitas", "Té Club", "Té"),
        ("7804200000043", "Té Lipton Yellow Label Caja 100 Bolsitas", "Lipton", "Té"),
        ("7804200000050", "Té Lipton Yellow Label Caja 25 Bolsitas", "Lipton", "Té"),
        ("7804200000067", "Hierbas Manzanilla Supremo 20 Bolsitas", "Supremo", "Té"),
        ("7804200000074", "Hierbas Menta Supremo 20 Bolsitas", "Supremo", "Té"),
        ("7804300000011", "Pan de Molde Blanco Ideal Grande 560 g", "Ideal", "Panadería"),
        ("7804300000028", "Pan de Molde Integral Ideal Grande 560 g", "Ideal", "Panadería"),
        ("7804300000035", "Pan de Molde Blanco Ideal Chico 350 g", "Ideal", "Panadería"),
        ("7804300000042", "Pan de Molde Integral Ideal Chico 350 g", "Ideal", "Panadería"),
        ("7804300000059", "Pan de Molde Brioche Ideal 420 g", "Ideal", "Panadería"),
        ("7804300000066", "Pan Pita Árabe Ideal Bolsa 4 un", "Ideal", "Panadería"),
        ("7804400000010", "Avena Quaker Tradicional Bolsa 400 g", "Quaker", "Cereales"),
        ("7804400000027", "Avena Quaker Instantánea Bolsa 400 g", "Quaker", "Cereales"),
        ("7804400000034", "Cereal Chocapic Nestlé Caja 400 g", "Nestlé", "Cereales"),
        ("7804400000041", "Cereal Corn Flakes Nestlé Caja 450 g", "Nestlé", "Cereales"),
        ("7804400000058", "Cereal Trix Nestlé Caja 400 g", "Nestlé", "Cereales"),
        ("7804400000065", "Cereal Milo Nestlé Caja 400 g", "Nestlé", "Cereales"),
        ("7804400000072", "Nesquik Chocolate en Polvo Bolsa 400 g", "Nestlé", "Cereales"),
        ("7804400000089", "Milo Nestlé en Polvo Lata 400 g", "Nestlé", "Cereales"),
        ("7805100000010", "Galletas Triton Vainilla McKay 126 g", "McKay", "Galletas"),
        ("7805100000027", "Galletas Triton Chocolate McKay 126 g", "McKay", "Galletas"),
        ("7805100000034", "Galletas Serranita McKay 130 g", "McKay", "Galletas"),
        ("7805100000041", "Galletas Vino McKay 140 g", "McKay", "Galletas"),
        ("7805100000058", "Galletas de Leche McKay 165 g", "McKay", "Galletas"),
        ("7805100000065", "Galletas Animalitos McKay 130 g", "McKay", "Galletas"),
        ("7805100000072", "Galletas Cream Crackers McKay 200 g", "McKay", "Galletas"),
        ("7805100000089", "Galletas Club Social Original 234 g", "McKay", "Galletas"),
        ("7805100000096", "Galletas Tuareg McKay 130 g", "McKay", "Galletas"),
        ("7805100000102", "Galletas Kuky McKay Chips Chocolate 120 g", "McKay", "Galletas"),
        ("7805100000119", "Galletas Frac Vainilla Costa 130 g", "Costa", "Galletas"),
        ("7805100000126", "Galletas Frac Chocolate Costa 130 g", "Costa", "Galletas"),
        ("7805100000133", "Galletas Nik Costa 71 g", "Costa", "Galletas"),
        ("7805100000140", "Galletas Criollitas Costa 100 g", "Costa", "Galletas"),
        ("7805100000157", "Galletas Oreo Original 119 g", "Oreo", "Galletas"),
        ("7805100000164", "Galletas Mini Chocman Costa 130 g", "Costa", "Galletas"),
        ("7805200000019", "Chocolate Super 8 Nestlé Original 29 g", "Nestlé", "Golosinas"),
        ("7805200000026", "Chocolate Super 8 Nestlé Dark 29 g", "Nestlé", "Golosinas"),
        ("7805200000033", "Chocolate Sahne-Nuss Nestlé Barra 100 g", "Nestlé", "Chocolates"),
        ("7805200000040", "Chocolate Sahne-Nuss Nestlé Barra 250 g", "Nestlé", "Chocolates"),
        ("7805200000057", "Chocolate Trencito Barra 100 g", "Nestlé", "Chocolates"),
        ("7805200000064", "Pastelito Chocman Costa 33 g", "Costa", "Golosinas"),
        ("7805200000071", "Golosina Chokita Nestlé (Ex-Negrita) 30 g", "Nestlé", "Golosinas"),
        ("7805200000088", "Barra Golpe Nestlé 27 g", "Nestlé", "Golosinas"),
        ("7805200000095", "Chocolate Capri Leche Nestlé 30 g", "Nestlé", "Golosinas"),
        ("7805200000101", "Bon o Bon Leche Arcor 15 g", "Arcor", "Golosinas"),
        ("7805200000118", "Chocolate Vizzio Costa Almendra 120 g", "Costa", "Chocolates"),
        ("7805200000125", "Caramelos Halls Mentol Tubo 28 g", "Halls", "Golosinas"),
        ("7805200000132", "Caramelos Halls Cereza Tubo 28 g", "Halls", "Golosinas"),
        ("7805200000149", "Chicles Trident Menta 5 un", "Trident", "Golosinas"),
        ("7805200000156", "Chicle Bubbaloo Frutilla 1 un", "Bubbaloo", "Golosinas"),
        ("7805200000163", "Gomitas Fruggele Ambrosoli Bolsa 100 g", "Ambrosoli", "Golosinas"),
        ("7805300000018", "Papas Fritas Lays Clásicas Bolsa 190 g", "Lays", "Snacks"),
        ("7805300000025", "Papas Fritas Lays Clásicas Bolsa 42 g", "Lays", "Snacks"),
        ("7805300000032", "Papas Fritas Lays Corte Americano 180 g", "Lays", "Snacks"),
        ("7805300000049", "Doritos Mega Queso Bolsa 140 g", "Doritos", "Snacks"),
        ("7805300000056", "Doritos Mega Queso Bolsa 42 g", "Doritos", "Snacks"),
        ("7805300000063", "Papas Fritas Ruffles Onduladas 185 g", "Ruffles", "Snacks"),
        ("7805300000070", "Cheetos Bolitas Queso 42 g", "Cheetos", "Snacks"),
        ("7805300000087", "Ramitas Evercrisp Saladas 150 g", "Evercrisp", "Snacks"),
        ("7805300000094", "Ramitas Evercrisp Queso 150 g", "Evercrisp", "Snacks"),
        ("7805300000100", "Ramitas Evercrisp Queso 50 g", "Evercrisp", "Snacks"),
        ("7805300000117", "Papas Pringles Original Tubo 124 g", "Pringles", "Snacks"),
        ("7805300000124", "Papas Pringles Crema y Cebolla Tubo 124 g", "Pringles", "Snacks"),
        ("7805300000131", "Maní Salado Marco Polo Bolsa 100 g", "Marco Polo", "Snacks"),
        ("7805300000148", "Papas Fritas Kryzpo Original Tubo 140 g", "Kryzpo", "Snacks"),
        ("7805400000017", "Vienesas Tradicionales Super Pollo Paquete 500 g", "Super Pollo", "Cecinas"),
        ("7805400000024", "Vienesas de Pavo Super Pollo 500 g", "Super Pollo", "Cecinas"),
        ("7805400000031", "Vienesas Sureñas San Jorge Paquete 500 g", "San Jorge", "Cecinas"),
        ("7805400000048", "Vienesas Tradicionales Llanquihue 500 g", "Llanquihue", "Cecinas"),
        ("7805400000055", "Jamón Colonial San Jorge Laminado 100 g", "San Jorge", "Cecinas"),
        ("7805400000062", "Jamón Pierna PF Laminado 100 g", "PF", "Cecinas"),
        ("7805400000079", "Jamón Sandwich Super Cerdo Laminado 100 g", "Super Cerdo", "Cecinas"),
        ("7805400000086", "Mortadela Lisa San Jorge Laminada 100 g", "San Jorge", "Cecinas"),
        ("7805400000093", "Salchichón Cerveza PF Laminado 100 g", "PF", "Cecinas"),
        ("7805400000109", "Paté de Ternera La Preferida Pote 125 g", "La Preferida", "Cecinas"),
        ("7805500000016", "Papas Prefritas Corte Tradicional McCain 750 g", "McCain", "Congelados"),
        ("7805500000023", "Papas Duquesas McCain Bolsa 500 g", "McCain", "Congelados"),
        ("7805500000030", "Hamburguesas Vacuno San Jorge 4 un 400 g", "San Jorge", "Congelados"),
        ("7805500000047", "Hamburguesas Vacuno La Crianza 4 un 400 g", "La Crianza", "Congelados"),
        ("7805500000054", "Nuggets de Pollo Super Pollo Bolsa 400 g", "Super Pollo", "Congelados"),
        ("7805500000061", "Empanadas de Queso Congeladas La Crianza 10 un", "La Crianza", "Congelados"),
        ("7805500000078", "Choclo Congelado Minuto Verde Bolsa 400 g", "Minuto Verde", "Congelados"),
        ("7805500000085", "Arvejas Congeladas Minuto Verde Bolsa 400 g", "Minuto Verde", "Congelados"),
        ("7805500000092", "Primavera de Verduras Minuto Verde 400 g", "Minuto Verde", "Congelados"),
        ("7805500000108", "Pizzetas Individuales Casa Tartufo 4 un", "Casa Tartufo", "Congelados"),
        ("7806100000017", "Cloro Clorinda Tradicional Botella 1 L", "Clorinda", "Aseo"),
        ("7806100000024", "Cloro Clorinda Gel Botella 900 ml", "Clorinda", "Aseo"),
        ("7806100000031", "Cloro Bleris Concentrado Botella 1 L", "Bleris", "Aseo"),
        ("7806100000048", "Limpiador Líquido Poett Lavanda Botella 900 ml", "Poett", "Aseo"),
        ("7806100000055", "Limpiador Fabuloso Frescura Marina 1 L", "Fabuloso", "Aseo"),
        ("7806100000062", "Desinfectante Aerosol Lysoform Original 360 ml", "Lysoform", "Aseo"),
        ("7806100000079", "Limpiador Mr. Músculo Cocina Gatillo 500 ml", "Mr. Músculo", "Aseo"),
        ("7806200000016", "Lavaloza Quix Limón Concentrado Botella 500 ml", "Quix", "Aseo"),
        ("7806200000023", "Lavaloza Quix Limón Concentrado Botella 750 ml", "Quix", "Aseo"),
        ("7806200000030", "Detergente en Polvo Omo Multiacción Bolsa 400 g", "Omo", "Aseo"),
        ("7806200000047", "Detergente en Polvo Rinso Bolsa 400 g", "Rinso", "Aseo"),
        ("7806200000054", "Suavizante Textil Suavitel Primaveral 500 ml", "Suavitel", "Aseo"),
        ("7806200000061", "Virutilla de Acero Inoxidable Virutex 2 un", "Virutex", "Aseo"),
        ("7806200000078", "Esponja Multiuso Scotch-Brite Verde 2 un", "Scotch-Brite", "Aseo"),
        ("7806300000015", "Papel Higiénico Confort Doble Hoja 4 Rollos", "Confort", "Higiene"),
        ("7806300000022", "Papel Higiénico Confort Doble Hoja 8 Rollos", "Confort", "Higiene"),
        ("7806300000039", "Papel Higiénico Confort Doble Hoja 12 Rollos", "Confort", "Higiene"),
        ("7806300000046", "Papel Higiénico Elite Doble Hoja 4 Rollos", "Elite", "Higiene"),
        ("7806300000053", "Papel Higiénico Elite Ultra 8 Rollos", "Elite", "Higiene"),
        ("7806300000060", "Toalla Nova Clásica Papel Absorbente 2 Rollos", "Nova", "Higiene"),
        ("7806400000014", "Jabón en Barra Rexona Antibacterial 90 g", "Rexona", "Higiene"),
        ("7806400000021", "Jabón en Barra Dove Original Hidratante 90 g", "Dove", "Higiene"),
        ("7806400000038", "Jabón en Barra Protex Antibacterial 85 g", "Protex", "Higiene"),
        ("7806400000045", "Shampoo Head & Shoulders Manzana Fresh 400 ml", "Head & Shoulders", "Higiene"),
        ("7806400000052", "Shampoo Pantene Pro-V Restauración 400 ml", "Pantene", "Higiene"),
        ("7806400000069", "Shampoo Ballerina Manzanilla Familiar 750 ml", "Ballerina", "Higiene"),
        ("7806400000076", "Pasta Dental Colgate Triple Acción 90 ml", "Colgate", "Higiene"),
        ("7806400000083", "Pasta Dental Colgate Total 12 Clean Mint 90 ml", "Colgate", "Higiene"),
        ("7806400000090", "Cepillo Dental Colgate Extra Clean Medio 1 un", "Colgate", "Higiene"),
        ("7806400000106", "Desodorante Rexona Roll-On Antibacterial 50 ml", "Rexona", "Higiene"),
        ("7806400000113", "Desodorante Dove Roll-On Original 50 ml", "Dove", "Higiene"),
        ("7806400000120", "Toallas Higiénicas Always Normal con Alas 8 un", "Always", "Higiene"),
        ("7806400000137", "Toallas Húmedas Huggies Triple Protección 48 un", "Huggies", "Bebés"),
        ("7806400000144", "Pañuelos Desechables Elite Paquete 10 un", "Elite", "Higiene"),
    ]
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.executemany("""
            INSERT OR IGNORE INTO catalogo_maestro (codigo_barras, nombre, marca, categoria)
            VALUES (?, ?, ?, ?)
        """, productos_chile)
        conn.commit()

def registrar_en_catalogo_maestro(codigo, nombre, marca="", categoria=""):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO catalogo_maestro (codigo_barras, nombre, marca, categoria)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(codigo_barras) DO UPDATE SET
                nombre = excluded.nombre,
                marca = excluded.marca,
                categoria = excluded.categoria
        """, (codigo, nombre, marca, categoria))
        conn.commit()

def buscar_en_catalogo_maestro(codigo):
    if not codigo:
        return None

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT codigo_barras, nombre, marca, categoria
            FROM catalogo_maestro 
            WHERE codigo_barras = ?
        """, (codigo,))
        prod = cursor.fetchone()
        if prod:
            return {
                "codigo_barras": prod[0],
                "nombre": prod[1],
                "marca": prod[2],
                "categoria": prod[3],
                "origen": "Local"
            }

    return None

    # Búsqueda complementaria en línea en Open Food Facts si el producto no está precargado
    try:
        url = f"https://world.openfoodfacts.org/api/v2/product/{codigo}.json"
        req = urllib.request.Request(url, headers={"User-Agent": "PuntoAgilPOS - Chile - 1.0"})
        with urllib.request.urlopen(req, timeout=2.0) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            if data.get("status") == 1 and "product" in data:
                p = data["product"]
                nombre = p.get("product_name_es") or p.get("product_name") or ""
                marca = p.get("brands") or ""
                categoria = p.get("categories") or ""
                if nombre:
                    nombre_completo = f"{nombre} ({marca})".strip() if marca else nombre
                    registrar_en_catalogo_maestro(codigo, nombre_completo, marca, categoria)
                    return {
                        "codigo_barras": codigo,
                        "nombre": nombre_completo,
                        "marca": marca,
                        "categoria": categoria,
                        "origen": "Open Food Facts (En Línea)"
                    }
    except Exception:
        pass

    return None

# --- CONSULTAS DE CAJEROS ---
def get_cajeros():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombre, password FROM cajeros ORDER BY nombre ASC")
        return cursor.fetchall()

def crear_cajero(nombre, password):
    nombre_clean = nombre.strip().title()
    if not nombre_clean:
        return False, "El nombre no puede estar vacío."
    with get_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO cajeros (nombre, password) VALUES (?, ?)", (nombre_clean, password))
            conn.commit()
            return True, "Cajero registrado con éxito."
        except sqlite3.IntegrityError:
            return False, "Ya existe un cajero registrado con este nombre."

def verificar_cajero_password(nombre, password):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT password FROM cajeros WHERE nombre = ?", (nombre,))
        res = cursor.fetchone()
        if res:
            return res[0] == password
        return False

def eliminar_cajero(nombre):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM cajeros WHERE nombre = ?", (nombre,))
        conn.commit()

# --- CONSULTAS DE PRODUCTOS ---
def get_producto_por_codigo(codigo):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, codigo_barras, nombre, precio_costo, precio, stock FROM productos WHERE codigo_barras = ?", (codigo,))
        return cursor.fetchone()

def buscar_productos_live(query):
    if not query:
        return []
    with get_connection() as conn:
        cursor = conn.cursor()
        like_q = f"%{query}%"
        cursor.execute("""
            SELECT id, codigo_barras, nombre, precio_costo, precio, stock 
            FROM productos 
            WHERE nombre LIKE ? OR codigo_barras LIKE ? 
            LIMIT 7
        """, (like_q, like_q))
        return cursor.fetchall()

def get_todos_productos(filtro_critico=False):
    with get_connection() as conn:
        cursor = conn.cursor()
        if filtro_critico:
            cursor.execute("SELECT id, codigo_barras, nombre, precio_costo, precio, stock FROM productos WHERE stock <= 5 ORDER BY stock ASC")
        else:
            cursor.execute("SELECT id, codigo_barras, nombre, precio_costo, precio, stock FROM productos ORDER BY nombre ASC")
        return cursor.fetchall()

def guardar_producto(codigo, nombre, precio_costo, precio, stock, prod_id=None):
    with get_connection() as conn:
        cursor = conn.cursor()
        if prod_id:
            cursor.execute("SELECT id, nombre FROM productos WHERE codigo_barras = ? AND id != ?", (codigo, prod_id))
            existente = cursor.fetchone()
            if existente:
                return False, f"El código '{codigo}' ya está asignado al producto '{existente[1]}'."

            cursor.execute("""
                UPDATE productos 
                SET codigo_barras = ?, nombre = ?, precio_costo = ?, precio = ?, stock = ?
                WHERE id = ?
            """, (codigo, nombre, precio_costo, precio, stock, prod_id))
            conn.commit()
            return True, "Producto actualizado con éxito."
        else:
            cursor.execute("SELECT id, nombre FROM productos WHERE codigo_barras = ?", (codigo,))
            existente = cursor.fetchone()
            if existente:
                return False, f"El código '{codigo}' ya existe para '{existente[1]}'. No se puede duplicar."

            cursor.execute("""
                INSERT INTO productos (codigo_barras, nombre, precio_costo, precio, stock)
                VALUES (?, ?, ?, ?, ?)
            """, (codigo, nombre, precio_costo, precio, stock))
            conn.commit()
            return True, "Producto registrado con éxito."

def sumar_stock_producto(prod_id, cantidad_a_sumar):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE productos SET stock = stock + ? WHERE id = ?", (cantidad_a_sumar, prod_id))
        conn.commit()

def eliminar_producto(prod_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM productos WHERE id = ?", (prod_id,))
        conn.commit()

# --- HISTORIAL DE CARGA DE STOCK (KARDEX) ---
def registrar_carga_stock(producto_id, cantidad, precio_costo_unitario, usuario_nombre, motivo="Reabastecimiento"):
    fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE productos SET stock = stock + ? WHERE id = ?", (cantidad, producto_id))
        
        if precio_costo_unitario > 0:
            cursor.execute("UPDATE productos SET precio_costo = ? WHERE id = ?", (precio_costo_unitario, producto_id))

        cursor.execute("""
            INSERT INTO historial_stock (producto_id, cantidad_agregada, precio_costo_unitario, fecha_hora, usuario_id, motivo)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (producto_id, cantidad, precio_costo_unitario, fecha_actual, usuario_nombre, motivo))
        conn.commit()
    return True, "Stock cargado correctamente."

def get_historial_stock(limite=100):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT hs.id, hs.fecha_hora, COALESCE(p.codigo_barras, 'N/A'), COALESCE(p.nombre, 'Producto Desconocido'), 
                   hs.cantidad_agregada, hs.precio_costo_unitario, hs.usuario_id, hs.motivo
            FROM historial_stock hs
            LEFT JOIN productos p ON hs.producto_id = p.id
            ORDER BY hs.id DESC
            LIMIT ?
        """, (limite,))
        return cursor.fetchall()

# --- CONTROL Y ARQUEO DE CAJA ---
def get_caja_abierta():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, usuario_apertura, fecha_apertura, monto_inicial, estado
            FROM caja_sesiones 
            WHERE estado = 'Abierta' 
            ORDER BY id DESC LIMIT 1
        """)
        return cursor.fetchone()

def abrir_caja(monto_inicial, usuario_nombre):
    caja_activa = get_caja_abierta()
    if caja_activa:
        return False, f"Ya existe una caja abierta iniciada por {caja_activa[1]}."

    fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO caja_sesiones (usuario_apertura, fecha_apertura, monto_inicial, estado)
            VALUES (?, ?, ?, 'Abierta')
        """, (usuario_nombre, fecha_actual, float(monto_inicial)))
        conn.commit()
    return True, "Caja abierta con éxito."

def registrar_movimiento_caja(sesion_id, tipo, monto, motivo, usuario_nombre):
    fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO caja_movimientos (sesion_id, tipo, monto, motivo, fecha_hora, usuario)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (sesion_id, tipo, float(monto), motivo, fecha_actual, usuario_nombre))
        conn.commit()
    return True, f"{tipo} de ${int(monto):,} registrada con éxito."

def get_resumen_caja(sesion_id=None):
    with get_connection() as conn:
        cursor = conn.cursor()
        if sesion_id:
            cursor.execute("SELECT id, usuario_apertura, fecha_apertura, monto_inicial, usuario_cierre, fecha_cierre, monto_esperado_efectivo, monto_real_efectivo, diferencia, observaciones, estado FROM caja_sesiones WHERE id = ?", (sesion_id,))
        else:
            cursor.execute("SELECT id, usuario_apertura, fecha_apertura, monto_inicial, usuario_cierre, fecha_cierre, monto_esperado_efectivo, monto_real_efectivo, diferencia, observaciones, estado FROM caja_sesiones WHERE estado = 'Abierta' ORDER BY id DESC LIMIT 1")
        
        sesion = cursor.fetchone()
        if not sesion:
            return None

        s_id = sesion[0]
        usuario_ap = sesion[1]
        fecha_ap = sesion[2]
        monto_ini = sesion[3]
        usuario_ci = sesion[4]
        fecha_ci = sesion[5] or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        estado_caja = sesion[10]

        cursor.execute("""
            SELECT COALESCE(SUM(total), 0)
            FROM ventas 
            WHERE medio_pago = 'Efectivo' 
              AND COALESCE(estado, 'Completada') != 'Anulada'
              AND (caja_sesion_id = ? OR (caja_sesion_id IS NULL AND fecha >= ? AND fecha <= ?))
        """, (s_id, fecha_ap, fecha_ci))
        ventas_efectivo = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COALESCE(SUM(total), 0)
            FROM ventas 
            WHERE medio_pago != 'Efectivo' 
              AND COALESCE(estado, 'Completada') != 'Anulada'
              AND (caja_sesion_id = ? OR (caja_sesion_id IS NULL AND fecha >= ? AND fecha <= ?))
        """, (s_id, fecha_ap, fecha_ci))
        ventas_otros = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COALESCE(SUM(monto), 0)
            FROM caja_movimientos 
            WHERE sesion_id = ? AND tipo = 'Entrada'
        """, (s_id,))
        entradas = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COALESCE(SUM(monto), 0)
            FROM caja_movimientos 
            WHERE sesion_id = ? AND tipo = 'Salida'
        """, (s_id,))
        salidas = cursor.fetchone()[0]

        efectivo_esperado = monto_ini + ventas_efectivo + entradas - salidas

        cursor.execute("""
            SELECT id, tipo, monto, motivo, fecha_hora, usuario 
            FROM caja_movimientos 
            WHERE sesion_id = ? 
            ORDER BY id DESC
        """, (s_id,))
        movimientos = cursor.fetchall()

        return {
            "sesion_id": s_id,
            "usuario_apertura": usuario_ap,
            "fecha_apertura": fecha_ap,
            "monto_inicial": monto_ini,
            "usuario_cierre": usuario_ci,
            "fecha_cierre": sesion[5],
            "estado": estado_caja,
            "ventas_efectivo": ventas_efectivo,
            "ventas_otros": ventas_otros,
            "entradas": entradas,
            "salidas": salidas,
            "efectivo_esperado": efectivo_esperado,
            "monto_real": sesion[7] or 0.0,
            "diferencia": sesion[8] or 0.0,
            "observaciones": sesion[9] or "",
            "movimientos": movimientos
        }

def cerrar_caja(sesion_id, monto_real_efectivo, usuario_nombre, observaciones=""):
    resumen = get_resumen_caja(sesion_id)
    if not resumen:
        return False, "Sesión de caja no encontrada."

    esperado = resumen["efectivo_esperado"]
    diferencia = float(monto_real_efectivo) - esperado
    fecha_cierre = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE caja_sesiones 
            SET usuario_cierre = ?,
                fecha_cierre = ?,
                monto_esperado_efectivo = ?,
                monto_real_efectivo = ?,
                diferencia = ?,
                observaciones = ?,
                estado = 'Cerrada'
            WHERE id = ?
        """, (usuario_nombre, fecha_cierre, esperado, float(monto_real_efectivo), diferencia, observaciones, sesion_id))
        conn.commit()

    return True, f"Caja cerrada con éxito. Diferencia: ${int(diferencia):,}"

def get_historial_cajas(limite=20):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, usuario_apertura, fecha_apertura, monto_inicial, 
                   usuario_cierre, fecha_cierre, monto_esperado_efectivo, 
                   monto_real_efectivo, diferencia, estado, observaciones
            FROM caja_sesiones 
            ORDER BY id DESC 
            LIMIT ?
        """, (limite,))
        return cursor.fetchall()

# --- CONSULTAS DE VENTAS ---
def registrar_venta(items_carrito, total_bruto, medio_pago="Efectivo", cajero_nombre="Cajero", monto_pagado=0.0, vuelto=0.0):
    if not items_carrito:
        return False, "El carrito está vacío."
    
    fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    caja_activa = get_caja_abierta()
    caja_id = caja_activa[0] if caja_activa else None

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO ventas (fecha, total, medio_pago, cajero_nombre, monto_pagado, vuelto, estado, caja_sesion_id) 
            VALUES (?, ?, ?, ?, ?, ?, 'Completada', ?)
        """, (fecha_actual, total_bruto, medio_pago, cajero_nombre, monto_pagado, vuelto, caja_id))
        venta_id = cursor.lastrowid
        
        for item in items_carrito:
            prod_id, _, nombre, precio_costo, precio_venta, cant, subtotal = item
            
            cursor.execute("""
                INSERT INTO detalle_ventas (venta_id, producto_id, nombre_item, cantidad, precio_costo_unitario, precio_unitario, subtotal)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (venta_id, prod_id, nombre, cant, precio_costo, precio_venta, subtotal))
            
            if prod_id is not None:
                cursor.execute("UPDATE productos SET stock = stock - ? WHERE id = ?", (cant, prod_id))
        
        conn.commit()
    return True, "Venta registrada con éxito."

def eliminar_venta(venta_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM detalle_ventas WHERE venta_id = ?", (venta_id,))
        cursor.execute("DELETE FROM ventas WHERE id = ?", (venta_id,))
        conn.commit()

def anular_venta(venta_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT estado FROM ventas WHERE id = ?", (venta_id,))
        res = cursor.fetchone()
        if not res:
            return False, "Transacción no encontrada."
        
        estado_actual = res[0]
        if estado_actual == "Anulada":
            return False, "Esta venta ya fue anulada previamente."

        cursor.execute("SELECT producto_id, cantidad FROM detalle_ventas WHERE venta_id = ?", (venta_id,))
        items = cursor.fetchall()
        for prod_id, cant in items:
            if prod_id is not None:
                cursor.execute("UPDATE productos SET stock = stock + ? WHERE id = ?", (cant, prod_id))
        
        cursor.execute("UPDATE ventas SET estado = 'Anulada' WHERE id = ?", (venta_id,))
        conn.commit()
        return True, "Venta anulada con éxito y stock restituido."

def limpiar_historial_reportes():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM detalle_ventas")
        cursor.execute("DELETE FROM ventas")
        cursor.execute("DELETE FROM sqlite_sequence WHERE name IN ('ventas', 'detalle_ventas')")
        conn.commit()
    return True, "Historial de ventas y reportes reiniciado a 1."

def limpiar_toda_la_base_datos(limpiar_cajeros=False):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM detalle_ventas")
        cursor.execute("DELETE FROM ventas")
        cursor.execute("DELETE FROM caja_movimientos")
        cursor.execute("DELETE FROM caja_sesiones")
        cursor.execute("DELETE FROM historial_stock")
        cursor.execute("DELETE FROM productos")
        if limpiar_cajeros:
            cursor.execute("DELETE FROM cajeros")
        cursor.execute("DELETE FROM sqlite_sequence WHERE name IN ('ventas', 'detalle_ventas', 'caja_sesiones', 'caja_movimientos', 'historial_stock', 'productos')")
        conn.commit()
    return True, "Base de datos restablecida como nueva."

def get_venta_por_id(venta_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, fecha, total, medio_pago, cajero_nombre, 
                   COALESCE(monto_pagado, total), COALESCE(vuelto, 0), COALESCE(estado, 'Completada')
            FROM ventas 
            WHERE id = ?
        """, (venta_id,))
        return cursor.fetchone()

def get_detalle_venta(venta_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, producto_id, nombre_item, cantidad, precio_costo_unitario, precio_unitario, subtotal
            FROM detalle_ventas
            WHERE venta_id = ?
            ORDER BY id ASC
        """, (venta_id,))
        return cursor.fetchall()

def get_dashboard_metricas(periodo="todos"):
    where_ventas = " WHERE COALESCE(estado, 'Completada') != 'Anulada'"
    where_join = " WHERE COALESCE(v.estado, 'Completada') != 'Anulada'"

    if periodo == "hoy":
        where_ventas += " AND DATE(fecha) = DATE('now', 'localtime')"
        where_join += " AND DATE(v.fecha) = DATE('now', 'localtime')"
    elif periodo == "semana":
        where_ventas += " AND DATE(fecha) >= DATE('now', '-7 days', 'localtime')"
        where_join += " AND DATE(v.fecha) >= DATE('now', '-7 days', 'localtime')"
    elif periodo == "mes":
        where_ventas += " AND strftime('%Y-%m', fecha) = strftime('%Y-%m', 'now', 'localtime')"
        where_join += " AND strftime('%Y-%m', v.fecha) = strftime('%Y-%m', 'now', 'localtime')"

    where_listado = ""
    if periodo == "hoy":
        where_listado = " WHERE DATE(fecha) = DATE('now', 'localtime')"
    elif periodo == "semana":
        where_listado = " WHERE DATE(fecha) >= DATE('now', '-7 days', 'localtime')"
    elif periodo == "mes":
        where_listado = " WHERE strftime('%Y-%m', fecha) = strftime('%Y-%m', 'now', 'localtime')"

    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute(f"SELECT SUM(total), COUNT(id) FROM ventas{where_ventas}")
        resumen_ventas = cursor.fetchone()
        total_ventas = resumen_ventas[0] if (resumen_ventas and resumen_ventas[0]) else 0.0
        cant_ventas = resumen_ventas[1] if (resumen_ventas and resumen_ventas[1]) else 0

        query_costo = f"""
            SELECT SUM(dv.cantidad * dv.precio_costo_unitario)
            FROM detalle_ventas dv
            JOIN ventas v ON dv.venta_id = v.id
            {where_join}
        """
        cursor.execute(query_costo)
        resumen_costo = cursor.fetchone()
        costo_total = resumen_costo[0] if (resumen_costo and resumen_costo[0]) else 0.0

        ganancia_neta = total_ventas - costo_total

        cursor.execute(f"""
            SELECT id, fecha, total, medio_pago, cajero_nombre, COALESCE(estado, 'Completada')
            FROM ventas{where_listado} 
            ORDER BY id DESC LIMIT 50
        """)
        ventas_recientes = cursor.fetchall()

        return {
            "total_ventas": total_ventas,
            "cant_ventas": cant_ventas,
            "costo_total": costo_total,
            "ganancia_neta": ganancia_neta,
            "ventas_recientes": ventas_recientes
        }
