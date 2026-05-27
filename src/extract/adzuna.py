"""
adzuna.py

Extractor de ofertas de trabajo de Data Analyst via Adzuna API REST.

Adzuna es un motor de búsqueda de empleo con cobertura en múltiples países.
Ofrece una API gratuita con hasta 250 requests diarios.

Flujo de este módulo:
    1. Carga las credenciales desde el archivo .env
    2. Para cada país en COUNTRIES, consulta la API página por página
    3. Acumula los resultados en una lista de diccionarios (JSON crudo)
    4. Devuelve esa lista para ser procesada por el módulo de carga (loader.py)

Documentación oficial de la API: https://developer.adzuna.com/docs/search
Registro gratuito: https://developer.adzuna.com/signup
"""

import requests  # Para hacer llamadas HTTP a la API
import os        # Para leer variables de entorno del sistema operativo
from dotenv import load_dotenv  # Para cargar el archivo .env con las credenciales
import time     # Para agregar pausas entre requests

# ---------------------------------------------------------------------------
# Configuración de credenciales
# Las credenciales se leen desde el archivo .env (nunca se hardcodean en el código).
# Estructura del .env:
#   ADZUNA_APP_ID=tu_app_id
#   ADZUNA_APP_KEY=tu_app_key
# ---------------------------------------------------------------------------
load_dotenv()

APP_ID = os.getenv("ADZUNA_APP_ID")
APP_KEY = os.getenv("ADZUNA_APP_KEY")


# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------

# URL base de todos los endpoints de la API de Adzuna
# Estructura completa: {BASE_URL}/{country}/search/{page}
BASE_URL = "https://api.adzuna.com/v1/api/jobs"

# Países a consultar con sus códigos según la API de Adzuna.
# Argentina (ar) no tiene cobertura en Adzuna.
# Para Argentina se usa Computrabajo, Indeed y Bumeran (ver src/extract/).
COUNTRIES = ["us", "gb", "au", "ca", "br", "mx"]


# ---------------------------------------------------------------------------
# Funciones
# ---------------------------------------------------------------------------

def fetch_jobs(country, what="data analyst", results_per_page=50, max_pages=5):
    """
    Consulta la API de Adzuna y devuelve todas las ofertas encontradas
    para un país dado, recorriendo múltiples páginas de resultados.

    La API de Adzuna devuelve los resultados paginados. Esta función
    recorre las páginas de 1 a max_pages y acumula todos los resultados
    en una sola lista.

    Argumentos:
        country (str): código de país según Adzuna. Ejemplos: "us", "gb", "au".
        what (str): término de búsqueda. Default: "data analyst".
        results_per_page (int): cantidad de resultados por página. Máximo: 50.
        max_pages (int): cantidad de páginas a consultar. Default: 5.
                         Con 50 resultados por página y 5 páginas = 250 ofertas por país.

    Returns:
        list: lista de diccionarios con los datos crudos devueltos por la API.
              Cada diccionario representa una oferta de trabajo.
              Los campos varían según disponibilidad, pero típicamente incluyen:
              title, company, location, description, salary_min, salary_max, created.

    Ejemplo de uso:
        jobs = fetch_jobs("us")
        jobs = fetch_jobs("gb", what="data engineer", max_pages=3)
    """
    jobs = []

    for page in range(1, max_pages + 1):
        # Construye la URL para el país y página actuales
        # Ejemplo: https://api.adzuna.com/v1/api/jobs/us/search/1
        url = f"{BASE_URL}/{country}/search/{page}"

        # Parámetros que se envían la URL
        # Ejemplo final: ...?app_id=xxx&app_key=yyy&what=data+analyst&results_per_page=50
        params = {
            "app_id": APP_ID,
            "app_key": APP_KEY,
            "what": what,
            "results_per_page": results_per_page,
            "content-type": "application/json"
        }

        response = requests.get(url, params=params)

        if response.status_code == 200:
            # Convierte la respuesta JSON en un diccionario de Python
            data = response.json()

            # Las ofertas viven en la clave "results" del JSON de respuesta
            for job in data["results"]:
                job["country"] = country
            jobs.extend(data["results"])
            print(f"Página {page} de {country}: {len(data['results'])} ofertas")
        else:
            # Si hay error, imprime el código HTTP y detiene la paginación
            # Códigos comunes: 401 (credenciales inválidas), 404 (país sin cobertura)
            print(f"Error en {country}, página {page}: {response.status_code}")
            break
        
        # Pausa de 2 segundos entre páginas para no sobrecargar el servidor.
        time.sleep(2)

    return jobs


# ---------------------------------------------------------------------------
# Ejecución directa (test rápido)
# Se ejecuta solo cuando se corre este archivo directamente: poetry run python src/extract/adzuna.py
# No se ejecuta cuando otro módulo importa este archivo.
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    for country in COUNTRIES:
        jobs = fetch_jobs(country)
        print(f"Total {country}: {len(jobs)} ofertas")