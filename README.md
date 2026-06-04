# Análisis del Mercado Laboral — Data Analyst

Proyecto end-to-end de análisis del mercado laboral para el rol de Data Analyst.
Extrae ofertas de trabajo reales mediante API y web scraping, las carga en una
base de datos SQLite, las transforma y analiza con Python, y exporta los resultados
para un dashboard en Power BI.

---

## Objetivo

Responder preguntas concretas sobre el mercado laboral para Data Analyst:

- ¿Qué skills son las más demandadas?
- ¿Qué tan accesible es el mercado para perfiles junior?
- ¿Cuánta experiencia se solicita?
- ¿Cómo varía el mercado por país?
- ¿Cuál es la brecha salarial entre países?

---

## Fuentes de datos

| Fuente | Método | Países | Registros |
|--------|--------|--------|-----------|
| Adzuna API | API REST gratuita | US, GB, AU, CA, BR, MX | 1626 |
| Computrabajo | Web scraping | AR | 62 |

**Total: 1688 ofertas recolectadas entre mayo y junio de 2026.**

---

## Stack tecnológico

| Categoría | Tecnología |
|-----------|------------|
| Lenguaje | Python 3.12 |
| Entorno | Poetry |
| Base de datos | SQLite |
| Análisis | pandas, re |
| Visualización | matplotlib, seaborn |
| Dashboard | Power BI |
| Extracción | requests, BeautifulSoup |
| Notebook | Jupyter |

---

## Estructura del proyecto
```
analisis-mercado-laboral/
│
├── data/
│   ├── jobs.db                  # Base de datos SQLite con datos crudos y limpios
│   └── processed/               # CSVs exportados para Power BI
│       ├── 1_skills_aggregated.csv
│       ├── 2_seniority_distribution.csv
│       ├── 3_experience_distribution.csv
│       ├── 4_skills_by_country.csv
│       ├── 5_salary_by_country.csv
│       └── 6_jobs_clean.csv
│
├── dashboard/
│   └── assets/                  # Gráficos exportados del notebook
│       ├── 3_1_skills_demandadas.png
│       ├── 3_2_seniority.png
│       ├── 3_3_experiencia.png
│       ├── 3_4_paises.png
│       └── 3_5_salario_paises.png
│
├── db/
│   └── schema.sql               # Schema de la base de datos
│
├── notebooks/
│   └── 01_eda.ipynb             # Exploración, limpieza y análisis
│
├── src/
│   ├── extract/
│   │   ├── adzuna.py            # Extracción via Adzuna API
│   │   └── computrabajo.py      # Scraping de Computrabajo
│   └── load/
│       └── loader.py            # Carga a SQLite
│
├── LICENSE
├── poetry.lock
├── .env.example                 # Variables de entorno requeridas
├── pyproject.toml               # Dependencias del proyecto (Poetry)
└── README.md
```

---

## Dasboard en Power BI
🚧 En construcción

---

## Instalación y uso

### 1. Clonar el repositorio

```bash
git clone https://github.com/JackyDye/analisis-mercado-laboral.git
cd analisis-mercado-laboral
```

### 2. Instalar dependencias

```bash
poetry install
```

### 3. Configurar credenciales

Ingresa tus credenciales de Adzuna en el `.env.example` y cambiasu nombre a `.env`

```bash
ADZUNA_APP_ID=tu_app_id_aqui
ADZUNA_APP_KEY=tu_app_key_aqui
```

Registrate gratis en [developer.adzuna.com](https://developer.adzuna.com/signup).

### 4. Correr el pipeline

```bash
poetry run python -m src.load.loader
```

Esto extrae las ofertas, las carga en `data/jobs.db` y está listo para el análisis.

### 5. Abrir el notebook

```bash
poetry run jupyter notebook notebooks/01_eda.ipynb
```

---

## Limitaciones conocidas

- La API gratuita de Adzuna trunca las descripciones a 500 caracteres, lo que
  subestima la detección de skills. Los resultados deben interpretarse como
  tendencias orientativas, no como estadísticas representativas.
- Computrabajo no devuelve descripción en el scraping, sus 62 registros
  quedan fuera del análisis NLP.
- La modalidad laboral tiene 98% de nulos, no se incluyó en el análisis.
- Los salarios están convertidos a USD al tipo de cambio del momento de
  ejecución del notebook. Una nueva ejecución puede generar valores distintos si los tipos de cambio actuales son otros.

---

## Insights

- **SQL** es la skill más demandada en todos los mercados
- **Solo el 10%** de las ofertas son explícitamente junior
- La experiencia más solicitada es entre **1 y 3 años**
- **US** lidera en salarios con una mediana de **$7.899 USD mensuales**
- La brecha salarial entre US y Argentina es de casi **10 veces**

---

*Datos recolectados: mayo - junio 2026 | Fuentes: Adzuna API, Computrabajo*