# Contexto del Proyecto

<!-- SECTION:CODING-STANDARDS -->
## Estándares de código (docs/architecture/coding-standards.md)
- Identificadores en inglés; docs/UI/mensajes en español; campos SECOP/TVEC (`id_contrato`, `id_documento`) sin transformar
- Puertos `AIExtractor`; adaptadores `AnthropicAIExtractor`
- Imports: stdlib → externos → relativos → otro módulo solo `<module>.services`
- Capas: `api → services → domain → adapters/repositories`; `domain/` sin ORM ni I/O; externos solo por puertos inyectados
- Nunca tablas de otro módulo ni SQL directo desde CLI/agentes; API encola, worker ejecuta
- Hechos solo inserción con `config_version_id`; jobs con `idempotency_key` y `correlation_id`
- Falta de dato = estado explícito; COP `int`, nunca `float`
- Tests (adoptado): pytest + Test Data Builder + 3A; Vitest
- ruff, mypy strict (domain/services), import-linter, ESLint, Prettier
<!-- END:CODING-STANDARDS -->

<!-- SECTION:ARCHITECTURE -->
## Arquitectura (docs/architecture/index.md)
- Señales trazables de compras públicas de televisores (SECOP II/TVEC); "mostrar hechos, no acusar"
- Monolito modular `backend/src/public_procurement/`: ingestion, documents, extraction, catalog, market, comparison, exploration, investigation, identity, operations (config, jobs, auditoría)
- Procesos: api (FastAPI), worker, dispatch, cli (Typer); SPA React+TS+Vite en `frontend/`
- PostgreSQL 16 = datos + cola de jobs + config (esquema por módulo); S3 (R2/MinIO) por SHA-256
- Externos: datos.gov.co Socrata, SECOP docs, S3, Resend; retail después
- IA/agentes: Azure AI Foundry vigente; ADR-011 Anthropic solo histórico; puertos agnósticos
- Reglas determinísticas sin IA; IA solo propone y es desactivable
- Agentes: herramientas sobre `services` con permisos de usuario; nunca SQL
- Sin microservicios, broker, Redis, caché, search engine, vector DB
- R0 scaffold mínimo incremental; R1 = MVP PO (ingesta→API→exploración + señales/casos mínimos)
<!-- END:ARCHITECTURE -->
