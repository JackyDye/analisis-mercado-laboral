-- =============================================================================
-- schema.sql
-- Define la estructura de la base de datos del proyecto.
-- Motor: SQLite
-- =============================================================================

CREATE TABLE IF NOT EXISTS jobs (

    -- Identificador único autogenerado por SQLite
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Campos comunes a ambas fuentes
    title       TEXT,
    company     TEXT,
    location    TEXT,
    country     TEXT,
    modality    TEXT,

    -- Salario en texto tal como viene de la fuente
    -- Adzuna puede traer valores numéricos pero Computrabajo trae texto
    -- La normalización se hace en la fase de transformación con pandas
    salary_raw  TEXT,

    -- Descripción completa de la oferta (disponible en Adzuna, no en Computrabajo)
    description TEXT,

    -- Fecha de publicación tal como viene de la fuente
    -- Adzuna: formato ISO "2026-05-25T10:00:00Z"
    -- Computrabajo: texto "Hace 2 horas"
    date_raw    TEXT,

    -- Identificador de la fuente: "adzuna" o "computrabajo"
    source      TEXT,

    -- Fecha y hora en que el registro fue insertado en la base de datos
    created_at  TEXT DEFAULT (datetime('now'))

);