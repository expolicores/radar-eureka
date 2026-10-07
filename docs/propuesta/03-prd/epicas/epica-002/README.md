# ÉPICA-002: De Documentos a Datos Comparables

**Volver a:** [Índice de Épicas](../../epicas.md)

---

## Resumen

Resuelve el cuello de botella identificado en la tesis: en SECOP II, el precio unitario, la cantidad, la marca y el modelo **solo existen dentro de los documentos** del proceso. Esta épica obtiene los documentos por la URL oficial, prioriza los que sirven (ofertas, evaluaciones económicas, cotizaciones, contratos, estudios previos) y extrae los datos de cada ítem de televisor con IA, guardando el documento y la página de origen de cada dato.

Es el **primer incremento de IA** del producto y la principal fuente de riesgo técnico. Incluye control de calidad: nivel de confianza con umbral configurable (sin valor hasta calibrarlo con D4-4), detección de inconsistencias aritméticas, marca de "información insuficiente", precio unitario derivado bajo las 6 condiciones de FR-099 y revisión humana con historial de correcciones. La extracción se puede desactivar sin afectar el resto del producto.

FR-026 (precios de múltiples oferentes) está pospuesto por D4 y no tiene historia en esta épica.

**Prioridad:** Crítica  
**FRs cubiertos:** FR-018, FR-019, FR-020, FR-021, FR-022, FR-023, FR-024, FR-025, FR-027, FR-028, FR-029, FR-030, FR-031, FR-032, FR-033, FR-034, FR-099, FR-100  
**Total HU:** 17 historias  
**Estado:** ✅ Generadas y Aprobadas

---

## Features y Historias de Usuario

### Feature: Obtener y Priorizar Documentos del Proceso

- [HU-014: Listar y registrar los documentos publicados de cada proceso candidato](./HU-014-listar-documentos-proceso-candidato/historia.md) — FR-018, FR-024 — Prioridad Crítica — 11 escenarios, 18 casos QA
- [HU-015: Priorizar los documentos relevantes de cada proceso para la extracción](./HU-015-priorizar-documentos-relevantes-proceso/historia.md) — FR-019 — Prioridad Crítica — 11 escenarios, 15 casos QA
- [HU-016: Descargar los documentos priorizados desde la URL oficial sin evadir restricciones](./HU-016-descargar-documentos-url-oficial/historia.md) — FR-020 — Prioridad Crítica — 11 escenarios, 16 casos QA
- [HU-017: Excluir documentos vacíos, formularios en blanco y duplicados](./HU-017-excluir-vacios-en-blanco-duplicados/historia.md) — FR-019 — Prioridad Crítica — 10 escenarios, 14 casos QA
- [HU-018: Descomprimir archivos ZIP y RAR y tratar su contenido como documentos del proceso](./HU-018-descomprimir-archivos-zip-rar/historia.md) — FR-021 — Prioridad Crítica — 11 escenarios, 14 casos QA

### Feature: Preparar Documentos para la Lectura

- [HU-019: Leer los formatos documentales soportados y generar su representación con ubicaciones](./HU-019-leer-formatos-documentales-soportados/historia.md) — FR-022 — Prioridad Crítica — 11 escenarios, 16 casos QA
- [HU-020: Detectar las páginas que requieren OCR o lectura multimodal](./HU-020-detectar-paginas-lectura-visual/historia.md) — FR-023 — Prioridad Crítica — 9 escenarios, 12 casos QA
- [HU-021: Conservar la copia y la evidencia de los documentos de los que se extraen datos](./HU-021-conservar-copia-evidencia-documental/historia.md) — FR-024 — Prioridad Crítica — 10 escenarios, 13 casos QA

### Feature: Extraer Datos de Ítems de Televisor

- [HU-022: Extraer con IA los datos de cada ítem de televisor con su evidencia de origen](./HU-022-extraer-items-televisor-con-evidencia/historia.md) — FR-025, FR-027, FR-100 — Prioridad Crítica — 14 escenarios, 24 casos QA
- [HU-023: Determinar si cada precio extraído es con IVA, sin IVA o de base indeterminada](./HU-023-determinar-base-tributaria-precio/historia.md) — FR-029 — Prioridad Crítica — 10 escenarios, 17 casos QA
- [HU-024: Calcular el precio unitario derivado solo cuando se cumplen las seis condiciones](./HU-024-calcular-precio-unitario-derivado/historia.md) — FR-099, FR-100 — Prioridad Crítica — 11 escenarios, 15 casos QA
- [HU-025: Marcar los ítems con información insuficiente indicando el motivo](./HU-025-marcar-items-informacion-insuficiente/historia.md) — FR-030 — Prioridad Crítica — 10 escenarios, 15 casos QA

### Feature: Controlar la Calidad de la Extracción

