# Historia de Usuario

**Como** desarrollador del equipo de Seguimiento Compras Públicas,
**Quiero** un esqueleto técnico mínimo del monolito modular (backend FastAPI, frontend React + TypeScript + Vite, PostgreSQL con Alembic y CI básico) que arranque, se pruebe y respete las fronteras de arquitectura,
**Para** construir sobre él el primer *vertical slice* de R1 (ingesta SECOP/TVEC → persistencia → API → exploración) sin rehacer la base ni introducir infraestructura que todavía no se necesita

## Descripción

R0 es una historia **técnica** introducida por el PO como primer objetivo de desarrollo (ver `docs/architecture/index.md`, «Orden de construcción»). Deja el proyecto ejecutable, testeable y preparado para el primer *vertical slice* de R1, **sin funcionalidades de negocio**.

**Incluye únicamente:**

- Estructura mínima del monolito modular (`backend/` con el paquete `public_procurement`, `frontend/`), según `coding-standards.md`.
- Backend FastAPI con el endpoint `/healthz`, que en R0 funciona como *health/readiness* del servicio (incluye la conexión a PostgreSQL); no se agrega un endpoint de *liveness* aparte.
- Frontend React + TypeScript (strict) + Vite que arranca localmente.
- Configuración por ambiente (local, CI, producción) por variables de entorno, sin secretos en el repositorio.
- PostgreSQL 16 + SQLAlchemy 2 + Alembic, con una migración inicial **vacía** (revisión sin operaciones, solo registra `alembic_version`).
- Logging estructurado básico en JSON (`module`, `event`, `correlation_id`, `request_id`).
- Backend: pytest, ruff, mypy (strict en `domain/` y `services`) e import-linter.
- Frontend: Vitest, ESLint y Prettier.
- CI básico en GitHub Actions: lint, typing y tests de backend y frontend (con PostgreSQL 16 como *service container*).

**No incluye todavía:** dispatcher completo, CLI administrativa completa, pipeline productivo de jobs, extracción documental, retail, benchmarks o señales completas, autenticación completa, *hardening* completo, ni módulos vacíos que el primer *vertical slice* aún no necesite. **Tampoco nada de IA:** ni el puerto `AIExtractor`, ni `FakeAIExtractor`, ni el módulo `extraction`, ni variables de configuración de IA, ni el adaptador de Azure AI Foundry. La preparación para Azure AI Foundry queda documentada en `docs/architecture/index.md` y se implementa cuando un *vertical slice* real de extracción o de agentes la necesite. No se crea código *placeholder* sin consumidor.

---

## Criterios de Aceptación

### Escenario 1: Flujo Principal

- **Dado** que el desarrollador clonó el repositorio, levantó PostgreSQL 16 con `docker compose` e instaló las dependencias (uv para el backend, npm para el frontend)
- **Cuando** ejecuta la migración inicial con Alembic, arranca el backend y arranca el frontend
- **Entonces** la migración termina sin error y registra su revisión en `alembic_version`, el backend responde `GET /healthz` con **200** e indica que la base de datos está conectada, y el frontend carga en el navegador desde el servidor de desarrollo de Vite

### Escenario 2: Validaciones

- **Dado** que el scaffold está implementado
- **Cuando** se ejecutan localmente o en el CI de GitHub Actions `ruff check`, `ruff format --check`, `mypy`, `lint-imports`, `pytest`, `npm run lint`, la verificación de Prettier y `npm test` (Vitest)
- **Entonces** todos terminan en verde, y `lint-imports` verifica las fronteras de capas y de módulos (desde otro módulo solo se importa `<module>.services`)

### Escenario 3: Casos Extremos

- **Dado** que PostgreSQL no está disponible o `DATABASE_URL` apunta a una base inaccesible
- **Cuando** se consulta `GET /healthz`
- **Entonces** el backend responde **503** con un *problem details* (RFC 9457) con `title` «Servicio no disponible» y `detail` «No fue posible verificar la conexión con la base de datos.», sin trazas ni datos internos, y registra el evento en el log JSON

### Escenario 4: Configuración por ambiente

- **Dado** que `DATABASE_URL`, la única variable obligatoria de R0, no está definida o está vacía
- **Cuando** arranca el backend
- **Entonces** el arranque falla con el mensaje «Falta la variable de entorno obligatoria: DATABASE_URL.»; `APP_ENV` y `LOG_LEVEL` son opcionales con valores por defecto `local` e `INFO`; ningún secreto está versionado y existe un `.env.example` con estas tres variables documentadas

### Escenario 5: Alcance controlado

- **Dado** el diff de R0
- **Cuando** se revisa contra el alcance de esta historia
- **Entonces** no hay dispatcher, CLI administrativa, cola o pipeline de jobs, autenticación, código ni configuración de IA (puertos, fakes, módulo `extraction`, variables o adaptadores), tablas de negocio, módulos vacíos fuera de los necesarios (`shared/` y `entrypoints/api/`) ni código *placeholder* sin consumidor

### Escenario 6: Identificadores de correlación

