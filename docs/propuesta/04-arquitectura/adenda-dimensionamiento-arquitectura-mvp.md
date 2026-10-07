# Adenda de Dimensionamiento para Arquitectura MVP — Seguimiento Compras Públicas

| Campo | Valor |
|---|---|
| **Proyecto** | Seguimiento Compras Públicas |
| **Fecha** | 2026-10-06 |
| **Autor / Aprobación** | Juan Camilo (PO) |
| **Estado** | Aprobada por el PO como insumo para `crear-arquitectura-solucion` |
| **Complementa** | `resolucion-gaps-arquitectura-mvp-compras-publicas.docx` (S-ARQ-01 a S-ARQ-10) |
| **Origen** | Re-evaluación v1.1 del reporte de validación de completitud PRD (69,1 %; gaps remanentes C2.3, C6.2, C1.4, C2.1, I3.2, I4.4) |

> **Naturaleza:** los valores de esta adenda son **supuestos de dimensionamiento y capacidad** para el diseño de arquitectura del MVP. **No** son alcance comprometido, métricas de negocio ni compromisos presupuestales. Se revisan solo si aparece una incompatibilidad técnica concreta o evidencia de uso que los contradiga.

---

## S-DIM-01 — Escenario de crecimiento (cierra el remanente de GAP-C001 / C2.3)

- **Horizonte de referencia:** **24 meses**.
- **Escenario de dimensionamiento:** hasta **5 categorías**, **5 años de histórico** y **50 usuarios activos** dentro de ese horizonte.
- **Línea base de operación (primeros 12 meses):** 1 categoría (televisores), unos 3 años de histórico, 3–5 usuarios piloto y hasta 20 concurrentes (S-ARQ-01).
- **Traducción a volumen:** ver S-DIM-02 y S-DIM-03.
- **Disparadores de revisión arquitectónica:** se mantienen los de GAP-C001 (más de 5 categorías, más de 5 años activos, más de 50 usuarios activos, colas sostenidas por horas o almacenamiento que deje de ser económicamente cómodo).

## S-DIM-02 — Almacenamiento (cierra C6.2 / I4.2)

| Concepto | Supuesto |
|---|---|
| **Volumen inicial** | **15 GB** (documentos originales + artefactos derivados + imágenes renderizadas + descomprimidos) |
| **Crecimiento de referencia** | **10 GB/año** |
| **Volumen a 24 meses (escenario)** | ~35 GB |
| **Base de datos PostgreSQL** | Del orden de pocos GB (metadatos, ítems, observaciones, señales versionadas, auditoría); no condiciona el diseño |
| **Optimización** | No se optimiza el almacenamiento (tiering, compresión, purga) antes de superar ampliamente este volumen |

**Contraste con evidencia D4 (muestra de 50 contratos):**
- Documentos originales priorizados: **175 MB** (190 archivos PDF/XLSX/DOCX), unos 3,5 MB por contrato.
- Imágenes renderizadas para lectura visual: **107 MB** (198 PNG), unos 2,1 MB por contrato.
- Total: **≈5,7 MB por contrato** → universo SECOP II de unos 355 contratos ≈ **2 GB** con documentos priorizados, o ≈ **5–6 GB** con el expediente completo (mediana de 21,5 docs por proceso).
- Los 15 GB iniciales dejan un **margen de 3× a 7×** sobre lo medido. Los 10 GB/año cubren el escenario de 5 categorías (estimado en 3–7 GB/año).
- TVEC no aporta documentos por ítem (A-012), así que su impacto en el almacenamiento de objetos es despreciable.

## S-DIM-03 — Transacciones, picos y estacionalidad (cierra C1.4)

