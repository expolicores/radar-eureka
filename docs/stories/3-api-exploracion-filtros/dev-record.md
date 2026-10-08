## Dev Agent Record — Dev-Rápido

### Debug Log

| # | Tipo | Descripción | Resolución |
|---|------|-------------|------------|
| 1 | Tipado | SQLAlchemy 2.1 tipa `select(Model)` como `Select[Model]` y el orden como expresión única | Anotaciones `Select[PurchaseRecord]` y `dict[PurchaseSort, ColumnElement[Any]]` |
| 2 | Test | El orden de departamentos de PostgreSQL sigue la intercalación del idioma («Córdoba» antes de «Cundinamarca»), no el orden por código de Python | La prueba compara contra un orden sin tildes |
| 3 | Herramienta | Una sustitución con regex sobre el test de integración rompió paréntesis | Archivo reescrito completo |

### Completion Notes

- ⚡ Dev-Rápido: lado de lectura de `ingestion` (`PurchaseQueryService`: búsqueda sin tildes en entidad, proveedor, NIT, objeto y referencia; filtros de fuente, modalidad, departamento, rango de valor y fechas; orden; paginación; ficha; opciones de filtro; fecha de corte) y nuevo módulo `exploration` (estado del análisis con precedencia, vistas tipadas *tool-ready*, API `GET /api/v1/purchases`, `/filters`, `/{id}`). Errores HTTP y de validación de toda la API en *problem details* en español (400 «Solicitud inválida» con el parámetro; 404). Contratos import-linter: capas `entrypoints → exploration → ingestion → shared` y «desde otro módulo solo `ingestion.services`».
- ✅ Verificado con PostgreSQL embebido: ruff, mypy, 4 contratos, `alembic check`; **102 tests pasan, 1 omitido** (autenticación `trust`). Prueba manual contra la base de la demo: búsqueda «alcaldia municipal de san rafael» encuentra `CO1.PCCNTR.0000142`; 1.280 compras con 5 estados del análisis (1.124 pendientes de comparación, 112 sin precio, 27 IVA indeterminado, 13 excluidas, 4 en revisión).
- 🧪 Cobertura QA: 9/9.
- ⚠️ No verificado aquí: CI (sin remoto).

### File List

| Acción | Archivo | Descripción |
|--------|---------|-------------|
| Creado | `backend/src/public_procurement/ingestion/domain/search.py` | Criterios, orden, rangos de valor, páginas y opciones |
| Modificado | `backend/src/public_procurement/ingestion/repositories.py` | `SqlPurchaseQueries` (búsqueda, ficha, opciones, fecha de corte) |
| Modificado | `backend/src/public_procurement/ingestion/services.py` | `PurchaseQueryService`, reexportes públicos (`__all__`) |
| Creado | `backend/src/public_procurement/exploration/{__init__.py,README.md,services.py,api.py}` | Módulo de exploración |
| Creado | `backend/src/public_procurement/exploration/domain/{__init__,analysis}.py` | Estado del análisis |
| Modificado | `backend/src/public_procurement/entrypoints/api/{app,errors}.py` | Cableado de sesiones y exploración; 400/404 en *problem details* |
| Modificado | `backend/pyproject.toml` | Contratos import-linter |
| Modificado | `backend/tests/builders.py` | `ItemStateBuilder` |
| Modificado | `backend/tests/integration/{conftest,test_ingestion_repository,test_migrations}.py` | Fixtures compartidas `migrated_engine`, `seeded_engine`, `load_seed` |
| Creado | `backend/tests/unit/exploration/{__init__,test_analysis,test_purchases_api}.py` | Estado del análisis y API |
| Creado | `backend/tests/integration/test_exploration_queries.py` | Búsqueda y filtros contra PostgreSQL |

### Revisión del diff

Herramienta: propia + revisor de estándares independiente — el revisor descartó por dudosos un `PurchaseSummaryView` armado a mano dentro de un doble de prueba y un import de `ingestion.domain` en un test de integración (las fronteras aplican a módulos).

| # | Categoría | Hallazgo | Archivo | Resultado |
|---|-----------|----------|---------|-----------|
| 1 | limpieza | La ficha ejecutaba las tres consultas de opciones de filtro solo para obtener la fecha de corte | `backend/src/public_procurement/exploration/services.py` | ✅ Aplicado (`latest_cutoff()`) |
| 2 | estandares | Tests del estado del análisis con datos armados a mano, sin Test Data Builder | `backend/tests/unit/exploration/test_analysis.py` | ✅ Aplicado (`ItemStateBuilder`) |
| 3 | limpieza | `assert` en los *handlers* de error del código productivo | `backend/src/public_procurement/entrypoints/api/errors.py` | ✅ Aplicado (comprobación explícita con respaldo al *handler* de 500) |

Revisar primero: `backend/src/public_procurement/exploration/api.py` (contrato de API expuesto) · `backend/src/public_procurement/entrypoints/api/errors.py` (errores de toda la API)

### Métricas Dev-Rápido

- Tiempo sesión IA: 10 min
- Tareas manuales DoD: 0 min
- Tiempo total: 10 min
