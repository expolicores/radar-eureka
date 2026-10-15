# Seguimiento Compras Públicas

Convierte los datos y documentos públicos de contratación colombiana (SECOP II y TVEC) en señales explicables y trazables que indican qué compras merecen revisión humana. La arquitectura está en [docs/architecture/index.md](docs/architecture/index.md) y los estándares de código en [docs/architecture/coding-standards.md](docs/architecture/coding-standards.md).

## Estado: MVP Beta (demo con datos simulados)

Plataforma navegable que simula el flujo principal del producto: *explorar → detectar señal → revisar comparación → guardar en un caso → continuar la investigación*. Los servicios, la persistencia, los modelos y la API se construyen como producto real; **todo lo externo es simulado** y reemplazable por su adaptador real sin cambiar el dominio:

| Módulo (`backend/src/public_procurement/`) | Qué hace | Fuente en el MVP Beta |
| ------------------------------------------ | -------- | --------------------- |
| `ingestion` | Compras SECOP II / TVEC, ítems clasificados por reglas, bitácora | Seed **ficticio** (puerto `PublicDataSource`) |
| `market` | Observaciones de precio retail (solo inserción) | Observaciones **simuladas** (puerto `RetailObservationSource`) |
| `comparison` | Benchmark 1 y 2, señales que merecen revisión, confianza (configuración `analitica-v1`, resultados versionados) | Determinístico, sin IA |
| `exploration` | Búsqueda, filtros y ficha de la compra | — |
| `investigation` | Casos privados con instantáneas y notas | Usuario de demostración (sin autenticación) |

Otras piezas: `shared/` (configuración, logs JSON, errores RFC 9457, persistencia), `entrypoints/api` (FastAPI, `/healthz`, `/api/v1/...`), `entrypoints/cli` (Typer), `frontend/` (React + TypeScript + Vite, cliente tipado generado desde OpenAPI), `docker-compose.yml` (PostgreSQL 16) y `.github/workflows/ci.yml`.

**Extensión inicial de Eureka:** adquisición real de procesos SECOP II (`p6dx-8zbt`) desde CLI,
en tablas separadas de las compras simuladas. No cambia los datos ni las pantallas de la beta.

**Documentos compartidos (fase 2):** inventario Socrata `dmgg-8hin` y descarga SECOP local
por proceso persistido, con versiones por SHA-256 e intentos auditables. Solo CLI, sin UI.

**Eureka (fase 3A):** descubrimiento comercial sobre metadata persistida, catálogo versionado,
scoring explicable y resultados idempotentes. No requiere UNSPSC coincidente ni descarta
automáticamente por cuantía alta. Solo CLI; no analiza el contenido documental.

**Todavía no incluye:** conectores reales de compras SECOP/TVEC o retail,
extracción documental, Eureka UI, autenticación y roles, dispatcher y cola de jobs,
IA (Azure AI Foundry), administración en la UI ni `Dockerfile`.

## Requisitos

