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
