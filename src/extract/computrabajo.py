"""
computrabajo.py

Scraper de ofertas de trabajo de Data Analyst en Computrabajo Argentina.

Computrabajo es uno de los principales portales de empleo en Argentina.
A diferencia de Adzuna, no ofrece una API pública, por lo que los datos
se obtienen mediante scraping del HTML público de la página de resultados.

¿Por qué scraping y no API?
    Adzuna no tiene cobertura para Argentina. Computrabajo permite acceder
    a sus ofertas públicas sin necesidad de login, lo que hace posible
    el scraping liviano con requests + BeautifulSoup.

Flujo de este módulo:
    1. Realiza un GET a cada página de resultados simulando un navegador real
    2. Parsea el HTML con BeautifulSoup
    3. Localiza cada oferta (elemento <article class="box_offer">)
    4. Extrae los campos relevantes de cada tarjeta
    5. Devuelve una lista de diccionarios lista para ser cargada a la base de datos

Fuente: https://www.computrabajo.com.ar/trabajo-de-data-analyst
"""

import requests                 # Para hacer las peticiones HTTP a Computrabajo
from bs4 import BeautifulSoup   # Para parsear y navegar el HTML de la respuesta
import time                     # Para agregar pausas entre requests


# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------

# URL base de búsqueda para el término "data analyst" en Argentina.
# La paginación se maneja agregando el parámetro ?p={numero_de_pagina}
# Ejemplo página 2: https://www.computrabajo.com.ar/trabajo-de-data-analyst?p=2
BASE_URL = "https://www.computrabajo.com.ar/trabajo-de-data-analyst"

# Dominio base para contruir URLs absolutas y extraer la descripción completa de la oferta
DOMAIN = "https://www.computrabajo.com.ar" 

# Headers para simular un usuario real.
# Sin esto, Computrabajo puede identificar el request como automático y bloquearlo.
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}


# ---------------------------------------------------------------------------
# Funciones
# ---------------------------------------------------------------------------

def scrape_jobs(max_pages=5):
    """
    Recorre las páginas de resultados de Computrabajo y recolecta todas las ofertas.

    Argumentos:
        max_pages (int): cantidad máxima de páginas a scrapear. Default: 5.

    Returns:
        list: lista de diccionarios con los datos extraídos de cada oferta.
              Cada diccionario es generado por parse_offer().

    Ejemplo de uso:
        jobs = scrape_jobs()
        jobs = scrape_jobs(max_pages=3)
    """
    jobs = []

    for page in range(1, max_pages + 1):
        # La página 1 no lleva parámetro de paginación en la URL
        if page == 1:
            url = BASE_URL
        else:
            url = f"{BASE_URL}?p={page}"

        response = requests.get(url, headers=HEADERS)

        if response.status_code != 200:
            print(f"Error en página {page}: {response.status_code}")
            break

        # Convierte el HTML crudo en un objeto navegable de BeautifulSoup
        soup = BeautifulSoup(response.text, "html.parser")

        # Cada oferta en el HTML es un <article class="box_offer">
        # find_all devuelve una lista con todas las ofertas que encuentre en la página
        offers = soup.find_all("article", class_="box_offer")

        if len(offers) == 0:
            print("No se encontraron más ofertas. Deteniendo scraper.")
            break

        print(f"Página {page}: {len(offers)} ofertas encontradas")

        for offer in offers:
            jobs.append(parse_offer(offer))

        # Pausa de 2 segundos entre páginas para no sobrecargar el servidor.
        time.sleep(2)

    return jobs

def fetch_description(url):
    """
    Intento de extracción de descripción desde la página individual.
    Deshabilitado: Computrabajo detecta requests automáticos y no devuelve
    el contenido real de la oferta. Se requeriría automatización de navegador
    (Playwright/Selenium) para obtener este dato, lo cual está fuera del
    alcance de este proyecto.

    Returns:
        None
    """
    return None

def parse_offer(article):
    """
    Extrae los campos de una oferta a partir de su elemento HTML.

    Cada oferta en Computrabajo tiene la siguiente estructura HTML:
        <article class="box_offer">
            <h2 class="fs18 fwB prB ...">
            <a class="js-o-link fc_base"       → título del puesto y URL
            <p class="dFlex vm_fx fs16 ...">
            <a class="fc_base t_ellipsis">     → empresa
            <p class="fs16 fc_base mt5"...>
            <span class="mr10">                → ubicación
            <div class="fs13 mt15"...>
            <span class="dIB mr10">            → salario o modalidad (no siempre ambos)
            <p class="fs13 fc_aux mt15">       → fecha de publicación

    Para la descripción se hace un segundo request a la página individual
    de cada oferta, usando la URL extraída del <a> dentro del <h2>.

    Para cada campo se usa el patrón:
        elemento = article.find(tag, class_=clase)
        valor = elemento.text.strip() if elemento else None

    El "if elemento else None" evita errores cuando un campo no está presente
    en la oferta (no todas las ofertas tienen salario, por ejemplo).

    Args:
        article: elemento BeautifulSoup correspondiente a un <article class="box_offer">

    Returns:
        dict: diccionario con los campos extraídos de la oferta.
    """
    # Título del puesto
    # Está dentro de un <h2 class="fs18 fwB prB">, y la URL de la oferta individual está en el <a> dentro del <h2>
    title_tag = article.find("h2", class_="fs18 fwB prB")
    title = None
    offer_url = None
    # la url de la oferta individual está en el href del <a> dentro del <h2>
    if title_tag:
        a_tag = title_tag.find("a")
        if a_tag:
            title = a_tag.text.strip()
            offer_url = a_tag.get("href")

    # Descripción completa desde la página individual
    description = fetch_description(offer_url) if offer_url else None

    # Nombre de la empresa
    # Está en un <a class="fc_base t_ellipsis"> dentro del párrafo de empresa
    company = article.find("a", class_="fc_base t_ellipsis")
    company = company.text.strip() if company else None

    # Ubicación (ciudad, provincia)
    # Está en un <span class="mr10"> dentro del párrafo de ubicación
    location = article.find("p", class_="fs16 fc_base mt5")
    location = location.find("span", class_="mr10").text.strip() if location else None

    # Salario y modalidad están en el mismo <div>, en dos <span> consecutivos
    # No todas las ofertas publican salario, por eso se inicializan en None
    salary = None
    modality = None
    details = article.find("div", class_="fs13 mt15")
    if details:
        spans = details.find_all("span", class_="dIB mr10")
        for span in spans:
            text = span.text.strip()
            # Si el texto contiene $ o números, es salario
            # Si no, es modalidad
            if "$" in text or any(char.isdigit() for char in text):
                salary = text
            else:
                modality = text

    # Fecha de publicación (ej: "Hace 2 horas", "Hace 3 días")
    date = article.find("p", class_="fs13 fc_aux mt15")
    date = date.text.strip() if date else None

    return {
        "title": title,
        "company": company,
        "location": location,
        "salary": salary,
        "modality": modality,
        "date": date,
        "description": description,
        "source": "computrabajo",  # Identifica de qué fuente viene el dato
        "country": "ar"            # País fijo para esta fuente
    }


# ---------------------------------------------------------------------------
# Ejecución directa (test rápido)
# Se ejecuta solo cuando se corre este archivo directamente: poetry run python src/extract/computrabajo.py
# No se ejecuta cuando otro módulo importa este archivo.
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    jobs = scrape_jobs()
    print(f"\nTotal: {len(jobs)} ofertas")
    if jobs:
        print(jobs[0])