| Escenario | Supuesto de capacidad |
|---|---|
| **Operación normal** | **< 1.000 operaciones de datos/jobs por día** (ingesta incremental diaria SECOP/TVEC, descargas, extracciones de contratos nuevos, recálculos, captura retail semanal) |
| **Pico de carga / reprocesamiento** | **Hasta 20.000 operaciones en un día** (p. ej. reprocesamiento masivo por cambio de prompt o modelo, re-normalización o recálculo global) |
| **Carga inicial histórica** | Batch ejecutable **durante varios días** (consistente con NFR-DAT-004: ≤ 7 días) |
| **Estacionalidad** | Posible mayor actividad alrededor de cierres e inicios de vigencias fiscales; **sin requisito de procesamiento en tiempo real** |
| **Tráfico interactivo** | 20 usuarios concurrentes (NFR-PER-003), ≤ 3 s p95 en búsquedas y ficha (NFR-PER-001/002) |

**Contraste con D1/D4:** unos 355 contratos × unos 8 documentos priorizados ≈ 2.840 descargas y extracciones, más la ingesta de 1.146 líneas TVEC y los recálculos asociados. Eso da unos 7.000–10.000 operaciones para la carga o el reprocesamiento completo del universo actual, dentro del pico de 20.000. La operación diaria (unos pocos contratos nuevos por día) queda muy por debajo de 1.000.

**Implicación:** el patrón scheduler + jobs en PostgreSQL + worker(s) (GAP-I007) es suficiente. No se requieren broker dedicado, streaming ni autoescalado agresivo.

## S-DIM-04 — Recálculo de benchmarks y señales (cierra el remanente de C2.1)

- **Objetivo:** recálculo **≤ 1 hora** después de terminar una ingesta relevante o de activar un cambio de configuración que lo requiera.
- **Consistencia:** eventual. **No se requiere consistencia inmediata.** Durante el recálculo se sirven los resultados vigentes anteriores con su versión y fecha de cálculo (coherente con las señales versionadas de A-127).
- **Ejecución:** job asíncrono fuera del request web (GAP-I007).

## S-DIM-05 — Dedicación del PO (cierra el remanente de GAP-I003 / I3.2)

| Actividad | Horas/semana (indicativo) |
|---|---|
| Desarrollo / revisión técnica | 4 h |
| Revisión humana / calidad de datos e IA | 2 h |
| Operación / carga manual | 1 h |
| Producto, pruebas y seguimiento | 1 h |
| **Total** | **8 h/semana** durante el MVP |

- La distribución puede variar semanalmente.
- **Supuesto arquitectónico clave:** el sistema debe ser **operable por una persona con dedicación parcial**. Esto prioriza la automatización de ingesta, jobs, backups, alertas y despliegue, y una cola de revisión humana acotada (umbral de aceptación configurable tras D4-4).

## S-DIM-06 — Región de datos (cierra el remanente de residencia en C2.4 / C4.1 / I3.4 / I4.4)

- **Decisión técnica provisional del MVP:** **East US / East US 2**, o la región equivalente más cercana disponible en los proveedores seleccionados.
- **Co-localización:** aplicación, base de datos, object storage y servicio IA en la **misma región o en regiones próximas**.
- **Revisión:** sujeta a cambio si aparecen requisitos jurídicos de residencia de datos. Se registra como ADR (vinculado a ADR-007) y como riesgo de cumplimiento a vigilar: transferencia internacional de datos bajo la Ley 1581/2012, mitigada por la clasificación L1/L2/L3, la minimización de datos personales antes de la IA y la exclusión de campos sensibles en la ingesta.

---

## Trazabilidad con gaps

| Supuesto | Gap / subcriterio que atiende |
|---|---|
| S-DIM-01 | GAP-C001 (C2.3), C1.4 (crecimiento) |
| S-DIM-02 | C6.2, I4.2 |
| S-DIM-03 | C1.4, C2.1 |
| S-DIM-04 | C2.1 |
| S-DIM-05 | GAP-I003 (I3.2) |
| S-DIM-06 | C2.4, C4.1, I3.4, I4.4 (residencia) |

**Declaración del PO:** con estos supuestos los gaps se consideran cerrados para efectos del MVP. No se requiere mayor dimensionamiento en esta fase, salvo que aparezca una incompatibilidad técnica concreta.
