# Seguimiento Compras Públicas - Estándares de Código

## Información General

### Propósito del Documento

Este documento define los estándares de código obligatorios y recomendados para el desarrollo en Seguimiento Compras Públicas. Garantizan consistencia, legibilidad y mantenibilidad del código.

- **Audiencia**: Desarrolladores, Code Reviewers, agentes de desarrollo del Método Ceiba
- **Última Actualización**: 2026-10-06
- **Estado**: Activo — **modo greenfield**

> **Origen de las reglas.** Al generar este documento no existe código del producto. Las reglas se derivan de
> [arquitectura-solucion-comercial.md](../propuesta/04-arquitectura/arquitectura-solucion-comercial.md)
> (Convenciones, Estrategia de Solución, Módulos, Aspectos Transversales 8.1–8.11, ADR-001 a ADR-015) y fueron
> confirmadas por el PO el 2026-10-06. Los ejemplos ilustran las reglas, no son código existente. El estándar
> se regenera desde el código real cuando exista el esqueleto de R1.

**Stack (ADR-009):** Python 3.12 · FastAPI · Pydantic v2 · SQLAlchemy 2 · Alembic · Typer · PostgreSQL 16 ·
React + TypeScript (Vite) · Docker · GitHub Actions · Railway.

---

## Estándares Obligatorios

### 1. Nomenclatura

**Idioma:**

| Elemento | Idioma |
| -------- | ------ |
| Identificadores de código: variables, funciones, clases, módulos, tablas, columnas, esquemas, valores de enum, *feature flags* | **Inglés** |
| Documentación, README, ADR, textos de UI, mensajes al usuario, plantillas de señales y *problem details* | **Español** |
| Campos de SECOP II / TVEC necesarios para la trazabilidad (`id_contrato`, `proceso_de_compra`, `id_documento`, `:id` de TVEC) | **Sin transformar** |

Los nombres en español de la arquitectura (`ejecutar_ingesta`, `ExtractorIA`, `ingesta`) se traducen al
implementarse (`run_ingestion`, `AIExtractor`, `ingestion`). Los campos de la fuente se mapean a nombres en
inglés **solo** si la trazabilidad no exige conservar el original. En ese caso se documenta el mapeo en el adaptador.

#### Variables y Funciones

```python
# ✅ CORRECTO — snake_case en inglés, verbo en funciones, unidad explícita
total_amount_cop: int = 12_500_000
cutoff_date: date
def run_ingestion(source: Source, mode: IngestionMode) -> IngestionRun: ...
id_contrato: str  # campo de SECOP II conservado por trazabilidad

# ❌ INCORRECTO — camelCase, español en identificadores, monto float
montoTotal = 12500000.0
def ejecutar_ingesta(fuente, modo): ...
```

```typescript
// ✅ CORRECTO — camelCase en TS; los campos de la API conservan el nombre del contrato OpenAPI
const activeSignals = data.items.filter((s) => s.status === "active");
// ❌ INCORRECTO — renombrar campos del contrato a mano
const senales = data.items.map((s) => ({ id: s.signal_id }));
```

#### Clases y Componentes

```python
# ✅ CORRECTO — PascalCase; puerto como sustantivo, adaptador con el proveedor como prefijo
class AIExtractor(Protocol): ...
class AnthropicAIExtractor(AIExtractor): ...
class RetailConnector(ABC): ...           # clase base: robots.txt, límites, User-Agent, suspensión
class AlkostoRetailConnector(RetailConnector): ...

# ❌ INCORRECTO — proveedor en el dominio o sufijos genéricos
class ClaudeService: ...
class ExtractionManager: ...
```

Componentes React en PascalCase (`ContractDetail`, `EvidenceViewer`) y hooks con prefijo `use` (`useSignalList`).

#### Archivos y Directorios

```
backend/src/public_procurement/<module>/   # ingestion, documents, extraction, catalog, market,
                                           # comparison, exploration, investigation, identity, operations
  api.py            # routers FastAPI del módulo (solo entrada/salida)
  services.py       # servicios de aplicación: única puerta de entrada al módulo
  domain/           # entidades, reglas y funciones puras; sin ORM ni I/O
  ports.py          # interfaces de dependencias externas
  adapters/         # implementaciones de puertos (socrata.py, anthropic.py, r2.py)
  repositories.py   # SQLAlchemy 2; tablas en el esquema PostgreSQL del módulo
  jobs.py           # handlers de jobs del worker
  README.md         # obligatorio por módulo, en español
frontend/src/features/<view>/ContractDetail.tsx   # .py en snake_case; .tsx de componentes en PascalCase
```

