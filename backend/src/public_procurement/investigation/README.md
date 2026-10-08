# Módulo `investigation`

Casos de investigación **privados** del Analista: guardan señales y compras como **instantáneas inmutables** y notas de seguimiento. Es dueño del esquema PostgreSQL `investigation`.

## Reglas

- **Privacidad por dueño:** todas las operaciones reciben el dueño; un caso ajeno se trata como inexistente (404).
- **Instantáneas:** al guardar una señal o una compra se copia lo que se ve en ese momento (señal: código, ítem, precio, mediana, desviación, confianza, configuración; compra: referencia, entidad, proveedor, valor, estado). Nunca se modifican; el enlace lleva a la versión actual.
- **Sin duplicados:** el mismo elemento no se guarda dos veces en un caso: es un estado de negocio (`SaveResult.ALREADY_SAVED`) que la API responde con 422.
- **Notas:** 1–5.000 caracteres, solo inserción en el MVP Beta; su texto nunca se escribe en logs.
- **Título:** 1–120 caracteres.

## Usuario actual

Mientras no exista el módulo `identity`, la API usa el **usuario de demostración** que entrega la raíz de composición (`app.state.current_user_provider`). Los servicios ya filtran por dueño: conectar la sesión real no cambia el módulo.

## Capas

| Archivo | Rol |
| ------- | --- |
| `domain/case.py` | Entidades, validaciones y errores de negocio |
| `repositories.py` | Tablas `case`, `case_item`, `case_note` |
| `services.py` | `InvestigationService` e instantáneas (vía `comparison.services` y `exploration.services`) |
| `api.py` | `/api/v1/cases` |