- [Docker](https://docs.docker.com/get-docker/) con Docker Compose
- [uv](https://docs.astral.sh/uv/) (instala Python 3.12 por su cuenta)
- Node.js 24

## Arranque local

```bash
# 1. Base de datos
docker compose up -d
# PostgreSQL del host: localhost:55432. Crear una base exclusiva para pruebas (solo una vez):
docker compose exec postgres createdb -U procurement public_procurement_test

# 2. Backend
cd backend
cp .env.example .env
uv sync
uv run alembic upgrade head
uv run python -m public_procurement.entrypoints.cli load-seed   # datos ficticios + señales
uv run uvicorn public_procurement.entrypoints.api.app:create_app --factory --reload
# http://localhost:8000/healthz · documentación de la API: http://localhost:8000/docs

# 3. Frontend (en otra terminal)
cd frontend
npm install
npm run dev
# http://localhost:5173 (el proxy de Vite lleva /api al backend)
```

### Sin Docker: PostgreSQL embebido (solo desarrollo)

En equipos sin Docker, el paso 1 se reemplaza por un PostgreSQL embebido (`pgserver`, grupo de dependencias `local-db`). `start` crea las bases `public_procurement` y `public_procurement_test` y deja `DATABASE_URL` y `TEST_DATABASE_URL` en `backend/.env`. Este modo conserva la dirección asignada por el servidor embebido; Docker usa 55432:

```bash
cd backend
uv run --group local-db python scripts/local_postgres.py start
```

No trae extensiones contrib (`pg_trgm`, `unaccent`) y acepta cualquier contraseña (autenticación `trust`): un test de integración se omite por eso. Detenerlo con `scripts/local_postgres.py stop`.

## Recorrido de la demo

1. **Señales** (inicio): indicadores, aviso «una señal no es una conclusión» y lista priorizada (confianza → desviación) con filtros.
2. **Detalle de la señal** (`SG-2026-0142`): Benchmark 1 con distribución y tabla de comparables, Benchmark 2 de mercado, confianza con penalizaciones; «★ Guardar en caso».
3. **Ficha de la compra**: datos clave e ítems con su resultado.
4. **Explorar compras**: búsqueda sin tildes, filtros (fuente, modalidad, departamento, valor, con señal) y estado del análisis.
5. **Mis casos**: instantáneas guardadas y notas.

### Datos de la demo

- `load-seed` carga ~1.280 compras **ficticias** de televisores (2023–2026), observaciones de mercado **simuladas** y recalcula las señales. Se puede relanzar: no duplica (las observaciones son de solo inserción).
- `recalculate-signals` vuelve a calcular con la configuración vigente y deja una nueva versión de los resultados (las anteriores se conservan).
- **Reiniciar la demo desde cero** (borra todos los datos, incluidos los casos): `uv run alembic downgrade base && uv run alembic upgrade head && uv run python -m public_procurement.entrypoints.cli load-seed`.

## Configuración

| Variable | Obligatoria | Por defecto | Descripción |
| -------- | ----------- | ----------- | ----------- |
| `DATABASE_URL` | Sí | — | Conexión a PostgreSQL (`postgresql+psycopg://usuario:clave@host:puerto/base`) |
| `TEST_DATABASE_URL` | Solo integración | — | Base separada, nombre terminado en `_test` y distinto del de desarrollo. Nunca se sustituye por `DATABASE_URL`. |
| `LOCAL_STORAGE_PATH` | No | `backend/.local/documents` | Almacenamiento documental por SHA-256; rutas relativas desde `backend/`. Se crea al descargar. |
| `DOCUMENT_TIMEOUT_SECONDS` | No | `120` | Timeout positivo de adquisición documental. |
| `DOCUMENT_MAX_BYTES` | No | `52428800` | Límite por archivo, 50 MiB por defecto. |
| `EXTRACTION_TIMEOUT_SECONDS` | No | `60` | Timeout del lector documental aislado. |
| `EXTRACTION_MAX_BYTES` | No | `52428800` | Tamaño máximo de entrada para extracción. |
| `EXTRACTION_MAX_CHARS` | No | `2000000` | Longitud máxima del texto extraído por documento. |
| `EXTRACTION_MAX_FRAGMENTS` | No | `10000` | Máximo de fragmentos por documento. |
| `EXTRACTION_MAX_PAGES` | No | `300` | Máximo de páginas PDF. |
| `APP_ENV` | No | `local` | Ambiente: `local`, `ci` o `production` |
| `LOG_LEVEL` | No | `INFO` | Nivel de log: `DEBUG`, `INFO`, `WARNING`, `ERROR` |

Los secretos van solo en variables de entorno; `backend/.env` no se versiona.

Si ya existe `.env`, actualizar la URL local de Docker a `localhost:55432` y añadir
`TEST_DATABASE_URL`; copiar el ejemplo no es necesario y podría sobrescribir configuración propia.

### Consultar y persistir procesos SECOP II

Desde `backend/`, aplicar la migración aditiva `uv run alembic upgrade head` antes de persistir:

```bash
# Solo consulta pública; no requiere DATABASE_URL ni escribe en PostgreSQL.
uv run python -m public_procurement.entrypoints.cli sync-processes --portfolio CO1.BDOS.10985405 --dry-run

# Consulta y persistencia idempotente en ingestion.secop_process.
uv run python -m public_procurement.entrypoints.cli sync-processes --portfolio CO1.BDOS.10985405

# Intervalo de publicación: inicio inclusivo, fin exclusivo.
uv run python -m public_procurement.entrypoints.cli sync-processes --published-from 2026-10-01 --published-before 2026-10-08 --page-size 1000 --max-pages 100
```

Identidad: dataset + `id_del_proceso`, con `id_del_portafolio` separado. La paginación usa
cursor Socrata por `:id`, sin offsets. Una consulta truncada, inválida o con versiones
contradictorias no se persiste. La carga guarda el estado publicado, no determina oportunidades
vigentes. No incorpora procesos a los benchmarks ni altera `load-seed`.

La consulta no tiene snapshot ni sincronización incremental automática; repetir las ventanas
o los portafolios refresca los datos. Fallos transitorios se reintentan, pero una respuesta
inválida cancela el lote. `radar_eureka_prueba.py` sigue siendo un spike documental separado;
su implementación no se utiliza en el módulo compartido. Las descargas seguras se ejecutan
con los comandos documentales siguientes.

### Inventario y descarga de documentos

Aplicar la migración aditiva `0007_documents_schema` antes de registrar documentos. El proceso
debe existir en `ingestion.secop_process` y tener portafolio. Desde `backend/`:

```bash
# Lee el proceso persistido y consulta Socrata; no escribe ni descarga archivos.
uv run python -m public_procurement.entrypoints.cli sync-documents --process CO1.REQ.11172521 --dry-run
# Registra únicamente el inventario.
uv run python -m public_procurement.entrypoints.cli sync-documents --process CO1.REQ.11172521
# Descarga o reintenta ese inventario; detecta cambios de contenido.
uv run python -m public_procurement.entrypoints.cli download-documents --process CO1.REQ.11172521
```

También se acepta el UUID interno en `--process`. Cada descarga deja un intento; contenido
idéntico reutiliza versión y binario. Errores del último intento no eliminan versiones previas.
Detalle de estados, seguridad y limitaciones en [documents/README.md](backend/src/public_procurement/documents/README.md).

### Descubrimiento comercial Eureka

Desde `backend/`, con procesos SECOP ya persistidos:

```bash
# Evaluar sin persistir; muestra desglose de score y razones.
uv run python -m public_procurement.entrypoints.cli evaluate-eureka --process CO1.REQ.11172521 --dry-run
# Aplicar primero 0008_eureka_discovery para guardar o actualizar resultados.
uv run python -m public_procurement.entrypoints.cli evaluate-eureka --process CO1.REQ.11172521
# Evaluación por departamento, incluyendo todas las cuantías.
uv run python -m public_procurement.entrypoints.cli evaluate-eureka --department Boyacá --dry-run
```

Se conserva un resultado vigente por proceso. Eureka no descarga documentos ni cambia compras,
señales o casos. El estado activo significa candidato para revisión: la metadata actual no
permite confirmar fecha de cierre. El ejemplo Covarachía obtuvo 65 puntos en dry-run, sin
coincidencia UNSPSC. Catálogo, reglas, modelo y decisiones pendientes en
[eureka/README.md](backend/src/public_procurement/eureka/README.md).

### Extracción y búsqueda documental

El módulo compartido `extraction` procesa PDF con texto embebido, DOCX y XLSX ya descargados.
Conserva texto original y ubicaciones verificables, sin modificar el score de Eureka.
Desde `backend/`:

```bash
# Analiza sin persistir; no necesita aplicar 0009 para este dry-run.
uv run python -m public_procurement.entrypoints.cli extract-documents --process CO1.REQ.11172521 --dry-run
# Persistencia y búsqueda requieren la migración aditiva 0009_extraction_schema.
uv run python -m public_procurement.entrypoints.cli extract-documents --process CO1.REQ.11172521
uv run python -m public_procurement.entrypoints.cli extract-document --document 869769892
uv run python -m public_procurement.entrypoints.cli search-extracted-text --process CO1.REQ.11172521 --term chocorramo
```

La extracción es idempotente por versión documental e identidad del extractor. Los errores
se conservan para reintento y las páginas sin texto se señalan para futura revisión/OCR.
No se aplicó la migración a desarrollo durante la implementación. Diseño, límites y evidencia
real de Covarachía en [extraction/README.md](backend/src/public_procurement/extraction/README.md).

### Hechos comerciales y operativos sobre evidencia

La Fase 3B-2 aplica reglas determinísticas sobre fragmentos ya persistidos; no vuelve a
descargar ni leer archivos y no modifica el score de Eureka. Desde `backend/`:

```bash
uv run python -m public_procurement.entrypoints.cli extract-structured --process CO1.REQ.11172521 --dry-run
# Persistencia y consulta requieren 0010_structured_extraction en el entorno elegido.
uv run python -m public_procurement.entrypoints.cli extract-structured --process CO1.REQ.11172521
uv run python -m public_procurement.entrypoints.cli show-structured --process CO1.REQ.11172521
```

Cada hecho guarda valor, confianza, regla versionada y evidencia con todos sus localizadores.
Los campos sin evidencia explícita permanecen ausentes. `show-structured --history` permite
consultar resultados históricos. Reglas, límites y validación real en
[extraction/STRUCTURED.md](backend/src/public_procurement/extraction/STRUCTURED.md).

### Consolidación canónica para Eureka

La Fase 3B-2.2 agrupa hechos equivalentes sin borrar sus evidencias. Los valores incompatibles
quedan en conflicto para revisión, y las entradas nuevas conservan snapshots históricos.
Desde `backend/`, con hechos estructurados persistidos:

```bash
uv run python -m public_procurement.entrypoints.cli consolidate-facts --process CO1.REQ.11172521 --dry-run
# Persistencia y consulta requieren 0011_fact_consolidation en el entorno elegido.
uv run python -m public_procurement.entrypoints.cli consolidate-facts --process CO1.REQ.11172521
uv run python -m public_procurement.entrypoints.cli show-canonical --process CO1.REQ.11172521 --with-evidence
```

Covarachía consolida 39 hechos en 18 resultados, sin conflictos; RUP, experiencia y número
de entregas permanecen ausentes. No cambia el score de Eureka. Diseño, reglas y limitaciones en
[extraction/CONSOLIDATION.md](backend/src/public_procurement/extraction/CONSOLIDATION.md).

### Detalle Eureka enriquecido

La Fase 3B-2.3 consulta hechos canónicos mediante servicios de extraction y los integra con
el score/prioridad persistidos. No requiere migración ni recalcula scoring. Desde `backend/`:

```bash
uv run python -m public_procurement.entrypoints.cli show-eureka-details --process CO1.REQ.11172521
uv run python -m public_procurement.entrypoints.cli show-eureka-details --process CO1.REQ.11172521 --json --with-evidence
```

El detalle incluye productos, ítems, ejecución, pago, requisitos, conflictos y campos ausentes.
La evidencia textual se expande bajo demanda. Covarachía conserva score 65 y prioridad alta;
la revisión de vigencia pendiente permanece visible. Arquitectura, contrato y límites en
[eureka/DETAILS.md](backend/src/public_procurement/eureka/DETAILS.md).

### UI Eureka

La Fase 3C incorpora `/eureka` y `/eureka/:opportunityId` en la beta. El listado consume
`GET /api/eureka/opportunities`; el detalle y sus acordeones de evidencia consultan los
endpoints de oportunidad y evidencia, sin modificar scoring ni datos documentales.
Con backend en 8000 y Vite en 5173, abrir `http://localhost:5173/eureka`.

Diseño, endpoints, arranque y validación real de Covarachía en
[eureka/UI.md](backend/src/public_procurement/eureka/UI.md).

## Calidad

| Acción | Backend (`backend/`) | Frontend (`frontend/`) |
| ------ | -------------------- | ---------------------- |
| Lint y tipado | `uv run ruff check . && uv run mypy src && uv run lint-imports` | `npm run lint && npm run typecheck` |
| Formato | `uv run ruff format .` | `npm run format` |
| Pruebas unitarias | `uv run pytest -m "not integration"` | `npm test` |
| Pruebas de integración (requiere PostgreSQL; **borran solo la base de pruebas**) | Configurar `TEST_DATABASE_URL`, mantener `DATABASE_URL` de desarrollo; `uv run pytest -m integration` | — |
| Contrato de la API → cliente TS | `uv run python scripts/export_openapi.py` | `npm run generate:api` |

### Fronteras de importación

Las fixtures de integración rechazan configuración productiva, URL de pruebas ausente,
nombres sin sufijo `_test` y nombres iguales al de desarrollo, incluso usando alias de host.
Alembic recibe explícitamente el mismo destino validado que usa el engine de pruebas.
CI crea únicamente `public_procurement_test` como destino de las pruebas destructivas.

`lint-imports` verifica las capas (`entrypoints` → `investigation` → `exploration` → `comparison` → `ingestion | market` → `shared`), que entre módulos solo se use `<module>.services`, que ningún `domain/` importe ORM, framework web ni drivers, y que `shared/` no dependa del framework web.
# Radar Eureka · Fase 4.1

El Radar consulta SECOP desde una fecha configurable, reutiliza el pipeline existente y genera
alertas históricas por afinidad comercial documental, sin un umbral obligatorio de score.
La nueva vista es `/eureka/alerts`; CLI, configuración, migración y scheduler externo se describen
en [RADAR.md](backend/src/public_procurement/eureka/RADAR.md).

La Fase 4.2 incorpora OCR local por página como fallback, conserva evidencia nativa y
diagnostica cobertura parcial. Instalación Windows, configuración, migración pendiente y
aceptación real se describen en [OCR.md](backend/src/public_procurement/extraction/OCR.md).

La Fase 4.3 incorpora `/search`, búsqueda transversal de procesos SECOP persistidos y
evidencia vigente, con FTS español y sin IA. Arquitectura, API, migración 0014,
pruebas y rendimiento: [Fase 4.3](docs/fase-4.3-search.md).
Evaluación de cobertura: [SEARCH_GAPS.md](SEARCH_GAPS.md).

La Fase 4.4 incorpora el dispatcher manual de alertas persistidas, captura local, adapter
Resend desacoplado y `/eureka/notifications` de solo lectura. Permanece disabled por defecto;
0015 está aplicada en desarrollo, con históricos intactos y envíos deshabilitados.
Validación operativa: [reporte](docs/validacion-4.4-desarrollo.md). Diseño final, CLI, idempotencia,
recuperación, digest y validación: [Fase 4.4](docs/fase-4.4-notifications.md).

Fase 4.5 agrega `run-eureka-cycle`, logs/embudo, health operacional y
`/eureka/operations`. `0016` está aplicada en desarrollo, con históricos intactos; los scripts
Windows no registran una tarea hasta su invocación autorizada. Automatización y
correos permanecen deshabilitados. [Operación local y pendientes](docs/fase-4.5-operations.md).
Auditoría de migración y smoke de lectura: [validación 0016](docs/validacion-4.5-migracion-desarrollo.md).
Operations permite [iniciar una corrida manual con confirmación](docs/ejecucion-manual-eureka-ui.md),
seguir su embudo por polling y consultar el resultado. El scheduler continúa sin registrar.