### 2. Estructura de Código

#### Organización de Imports

```python
# ✅ CORRECTO — orden aplicado por ruff (isort)
from datetime import date                                         # 1. Librería estándar
from pydantic import BaseModel                               # 2. Librerías externas
from .domain.pricing import calculate_derived_price          # 3. Mismo módulo (relativo)
from public_procurement.operations.services import active_config  # 4. Otro módulo: SOLO services

# ❌ INCORRECTO — entrar al dominio o al repositorio de otro módulo
from public_procurement.catalog.repositories import NormalizedProductRepository
```

#### Estructura de Funciones

```python
# Funciones pequeñas, tipadas y con una responsabilidad. Los cálculos de dominio son puros y versionados:
# reciben la versión de configuración en lugar de leerla de un global.
def calculate_deviation(item_price_cop: int, median_cop: int, config: ConfigVersion) -> Deviation:
    if median_cop <= 0:
        return Deviation.undetermined(reason="median_unavailable")
    percentage = Decimal(item_price_cop - median_cop) / Decimal(median_cop) * 100
    return Deviation(percentage=percentage, config_version_id=config.id)
```

- Tipado obligatorio en firmas públicas (ver mypy en *Configuración de Herramientas*).
- Montos en COP como `int`, `Decimal` solo para cálculos intermedios. **Nunca `float` para dinero.**
- Fechas de negocio con `date`; marcas de tiempo con `datetime` con zona (UTC al guardar, `America/Bogota` al presentar y programar).

### 3. Manejo de Errores

Taxonomía (8.6):
- **Técnicos:** excepción; reintento si es transitorio; reporte a Sentry.
- **De calidad de datos:** rechazo o advertencia con motivo de catálogo cerrado.
- **De negocio:** **estado del dominio**, nunca excepción.

```python
# ✅ CORRECTO — la falta de información es un estado explícito
if tax_base is None:
    return PriceResult(status=PriceStatus.TAX_BASE_UNDETERMINED)

# ✅ CORRECTO — error técnico transitorio: el job decide si reintenta
except httpx.TimeoutException as exc:
    raise TransientError("socrata_timeout") from exc

# ❌ INCORRECTO — valor por defecto que oculta la falta de información
vat = item.vat or Decimal("0.19")
# ❌ INCORRECTO — tragarse la excepción
except Exception:
    pass
```

- API: errores en formato **problem details (RFC 9457)** con `title` y `detail` en español: 400, 401, 403, 404 (también para recursos ajenos), 409 (conflicto de versión), 422 (regla de negocio), 503 (dependencia degradada). Sin trazas ni datos internos.
- No se reintentan los errores de validación ni los bloqueos retail; estos últimos suspenden la fuente.

### 4. Restricciones Arquitectónicas de Codificación

#### Respeto de Capas y Responsabilidades

Capas de cada módulo: **api / services → domain → adapters / repositories** (ADR-001, ADR-005).

```python
# ✅ CORRECTO — el servicio depende de puertos inyectados; la API encola y el worker ejecuta
class ExtractionService:
    def __init__(self, extractor: AIExtractor, storage: ObjectStorage, repo: ExtractionRepository): ...

@router.post("/api/v1/ingestions/{source}/rerun", status_code=202)
def rerun(source: str, svc: OperationsService = Depends(get_operations_service)) -> QueuedJob:
    return svc.enqueue(JobType.INGESTION, payload={"source": source})

# ❌ INCORRECTO — SDK del proveedor en dominio/servicio, o llamada externa dentro del request
import anthropic
client = anthropic.Anthropic()
```

- **Fronteras entre módulos:** un módulo solo importa el `services.py` de otro y **no accede a sus tablas**. Se verifica con `import-linter` en CI.
- **Dependencias externas solo por puertos:** `PublicDataSource`, `DocumentRepository`, `RetailConnector`, `AIExtractor`, `ObjectStorage`, `Mailer`, `JobQueue`.
- **Dominio sin ORM:** las entidades de `domain/` no heredan de modelos SQLAlchemy; los repositorios hacen el mapeo.
- **CLI y agentes** usan los mismos servicios de aplicación que la API, sin SQL directo (ADR-008).
- **SPA sin reglas de negocio:** solo presenta lo que entrega la API.