- **Dado** una solicitud al backend
- **Cuando** llega con las cabeceras `X-Correlation-ID` y `X-Request-ID` con valores válidos
- **Entonces** el backend reutiliza esos valores; si una cabecera no llega o no es válida, genera un valor nuevo para ella; en ambos casos `correlation_id` y `request_id` aparecen en las líneas de log de la solicitud y se devuelven en las cabeceras `X-Correlation-ID` y `X-Request-ID` de la respuesta, también en las respuestas de error

---

## Información Recopilada

### Usuario y Contexto

- **Tipo de usuario:** desarrollador (historia técnica; ningún Analista ni Administrador interactúa con R0)
- **Permisos requeridos:** ninguno; `/healthz` es público y no expone datos internos
- **Valor de negocio:** habilita construir R1 (MVP del PO) sobre una base que ya cumple las fronteras de arquitectura, los estándares y el CI, y reduce el retrabajo del primer *vertical slice*

### Reglas de Negocio

- Sin reglas de negocio: R0 es técnico.
- Reglas técnicas obligatorias (de `coding-standards.md` y `CLAUDE.md`):
  - Identificadores en inglés; documentación, UI y mensajes en español.
  - Capas `api → services → domain → adapters/repositories`; `domain/` sin ORM ni I/O.
  - Dependencias externas solo por puertos inyectados; ningún SDK de proveedor en dominio o servicios.
  - Errores de API en *problem details* (RFC 9457) en español; 503 para una dependencia degradada.
  - Logs JSON con `module`, `event`, `correlation_id` y `request_id`; nunca datos L3 ni correos.
  - Secretos solo en variables de entorno, nunca en el repositorio.
  - Variables de R0: `DATABASE_URL` (obligatoria), `APP_ENV` (opcional, por defecto `local`) y `LOG_LEVEL` (opcional, por defecto `INFO`). Ninguna variable de Azure AI Foundry, correo, *storage* ni otros servicios.
  - Correlación: `X-Correlation-ID` y `X-Request-ID` se reutilizan si llegan válidas y se generan si no; se propagan a los logs y a la respuesta. Sin *tracing* distribuido en R0.
  - Python 3.12 (`requires-python >=3.12,<3.13`), gestionado con uv y lockfile.

### Interfaz

- `GET /healthz` (backend, fuera de `/api/v1`): *health/readiness*; 200 con la base conectada, 503 sin ella.
- Frontend: página inicial mínima en español que confirma que la SPA arranca (sin vistas de negocio).

### Sistemas Externos

- **PostgreSQL 16:** local con Docker Compose; en CI como *service container* de GitHub Actions.
- **GitHub Actions:** CI de lint, typing y tests.
- **Azure AI Foundry:** fuera de R0. Su preparación está documentada en `docs/architecture/index.md`; no hay código ni configuración.

### Disparadores

- El desarrollador ejecuta la migración inicial de Alembic.
- El desarrollador arranca el backend (servidor de desarrollo).
- El desarrollador arranca el frontend (servidor de desarrollo de Vite).
- Un cliente o monitor consulta `GET /healthz`, con o sin cabeceras de correlación (se puede relanzar en cualquier momento).
- Se abre o actualiza un *pull request*, o se hace *push* (dispara el CI).

### Entidades del Dominio

- N/A: historia técnica sin entidades de negocio.

### Alcance y Continuidad

- Primera historia del proyecto (greenfield). Lo excluido (dispatcher, CLI, cola de jobs, autenticación, IA, tablas de negocio) se incorpora cuando un *slice* de R1 o posterior lo necesite.
- Decisiones confirmadas por el PO el 2026-10-07:
  - PostgreSQL local con Docker Compose.
  - Python 3.12 y uv son el **estándar objetivo**, aunque el equipo actual (Python 3.14, sin uv ni Docker) no pueda ejecutarlos localmente.
  - Migración inicial vacía.
  - Vacíos de `qa.md` cerrados: cabeceras de correlación, variables de R0 y textos exactos del 503 y del arranque fallido.
  - `/healthz` es *health/readiness* (503 sin PostgreSQL); sin endpoint de *liveness* aparte en R0.
  - Sin código de IA en R0: `AIExtractor`, `FakeAIExtractor`, el módulo `extraction` y las variables de IA se retiran del alcance.
- **Validación:** la validación completa (conexión a PostgreSQL, migración, tests y typing con Python 3.12) se hace en CI y, después, en un entorno local que tenga Docker y uv.

### Preview de Interfaz

N/A

---

## Contexto y Referencias

**Arquitectura:** `docs/architecture/index.md`, `docs/architecture/coding-standards.md`, `CLAUDE.md`
**Historias relacionadas:** ninguna (primera historia; habilita el primer *vertical slice* de R1)
**Lecciones aprendidas:** los scripts de los spikes D1/D4/D6 no son referencia de arquitectura ni de estilo

---

## Definición de Terminado (Inicial)

- [ ] Funcionalidad implementada según criterios de aceptación
- [ ] Validaciones funcionando correctamente
- [ ] Mensajes implementados
