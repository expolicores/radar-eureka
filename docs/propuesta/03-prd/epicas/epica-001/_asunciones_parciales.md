# Asunciones parciales — ÉPICA-001: Universo de Compras Públicas de Televisores

**Fecha:** 2026-10-02 | **Autor:** Juan Camilo (PO) | **Total de asunciones:** 25

| Asunción | Categoría | HUs Relacionadas (IDs temporales) | Impacto | Estado |
|---|---|---|---|---|
| La ingesta SECOP II trae solo contratos que cumplen un prefiltro amplio de televisores (UNSPSC `V1.52161505` o términos en objeto/descripción), no el dataset completo | Técnico | HU-001, HU-002 | Alto | Resuelta |
| Los nombres exactos de los campos sensibles del dataset no están documentados; se usa lista blanca de campos más patrones prohibidos de control | Seguridad | HU-001, HU-002, HU-007 | Alto | Resuelta |
| `documento_proveedor` no es un campo excluido por FR-006 y se conserva como excepción explícita | Seguridad | HU-001, HU-007 | Medio | Resuelta |
| Campos no verificados en D1 (`departamento`, `ciudad`, `tipo_de_contrato`, fechas de inicio/fin, campos de órdenes TVEC) se guardan nulos si no existen, con advertencia | Datos | HU-001, HU-004 | Bajo | Resuelta |
| La fecha de corte se toma de `rowsUpdatedAt` de los metadatos del dataset; si falla, se usa la hora de inicio marcada como aproximada | Datos | HU-001, HU-002, HU-003, HU-004 | Medio | Resuelta |
| Valores operativos iniciales configurables: página de 1.000 registros, tiempo de espera de 60 s, 3 reintentos (2, 4, 8 s), abandono de ejecución a las 6 h | Técnico | HU-001, HU-002, HU-003, HU-004, HU-006 | Bajo | Resuelta |
| La carga incremental usa marca de agua con solape configurable (valor inicial 24 h) y hora de ejecución 02:00 (SECOP), 02:30 (ítems TVEC), 03:00 (órdenes TVEC) America/Bogota | Técnico | HU-002, HU-003, HU-004 | Medio | Resuelta |
| Contratos que dejan de cumplir el prefiltro se capturan con una consulta de seguimiento por identificador y nunca se eliminan | Datos | HU-002, HU-008 | Medio | Resuelta |
| Solo los cambios en objeto, descripción o UNSPSC devuelven un contrato a "Pendiente de marcación" | Negocio | HU-002 | Bajo | Resuelta |
| Dataset de ítems TVEC: `usqp-5nsn` por defecto (trae entidad) y `3hdv-smhz` como alterno configurable | Integraciones | HU-003 | Medio | Resuelta |
| En la TVEC la fecha de actualización del registro es el campo de sistema `:updated_at` de Socrata; la deduplicación usa `:id` más una clave natural | Integraciones | HU-003 | Medio | Resuelta |
| La TVEC no publica URL por ítem; se guarda una referencia reproducible a la API oficial | Datos | HU-003, HU-004 | Bajo | Resuelta |
| La ventana histórica (inicial 2023-01-01) se aplica también a la TVEC con el mismo parámetro | Negocio | HU-003 | Medio | Resuelta |
| La relación ítem TVEC ↔ orden (`rgxm-mmea`) no está verificada; se gestiona con estados de relación, reintento e indicador de relación; tolerancia de fecha ítem/orden de 31 días | Integraciones | HU-004 | Alto | Resuelta |
| Catálogo de calidad con severidad Rechazo/Advertencia; valor del contrato en cero o negativo es advertencia; diferencia precio × cantidad ≠ total en la TVEC es advertencia (tolerancia 1 % o COP 1.000) | Datos | HU-005 | Medio | Resuelta |
| Una versión inválida de un registro no borra la versión válida anterior | Datos | HU-005 | Medio | Resuelta |
| Errores técnicos de ejecución se distinguen de rechazos de calidad; se agregan contadores "sin cambios" y "con advertencias" con invariante | Técnico | HU-006 | Bajo | Resuelta |
| La verificación de datos sensibles con valores testigo solo corre fuera de producción | Seguridad | HU-007 | Medio | Resuelta |
| Los términos coinciden como palabras completas con plural ("tv" no coincide con "tvec"); "televisión" no es término inicial | Negocio | HU-008, HU-009, HU-010, HU-011 | Alto | Resuelta |
| La TVEC usa la misma lista de términos que SECOP II | Negocio | HU-009 | Bajo | Resuelta |
| Listas iniciales de términos por regla de clasificación (no compra, accesorios, servicios, productos excluidos, kits) configurables y versionadas; casos ambiguos van a "Requiere revisión" en vez de excluirse | Negocio | HU-010, HU-011 | Alto | Resuelta |
| Los ítems SECOP II provienen de la extracción documental (otra épica) o del Administrador; la clasificación define los campos mínimos que necesita | Integraciones | HU-010 | Medio | Resuelta |
| Clasificación de contratos SECOP II en dos niveles (preliminar por texto y confirmada por ítems), con indicadores `en_analisis` y `apto_gestion_documental` | Negocio | HU-011, HU-013 | Alto | Resuelta |
| La IA de clasificación produce sugerencias; la aceptación automática está deshabilitada hasta definir un umbral (0,50–1,00) calibrado con revisión manual; la IA no recibe nombres de entidades ni proveedores | Negocio | HU-012 | Medio | Resuelta |
| La corrección manual exige motivo de lista cerrada y comentario (10–500 caracteres), puede devolverse a automática, y el criterio de ≥ 95 % se mide con muestras aleatorias reproducibles | Negocio | HU-013 | Alto | Resuelta |
