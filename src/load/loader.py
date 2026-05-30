"""
loader.py

Módulo responsable de crear la base de datos y cargar las ofertas extraídas por los módulos de extracción (adzuna.py y computrabajo.py).

Flujo de este módulo:
    1. Crea la base de datos SQLite si no existe
    2. Ejecuta el schema.sql para crear las tablas
    3. Recibe listas de ofertas y las inserta en la tabla "jobs"
    4. Evita duplicados comparando título + empresa + país

Base de datos: data/jobs.db
Schema: db/schema.sql
"""

from sqlalchemy import create_engine, text
from pathlib import Path

# ---------------------------------------------------------------------------
# Rutas del proyecto
# ---------------------------------------------------------------------------

# Directorio raíz del proyecto (dos niveles arriba de src/load/)
ROOT_DIR = Path(__file__).resolve().parent.parent.parent

# Ruta a la base de datos SQLite
DB_PATH = ROOT_DIR / "data" / "jobs.db"

# Ruta al archivo con el schema SQL
SCHEMA_PATH = ROOT_DIR / "db" / "schema.sql"

# ---------------------------------------------------------------------------
# Funciones
# ---------------------------------------------------------------------------

def get_engine():
    """
    Crea y devuelve el motor de conexión a la base de datos SQLite.

    El motor es el objeto principal de SQLAlchemy, gestiona la conexión 
    y permite ejecutar queries desde Python.

    Returns:
        engine: objeto SQLAlchemy Engine conectado a data/jobs.db
    """
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)  # Crea la carpeta data/ si no existe
    return create_engine(f"sqlite:///{DB_PATH}") # Crea la conexión a SQLite

def init_db():
    """
    Crea la base de datos y ejecuta schema.sql para crear las tablas.

    Si la base de datos ya existe, no la sobreescribe.
    CREATE TABLE IF NOT EXISTS en el schema.sql asegura que no se pierdan datos existentes.

    Se llama una sola vez al inicio del pipeline.
    """
    engine = get_engine()
    schema = SCHEMA_PATH.read_text(encoding="utf-8") # Lee el contenido de schema.sql como string

    with engine.connect() as conn: # Abre una conexión a la base de datos
        conn.execute(text(schema)) # Ejecuta el SQL del schema para crear las tablas
        conn.commit() # Confirma los cambios

    print(f"Base de datos inicializada en: {DB_PATH}")

def insert_jobs(jobs, source):
    """
    Inserta una lista de ofertas en la tabla jobs evitando duplicados.

    Para evitar duplicados compara título + empresa + país. Si una oferta
    con esa combinación ya existe en la base de datos, se omite.
    Esto permite correr el pipeline múltiples veces sin generar registros repetidos.

    Argumentos:
        jobs (list): lista de diccionarios con los datos de las ofertas. Generada por fetch_jobs() o scrape_jobs() en el módulo de extract.
        source (str): identificador de la fuente. Valores: "adzuna", "computrabajo".
    """
    engine = get_engine()

    # Contadores para el reporte final
    inserted = 0  # Ofertas nuevas insertadas
    skipped = 0   # Ofertas omitidas por ser duplicados

    with engine.connect() as conn:
        for job in jobs:

            # ------------------------------------------------------------------
            # Control de duplicados
            # Antes de insertar, verificamos si ya existe una oferta con el mismo
            # título, empresa y país. Si existe, la omitimos.
            # Usamos :title, :company, :country como parámetros nombrados
            # ------------------------------------------------------------------
            # Extraer company como texto independientemente de la fuente
            if source == "adzuna":
                company = job.get("company", {}).get("display_name")
                country = job.get("country")
            else:
                company = job.get("company")
                country = job.get("country")

            existing = conn.execute(text("""
                SELECT id FROM jobs
                WHERE title = :title
                AND company = :company
                AND country = :country
            """), {
                "title": job.get("title"),
                "company": company,
                "country": country
            }).fetchone()

            if existing:
                skipped += 1
                continue  # Saltamos al siguiente job sin insertar

            # ------------------------------------------------------------------
            # Inserción según la fuente
            # Cada fuente tiene una estructura de datos distinta, por eso
            # el mapeo de campos se hace por separado para cada una.
            # ------------------------------------------------------------------

            if source == "adzuna":
                # Adzuna devuelve company y location como diccionarios anidados:
                # {"company": {"display_name": "Google"}, "location": {"display_name": "London"}}
                # Por eso usamos .get("display_name") para extraer el texto.
                conn.execute(text("""
                    INSERT INTO jobs (title, company, location, country, modality,
                                     salary_raw, description, date_raw, source)
                    VALUES (:title, :company, :location, :country, :modality,
                            :salary_raw, :description, :date_raw, :source)
                """), {
                    "title": job.get("title"),
                    "company": job.get("company", {}).get("display_name"),
                    "location": job.get("location", {}).get("display_name"),
                    "country": job.get("country"),
                    "modality": None,  # Adzuna no provee este campo
                    # salary_min es numérico en Adzuna, lo convertimos a texto
                    # para unificarlo con el formato de Computrabajo
                    "salary_raw": str(job.get("salary_min")) if job.get("salary_min") else None,
                    "description": job.get("description"),
                    "date_raw": job.get("created"),  # Formato ISO: "2026-05-25T10:00:00Z"
                    "source": "adzuna"
                })

            elif source == "computrabajo":
                # Computrabajo devuelve todos los campos como strings directamente,
                # sin estructuras anidadas. El mapeo es más directo.
                conn.execute(text("""
                    INSERT INTO jobs (title, company, location, country, modality,
                                     salary_raw, description, date_raw, source)
                    VALUES (:title, :company, :location, :country, :modality,
                            :salary_raw, :description, :date_raw, :source)
                """), {
                    "title": job.get("title"),
                    "company": job.get("company"),
                    "location": job.get("location"),
                    "country": job.get("country"),
                    "modality": job.get("modality"),
                    "salary_raw": job.get("salary"),
                    "description": job.get("description"),
                    "date_raw": job.get("date"),  # Formato relativo: "Hace 2 horas"
                    "source": "computrabajo"
                })

            inserted += 1

        # Confirma todos los inserts de esta sesión
        conn.commit()

    print(f"[{source}] Insertadas: {inserted} | Omitidas (duplicados): {skipped}")

# ---------------------------------------------------------------------------
# Ejecución directa (test rápido)
# Inicializa la base de datos y corre el pipeline completo:
# Adzuna (todos los países) + Computrabajo (Argentina)
# Se ejecuta solo cuando se corre este archivo directamente: poetry run python src/load/loader.py
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    from src.extract.adzuna import fetch_jobs, COUNTRIES
    from src.extract.computrabajo import scrape_jobs

    # Inicializar la base de datos y crear las tablas
    init_db()

    # Extraer e insertar ofertas de Adzuna para cada país
    for country in COUNTRIES:
        print(f"\nExtrayendo {country} desde Adzuna...")
        jobs = fetch_jobs(country)
        insert_jobs(jobs, source="adzuna")

    # Extraer e insertar ofertas de Computrabajo para Argentina
    print("\nExtrayendo Argentina desde Computrabajo...")
    jobs = scrape_jobs()
    insert_jobs(jobs, source="computrabajo")

    print("\nPipeline completado.")