- [HU-026: Aplicar el umbral configurable de aceptación automática y dirigir a revisión los datos dudosos](./HU-026-aplicar-umbral-aceptacion-automatica/historia.md) — FR-028 — Prioridad Crítica — 11 escenarios, 15 casos QA
- [HU-027: Detectar inconsistencias aritméticas en los datos extraídos y dirigirlas a revisión de calidad](./HU-027-detectar-inconsistencias-aritmeticas/historia.md) — FR-031 — Prioridad Crítica — 10 escenarios, 14 casos QA
- [HU-028: Validar, corregir o rechazar los datos extraídos de un ítem conservando el historial](./HU-028-revisar-datos-extraidos-item/historia.md) — FR-032 — Prioridad Crítica — 12 escenarios, 19 casos QA

### Feature: Operar y Medir la Extracción con IA

- [HU-029: Activar o desactivar la extracción con IA por configuración sin afectar las funciones determinísticas](./HU-029-desactivar-extraccion-ia-configuracion/historia.md) — FR-033 — Prioridad Crítica — 9 escenarios, 11 casos QA
- [HU-030: Registrar el costo estimado y el tiempo de procesamiento de la extracción por documento](./HU-030-registrar-costo-tiempo-extraccion/historia.md) — FR-034 — Prioridad Alta — 10 escenarios, 13 casos QA

---

## Matriz de Trazabilidad

| HU | FR | Rol Principal | Valor de Negocio |
|---|---|---|---|
| [HU-014](./HU-014-listar-documentos-proceso-candidato/historia.md) | FR-018, FR-024 | Administrador | Inventario documental trazable a la URL oficial de cada proceso |
| [HU-015](./HU-015-priorizar-documentos-relevantes-proceso/historia.md) | FR-019 | Administrador | Selección de los documentos con precios sin procesar todo el proceso |
| [HU-016](./HU-016-descargar-documentos-url-oficial/historia.md) | FR-020 | Administrador | Obtención legítima del contenido, sin evadir restricciones |
| [HU-017](./HU-017-excluir-vacios-en-blanco-duplicados/historia.md) | FR-019 | Administrador | Cupos y costo usados solo en documentos con datos |
| [HU-018](./HU-018-descomprimir-archivos-zip-rar/historia.md) | FR-021 | Administrador | Cotizaciones y anexos en comprimidos disponibles para extraer |
| [HU-019](./HU-019-leer-formatos-documentales-soportados/historia.md) | FR-022 | Administrador | Contenido uniforme con ubicaciones estables (página, hoja, celda) |
| [HU-020](./HU-020-detectar-paginas-lectura-visual/historia.md) | FR-023 | Administrador | Recupera tablas de precios escaneadas o incrustadas como imagen |
| [HU-021](./HU-021-conservar-copia-evidencia-documental/historia.md) | FR-024 | Analista | Evidencia reproducible aunque el original cambie o desaparezca |
| [HU-022](./HU-022-extraer-items-televisor-con-evidencia/historia.md) | FR-025, FR-027, FR-100 | Analista | Precio unitario y características del televisor adjudicado con evidencia |
| [HU-023](./HU-023-determinar-base-tributaria-precio/historia.md) | FR-029 | Analista | Nunca se mezclan en silencio valores con y sin IVA |
| [HU-024](./HU-024-calcular-precio-unitario-derivado/historia.md) | FR-099, FR-100 | Analista | Más cobertura de precios sin distorsión por bienes o servicios mezclados |
| [HU-025](./HU-025-marcar-items-informacion-insuficiente/historia.md) | FR-030 | Analista | Distingue fuente sin dato de dato no extraído |
| [HU-026](./HU-026-aplicar-umbral-aceptacion-automatica/historia.md) | FR-028 | Administrador (Revisor) | Ningún dato crítico dudoso llega a comparación sin revisión |
| [HU-027](./HU-027-detectar-inconsistencias-aritmeticas/historia.md) | FR-031 | Administrador (Revisor) | Detecta errores de lectura o de tabla como revisión de calidad |
| [HU-028](./HU-028-revisar-datos-extraidos-item/historia.md) | FR-032 | Administrador (Revisor) | Correcciones humanas trazables; datos revisados disponibles |
| [HU-029](./HU-029-desactivar-extraccion-ia-configuracion/historia.md) | FR-033 | Administrador | La IA se apaga sin afectar el resto del producto |
| [HU-030](./HU-030-registrar-costo-tiempo-extraccion/historia.md) | FR-034 | Administrador | Costo y tiempo por documento visibles para decidir el modelo |

---

## Exclusiones Explícitas de Esta Épica

- NO incluye el agente de investigación (siguiente incremento agéntico, post-MVP).
- NO incluye la extracción y comparación de precios de **múltiples oferentes** (FR-026, pospuesta por D4 → ÉPICA-009).
- NO incluye la extracción de cláusulas contractuales, garantías ni condiciones de entrega.
- NO incluye procesar todos los documentos de cada proceso, solo los priorizados.
- NO incluye la extracción de categorías distintas a televisores.
- NO incluye la base de conocimiento RAG sobre los documentos.

---

**Última actualización:** 2026-10-02  
**Generado por:** Workflow generar-historias-usuario

> **Método Ceiba generar hus** v6.1.95 | Modelo: claude-opus-5-5 | Usuario: Juan Camilo | Fecha: 2026-10-02
