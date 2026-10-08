# Módulo `exploration`

Lectura de las compras para el Analista: listado con búsqueda, filtros, orden y paginación; ficha de la compra; opciones de filtro y fecha de corte de los datos. **No tiene tablas propias**: lee las compras por `ingestion.services` (nunca sus tablas).

## Responsabilidades

- **Estado del análisis** de cada compra (`domain/analysis.py`), con precedencia: excluido → revisión de calidad → sin precio unitario → IVA indeterminado → pendiente de comparación. El slice de señales agrega «con señal» y «comparado sin señal».
- **Vistas tipadas** (`services.py`) sin dependencias HTTP, listas para exponerse también como herramientas de agentes.
- **API** (`api.py`): `GET /api/v1/purchases`, `GET /api/v1/purchases/filters`, `GET /api/v1/purchases/{id}`.

## Capas

| Archivo | Rol |
| ------- | --- |
| `domain/analysis.py` | Regla pura del estado del análisis |
| `services.py` | `ExplorationService`: compone las vistas a partir de `ingestion.services` |
| `api.py` | Router FastAPI y esquemas de respuesta; solo entrada y salida |
