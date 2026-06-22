import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))      
DB = os.path.join(BASE_DIR, "graphics.db")                  

# --- CONEXION ---
def conexion():
    # Si no existe graphics.db, la crea
    conn = sqlite3.connect(DB)
    conn.execute("PRAGMA foreign_keys = ON")    #Activa las claves foraneas
    cur = conn.cursor()
    return conn, cur     #Devuelve conn(commit/close), cur(execute queries)

# --- TABLAS ---
def crear_tablas():
    conn, cur = conexion()
    try:
        # --- CREA LAS TABLAS SI NO EXISTE ---
        cur.execute("""
            CREATE TABLE IF NOT EXISTS esponja (
                id INTEGER PRIMARY KEY,
                largo INTEGER NOT NULL,
                ancho INTEGER NOT NULL,
                espesor INTEGER NOT NULL 
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS mediciones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                esponja_id INTEGER,
                largo INTEGER NOT NULL,
                ancho INTEGER NOT NULL,
                espesor INTEGER NOT NULL,
                fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(esponja_id) REFERENCES esponja(id)
                )
            """)

        conn.commit()
    except Exception as e:
        print(f'Error: {e}')
    finally:
        conn.close()

# --- INSERT ESPONJA CON VALOR NOMINAL (VALOR PREDETERMINADO) ---
def insert_esponja(id_, largo, ancho, espesor):
    conn, cur = conexion()
    try:
        cur.execute("""
            INSERT INTO esponja (id, largo, ancho, espesor)
            VALUES (?, ?, ?, ?)
        """, (id_, largo, ancho, espesor))
        conn.commit()
        print("Esponja insertada")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

# --- INSERT MEDICION (DATO INGRESADO POR EL USER) ---
def insert_medicion(esponja_id, largo, ancho, espesor):
    conn, cur = conexion()
    try:
        cur.execute("""
            INSERT INTO mediciones (esponja_id, largo, ancho, espesor) 
            VALUES (?,?,?,?)
        """, (esponja_id, largo, ancho, espesor))
        conn.commit()
        print("Medición insertada")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

# --- GET ESPONJA ---
def get_esponja(id_):
    conn, cur = conexion()
    try:
        cur.execute("""
            SELECT id, largo, ancho, espesor 
            FROM esponja 
            WHERE id = ?
        """, (id_,))

        print(f"Get exitoso: {id_}")
        return cur.fetchone()
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

# --- CREAR VISTA ---
def vistas():
    conn, cur = conexion()

    try:
        cur.execute("""
            CREATE VIEW IF NOT EXISTS vista_diferencias AS
                SELECT 
                    m.id,
                    m.esponja_id,
                    m.fecha,
                    (m.largo - e.largo) AS diff_largo,
                    (m.ancho - e.ancho) AS diff_ancho,
                    (m.espesor - e.espesor) AS diff_espesor
                FROM mediciones m
                JOIN esponja e ON m.esponja_id = e.id
        """
        )

        conn.commit()
        print("Vista creada!")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

def cargar_datos_esponja(esponja_id):
    conn, cur = conexion()
    try:
        cur.execute("""
            SELECT largo, ancho, espesor
            FROM esponja
            WHERE id = ?
        """, (esponja_id,))
        return cur.fetchone()    #RETURN [(largo, ancho, espesor)]
    except Exception as e:
        print(f"Error: {e}")
        return[]
    finally:
        conn.close()

def cargar_mediciones_reales(esponja_id):
    conn, cur = conexion()
    try:
        cur.execute("""
            SELECT id, largo, ancho, espesor, fecha
            FROM mediciones
            WHERE esponja_id = ?
            ORDER BY fecha ASC
        """, (esponja_id,))
        return cur.fetchall()    #RETURN [(id, largo, ancho, espesor)]
    finally:
        conn.close()