#### Reglas transversales obligatorias

- **Solo inserción** (ADR-012): extracciones, revisiones, observaciones, benchmarks, señales y calificaciones no admiten `UPDATE` de valores de negocio ni `DELETE`. Una corrección crea una nueva versión (`version`, `is_current`, `created_at`). Cada cálculo guarda `config_version_id`.
- **Jobs idempotentes:** cada job lleva una `idempotency_key` única y propaga el `correlation_id`. Una transacción por unidad de trabajo, y **nunca** una transacción abierta mientras se llama a un servicio externo.
- **IA desactivable:** se respeta el flag `ai.extraction.enabled`. La IA solo propone; la normalización, el emparejamiento, el benchmark y la señal son determinísticos.
- **Migraciones con Alembic**, compatibles hacia adelante (expandir → migrar → contraer). SQL siempre parametrizado.
- **Datos L3:** nunca en logs ni en el paquete que se envía a la IA. Los campos sensibles excluidos no existen en ninguna tabla.
- **Textos al usuario** generados por plantilla en español, sin "sobreprecio", "corrupción", "fraude" ni "hallazgo fiscal" (NFR-CUM-007).
- **Logs JSON** con `module`, `event`, `correlation_id`, `job_id`/`request_id` y `user_id` (nunca el correo).
- **Secretos** solo en variables del PaaS, nunca en el repositorio.

### 5. UI / Design System

N/A — el proyecto no tiene insumos de diseño (Tokens.json/Hoja_Variantes.md) generados todavía.

### 6. Pruebas Unitarias

#### Convención de Testing: adoptada (sin código existente) — pytest + Test Data Builder + patrón 3A

**Obligatorio:** pruebas unitarias para toda regla determinística (clasificación, precio derivado, base
tributaria, normalización, emparejamiento, benchmarks, confianza y señales). Las pruebas de integración de
adaptadores usan dobles; en CI no se usa red real.

```python
# ✅ CORRECTO — nombre descriptivo, builder y patrón 3A
def test_signal_is_withheld_when_data_has_no_evidence_locator():
    # Arrange
    item = ItemBuilder().with_price_cop(2_000_000).without_locators().build()
    benchmark = BenchmarkBuilder().with_median_cop(1_200_000).build()
    # Act
    signal = generate_signal(item, benchmark, ConfigVersionBuilder().build())
    # Assert
    assert signal.status == SignalStatus.WITHHELD

# ❌ INCORRECTO — nombre genérico, datos inline sin builder, varias conductas en un solo test
def test_signal():
    s = generate_signal(Item(1, 2000000, [], ...), Benchmark(...), cfg)
    assert s
```

Frontend: Vitest + Testing Library con el mismo patrón 3A; la descripción del `it(...)` puede ir en español.

### 7. Patrones Anteriores — No Replicar

N/A — no se detectaron convenciones divergentes porque no existe código del producto. Los scripts de los spikes en
`docs/propuesta/03-prd/insumos/d*-scripts/` son exploratorios y **no** son referencia de estilo: tienen varias
sentencias por línea, usan `open()` sin `with` y no tienen tipos ni pruebas.

---

## Convenciones Recomendadas

### 1. Organización de Archivos

```
/
├── backend/            # pyproject.toml, src/public_procurement/<module>/, tests/, alembic/
│   ├── src/public_procurement/entrypoints/{api,worker,scheduler,cli}/
│   ├── src/public_procurement/shared/   # logging, errores, tipos comunes (sin lógica de negocio)
│   ├── prompts/        # prompts, esquemas y configuración del modelo, versionados
│   └── tests/{unit,integration,e2e,golden}/
├── frontend/           # package.json, src/features/, src/api/ (cliente generado del OpenAPI)
├── docs/adr/           # un archivo por ADR (MADR), en español
├── Dockerfile          # imagen única para web, worker y scheduler
└── .github/workflows/  # CI: lint, tipado, pruebas, build, análisis de dependencias
```

### 2. Patrones de Código

