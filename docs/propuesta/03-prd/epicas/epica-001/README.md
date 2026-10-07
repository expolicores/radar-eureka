# ÉPICA-001: Universo de Compras Públicas de Televisores

**Volver a:** [Índice de Épicas](../../epicas.md)

---

## Resumen

Construye el universo de datos sobre el que trabaja todo el producto: los contratos de SECOP II y los ítems de la Tienda Virtual del Estado Colombiano (TVEC) relacionados con televisores, con 3 años de histórico y actualización continua, obtenidos por la API oficial de datos.gov.co sin scraping. Convierte las dos fuentes en un universo único y confiable de **ítems de televisor**: identifica candidatos por UNSPSC `52161505` y/o texto, y los clasifica de forma estricta contra el límite de categoría aprobado, con criterio, método y corrección manual. Aplica minimización de datos: los campos personales sensibles del dataset de contratos nunca entran al sistema.

**Prioridad:** Crítica  
**FRs cubiertos:** FR-001 a FR-017  
**Total HU:** 13 historias  
**Estado:** ✅ Generadas (modo automático; pendientes de revisión del PO)

---

## Features y Historias de Usuario

### Feature 1: Ingestar Contratos SECOP II

- [HU-001: Carga inicial del histórico de contratos SECOP II](./HU-001-carga-inicial-historico-secop-ii/historia.md) — Crítica
- [HU-002: Carga incremental periódica de contratos SECOP II](./HU-002-carga-incremental-secop-ii/historia.md) — Crítica

### Feature 2: Ingestar Órdenes de la TVEC

- [HU-003: Ingesta inicial e incremental de ítems de la TVEC](./HU-003-ingesta-items-tvec/historia.md) — Crítica
- [HU-004: Relacionar cada ítem TVEC con su orden de compra, entidad y fecha](./HU-004-relacion-item-orden-entidad-tvec/historia.md) — Crítica

### Feature 3: Controlar Calidad y Trazabilidad de la Ingesta

- [HU-005: Validaciones de calidad en la ingesta y registro de rechazos](./HU-005-validaciones-calidad-ingesta/historia.md) — Crítica
- [HU-006: Bitácora de ejecuciones de ingesta](./HU-006-bitacora-ejecuciones-ingesta/historia.md) — Crítica
- [HU-007: Verificación automática de ausencia de datos personales sensibles](./HU-007-verificacion-ausencia-datos-sensibles/historia.md) — Crítica

### Feature 4: Identificar Candidatos a Televisor

- [HU-008: Marcar candidatos a televisor en contratos SECOP II](./HU-008-marcar-candidatos-secop-ii/historia.md) — Crítica
- [HU-009: Marcar candidatos a televisor en ítems de la TVEC](./HU-009-marcar-candidatos-tvec/historia.md) — Crítica

### Feature 5: Clasificar Ítems de Televisor

- [HU-010: Clasificar ítems candidatos contra el límite de categoría por reglas](./HU-010-clasificar-items-por-reglas/historia.md) — Crítica
- [HU-011: Clasificar contratos SECOP II y soportar contratos mixtos a nivel de ítem](./HU-011-clasificar-contratos-secop-mixtos/historia.md) — Crítica
- [HU-012: Clasificación asistida por IA de candidatos que requieren revisión](./HU-012-clasificacion-asistida-ia/historia.md) — Alta
- [HU-013: Revisión y corrección manual de la clasificación de candidatos](./HU-013-revision-correccion-manual-clasificacion/historia.md) — Crítica

---

## Matriz de Trazabilidad

| HU | FR | Rol Principal | Valor de Negocio |
|---|---|---|---|
| HU-001 | FR-001, FR-002, FR-006, FR-008, FR-009 | Administrador | Universo inicial SECOP II trazable y sin datos sensibles |
| HU-002 | FR-003, FR-006, FR-008, FR-009 | Administrador | Universo actualizado a diario sin reprocesar histórico ni IA |
| HU-003 | FR-004, FR-002, FR-003, FR-008, FR-009 | Administrador | Ítems TVEC estructurados, base principal del Benchmark 1 |
| HU-004 | FR-004, FR-005, FR-003, FR-008, FR-009 | Administrador | Cada compra TVEC con entidad, proveedor y fecha |
| HU-005 | FR-010 | Administrador | Universo sin datos rotos y rechazos explicables |
| HU-006 | FR-007 | Administrador | Trazabilidad operativa de cada ingesta |
| HU-007 | FR-006 | Administrador | Cumplimiento verificable de minimización de datos (Ley 1581/2012) |
| HU-008 | FR-011 | Administrador | Candidatos SECOP II explícitos y explicables |
| HU-009 | FR-012 | Administrador | Candidatos TVEC precisos |
| HU-010 | FR-013, FR-014, FR-015 | Administrador | Solo televisores comparables entran al análisis |
| HU-011 | FR-013, FR-015, FR-017 | Administrador | Contratos mixtos analizados solo por sus ítems de televisor |
| HU-012 | FR-013, FR-015 | Administrador | Menos revisión manual con control de calidad |
| HU-013 | FR-016, FR-015 | Administrador (Revisor) | Clasificación confiable y medición del acierto ≥ 95 % |

---

## Exclusiones Explícitas de Esta Épica

- NO incluye SECOP I (Adenda 1).
- NO incluye categorías distintas a televisores.
- NO incluye el dataset de Procesos (`p6dx-8zbt`) como unidad base; se usa solo como complemento si el PRD lo requiere.
- NO incluye adiciones, modificaciones ni ejecución del contrato (ciclo de vida).
- NO incluye scraping del portal SECOP.

---

**Última actualización:** 2026-10-02  
**Generado por:** Workflow generar-historias-usuario

> **Método Ceiba generar hus** v6.1.95 | Modelo: claude-opus-5-5 | Usuario: Juan Camilo | Fecha: 2026-10-02
