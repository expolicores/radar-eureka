## Dev Agent Record — Dev-Rápido

### Debug Log

| # | Tipo | Descripción | Resolución |
|---|------|-------------|------------|
| 1 | Entorno | `pgserver.psql()` falla cuando la ruta del proyecto tiene espacios («COMPRAS PUBLICAS») | `scripts/local_postgres.py` crea las bases con psycopg y `sql.Identifier` |
| 2 | Entorno | PostgreSQL embebido 16.2 sin extensiones contrib (`pg_trgm`, `unaccent`) y con autenticación `trust` | Nada de este slice usa contrib; el test de contraseña incorrecta se omite con motivo cuando el servidor acepta cualquier clave (en CI con PostgreSQL 16 sí corre) |
| 3 | Bug R0 | `alembic/env.py` llamaba `fileConfig` con `disable_existing_loggers=True`: al migrar dentro del mismo proceso (tests de integración) desactivaba los loggers de la aplicación y fallaban 6 tests de logs | `disable_existing_loggers=False` |
| 4 | Test R0 | `test_migrations.py` esperaba que `0001_initial` fuera la última revisión | Compara contra la cabeza real de Alembic (`ScriptDirectory`) |
| 5 | Riesgo de datos | Los tests de integración hacen `downgrade base` y borrarían la base de la demo | Base aparte `public_procurement_test`; los tests reciben su URL por `DATABASE_URL` en el entorno |
| 6 | Seed | Índice fuera de rango en proveedores TVEC de los comparables | `(index + 1) % 4` |
| 7 | Tipado | `Protocol` `UnitOfWork` incompatible con `SqlUnitOfWork` (atributo mutable y `__exit__`) | `purchases` como propiedad de solo lectura, `__enter__ -> Self` y firma completa de `__exit__` |

### Completion Notes

- ⚡ Dev-Rápido: módulo `ingestion` (primer módulo de dominio). Dominio puro con compras SECOP II/TVEC, ítems, atributos de TV y estados explícitos (`UnitPriceStatus`, `VatBasis`), clasificación por reglas del sustantivo principal (incluido / accesorio / servicio / dudoso), privacidad de personas naturales. Puerto `PublicDataSource` con adaptador **seed** determinístico (~1.280 compras ficticias 2023–2026, incluida `CO1.PCCNTR.0000142` del mockup y sus 14 comparables), repositorio SQLAlchemy con upsert idempotente y bitácora `ingestion_run` por fuente, migración `0002_ingestion_schema` (esquema `ingestion`, restricciones de identidad y de privacidad), CLI Typer `load-seed`, script de PostgreSQL embebido y README del módulo.
- ✅ Verificado localmente con PostgreSQL 16.2 embebido: ruff, formato, mypy (strict en dominio y servicios), import-linter (3 contratos, incluido «el dominio no tiene ORM, web ni I/O»), `alembic check` sin diferencias entre modelos y migración, **67 tests pasan y 1 se omite** (incluidos por primera vez los de integración de R0). Carga real: 348 contratos SECOP II + 932 órdenes TVEC; la segunda carga no duplica (0 nuevas).
- 🧪 Cobertura QA: 6/6 (QA-01…QA-06 con test unitario y de integración).
- 📝 Decisiones autónomas registradas en `refinamiento.md` (identidad con nombres de campo de la fuente, clasificación por sustantivo principal, Typer para la CLI, grupo `local-db`, `source_url` vacío en el seed).
- ⚠️ No verificado aquí: CI de GitHub Actions (sin remoto) y PostgreSQL 16 con autenticación por contraseña.

### File List

| Acción | Archivo | Descripción |
|--------|---------|-------------|
| Creado | `backend/src/public_procurement/shared/persistence.py` | `Base` declarativa con convención de nombres y fábrica de sesiones |
| Creado | `backend/src/public_procurement/ingestion/{__init__.py,README.md}` | Módulo y documentación |
| Creado | `backend/src/public_procurement/ingestion/domain/{__init__,purchase,classification}.py` | Dominio puro |
| Creado | `backend/src/public_procurement/ingestion/ports.py` | Puerto `PublicDataSource` |
| Creado | `backend/src/public_procurement/ingestion/adapters/{__init__,seed,seed_data}.py` | Fuente seed ficticia |
| Creado | `backend/src/public_procurement/ingestion/{repositories,unit_of_work,services}.py` | Persistencia, transacción y servicio |
| Creado | `backend/src/public_procurement/entrypoints/cli/{__init__,__main__}.py` | CLI `load-seed` |
| Creado | `backend/scripts/local_postgres.py` | PostgreSQL embebido de desarrollo |
| Creado | `backend/alembic/versions/0002_ingestion_schema.py` | Esquema `ingestion` |
| Modificado | `backend/alembic/env.py` | Metadata de los módulos, `include_schemas`, loggers sin desactivar |
| Modificado | `backend/pyproject.toml`, `backend/uv.lock` | Typer, grupo `local-db`, contratos import-linter, confusables permitidos |
| Modificado | `.gitignore`, `README.md` | `backend/.local/`; arranque sin Docker y datos de la demo |
| Modificado | `backend/tests/{builders,doubles}.py` | Builders de fuente; repositorio, unidad de trabajo y fuente en memoria |
| Creado | `backend/tests/unit/ingestion/*` (4 archivos de test) | Clasificación, construcción, seed, servicio |
| Creado | `backend/tests/integration/test_ingestion_repository.py` | Carga real, idempotencia, ida y vuelta, privacidad en el esquema |
| Modificado | `backend/tests/integration/{test_migrations,test_healthz_database}.py` | Cabeza real de Alembic; omisión con autenticación `trust` |

### Revisión del diff

Herramienta: propia + revisor de estándares independiente — el revisor descartó por dudosos: imports de la CLI a `adapters`/`domain` (raíz de composición), `ValueError` por identificador faltante, f-string con nombre de esquema constante, upsert de compras (fuera de ADR-012) y un comentario con «sobreprecio» (se cambió igual a «desviación alta»).

| # | Categoría | Hallazgo | Archivo | Resultado |
|---|-----------|----------|---------|-----------|
| 1 | estandares | Montos calculados con `float` en el generador seed (factores de año, dispersión, división del IVA, redondeo) | `backend/src/public_procurement/ingestion/adapters/seed_data.py` | ✅ Aplicado (`Decimal` y puntos básicos enteros; redondeo entero) |
| 2 | estandares | Dos tests verificaban varias conductas a la vez | `backend/tests/unit/ingestion/test_seed_data.py` | ✅ Aplicado (separados en 4 tests) |
| 3 | bug | `fileConfig` de Alembic desactivaba los loggers de la aplicación | `backend/alembic/env.py` | ✅ Aplicado |
| 4 | limpieza | Mensajes de la CLI con tildes salen mal codificados en consolas Windows sin UTF-8 | `backend/src/public_procurement/entrypoints/cli/__main__.py` | — No aplicado: depende de la consola (`PYTHONIOENCODING=utf-8` lo resuelve); no afecta datos |

Revisar primero: `backend/alembic/versions/0002_ingestion_schema.py` (migración de esquema) · `backend/src/public_procurement/ingestion/repositories.py` (persistencia y upsert)

### Métricas Dev-Rápido

- Tiempo sesión IA: 14 min
- Tareas manuales DoD: 0 min
- Tiempo total: 14 min