```python
# Esquemas Pydantic compartidos: la salida de la IA se valida con el mismo modelo que se exporta a JSON Schema
class ExtractedItem(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    description: str
    quantity: int = Field(gt=0)
    unit_price_cop: int | None
    locators: list[EvidenceLocator] = Field(min_length=1)

# Enums para estados y catálogos cerrados; un miembro por línea, nunca strings sueltos
class JobStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    NEEDS_INTERVENTION = "needs_intervention"
    CANCELLED = "cancelled"
```

- Inyección de dependencias con `Depends` de FastAPI en la API y con una fábrica explícita en el worker y la CLI.
- Frontend: cliente tipado generado del OpenAPI. Cada vista maneja los estados cargando, vacío, error, procesando y resultado, con textos en español.

### 3. Convenciones Complementarias para Tests

```python
# Naming: test_<behavior>_when_<condition>
# Dobles en memoria para los puertos (FakePublicDataSource, FakeAIExtractor, InMemoryObjectStorage)
# Integración con PostgreSQL real en un contenedor de CI (no SQLite)
# Pruebas de autorización en el 100 % de los endpoints de casos (404 para terceros)
# Prueba automática de términos prohibidos sobre las plantillas y las respuestas de la API
# Prueba automática de que los campos sensibles no existen en ninguna tabla
# Golden dataset (D4-4) como puerta para cambios de modelo, prompt o esquema
```

---

## Configuración de Herramientas

> Herramientas **confirmadas** por el PO: ruff, mypy, pytest, import-linter, ESLint, Prettier y Vitest.
> Los archivos se crean con el esqueleto de R1, y desde ese momento su configuración y sus comandos son **obligatorios**.

### Linter

```toml
# backend/pyproject.toml
[tool.ruff]
target-version = "py312"
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "W", "I", "N", "UP", "B", "S", "SIM", "RUF", "DTZ", "PT"]

[tool.mypy]
python_version = "3.12"
plugins = ["pydantic.mypy"]
check_untyped_defs = true

[[tool.mypy.overrides]]   # strict inicial: dominio y servicios de aplicación
module = ["public_procurement.*.domain.*", "public_procurement.*.services"]
strict = true
# adapters, migraciones de alembic y tests: chequeo estándar, sin strict

[tool.importlinter]
root_package = "public_procurement"
# Un contrato por módulo: desde otro módulo solo se permite importar <module>.services
```

Frontend: `eslint.config.js` con typescript-eslint (`recommended-type-checked`) + `react-hooks`; `tsconfig` con `"strict": true`.

### Formatter

```toml
# backend/pyproject.toml
[tool.ruff.format]
quote-style = "double"
```

Frontend: `.prettierrc` con `{ "printWidth": 100, "singleQuote": false, "trailingComma": "all" }`.

### Comandos

Obligatorios desde la creación del esqueleto de R1. El CI los ejecuta en cada PR.

| Acción | Comando |
| ------ | ------- |
| Lint | `ruff check . && mypy src && lint-imports` · `npm run lint` |
| Lint con corrección | `ruff check --fix .` · `npm run lint -- --fix` |
| Formato | `ruff format .` · `npx prettier --write .` |
| Tests unitarios | `pytest tests/unit` · `npm test` (Vitest) |
| Build | `docker build .` (incluye `npm run build`) |

---

## Recomendaciones de Evolución

- **Ampliar mypy strict** a los adaptadores cuando sus tipos se estabilicen.
- **pre-commit** con ruff, ruff-format, mypy y prettier, para que los errores aparezcan antes del CI.
- **Generar el cliente TypeScript** desde el OpenAPI en CI (p. ej., `openapi-typescript`) para detectar rupturas de contrato.
- **Análisis de dependencias** en CI (`pip-audit`, `npm audit` o Dependabot) para cumplir 8.7 y llegar preparados a la revisión OWASP.
- **Pruebas de propiedades** (Hypothesis) para la normalización y los cálculos de precio.

---

## Referencias y Recursos

- [Arquitectura de solución](../propuesta/04-arquitectura/arquitectura-solucion-comercial.md) — Convenciones, 8.1–8.11, ADR-001 a ADR-015
- RFC 9457 (Problem Details), documentación de FastAPI, SQLAlchemy 2, Pydantic v2, ruff e import-linter

---

> **Método Ceiba generar-estandares-codigo** v6.1.97 | Usuario: Juan Camilo | Fecha: 2026-10-06
