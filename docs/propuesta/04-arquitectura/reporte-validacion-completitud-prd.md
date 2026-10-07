# Reporte de Validación de Completitud PRD - Seguimiento Compras Públicas

## 📋 Información del Proyecto

| Campo                      | Valor                      |
| -------------------------- | -------------------------- |
| **Nombre del Proyecto**    | Seguimiento Compras Públicas           |
| **Fecha de Validación**    | 2026-10-05                     |
| **Usuario Responsable**    | Juan Camilo                |
| **Idioma de Comunicación** | Español   |
| **Idioma de Documentos**   | Español |

---

## 🎯 Resumen Ejecutivo

🎯 **Resultado de Validación v1.2 — VIGENTE (2026-10-06):** 71.1% de completitud - ⚠️ APTO CON RESERVAS - Completar gaps críticos · gaps críticos: 0 · ✅ habilita `crear-arquitectura-solucion` (ver "Re-evaluación v1.2")

🗂️ **Resultado v1.1 (2026-10-06):** 69.1% - ⚠️ PARCIALMENTE APTO · gaps críticos: 1

🗂️ **Resultado v1.0 (2026-10-05):** 63.5% de completitud - ⚠️ PARCIALMENTE APTO - Requiere mejoras importantes

**Gaps Identificados v1.2:** 🚨 0 críticos, ⚠️ 16 importantes, ℹ️ 16 menores · *(v1.1: 1 / 16 / 16 · v1.0: 3 / 18 / 16)*

> ℹ️ Estos conteos usan los umbrales del cálculo de completitud: puntaje < 12, < 13 y < 16. Con la fórmula de categorización del análisis de gaps, el resultado es **0 críticos bloqueantes, 7 importantes y 11 menores** (ver "Análisis de Gaps Identificados" y "Observación sobre la Sensibilidad de la Métrica").

> 📊 **Detalle completo del cálculo objetivo disponible en la sección "Cálculo Objetivo del Nivel de Completitud"**

---

## ✅ Re-evaluación v1.2 (2026-10-06): Adenda de Dimensionamiento — RESULTADO VIGENTE

**Nuevo insumo evaluado:** `docs/propuesta/04-arquitectura/adenda-dimensionamiento-arquitectura-mvp.md` (S-DIM-01 a S-DIM-06, aprobada por el PO). Contiene el horizonte de 24 meses, el almacenamiento de 15 GB + 10 GB/año (contrastado con D4: ≈5,7 MB por contrato), la capacidad de < 1.000 ops/día con picos de 20.000, el recálculo en ≤ 1 h con consistencia eventual, la dedicación del PO de 8 h/semana y la región provisional East US / East US 2.

**Método:** un evaluador independiente re-puntuó los 56 subcriterios partiendo de v1.1, con el criterio conservador del workflow.

| Categoría | v1.0 | v1.1 | **v1.2** | % v1.2 | Peso | Contribución |
|---|---|---|---|---|---|---|
| 🚨 Críticos | 287 | 301 | **312/360** | 86.7 % | 3,0 | 43.3 |
| ⚠️ Importantes | 190 | 224 | **229/360** | 63.6 % | 2,0 | 21.2 |
| ℹ️ Menores | 105 | 114 | **114/288** | 39.6 % | 1,0 | 6.6 |
| **🎯 TOTAL** | 582 | 639 | **655/1008** | **71.1 %** | 6,0 | **71.1** |

```
Puntuación_Ponderada_Total = (86.7 × 3) + (63.6 × 2) + (39.6 × 1) = 426.8
Nivel_Completitud = 426.8 / 6 = 71.1 %  →  readiness_score = 71.1 %
critical_gaps_count  (C < 12) = 0
important_gaps_count (I < 13) = 16
minor_gaps_count     (M < 16) = 16
overall_status = "⚠️ APTO CON RESERVAS - Completar gaps críticos"
```

**Evolución:** 63,5 % (v1.0) → 69,1 % (v1.1) → **71.1 % (v1.2)**. Gaps críticos: 3 → 1 → **0**.

**Validación obligatoria para proceder con la arquitectura** (readiness_score ≥ 70 % y critical_gaps_count ≤ 2): ✅ **SUPERADA**.

### Subcriterios que suben en v1.2
| Subcriterio | Puntaje v1.1 → v1.2 | Δ | Aporte de la adenda | Gap remanente |
|---|---|---|---|---|
| **C1.4** | 15 → **18** | +3 | S-DIM-03: <1.000 ops/día en operación normal, pico de 20.000 ops/día, carga inicial en varios días (≤7 días), estacionalidad por vigencias fiscales sin tiempo real; S-DIM-01: crecimiento a 24 meses. Cubre los 4 puntos; C 1→2 | Estacionalidad solo cualitativa; supuestos sin validar con uso real |
| **C2.1** | 15 → **18** | +3 | S-DIM-03 throughput por escenario (normal/pico/carga inicial) + 20 concurrentes y ≤3 s p95; S-DIM-04 recálculo ≤1 h con consistencia eventual. Cierra el gap de throughput y tiempo de recálculo; C 1→2 | Sin TPS interactivo por segundo (aceptable: throughput en ops/día) |
| **C2.3** | 10 → **12** | +2 | S-DIM-01 fija horizonte de 24 meses para el escenario (5 categorías, 5 años, 50 usuarios); S-DIM-02/03 lo traducen a volumen (~35 GB, picos de 20.000 ops/día); disparadores de revisión; C 1→2 | Supuesto aprobado por el PO, sin validar con evidencia de demanda |
| **C6.2** | 15 → **18** | +3 | S-DIM-02: 15 GB iniciales, 10 GB/año, ~35 GB a 24 meses, BD de pocos GB, contrastado con D4 (≈5,7 MB/contrato). Cierra el gap 'almacenamiento no cuantificado'; C 1→2 | Políticas de retención no definidas (ver I4.3) |
| **I3.2** | 15 → **18** | +3 | S-DIM-05: PO con 8 h/semana desglosadas por actividad y supuesto de operación por una persona con dedicación parcial (limitación de capacidad). Cierra el gap; C 1→2 | Planes de capacitación no considerados |
| **I4.2** | 10 → **12** | +2 | S-DIM-02: volumen inicial 15 GB, crecimiento de 10 GB/año, proyección ~35 GB a 24 meses; archivado/tiering/purga descartados explícitamente para el MVP; C 1→2 | Picos estacionales de almacenamiento no considerados (bajo impacto) |

### ⚠️ Reservas que acompañan el estado "APTO CON RESERVAS"
Los gaps que siguen abiertos no bloquean la arquitectura. Deben tratarse durante el diseño o en paralelo:
1. **Dependencias externas como gates:** INV-01 (IVA TVEC → confiabilidad del Benchmark 1), D4-4 (umbral de aceptación automática) y ToS de Alkosto/Falabella (conectores retail detrás de feature flag).
2. **Proveedores sin seleccionar (C3.3):** LLM/OCR, correo y object storage. Se resuelven con ADRs en `crear-arquitectura-solucion`, respetando la región S-DIM-06, el presupuesto S-ARQ-06 y las condiciones de privacidad de GAP-I006.
3. **Modelo de datos (C6.1, I1.4):** relaciones, cardinalidades y máquina de estados del ítem. Se derivan en el diseño.
4. **Sensibilidad (I4.4, I4.3):** inventario de campos L3, matriz de acceso, DPA del proveedor IA y retención/supresión de datos personales (Ley 1581). Se tratan en ADR-007.
5. **Residencia de datos:** la región East US es provisional y queda como riesgo de cumplimiento (transferencia internacional), sujeta a revisión jurídica.
6. **UX/UI:** la cobertura (34,3 %) es independiente y no bloquea la arquitectura. El framework visual se decide como ADR de frontend.

---

## 🔄 Re-evaluación v1.1 (2026-10-06): Documento de Resolución de Gaps (histórico)

**Nuevo insumo evaluado:** `docs/propuesta/04-arquitectura/resolucion-gaps-arquitectura-mvp-compras-publicas.docx` (2026-10-06), con los supuestos S-ARQ-01 a S-ARQ-10, una decisión por cada gap C001–C003, I001–I007 y M001–M011, las dependencias externas tratadas como *gates* y 8 ADRs propuestos.

**Método:** los 3 evaluadores especializados re-puntuaron los 56 subcriterios con el criterio conservador del workflow. Un puntaje solo sube si el documento aporta información concreta que cierra el gap. Los diferimientos ("se definirá", "fuera de arquitectura") y los supuestos sin cifra no suben completitud ni claridad.

### 📊 Resultado v1.1

| Categoría | Puntaje v1.0 | Puntaje v1.1 | % v1.1 | Peso | Contribución |
|---|---|---|---|---|---|
| 🚨 Críticos | 287/360 | **301/360** | 83.6 % | 3,0 | 41.8 |
| ⚠️ Importantes | 190/360 | **224/360** | 62.2 % | 2,0 | 20.7 |
| ℹ️ Menores | 105/288 | **114/288** | 39.6 % | 1,0 | 6.6 |
| **🎯 TOTAL** | **582/1008** | **639/1008** | **69.1 %** | 6,0 | **69.1** |

```
Puntuación_Ponderada_Total = (83.6 × 3) + (62.2 × 2) + (39.6 × 1) = 414.9
Nivel_Completitud = 414.9 / 6 = 69.1 %  →  readiness_score = 69.1 %
critical_gaps_count  (C < 12) = 1  → C2.3
important_gaps_count (I < 13) = 16
minor_gaps_count     (M < 16) = 16
overall_status = "⚠️ PARCIALMENTE APTO - Requiere mejoras importantes"
```

**Categorización formal (fórmula del paso 0.4):** críticos bloqueantes = **0** · importantes = **2** (I3.2, I4.4)

**Evolución:** 63,5 % → **69.1 %**. Gaps críticos: 3 → **1**. El criterio de gaps críticos (≤ 2) **ya se cumple**. El umbral de completitud (≥ 70 %) **no se alcanza por 0.9 puntos porcentuales**.

### ✅ Subcriterios que suben

#### 🚨 Críticos
| Subcriterio | Puntaje v1.0 → v1.1 | Δ | Aporte del documento de resolución | Gap remanente |
|---|---|---|---|---|
| **C2.3** | 6 → **10** | +4 | S-ARQ-01 cuantifica horizonte 12 meses y escenario de evolución (5 categorías, 5 años, 50 usuarios); GAP-C001 fija límites de revisión; P 1→2, Cl 1→2 | Escenario sin fecha ni traducción a volumen de datos; supuesto no validado |
| **C2.4** | 15 → **18** | +3 | GAP-I006: clasificación L1/L2/L3, cifrado en tránsito y reposo, minimización antes de IA, condiciones de no entrenamiento; S-ARQ-09 sin acceso directo a BD; C 1→2 | Residencia/región de datos sin definir |
| **C4.1** | 15 → **18** | +3 | S-ARQ-05 PaaS gestionado; S-ARQ-10 ambientes; GAP-I004 CI/CD, rollback, secretos; topología §7; C 1→2 | Región/residencia de datos sin definir |
| **C4.4** | 10 → **12** | +2 | S-ARQ-06 techo COP 300.000/mes + USD 50/mes IA; S-ARQ-07 operación best-effort; S-ARQ-08 equipo; GAP-I001 perfil; C 1→2 | Límites concretos de Railway; techo provisional |
| **C5.3** | 10 → **12** | +2 | GAP-C003 secuencia R1–R6 walking skeleton + regla de paralelismo; C 1→2 | Dependencias a nivel de HU no mapeadas |

#### ⚠️ Importantes
| Subcriterio | Puntaje v1.0 → v1.1 | Δ | Aporte del documento de resolución | Gap remanente |
|---|---|---|---|---|
| **I1.2** | 10 → **12** | +2 | GAP-I007 estrategia común de jobs (idempotency key, estado, intentos, correlation id, backoff); M002 estados de UI; M005 runbook; Cl 1→2 | Sin catálogo transversal de códigos de error |
| **I2.2** | 6 → **10** | +4 | GAP-I001 perfil Python/SQL/APIs/IA, stack Python + PostgreSQL, estándares mínimos; S-ARQ-08; P 1→2, Cl 1→2 | Tiempos objetivo de cambio; framework frontend sin elegir |
| **I2.4** | 8 → **10** | +2 | GAP-I002 pirámide de pruebas, CI por PR, golden dataset D4-4 con gate de promoción; S-ARQ-10 ambientes; C 1→2 | Cobertura objetivo y umbrales de no regresión sin cuantificar |
| **I3.1** | 10 → **12** | +2 | §1 y S-ARQ-02..05: monolito modular, PostgreSQL, S3, PaaS; prohibición de Kafka/K8s/service mesh; C 1→2 | Versiones/capacidad de Railway existente |
| **I3.2** | 9 → **15** | +6 | S-ARQ-08/GAP-I003 composición (PO + agentes); GAP-I001 competencias; S-ARQ-07 soporte; P 1→2, Cl 1→2 | Dedicación del PO (h/semana por rol) sin cuantificar |
| **I3.3** | 10 → **12** | +2 | S-ARQ-06 techo COP 300.000/mes + USD 50/mes IA; C 1→2 | Licenciamiento OCR/IA y librerías RAR |
| **I3.4** | 10 → **12** | +2 | GAP-I004 CI/CD, rollback, migraciones forward-compatible, secretos, cifrado gestionado; GAP-I006 condiciones al proveedor IA; C 1→2 | Residencia de datos 'se seleccionará'; sin IaC |
| **I4.1** | 15 → **18** | +3 | GAP-I005 modelo canónico con 18 entidades, versión y procedencia; M001 formatos; Cl 1→2 | Relaciones y cardinalidades; A-014 |
| **I4.2** | 8 → **10** | +2 | S-ARQ-01/GAP-C001 rango de crecimiento con disparadores; Cl 1→2 | Volumen en GB, proyecciones y archivado |
| **I4.4** | 12 → **15** | +3 | GAP-I006 clasificación L1/L2/L3, cifrado, minimización, condiciones del proveedor IA; C 1→2 | Inventario L3, matriz de acceso, DPA concreto, residencia |
| **I5.1** | 15 → **18** | +3 | GAP-I007 scheduler + jobs en PostgreSQL con idempotencia y backoff, ruta a Redis; S-ARQ-09 puertos/adaptadores; contract tests; Cl 1→2 | Manejo de cambios de esquema Socrata; A-014 |
| **I6.1** | 10 → **12** | +2 | S-ARQ-09 y §8 tools para agentes con contrato (ADR-008); proveedor IA intercambiable; M008; migraciones forward-compatible; C 1→2 | Versionado de API; despliegue sin downtime |
| **I6.2** | 5 → **6** | +1 | GAP-I004 rollback por redeploy; I005 versión/procedencia; M005 relanzar; C 1→2 | Criterio de conciliación de la carga inicial |

#### ℹ️ Menores
| Subcriterio | Puntaje v1.0 → v1.1 | Δ | Aporte del documento de resolución | Gap remanente |
|---|---|---|---|---|
| **M3.1** | 8 → **10** | +2 | M005 cataloga runbook mínimo (relanzar ingesta/extracción, job fallido, restaurar backup, rotar secreto, desactivar proveedor/fuente); P 1→2 | Runbooks sin pasos; sin verificación periódica de restauración ni depuración de temporales |
| **M3.2** | 2 → **4** | +2 | M006 define README operativo + onboarding corto; manual formal diferido; C 0→1, Cl 1→2 | Sin tutoriales, capacitación ni guías; contenido de onboarding pendiente |
| **M3.3** | 4 → **5** | +1 | M007 + S-ARQ-07: canal único con el PO, best-effort horario hábil, sin SLA ni on-call; P 1→2 | Sin scripts ni métricas de soporte |
| **M3.4** | 10 → **12** | +2 | M008 variables por ambiente + configuración versionada + logs JSON; S-ARQ-10 ambientes; secretos en PaaS; C 1→2 | Niveles de log por ambiente (detalle) |
| **M5.1** | 3 → **5** | +2 | M010: índices y consultas primero, caché solo con medición, sin Redis; C001: índices, paginación, batch; P 1→2, Cl 1→2 | Sin índices concretos ni decisión de precálculo |

### 📌 Gaps cerrados por el documento
- **GAP-C002** (C4.4 → 12) y **GAP-C003** (C5.3 → 12): cerrados.
- **GAP-C001** (C2.3: 6 → 10): **mejora pero sigue < 12**. El escenario de crecimiento no tiene horizonte temporal ni se traduce a volumen de datos o documentos.
- **GAP-I004, I005, I007**: cerrados (I3.4 = 12, I4.1 = 18, I5.1 = 18).
- **GAP-I001, I002, I003, I006**: mejoran pero conservan remanentes (tiempos de cambio, umbrales de no regresión, dedicación del PO, inventario L3 y residencia).

### 🔎 Gaps remanentes con mayor efecto en el puntaje

| Subcriterio | Puntaje | Qué falta (concreto) | Ganancia potencial |
|---|---|---|---|
| C2.3 Escalabilidad | 10 | Horizonte temporal del escenario (p. ej. 24 meses) + traducción a volumen (contratos, documentos, GB) | +2 crít. (y elimina el último gap crítico) |
| C6.2 Volumen de datos | 15 | Estimación de almacenamiento en GB (documentos, artefactos derivados, imágenes) y crecimiento anual | +3 crít. |
| C1.4 Volúmenes de transacciones | 15 | Transacciones/día, picos (p. ej. reprocesamiento masivo, carga inicial) y estacionalidad | +3 crít. |
| C2.1 Performance | 15 | Tiempo objetivo de recálculo de benchmarks/señales tras ingesta o cambio de configuración | +3 crít. |
| C3.3 Servicios de terceros | 15 | Selección (o shortlist) de proveedor LLM/OCR, correo y object storage, con rate limits y modo batch | +3 crít. |
| I3.2 Capacidades del equipo | 15 | Horas/semana del PO por rol (desarrollo, revisión humana, carga manual, operación) | +3 imp. |
| I4.4 / I3.4 Sensibilidad y residencia | 15 / 12 | Región de datos decidida; inventario de campos L3; requisitos de DPA del proveedor IA | +3 imp. |

> Con solo las primeras cuatro filas (información estimable con D1/D4 + decisiones rápidas del PO), el puntaje subiría ~1,5 pp y superaría el umbral.

---

## 📂 Documentación Analizada

### **📋 Disponibilidad de Documentación Comercial**

**✅ Documentos Encontrados:**

1. **PRD — Seguimiento Compras Públicas** - Documento de requisitos de producto
   - **Ubicación:** `docs/propuesta/03-prd/PRD.md`
   - **Estado:** Aprobado conceptualmente (2026-10-02) — D4 completado; sujeto a validación de precisión D4-4 y validación de usuarios D5
   - **Contenido:** 100 FRs en 13 dominios, NFRs cuantificados (calidad analítica, seguridad, cumplimiento, frescura, performance, disponibilidad, usabilidad, observabilidad/costos, evolutividad), 3 user journeys, 9 épicas, exclusiones, supuestos críticos, riesgos, validaciones técnicas pendientes y preguntas abiertas

2. **Épicas Funcionales** - Detalle de épicas e historias de usuario
   - **Ubicación:** `docs/propuesta/03-prd/epicas.md` y `docs/propuesta/03-prd/epicas/epica-001` … `epica-008/`
   - **Estado:** Generadas; 8 épicas con carpeta de HUs (ÉPICA-009 Post-MVP sin HUs detalladas)
   - **Contenido:** 113 historias de usuario (13+17+11+12+15+15+14+16), cada una con `historia.md`, `especificacion.md`, `qa.md`, `cambios.md` e `index.md`; README y asunciones parciales por épica

3. **Brief de Alcance** - Resumen de necesidades del producto
   - **Ubicación:** `docs/propuesta/02-brief-alcance/brief-alcance.md`
   - **Estado:** Aprobado (2026-10-01) con Adendas A1 (spike D1), A2 (spike D6) y A3 (spike D4) del 2026-10-02
   - **Contenido:** Problemas, usuarios, objetivos, métricas de éxito y alcance del MVP

4. **Asunciones del PRD** - Supuestos documentados
   - **Ubicación:** `docs/propuesta/03-prd/asunciones.md` y `epicas/epica-00X/_asunciones_parciales.md`
   - **Estado:** Vigente
   - **Contenido:** Supuestos globales y por épica que soportan el PRD

5. **Spikes técnicos D1, D4 y D6** - Evidencia técnica de factibilidad
   - **Ubicación:** `docs/propuesta/03-prd/insumos/D1-spike-secop-datos-abiertos.md`, `D4-spike-extraccion-documental.md`, `D6-spike-fuentes-precios-mercado.md` (+ scripts y resultados JSON)
   - **Estado:** Completados
   - **Contenido:** D1 — datasets SECOP II/TVEC en datos.gov.co; D4 — extracción documental sobre muestra de 41 contratos con métricas y costo estimado; D6 — fuentes retail de precios de mercado

6. **Insumos de la iniciativa** - Contexto y base teórica
   - **Ubicación:** `docs/propuesta/01-insumos-cliente/# CONTEXTO DE INICIATIVA.md` y `TESIS (base teorica).md`
   - **Estado:** Insumo original
   - **Contenido:** Contexto de la iniciativa y tesis "Plataforma de Visualización de Datos para Control Fiscal de Compras Públicas" (U. Externado, 2025)

7. **Artefactos complementarios** - Visualización y consolidado de HUs
   - **Ubicación:** `docs/propuesta/03-prd/user-story-map.html`, `docs/historias-usuario-consolidado-2026-10-05.csv`
   - **Estado:** Generados
   - **Contenido:** User story map y consolidado tabular de historias de usuario

**📂 Documentos NO encontrados en ruta esperada:**
- Ninguno de los documentos principales esperados (`PRD.md`, `epicas.md`, `brief-alcance.md`) está ausente
- ÉPICA-009 (Contexto Ampliado y Capacidades Pospuestas, Post-MVP) no cuenta con carpeta de historias de usuario detalladas

**📄 Calidad de Documentación Disponible:**
- **PRD:** Muy alta. Es completo y trazable: 100 FRs, journeys, épicas, exclusiones, riesgos y decisiones P-01…P-15 y D4-1…D4-4. Delega a arquitectura toda la definición de stack y despliegue.
- **NFRs:** Cuantificados por categoría y etiquetados por nivel de certeza (Meta Brief / Decisión PRD / valor inicial configurable). Faltan cifrado en reposo, volumen de almacenamiento, entornos y CI/CD.
- **Épicas/Casos de uso:** Excelente. 8 épicas MVP con 113 HUs muy detalladas: 11–14 escenarios Dado/Cuando/Entonces con errores y flujos alternos, más qa.md con 11–24 casos. Hay 213 asunciones validadas por el PO. Los `especificacion.md` están vacíos (plantilla) y algunas HUs siguen en Borrador.
- **User Journeys:** 3 journeys claros (J1 universo→señal, J2 retomar investigación, J3 operación del Administrador), con FRs/NFRs vinculados y duración esperada.
- **Exclusiones:** Explícitas a nivel de producto, técnico y por épica.
- **Riesgos:** Sólidos (8 riesgos técnicos del PRD + R1–R10 del Brief, con nivel y mitigación). No incluyen riesgos propios de arquitectura u operación.
- **Preguntas pendientes:** Bien registradas. Siguen abiertas D4-4 (precisión), INV-01 (IVA TVEC), D2 (línea base), D5 (usuarios) y la revisión de ToS retail. INV-01 bloquea el cierre de la arquitectura analítica del Benchmark 1.

---

## 🔍 Análisis Detallado de Completitud

**ANÁLISIS EXHAUSTIVO POR SECCIONES ARQUITECTÓNICAS:**

#### **📋 Introducción y Objetivos - ✅ COMPLETO**
- ✅ **Requisitos Funcionales:** 100 FRs en 13 dominios (95 MVP + 5 Post-MVP: FR-026, FR-095 a FR-098), con matriz HU↔FR por épica. Cubren ingesta SECOP II (`jbjy-vk9h`, histórico desde 2023-01-01, incremental diaria desacoplada del reprocesamiento IA) y TVEC (`usqp-5nsn`/`3hdv-smhz` + `rgxm-mmea`), clasificación por ítem (UNSPSC 52161505 + texto), gestión documental (unos 8 docs priorizados por proceso, ZIP/RAR, OCR/multimodal, copia + hash), extracción IA, normalización, observaciones retail, benchmarks 1/2, señales, ficha, casos, autenticación y administración/KPIs. *Detalle menor:* la ÉPICA-009 no tiene HUs, y no se define qué capacidades administrativas tendrán UI (queda a arquitectura).
- ✅ **Objetivos de Calidad:** NFRs cuantificados. Calidad analítica: NFR-CAL-001 a 008 (precisión ≥90 % en ≥50 docs, extracción ≥80 % provisional, trazabilidad 100 %, 0 % mezcla de IVA, ≥70 % de señales sustentadas, reducción de tiempo ≥70 %). Seguridad: NFR-SEG-001 a 008 (TLS 1.2+, hash Argon2/bcrypt, sesión de 30 min, OWASP Top 10, auditoría 12 meses). Datos: NFR-DAT (diaria, ≤48 h/≤72 h, histórico ≤7 días, 3 reintentos). Rendimiento: NFR-PER (≤3 s p95, 20 concurrentes, extracción ≤5 min p95). Disponibilidad: NFR-DIS (99 % mensual, backup diario con 30 días, RPO/RTO ≤24 h). Usabilidad: NFR-USA (WCAG 2.1 AA, ≤3 clics). Observabilidad: NFR-OBS. Evolutividad: NFR-EVO. *Faltan:* cifrado en reposo, límites de escalabilidad post-MVP, tiempo para recalcular benchmarks/señales, retención y volumen de la copia documental, y entornos no productivos. Los valores son objetivos de piloto, no SLA.
- ✅ **Stakeholders:** El PO (Juan Camilo Sierra) es patrocinador, decisor y revisor técnico, y en el MVP también Administrador y Revisor. Agentes del Método Ceiba como ejecutores. Validadores: 3–5 analistas por conseguir. Segmentos hipotéticos H1–H4 (periodistas, veedores, ONG/academia, control político). *Faltan:* confirmar al patrocinador ([Supuesto]), validar los segmentos (D2/D5) y definir stakeholders técnicos u operativos aparte del PO.

#### **🚫 Restricciones - ✅ COMPLETO**
- ✅ **Técnicas:** Web desktop-first y responsive (sin app nativa ni IE). La base determinística funciona sin IA, y la IA se desactiva sin redespliegue (FR-033, NFR-EVO-003). Stack no cerrado (el de la tesis no es obligatorio). Azure/Foundry solo si se justifica. Arquitectura híbrida permitida. Orden de adquisición: API oficial → sitemap → lectura permitida → carga manual. No se evaden CAPTCHA ni se hace scraping del portal SECOP. Normalización y emparejamiento sin IA (A-065). Límites operativos en A-006, A-036, A-040, A-042 y A-104. *Faltan:* decisiones de stack, nube, proveedor LLM/OCR, motor de búsqueda y almacenamiento de objetos (delegadas a arquitectura).
- ✅ **Organizacionales:** Presupuesto y fecha no son restricción de diseño, pero hay que identificar drivers de costo. La infraestructura de Express App cuesta unos COP 100.000/mes. Opera una sola persona (el PO) con apoyo de agentes. Sin jurídico permanente. Costo IA estimado en D4: unos USD 0,05/contrato (unos USD 19 para 355 contratos, con margen ×1,5–3). *Faltan:* techo de costo mensual, capacidad de soporte/on-call y composición del equipo de desarrollo.
- ✅ **Regulatorias:** Ley 1581/2012 (política antes del registro, lista blanca de campos, documento de persona natural oculto). Leyes 1712/2014 y 1150/2007. Ley 1480/2011 (IVA retail, sin verificación jurídica). robots.txt, ritmo de 1 solicitud cada 2 s y 2.000/semana, User-Agent con contacto. Lenguaje no acusatorio verificable (FR-064, NFR-CUM-007). OWASP Top 10. Auditoría 12 meses. *Faltan:* revisión de ToS de Alkosto y Falabella (bloquea producción), verificación jurídica del IVA, residencia y región de los datos, y aval para que el proveedor IA procese documentos públicos con datos personales.

#### **🌐 Contexto y Alcance - ✅ COMPLETO**
- ✅ **Usuarios:** 2 roles (Analista, Administrador = PO/Revisor) con matriz de permisos (FR-086, A-165, A-175, A-176). Sistemas externos: API Socrata de datos.gov.co (SECOP II Contratos; Archivos Descarga `dmgg-8hin`, `nbae-kzan`, `3skv-9na7`, `kgcd-kt7i`, `f8va-cf4m`; TVEC), community.secop.gov.co, sitemaps y schema.org de Alkosto y Falabella, correo electrónico y servicio IA multimodal. *Faltan:* diagrama de contexto C4-L1, proveedor de correo y de IA/OCR, y verificar relaciones TVEC ítem↔orden (A-014) y los límites de la API Socrata.
- ✅ **Integraciones:** Modos y horarios definidos: SoQL con app token, incremental por `:updated_at` con solape de 24 h, 02:00/02:30/03:00 America/Bogota, retail los lunes a las 02:00. Reintentos exponenciales, suspensión ante 403/429/CAPTCHA, conectores retail desacoplados, carga manual/CSV como canal alterno, alertas por correo. *Faltan:* contratos de interfaz formales, estrategia ante cambios de esquema, especificación de la integración IA (API, modelo, rate limits, batch) y patrón de orquestación de jobs.
- ✅ **Entradas/Salidas:** Entradas: registros SECOP/TVEC, documentos multiformato, observaciones retail, carga manual con evidencia (1–5 archivos ≤10 MB), CSV+ZIP, plantilla de validación, configuración versionada. Salidas: datos por ítem con evidencia de página/celda, benchmarks y señales con evidencia, ficha, listas, casos con instantánea, KPIs, costos, auditoría exportable (≤100.000 eventos) y alertas. *Faltan:* modelo de datos lógico/canónico consolidado y API para terceros (Post-MVP).

#### **⚙️ Diseño Técnico - ⚠️ PARCIAL**
- ⚠️ **Volumetría:** Unos 355 contratos SECOP II (≈100/año, 272 entidades), 1.146 líneas TVEC, 930 órdenes, unas 6.000 unidades. Mediana de 21,5 docs por proceso (5–419), con unos 8 priorizados. 34,9 % de páginas escaneadas. Unos 14.800 tokens por contrato (p90 30.200). 3–5 analistas, 1 administrador, 20 concurrentes. *Faltan:* volumen de almacenamiento (GB de copias documentales e imágenes), crecimiento de observaciones y señales versionadas, TPS y proyección para la expansión post-MVP.
- ✅ **Casos de Uso:** 3 User Journeys con duración (J1 10–15 min, J2 5–10 min, J3 30–60 min/semana). 113 HUs con 11–14 escenarios (errores, concurrencia, límites), reglas de negocio, INVEST y DoD, más qa.md. 213 asunciones validadas. *Faltan:* notas técnicas en `especificacion.md` (vacíos), cierre del estado Borrador de algunas HUs y mockups (D5).
- ⚠️ **Despliegue:** Web por URL, solo HTTPS, gestor de secretos, backup diario con RPO/RTO ≤24 h que incluye copias documentales, 99 % mensual, IA desactivable sin redespliegue. Hay mención a entornos de validación. Infraestructura existente reutilizable si se justifica. *Faltan:* definición de entornos (dev/staging/prod), CI/CD, estrategia de despliegue y rollback, región/nube, IaC, monitoreo/APM, ejecución de jobs batch y workers asíncronos, ventana de mantenimiento y plan de carga inicial del histórico.

#### **🎯 Calidad y Riesgos - ⚠️ PARCIAL**
- ⚠️ **Escenarios Calidad:** Hay NFRs convertibles en escenarios: caída de la API con 3 reintentos (NFR-DAT-005), alerta ≤1 h (NFR-OBS-002), suspensión ante CAPTCHA/403/429, ≤3 s p95 con 20 concurrentes, nueva fuente solo con un conector (NFR-EVO-001), nueva categoría por configuración (NFR-EVO-002), IA apagada sin afectar lo determinístico, degradación del Benchmark 2 sin bloquear el Benchmark 1, autorización en el 100 % de los endpoints. *Faltan:* escenarios formales (estímulo/fuente/entorno/artefacto/respuesta/medida), árbol de utilidad y escenarios de ataque, de recuperación ante desastre, de pico de reprocesamiento y de cambio de proveedor IA.
- ✅ **Riesgos:** 8 riesgos técnicos con nivel y mitigación. Altos: SECOP II con 50–56 % de registros sin precio unitario, falsos positivos en emparejamiento, usuario no validado. Medios: INV-01, retail, costo IA, datos.gov.co, legal. Factores de complejidad con % de esfuerzo. R1–R10 del Brief. Limitaciones de D1, D4 y D6. *Faltan:* riesgos de arquitectura y operación (operador único, lock-in IA, deriva del modelo, crecimiento del almacenamiento), dueños y disparadores de contingencia.
- ✅ **Criterios Éxito:** KPIs a 3 meses (precisión ≥90 %, extracción ≥80 % provisional, trazabilidad 100 %, comparabilidad 100 %, 0 % mezcla de IVA, ≥3 usuarios, ≥70 % de señales sustentadas, reducción de tiempo ≥70 %), criterio técnico de extremo a extremo SECOP→señal→evidencia, criterios por épica y fórmulas en A-203 a A-211. *Pendiente:* precisión real (D4-4), línea base D2, meta de cobertura provisional. INV-01 bloquea el cierre analítico del Benchmark 1.

**Resultado del análisis de documentación comercial (16 elementos):** ✅ 12 ENCONTRADO · ⚠️ 4 PARCIAL · ❌ 0 NO ENCONTRADO

---

## 📊 Resumen de Completitud 

### **📊 Matriz de Completitud - Documentación Comercial Seguimiento Compras Públicas**

**Convenciones:** ✅ COMPLETA (detalle suficiente) · ⚠️ PARCIAL (hay información, falta profundidad) · ❌ FALTANTE (no hay información) · 🔍 INFERIBLE (se puede deducir de otros elementos)

| # | Sección Arquitectura | Estado | Información Disponible | Información Faltante | Impacto |
|---|----------------------|--------|------------------------|----------------------|---------|
| 1 | **Resumen de Requisitos Funcionales** | ✅ | 100 FRs en 13 dominios (95 MVP + 5 Post-MVP), matriz HU↔FR, 8 épicas MVP con 113 HUs | ÉPICA-009 sin HUs. No se define qué capacidades administrativas tendrán UI | Bajo |
| 2 | **Objetivos de Calidad / NFRs** | ✅ | NFR-CAL, SEG, CUM, DAT, PER, DIS, USA, OBS y EVO cuantificados y etiquetados por nivel de certeza | Cifrado en reposo; recálculo de benchmarks/señales; límites de escalabilidad post-MVP | Medio |
| 3 | **Stakeholders y expectativas** | ✅ | PO = patrocinador, decisor, Administrador y Revisor; analistas validadores (3–5); segmentos H1–H4; objetivos priorizados | Patrocinador marcado [Supuesto]; segmentos sin validar (D2/D5); sin stakeholders operativos o técnicos | Bajo |
| 4 | **Restricciones Técnicas** | ✅ | Web desktop-first responsive; IA desactivable; normalización determinística; orden de adquisición de fuentes; límites operativos (A-006, A-036, A-040, A-042, A-104) | Stack, nube, proveedor LLM/OCR, motor de búsqueda y almacenamiento de objetos: delegados a arquitectura | Medio |
| 5 | **Restricciones Organizacionales** | ✅ | Operador único (PO + agentes); costo bajo deseable; infraestructura existente de unos COP 100.000/mes; costo IA de unos USD 0,05/contrato (D4) | Techo de costo mensual; capacidad de soporte/on-call; composición del equipo de desarrollo | Medio |
| 6 | **Compliance / Regulatorio** | ✅ | Ley 1581/2012 (lista blanca, ocultamiento), Leyes 1712/2014 y 1150/2007, robots.txt y ritmo de solicitudes, lenguaje no acusatorio, OWASP, auditoría 12 meses | ToS retail sin revisar (bloquea producción); IVA retail sin aval jurídico; residencia de datos; tratamiento de datos personales por el proveedor IA | Alto |
| 7 | **Contexto: Usuarios y Sistemas Externos** | ✅ | 2 roles con matriz de permisos; datasets Socrata identificados (SECOP II, Archivos, TVEC); community.secop.gov.co; Alkosto y Falabella; correo | Diagrama de contexto C4-L1 🔍 (se puede inferir); proveedor de correo e IA; relación TVEC ítem↔orden (A-014) sin verificar | Medio |
| 8 | **Integraciones Requeridas** | ✅ | API SoQL con token, incremental por `:updated_at` + 24 h, horarios, reintentos, suspensión ante 403/429/CAPTCHA, conectores desacoplados, carga manual/CSV | Contratos de interfaz; manejo de cambios de esquema; integración IA (API, rate limits, batch); orquestación de jobs | Medio |
| 9 | **Entradas / Salidas del Sistema** | ✅ | Formatos de entrada (docs multiformato, CSV+ZIP, evidencia de carga manual) y de salida (datos con evidencia, benchmarks, señales, casos, KPIs, auditoría) | Modelo de datos lógico/canónico 🔍 (se puede inferir de FRs y asunciones); API para terceros (Post-MVP) | Medio |
| 10 | **Volumetría de Datos y Usuarios** | ⚠️ | Unos 355 contratos SECOP II, 1.146 líneas TVEC, 930 órdenes; 21,5 docs por proceso (≈8 priorizados); 34,9 % de páginas escaneadas; unos 14.800 tokens por contrato; 3–5 analistas; 20 concurrentes | Volumen de almacenamiento (GB) 🔍 (estimable con métricas D4); crecimiento de observaciones y señales; TPS; proyección post-MVP | Medio |
| 11 | **Casos de Uso Principales** | ✅ | 3 User Journeys con duración; 113 HUs con 11–14 escenarios (errores, concurrencia, límites), DoD y QA; 213 asunciones validadas | `especificacion.md` vacíos; HUs en Borrador; sin mockups (D5) | Bajo |
| 12 | **Requerimientos de Despliegue** | ⚠️ | HTTPS, gestor de secretos, backup diario, RPO/RTO ≤24 h, 99 % mensual, IA desactivable sin redespliegue, infraestructura existente reutilizable si se justifica | Entornos (dev/staging/prod), CI/CD, rollback, región/nube, IaC, APM, workers y scheduler, plan de carga inicial del histórico | Alto |
| 13 | **Escenarios de Calidad** | ⚠️ | NFRs medibles convertibles en escenarios 🔍 (resiliencia de ingesta, alerta ≤1 h, p95 ≤3 s, evolutividad, degradación del Benchmark 2, IA apagada) | Escenarios formales estímulo/respuesta/medida; árbol de utilidad; DR, ataques, pico de reprocesamiento, cambio de proveedor IA | Medio |
| 14 | **Riesgos Conocidos** | ✅ | 8 riesgos técnicos del PRD con mitigación + R1–R10 del Brief; % de complejidad por factor; limitaciones de D1, D4 y D6 | Riesgos de arquitectura u operación (operador único, lock-in IA, deriva del modelo, almacenamiento); dueños y disparadores | Medio |
| 15 | **Criterios de Éxito Medibles** | ⚠️ | KPIs a 3 meses con fórmulas (A-203 a A-211); criterio técnico de extremo a extremo; criterios por épica | Precisión real pendiente de D4-4; línea base D2; meta de cobertura provisional; **INV-01 (IVA TVEC) bloquea el cierre analítico del Benchmark 1** | Alto |

### **📈 Métricas de Completitud Global**

> 📊 **Las métricas detalladas y el cálculo objetivo completo se encuentran en la sección "Cálculo Objetivo del Nivel de Completitud"**

**Distribución de las 15 secciones arquitectónicas:**

| Estado | Cantidad | Secciones |
|--------|----------|-----------|
| ✅ COMPLETA | 11 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 11, 14 |
| ⚠️ PARCIAL | 4 | 10 Volumetría, 12 Despliegue, 13 Escenarios de Calidad, 15 Criterios de Éxito |
| ❌ FALTANTE | 0 | — |
| 🔍 INFERIBLE (gaps puntuales) | 4 | C4-L1 (7), modelo de datos canónico (9), almacenamiento en GB (10), escenarios de calidad desde NFRs (13) |

**Distribución por impacto de los faltantes:** Alto: 3 (Compliance, Despliegue, Criterios de Éxito/INV-01) · Medio: 9 · Bajo: 3

**Lectura del resumen:**
- La documentación funcional y de negocio es **sobresaliente**: requisitos, casos de uso, restricciones y compliance están documentados con trazabilidad.
- Los faltantes se concentran en **aspectos que el PRD delega explícitamente a arquitectura** (stack, despliegue, operación, modelo de datos). Esto es normal en un PRD y no implica un defecto del documento comercial.
- Los faltantes de **impacto alto** que no dependen de arquitectura son: revisión de ToS retail y aval jurídico, resolución de INV-01 y cierre de D4-4. Afectan la viabilidad de componentes concretos (captura retail, Benchmark 1, extracción IA), no la descomposición general del sistema.

---

## 🚨 Análisis de Gaps Identificados (v1.0)

> **Método:** 3 evaluadores especializados (críticos C1–C6, importantes I1–I6, menores M1–M5) puntuaron los 56 subcriterios con **Puntuación = (Presencia + Completitud + Claridad) × Impacto Arquitectónico** (rango 3–18) y aplicaron la fórmula de categorización de cada categoría.

**Consolidado de la evaluación:**

| Categoría | Subcriterios | ✅ Cumple | ⚠️ Parcial | ❌ No cumple | 🔍 Inferible | Puntaje | Gaps según fórmula |
|---|---|---|---|---|---|---|---|
| 🚨 Críticos (C1–C6) | 20 | 13 | 6 | 0 | 1 | 287/360 | **0 críticos** |
| ⚠️ Importantes (I1–I6) | 20 | 7 | 12 | 0 | 1 | 190/360 | **7 importantes** |
| ℹ️ Menores (M1–M5) | 16 | 8 | 7 | 1 | 0 | 105/288 | **11 menores** |

### **🚨 GAPS CRÍTICOS (Bloquean arquitectura)**

**Según la fórmula de categorización no hay gaps CRÍTICOS.** Ningún subcriterio C1–C6 tiene Puntuación ≤ 12 con Impacto = 3, ni Presencia = 0 con Impacto ≥ 2. Los 13 subcriterios de impacto 3 obtuvieron 15 o 18 puntos.

**Subcriterios críticos con puntuación baja (< 12)**, sin bloqueo según la fórmula porque su impacto es 2. Se cuentan como gap crítico en la métrica del paso 0.6:

#### **GAP-C001: Escalabilidad no proyectada (C2.3 — 6/18)**
- **Descripción:** El roadmap post-MVP es solo cualitativo (nuevas categorías, más años de histórico, agente, RAG, SECOP I con unos 240 contratos más). El crecimiento a 1–3 años no está cuantificado y no hay límites de escalabilidad.
- **Impacto:** Sin un supuesto de crecimiento no se puede validar que la persistencia, el almacenamiento documental y el pipeline de extracción sigan funcionando al ampliar categorías o años. NFR-EVO-001/002 mitigan parcialmente.
- **Timeline:** Se resuelve antes o durante la arquitectura de solución (1–2 días).
- **Estado:** ⏳ **NO BLOQUEANTE — documentar supuesto**
- **Recomendación:** Que el PO declare un escenario de crecimiento de referencia (p. ej. ×5 categorías y ×2 años en 24 meses) y que arquitectura lo use como supuesto de dimensionamiento.

#### **GAP-C002: Limitaciones de la infraestructura existente y operación (C4.4 — 10/18)**
- **Descripción:** La infraestructura de Express App (Railway, PostgreSQL, Google; unos COP 100.000/mes) está inventariada, pero sin límites de capacidad, red o seguridad. Tampoco hay techo de costo mensual ni capacidad de soporte u on-call del operador único.
- **Impacto:** Condiciona la elección entre reutilizar infraestructura o usar servicios gestionados, y el nivel de automatización operativa necesario.
- **Timeline:** 1 día (inventario técnico + decisión del PO sobre costo máximo).
- **Estado:** ⏳ **NO BLOQUEANTE — precisar**
- **Recomendación:** Definir un techo de costo mensual de referencia, documentar planes y límites de Railway/PostgreSQL y explicitar la disponibilidad del PO para operar (horario, tiempo de reacción).

#### **GAP-C003: Dependencias entre fases no mapeadas (C5.3 — 10/18)**
- **Descripción:** El MVP está bien delimitado (ÉPICA-001 a 008), pero no hay un mapa explícito de dependencias entre épicas e HUs. Las versiones futuras no tienen incrementos funcionales detallados.
- **Impacto:** Afecta la secuencia de construcción y la estrategia de entregas incrementales. El orden se puede inferir del flujo de datos.
- **Timeline:** 1 día (workflow de análisis de dependencias de HUs).
- **Estado:** ⏳ **NO BLOQUEANTE — derivable**
- **Recomendación:** Ejecutar el análisis de dependencias de historias de usuario y confirmar con el PO la secuencia de releases.

> ⚠️ **Dependencias externas abiertas (no son gaps documentales, pero condicionan componentes):** **INV-01** (IVA de TVEC) bloquea el cierre analítico del Benchmark 1. **D4-4** define la precisión real y el umbral de aceptación automática de la extracción IA. La **revisión de ToS de Alkosto y Falabella** bloquea la captura retail en producción. Ninguna impide la descomposición del sistema en componentes.

### **⚠️ GAPS IMPORTANTES (Arquitectura incompleta)**

#### **GAP-I001: Perfil técnico del mantenedor y requerimientos de mantenibilidad (I2.2 — 6/18)**
- **Impacto:** Con un único mantenedor (el PO apoyado en agentes), las competencias y tecnologías dominadas condicionan directamente la elección de stack, el uso de servicios gestionados y la complejidad aceptable.
- **Faltante:** Competencias técnicas del PO, tecnologías preferidas o dominadas, estándares de código y documentación, y tiempos objetivo para cambios típicos (agregar un parámetro, un conector o una categoría).
- **Estado:** ⚠️ **IMPORTANTE**
- **Recomendación:** Que el PO documente su perfil técnico y sus preferencias de lenguaje y framework. Definir estándares de código antes del desarrollo (workflow *generar-estandares-codigo*).

#### **GAP-I002: Estrategia de pruebas y evaluación de la IA (I2.4 — 8/18)**
- **Impacto:** Afecta la estimación, el pipeline de CI y la capacidad de detectar regresiones de precisión cuando cambian el modelo o el prompt (NFR-CAL-001 ≥90 %).
- **Faltante:** Estrategia por niveles (unitarias, integración, e2e, contrato), cobertura objetivo, entornos de prueba, mocks y fixtures de Socrata y retail, y un arnés de regresión del extractor IA sobre la muestra validada de D4-4.
- **Estado:** ⚠️ **IMPORTANTE**
- **Recomendación:** Definir la estrategia de pruebas en la arquitectura detallada. Convertir las 228 filas validadas de D4-4 en un *golden dataset* versionado para la evaluación continua del extractor.

#### **GAP-I003: Capacidades del equipo de desarrollo y dedicación (I3.2 — 9/18)**
- **Impacto:** Es el subcriterio importante de mayor impacto (3). Afecta de forma significativa la estimación de esfuerzo y tiempo, la elección entre servicios gestionados y autogestionados, y el riesgo de operador único.
- **Faltante:** Tamaño y composición del equipo (humano, agéntico o mixto), dedicación del PO repartida entre desarrollo, revisión humana, carga manual y operación, y capacidad de soporte.
- **Estado:** ⚠️ **IMPORTANTE**
- **Recomendación:** Que el PO declare la composición del equipo y las horas por semana disponibles por actividad. Arquitectura debe priorizar servicios gestionados y automatización operativa para reducir carga.

#### **GAP-I004: Procedimientos de aprovisionamiento, despliegue y políticas de datos (I3.4 — 10/18)**
- **Impacto:** Afecta la estimación (pipeline y entornos) y la selección del proveedor IA y de la región de nube.
- **Faltante:** CI/CD, IaC, promoción entre entornos, rollback, ventana de mantenimiento, política de residencia de datos y aval para que el proveedor IA procese documentos públicos con datos personales.
- **Estado:** ⚠️ **IMPORTANTE**
- **Recomendación:** Que el PO decida sobre la residencia de datos y el uso de proveedores IA externos. Arquitectura define entornos, pipeline y estrategia de despliegue y rollback mediante ADRs.

#### **GAP-I005: Modelo de datos lógico consolidado (I4.1 — 15/18, 🔍 INFERIBLE)**
- **Impacto:** Es la base del diseño de persistencia, versionado (señales, configuración, instantáneas) y trazabilidad de evidencia. Si se dispersa, hay riesgo de inconsistencias entre HUs.
- **Faltante:** Modelo canónico y mapa de dependencias: contrato/orden ↔ ítem ↔ documento/evidencia ↔ normalización ↔ emparejamiento ↔ observación ↔ benchmark ↔ señal versionada ↔ caso/instantánea. Hoy está disperso en FRs y 213 asunciones.
- **Estado:** ⚠️ **IMPORTANTE (se puede inferir)**
- **Recomendación:** Arquitectura deriva el modelo de datos lógico de los FRs y las asunciones, junto con la máquina de estados del ítem a lo largo del pipeline (observación de I1.4), y lo valida con el PO.

#### **GAP-I006: Clasificación de sensibilidad y cifrado (I4.4 — 12/18)**
- **Impacto:** Condiciona la selección del proveedor IA/OCR y del almacenamiento, y la configuración de cifrado.
- **Faltante:** Clasificación formal por niveles de sensibilidad, cifrado en reposo por clasificación y tratamiento de los datos personales contenidos en documentos enviados al proveedor IA (DPA, retención, región).
- **Estado:** ⚠️ **IMPORTANTE**
- **Recomendación:** Definir una clasificación de 3 niveles (público oficial / interno / personal-sensible) con cifrado en reposo por defecto. Seleccionar un proveedor IA con política de no retención y no entrenamiento.

#### **GAP-I007: Patrones de integración y orquestación (I5.1 — 15/18)**
- **Impacto:** Afecta la selección de patrones (scheduler, colas, workers), la resiliencia del pipeline y el cambio de proveedor IA.
- **Faltante:** Patrón de orquestación de jobs (scheduler, colas, workers, idempotencia, reprocesos), contrato de integración con IA/OCR (API, rate limits, batch, abstracción de proveedor), estrategia ante cambios de esquema de Socrata y verificación de la relación ítem↔orden de TVEC (A-014).
- **Estado:** ⚠️ **IMPORTANTE**
- **Recomendación:** Arquitectura define el patrón de orquestación y una capa de abstracción del proveedor IA (puerto/adaptador). Agregar validación de esquema en la ingesta y cerrar A-014 con una verificación técnica.

### **ℹ️ GAPS MENORES (Refinamiento posterior)**

| Código | Subcriterio | Puntaje | Gap | Recomendación |
|---|---|---|---|---|
| GAP-M001 | M1.2 Formatos de intercambio | 10/18 | Sin esquemas formales de API interna ni contrato JSON de salida del extractor IA; sin catálogo de códigos de error | Definir en el diseño detallado (OpenAPI + JSON Schema del extractor) |
| GAP-M002 | M1.3 Textos de interfaz | 5/18 | Sin tooltips ni ayuda contextual; sin i18n; onboarding sin contenido | Definir con los mockups de D5 |
| GAP-M003 | M2.1 Features opcionales | 5/18 | Sin lista consolidada de mejoras UX opcionales o personalización | Registrar en backlog Post-MVP |
| GAP-M004 | M2.4 Mejoras incrementales UX | 5/18 | Sin refinamientos visuales ni micro-optimizaciones de flujo | Resolver con UX/UI tras D5 |
| GAP-M005 | M3.1 Procedimientos operacionales | 8/18 | Sin verificación de restauración, rotación de secretos, depuración de temporales ni runbooks | Incluir runbooks mínimos en la arquitectura detallada |
| GAP-M006 | M3.2 Manuales de usuario | 2/18 | Sin estructura de documentación de usuario ni tutoriales | Onboarding mínimo en producto (coherente con piloto de 3–5 analistas) |
| GAP-M007 | M3.3 Procesos de soporte | 4/18 | Sin niveles de soporte, escalamiento ni métricas de atención | Definir el SLA interno de atención de reportes de error |
| GAP-M008 | M3.4 Configuraciones administrativas | 10/18 | Sin configuración por ambiente ni niveles o formato de log | Definir con la estrategia de entornos (GAP-I004) |
| GAP-M009 | M4.1 Elementos estéticos | 1/18 | Sin paleta, tipografía, iconografía ni codificación visual de confianza o estados | Resolver en el levantamiento UI (D5) |
| GAP-M010 | M5.1 Optimizaciones específicas | 3/18 | Sin estrategia de caché, índices ni precálculo de agregados | Resolver en implementación (volumen bajo) |
| GAP-M011 | M5.2 Configuraciones de performance | 10/18 | Sin pool de conexiones ni ajustes de memoria de workers OCR o multimodal | Definir con el stack elegido |

> ℹ️ **Nota metodológica:** la fórmula multiplica por el Impacto Arquitectónico. Por eso los subcriterios menores (impacto 1–2) obtienen puntajes bajos aunque estén bien documentados (p. ej. M2.3 CUMPLE = 6/18). El puntaje refleja **relevancia × calidad**, no solo calidad documental.

### **📋 Evaluación Detallada por Subcriterio**

*Leyenda: P = Presencia (0–2) · C = Completitud (0–2) · Cl = Claridad (0–2) · Imp = Impacto arquitectónico (1–3)*

#### 🚨 Criterios Críticos (C1–C6) — 287/360

| Subcriterio | Estado | P | C | Cl | Imp | Puntaje | Categoría Gap | Evidencia | Gap Identificado |
|---|---|---|---|---|---|---|---|---|---|
| **C1.1** | ✅ CUMPLE | 2 | 1 | 2 | 3 | **15**/18 | NINGUNO | Analista y Administrador (=PO/Revisor) con matriz de permisos (FR-086, A-165, A-175, A-176), acceso por invitación (FR-083); 3-5 analistas, 1 admin, 20 concurrentes (NFR-PER-003); dispositivos y navegadores (NFR-USA-001/002); perfil técnico por segmento H1-H4; patrones de uso en J1-J3 | Frecuencia real de uso y segmento adoptante sin validar (D2/D5); 0-2 contactos |
| **C1.2** | ✅ CUMPLE | 2 | 2 | 2 | 2 | **12**/18 | NINGUNO | Problema articulado (revisión manual proceso por proceso); 4 objetivos priorizados; KPIs a 3 meses cuantificados (NFR-CAL-001..008); criterio técnico de extremo a extremo; fórmulas A-203..211 | Valor económico no cuantificado por decisión (monetización no decidida); línea base D2 y precisión D4-4 pendientes |
| **C1.3** | ✅ CUMPLE | 2 | 2 | 2 | 3 | **18**/18 | NINGUNO | Flujo de extremo a extremo SECOP→identificación→documentos→extracción→normalización→comparación→señal→evidencia; 3 journeys paso a paso; 100 FRs; 113 HUs; actores e interacciones (FR-090, FR-070, FR-069, FR-077..082) | especificacion.md vacíos; sin mockups (D5) |
| **C1.4** | ⚠️ PARCIAL | 2 | 1 | 2 | 3 | **15**/18 | NINGUNO | ~355 contratos SECOP II, 1.146 líneas TVEC, 930 órdenes, ~6.000 unidades (D1 §8); 21,5 docs/proceso, ~8 priorizados (D4, FR-019); retail <1.000 solicitudes/semana (D6); ingesta diaria, retail semanal (NFR-DAT-001/003); histórico ≤7 días (NFR-DAT-004) | Sin TPS, picos, estacionalidad (ciclos fiscales) ni proyección de crecimiento (inferible: volumen muy bajo) |
| **C2.1** | ✅ CUMPLE | 2 | 1 | 2 | 3 | **15**/18 | NINGUNO | ≤3 s p95 búsquedas y ficha (NFR-PER-001/002); 20 concurrentes (NFR-PER-003); extracción ≤5 min p95 (NFR-PER-004); ≤48 h / ≤72 h (NFR-DAT-002); histórico ≤7 días; CSV asíncrono (A-104) | Sin TPS explícito ni tiempo de recálculo de benchmarks/señales ni throughput de reprocesamiento IA |
| **C2.2** | ✅ CUMPLE | 2 | 2 | 2 | 3 | **18**/18 | NINGUNO | 99 % mensual (NFR-DIS-001); backup diario, 30 días, RPO/RTO ≤24 h (NFR-DIS-002); backup de datos irreconstruibles (NFR-DIS-003); 3 reintentos (NFR-DAT-005); alerta ≤1 h (NFR-OBS-002); horarios de jobs (A-007) | Horario de operación implícito (24/7) y ventana de mantenimiento no declarados; no son SLA |
| **C2.3** | ⚠️ PARCIAL | 1 | 1 | 1 | 2 | **6**/18 | NINGUNO | Roadmap post-MVP cualitativo (nuevas categorías, más años, agente, RAG, SECOP I +240 contratos); NFR-EVO-001/002; alcance nacional sin expansión geográfica | Crecimiento a 1-3 años no cuantificado; sin límites de escalabilidad definidos |
| **C2.4** | ✅ CUMPLE | 2 | 1 | 2 | 3 | **15**/18 | NINGUNO | Ley 1581/2012 (NFR-CUM-001); sensibles excluidos (FR-006, NFR-SEG-005, A-002, A-003); TLS 1.2+, hash adaptativo, sesión 30 min, aislamiento de casos, secretos, auditoría 12 meses, OWASP (NFR-SEG-001..008); bloqueo por intentos (A-171) | Cifrado en reposo, residencia de datos y aval de procesamiento por proveedor IA sin definir |
| **C3.1** | ✅ CUMPLE | 2 | 2 | 2 | 3 | **18**/18 | NINGUNO | Socrata datos.gov.co (jbjy-vk9h; Archivos A-027; TVEC usqp-5nsn, 3hdv-smhz, rgxm-mmea); community.secop.gov.co (A-028); Alkosto y Falabella (D6); limitaciones documentadas (D1 §7, A-012, A-014, robots/ToS); sin legacy | Límites exactos de la API Socrata sin verificar; relación ítem↔orden TVEC sin verificar (A-014) |
| **C3.2** | ✅ CUMPLE | 2 | 2 | 2 | 3 | **18**/18 | NINGUNO | Datasets oficiales como fuente de verdad con identificador, URL (FR-008), fecha de corte (FR-009, A-005), copia con hash (FR-024, A-043); base propia de observaciones insert-only (FR-041, FR-053, A-087); sincronización incremental (FR-003, A-007, A-011); flujo mapeado en dominios 1-8 | Sin estrategia ante cambios de esquema ni contrato de interfaz formal |
| **C3.3** | ⚠️ PARCIAL | 2 | 1 | 2 | 3 | **15**/18 | NINGUNO | IA multimodal/OCR (FR-023, FR-025; multimodal indispensable en 52 % de contratos, D4); correo (FR-083, FR-085, A-189); app token Socrata (NFR-SEG-006); costo IA ~USD 0,05/contrato (D4 §7); IA desactivable (FR-033, NFR-EVO-003) | Proveedor LLM/OCR, correo y servicios cloud no seleccionados; sin niveles de servicio, rate limits ni batch del proveedor IA |
| **C4.1** | ⚠️ PARCIAL | 2 | 1 | 2 | 3 | **15**/18 | NINGUNO | Web por URL; híbrida permitida; stack no cerrado; Azure/Foundry solo justificado; infraestructura existente reutilizable si se justifica; entornos de validación mencionados (A-018, A-105) | Sin estrategia/proveedor cloud, ambientes (dev/staging/prod) ni región/residencia de datos |
| **C4.2** | ✅ CUMPLE | 2 | 2 | 2 | 2 | **12**/18 | NINGUNO | Web responsive desktop-first sin app nativa ni IE; 1366x768 / 768 / 360 px (NFR-USA-001); 2 últimas versiones (NFR-USA-002); WCAG 2.1 AA (NFR-USA-004); ≤3 clics (NFR-USA-003) | Ninguno relevante |
| **C4.3** | ✅ CUMPLE | 2 | 1 | 2 | 3 | **15**/18 | NINGUNO | Ley 1581 (NFR-CUM-001, A-166, FR-087, A-169); Leyes 1712, 1150, 1480; robots.txt, ritmo, User-Agent, cero evasión, ToS (NFR-CUM-002..006, A-105); lenguaje no acusatorio (FR-064, NFR-CUM-007, A-134); auditoría (FR-094, NFR-SEG-007, A-213) | ToS retail pendientes (bloquea captura en producción); aval jurídico del IVA retail; conformidad del tratamiento por proveedor IA |
| **C4.4** | ⚠️ PARCIAL | 2 | 1 | 2 | 2 | **10**/18 | NINGUNO | Infraestructura existente inventariada (Railway, PostgreSQL, Google; ~COP 100.000/mes); producto independiente; drivers de costo a identificar; operador único + agentes | Sin límites de capacidad/red/seguridad de Railway, techo de costo mensual ni capacidad de soporte/on-call |
| **C5.1** | ✅ CUMPLE | 2 | 2 | 2 | 3 | **18**/18 | NINGUNO | 95 FRs MVP en 8 épicas; fuera de alcance y exclusiones explícitas (PRD §5, epicas.md); límite de categoría (FR-013); entradas y salidas definidas | Sin diagrama C4-L1 (inferible) |
| **C5.2** | ✅ CUMPLE | 2 | 2 | 2 | 2 | **12**/18 | NINGUNO | Sistema nuevo sin acoplamiento con Express App; fuentes solo consumidas; separación ingesta/extracción (FR-003), adquisición/uso (Adenda 2), base determinística (FR-033, A-065), conectores aislados (NFR-EVO-001) | Decidir qué capacidades administrativas tienen UI (Dominio 12) |
| **C5.3** | ✅ CUMPLE | 2 | 1 | 2 | 2 | **10**/18 | NINGUNO | MVP = ÉPICA-001..008 (Críticas/Alta), ÉPICA-009 Post-MVP; validaciones bloqueantes en PRD §7 (D4-4, INV-01, D5, D2, ToS); priorización del flujo explorar→señal→evidencia→caso | Sin mapa explícito de dependencias entre épicas/HUs; versiones futuras sin incrementos detallados |
| **C6.1** | 🔍 INFERIBLE | 2 | 1 | 2 | 3 | **15**/18 | NINGUNO | Entidades extraíbles de FRs: contrato/orden, ítem, documento, dato extraído con evidencia, producto normalizado, emparejamiento, observación, benchmark, señal, caso/nota/instantánea, usuario/rol, configuración, auditoría; reglas de consistencia (A-087, A-127, NFR-DAT-005, A-057, A-193, A-048) | Sin modelo conceptual/lógico consolidado |
| **C6.2** | ⚠️ PARCIAL | 2 | 1 | 2 | 3 | **15**/18 | NINGUNO | Registros cuantificados (355 contratos, 1.146 líneas, 930 órdenes, ~8 copias/proceso; D4: 190 docs y 1.234 páginas en 50 contratos); límites por archivo (A-036, A-040, A-101); retención por tipo (NFR-SEG-007, NFR-OBS-003, NFR-DIS-002, A-043, A-089) | Sin estimación en GB de documentos e imágenes ni crecimiento de observaciones y señales (estimable: pocos GB) |

#### ⚠️ Criterios Importantes (I1–I6) — 190/360

| Subcriterio | Estado | P | C | Cl | Imp | Puntaje | Categoría Gap | Evidencia | Gap Identificado |
|---|---|---|---|---|---|---|---|---|---|
| **I1.1** | ✅ CUMPLE | 2 | 2 | 2 | 2 | **12**/18 | NINGUNO | 3 User Journeys paso a paso con duración (PRD §3); 113 HUs con 11-14 escenarios con flujos alternos y bordes (ej. HU-059, HU-022); qa.md con precondiciones, datos y casos positivos/negativos/permisos; INVEST y DoD | ÉPICA-009 sin HUs; especificacion.md vacíos; HUs en Borrador (PO); sin mockups (D5) |
| **I1.2** | ✅ CUMPLE | 2 | 2 | 1 | 2 | **10**/18 | NINGUNO | Falla IA (HU-022 E13/RN-15: 300 s, 3 reintentos); API/descarga (NFR-DAT-005, A-006, A-029); bloqueo retail (FR-047, A-110); Benchmark 2 (A-125); bitácora distingue error técnico vs calidad (A-017); mensajes (A-171, A-183, A-153); recuperación (FR-088, A-187, A-188, A-048) | Sin catálogo transversal de errores ni estrategia común de presentación/recuperación e idempotencia de jobs |
| **I1.3** | ✅ CUMPLE | 2 | 2 | 2 | 2 | **12**/18 | NINGUNO | Reglas con condiciones (FR-099 seis condiciones, FR-100/FR-013, FR-057/A-049/A-120/A-122, FR-058/059, FR-063/A-126); rangos (A-057, A-084, A-101, A-104, A-167); validaciones multicampo (A-055, A-015, A-074, A-078) | Ninguno relevante para arquitectura |
| **I1.4** | ✅ CUMPLE | 2 | 2 | 1 | 2 | **10**/18 | NINGUNO | Estados por entidad: clasificación (FR-015, A-023), aceptación (A-053/054), señal Vigente/No vigente/Retenida (HU-059 RN-08, A-127, A-131), reportes (A-136), etapas (FR-075, A-159), fuentes (A-185, A-188), observaciones (A-087), invitaciones (A-162..164); permisos y auditoría (FR-016, FR-032, A-135, A-175, FR-094, A-213) | Sin máquina de estados consolidada del ítem a lo largo del pipeline (inferible, dispersa en 5 épicas) |
| **I2.1** | ⚠️ PARCIAL | 2 | 1 | 2 | 1 | **5**/18 | NINGUNO | NFR-USA-001..004 (breakpoints, navegadores, ≤3 clics, WCAG 2.1 AA); perfil técnico por segmento H1-H4; formatos de presentación (A-132, A-152, A-156); onboarding mínimo | Sin tiempo máximo de aprendizaje ni criterio formal de satisfacción (SUS); segmento no validado (D2/D5) |
| **I2.2** | ⚠️ PARCIAL | 1 | 1 | 1 | 2 | **6**/18 | IMPORTANTE | MVP operable por una persona apoyada en agentes (Brief supuesto 6); PO revisor técnico; stack no cerrado; NFR-EVO-001..003; configuración versionada (A-193) | Sin competencias técnicas del mantenedor, tecnologías preferidas/dominadas, estándares de código ni tiempos objetivo de cambio; condiciona stack y servicios gestionados |
| **I2.3** | ✅ CUMPLE | 2 | 2 | 1 | 2 | **10**/18 | NINGUNO | KPIs de negocio (FR-091, FR-093, A-203..211); costos (FR-034, NFR-OBS-001, A-059, A-212); bitácora (FR-007, A-017); alertas (NFR-OBS-002, A-185, A-189); auditoría (FR-094, NFR-SEG-007, A-213); logs (NFR-OBS-003) | Sin niveles de logging por componente, monitoreo técnico (APM, p95, 5xx, workers) ni umbrales de alerta técnicos adicionales (costo IA, cola de extracción) |
| **I2.4** | ⚠️ PARCIAL | 2 | 1 | 1 | 2 | **8**/18 | IMPORTANTE | 113 qa.md con casos y matriz de cobertura; autorización 100 % endpoints (NFR-SEG-004); términos prohibidos verificables (NFR-CUM-007); OWASP (NFR-SEG-008); valores testigo fuera de prod (A-018); validación IA ≥50 docs / D4-4 (NFR-CAL-001, FR-092, A-202) | Sin estrategia por niveles (unit/integración/e2e/contrato), cobertura objetivo, entornos, mocks de Socrata/retail ni arnés de regresión del extractor IA |
| **I3.1** | ✅ CUMPLE | 2 | 1 | 2 | 2 | **10**/18 | NINGUNO | Infraestructura existente Express App (Railway, PostgreSQL, Google; ~COP 100.000/mes) reutilizable sin acoplamiento (CONTEXTO §12); tecnología no cerrada (CONTEXTO §13, Brief); Azure/Foundry solo justificado (PRD §5); híbrida permitida | Sin detalle de versiones/capacidad de Railway y PostgreSQL existentes (estándares corporativos no aplican) |
| **I3.2** | ⚠️ PARCIAL | 1 | 1 | 1 | 3 | **9**/18 | IMPORTANTE | Ejecutores = agentes del Método Ceiba, PO decide y revisa (Brief); operable por una persona (supuesto 6); PO es Administrador y Revisor (P-08); sin jurídico permanente | Sin tamaño/composición del equipo, dedicación del PO (desarrollo vs revisión vs carga manual vs operación), competencias ni capacidad de soporte/on-call |
| **I3.3** | ⚠️ PARCIAL | 2 | 1 | 2 | 2 | **10**/18 | NINGUNO | Sin tope de presupuesto pero identificar drivers de costo (Brief); preferencia por costo bajo (~COP 100.000/mes actual); costo IA ~USD 0,05/contrato (D4 §7); sin créditos Azure; costo mensual por componente (NFR-OBS-001) | Sin techo de costo mensual ni análisis de licenciamiento (OCR/IA, librerías RAR) |
| **I3.4** | ⚠️ PARCIAL | 2 | 1 | 2 | 2 | **10**/18 | IMPORTANTE | Seguridad NFR-SEG-001..008; Ley 1581 (NFR-CUM-001, FR-087, A-166, A-169); lista blanca (FR-006, A-002, A-003); reglas de fuentes (NFR-CUM-002..006); revisión de código anti-evasión (NFR-CUM-005); aprovisionamiento de administradores (A-165) | Sin procedimientos de CI/CD, IaC, promoción, rollback ni ventana de mantenimiento; sin política de residencia de datos ni aval de procesamiento por proveedor IA |
| **I4.1** | 🔍 INFERIBLE | 2 | 2 | 1 | 3 | **15**/18 | IMPORTANTE | Atributos por tipo: ítem (FR-025, A-044, A-047), esquema normalizado (FR-035), observación (FR-042, A-084..086), señal (FR-065, HU-059 RN-07), evidencia (FR-024, A-040, A-041), instantánea (FR-081, A-178), configuración (A-193), auditoría (A-213); formatos de intercambio (SoQL/JSON, multiformato, CSV RFC 4180, schema.org); identificadores (A-040, A-076, A-039) | Sin modelo de datos lógico/canónico consolidado ni mapa de dependencias entre entidades (inferible pero disperso en 213 asunciones) |
| **I4.2** | ⚠️ PARCIAL | 2 | 1 | 1 | 2 | **8**/18 | NINGUNO | ~355 contratos SECOP II, ~1.150 líneas TVEC, 930 órdenes (D1, NFR-DAT-004); 21,5 docs/proceso, 34,9 % escaneadas, 200 MB/archivo (D4, A-036); 332 URLs TV Alkosto (D6); sin purga (A-089, A-043, A-127) | Sin volumen en GB ni proyección de crecimiento de observaciones, señales, instantáneas y auditoría; sin política de archivado (estimable con D4) |
| **I4.3** | ⚠️ PARCIAL | 2 | 1 | 2 | 2 | **10**/18 | NINGUNO | Retención por tipo (NFR-SEG-007, NFR-OBS-003, NFR-DIS-002, A-089, A-043, A-127, A-182); backup RPO/RTO ≤24 h (NFR-DIS-003); migración = carga inicial del histórico (FR-002, NFR-DAT-004, HU-001) | Sin política de retención/supresión de datos personales de usuarios (Ley 1581), de documentos no usados ni prueba de restauración |
| **I4.4** | ⚠️ PARCIAL | 2 | 1 | 1 | 3 | **12**/18 | IMPORTANTE | Exclusión de sensibles (FR-006, NFR-SEG-005, A-002, A-018); documento persona natural oculto (A-003); control de acceso (FR-082, NFR-SEG-004, A-183, A-090, A-133, A-155, A-043); minimización hacia la IA (A-024, A-168); hash de contraseñas (NFR-SEG-002) | Sin clasificación formal por niveles ni cifrado en reposo por clasificación; sin tratamiento definido de datos personales enviados al proveedor IA (DPA, retención, región) ni residencia de datos |
| **I5.1** | ⚠️ PARCIAL | 2 | 2 | 1 | 3 | **15**/18 | IMPORTANTE | REST SoQL con app token, descarga de dominio oficial en lista blanca (A-028), sitemaps/schema.org (D6), correo (A-189); batch incremental con marca de agua (A-007), extracción asíncrona (NFR-PER-004), desacople ingesta/IA (FR-003), conectores retail (NFR-EVO-001), canal manual/CSV (FR-052); reintentos (NFR-DAT-005, A-006, A-029), suspensión (FR-047, A-110), ritmo (NFR-CUM-003, A-036) | Sin patrón de orquestación de jobs (scheduler, colas, workers, idempotencia), contrato con servicio IA/OCR ni estrategia ante cambios de esquema Socrata; relación ítem TVEC↔orden sin verificar (A-014) |
| **I5.2** | ⚠️ PARCIAL | 1 | 1 | 1 | 1 | **3**/18 | NINGUNO | Web HTTPS responsive (NFR-USA-001); límites de descarga (A-036); ritmo retail (NFR-CUM-003); degradación funcional (FR-060, FR-033, NFR-DAT-005) | Sin estimación de ancho de banda, restricciones de conectividad ni redundancia (impacto bajo por volumen piloto) |
| **I6.1** | ⚠️ PARCIAL | 2 | 1 | 2 | 2 | **10**/18 | NINGUNO | Nueva fuente por conector (NFR-EVO-001), nueva categoría por configuración (NFR-EVO-002), IA desactivable (NFR-EVO-003, FR-033, A-058); configuración versionada (FR-089, A-193, A-196); tablas configurables (A-021, A-062, A-066); evolución Post-MVP identificada (PRD §5) | Sin estrategia de versionado de API, despliegue sin downtime ni puntos de extensión para incremento agéntico (tool calling/MCP) |
| **I6.2** | ✅ CUMPLE | 2 | 1 | 2 | 1 | **5**/18 | NINGUNO | Greenfield (Brief); Express App independiente (PRD §5); única migración = carga inicial de 3 años (FR-002, NFR-DAT-004 ≤7 días, HU-001, A-013) con relanzamiento (A-187) | Sin plan de rollback de despliegues ni de reprocesamientos masivos; sin criterio de conciliación de la carga inicial |

#### ℹ️ Criterios Menores (M1–M5) — 105/288

| Subcriterio | Estado | P | C | Cl | Imp | Puntaje | Categoría Gap | Evidencia | Gap Identificado |
|---|---|---|---|---|---|---|---|---|---|
| **M1.1** | ✅ CUMPLE | 2 | 2 | 2 | 1 | **6**/18 | NINGUNO | Validaciones de campo con rangos, formatos y mensajes exactos (A-084, A-167, A-168, A-177, A-182, A-057, A-076, A-025; HU-049 RN-03/04; validación entre campos A-095) | Ninguno relevante; algunas HU en Borrador |
| **M1.2** | ⚠️ PARCIAL | 2 | 1 | 2 | 2 | **10**/18 | MENOR | CSV carga detallada (A-104, HU-049 RN-01..08); campos Socrata (D1 §3/§7); formato id comprimidos (A-040); GTIN-14 (A-076); catálogos cerrados (A-052, A-160); plantilla validación (A-202); auditoría exportable (A-213) | Sin esquemas formales de API interna ni contrato JSON de salida del extractor IA; sin catálogo unificado de códigos de error |
| **M1.3** | ✅ CUMPLE | 2 | 1 | 2 | 1 | **5**/18 | MENOR | Textos exactos de UI en HU-063 RN-02/05/07, HU-086, A-183, A-157, A-139, A-144; lista de términos prohibidos (NFR-CUM-007, A-134); copy en español | Sin tooltips/ayuda contextual; sin i18n (solo español implícito); contenido del onboarding sin definir |
| **M1.4** | ✅ CUMPLE | 2 | 2 | 2 | 2 | **12**/18 | NINGUNO | Parámetros con valor inicial y rango configurable (A-006, A-007, A-034, A-036, A-040, A-042, A-051, A-130, A-162, A-171, A-173, A-195; A-192 límites de cordura; A-193 configuración versionada) | Ninguno; umbral de aceptación automática pendiente de D4-4 por decisión explícita (A-194) |
| **M2.1** | ✅ CUMPLE | 2 | 1 | 2 | 1 | **5**/18 | MENOR | Candidatas Post-MVP FR-095..098 y FR-026 pospuesta (ÉPICA-009); exclusiones A-181, A-169; atajos A-143, A-158 | Sin lista consolidada de mejoras UX opcionales ni personalización avanzada (vistas guardadas, favoritos) |
| **M2.2** | ✅ CUMPLE | 2 | 2 | 2 | 2 | **12**/18 | NINGUNO | KPIs FR-091 (HU-106..110, A-203..211, A-205), costos NFR-OBS-001 (HU-111, A-212), cola de revisión FR-090 (A-198), auditoría HU-113 (A-213), estado de fuentes HU-098, bitácora FR-007, filtros/paginación FR-071..073 | Exportación de expediente FR-098 Post-MVP; sin exportación de resultados de exploración (decisión de alcance) |
| **M2.3** | ✅ CUMPLE | 2 | 2 | 2 | 1 | **6**/18 | NINGUNO | Correos de falla con asunto exacto, ≤60 min, reintentos y destinatarios (HU-100, NFR-OBS-002, A-189); suspensión retail (A-110, A-190); invitación (HU-084); restablecimiento (A-174); aviso de sesión (A-173) | Ninguno relevante; alertas proactivas al Analista fuera de alcance por decisión |
| **M2.4** | ✅ CUMPLE | 2 | 1 | 2 | 1 | **5**/18 | MENOR | WCAG 2.1 AA (NFR-USA-004), ≤3 clics (NFR-USA-003), estado en URL (A-151), redirección post-login (A-172), tabla equivalente a gráficos (A-156), scroll horizontal móvil (HU-063 RN-08) | Sin listado de refinamientos visuales opcionales; mockups D5 pendientes |
| **M3.1** | ⚠️ PARCIAL | 1 | 1 | 2 | 2 | **8**/18 | MENOR | Backup diario 30 días, RPO/RTO ≤24 h (NFR-DIS-002/003); auditoría 12 meses; logs 30 días; sin purga (A-089, A-043); relanzamiento de ingesta (HU-099, A-187); reactivación de fuentes (A-188); J3 operación semanal | Sin procedimientos de verificación de restauración, rotación de secretos, depuración de temporales ni runbooks |
| **M3.2** | ⚠️ PARCIAL | 1 | 0 | 1 | 1 | **2**/18 | MENOR | Onboarding mínimo en producto (Brief, PRD §5); plantilla CSV con ejemplo (HU-049); correo de invitación explicativo (HU-084) | Sin estructura de documentación de usuario, tutoriales ni guías de resolución (coherente con piloto de 3-5 analistas) |
| **M3.3** | ⚠️ PARCIAL | 1 | 1 | 2 | 1 | **4**/18 | MENOR | Reporte de errores con catálogo y estados (FR-070, HU-067/068, A-136); PO como único Administrador/Revisor (P-08); cola de revisión (FR-090, A-197) | Sin niveles de soporte, escalamiento, scripts ni métricas de atención |
| **M3.4** | ⚠️ PARCIAL | 2 | 1 | 2 | 2 | **10**/18 | MENOR | Retención de logs configurable (NFR-OBS-003); secretos (NFR-SEG-006); IA desactivable (NFR-EVO-003); configuración versionada (FR-089, A-193); frecuencias (A-195); entornos de validación/producción mencionados (A-018, A-105); enmascaramiento en auditoría (A-213) | Sin configuración por ambiente ni niveles/formato de log |
| **M4.1** | ❌ NO CUMPLE | 0 | 0 | 1 | 1 | **1**/18 | MENOR | Solo indirecto: contraste WCAG (NFR-USA-004), gráfico de puntos (A-156), etiquetas visibles (HU-063, HU-049) | Sin paleta, tipografía, iconografía, codificación visual de confianza/estados ni animaciones (esperable antes de D5) |
| **M4.2** | ✅ CUMPLE | 2 | 2 | 2 | 1 | **6**/18 | NINGUNO | Breakpoints 1366x768 / 768 / 360 px (NFR-USA-001); 2 últimas versiones de navegadores (NFR-USA-002); adaptación de tablas en móvil (HU-063 RN-08) | Sin ajustes de layout por vista para móvil (detalle UI) |
| **M5.1** | ⚠️ PARCIAL | 1 | 1 | 1 | 1 | **3**/18 | MENOR | Carga incremental (FR-003), ~8 docs priorizados (FR-019), páginas relevantes (Riesgo 5), no reextraer (A-030), límite visual (A-042), lastmod de sitemaps (A-109), dedupe SHA-256 (A-039) | Sin estrategia de caché de consultas, índices ni precálculo de agregados (se resuelve en implementación por bajo volumen) |
| **M5.2** | ⚠️ PARCIAL | 2 | 1 | 2 | 2 | **10**/18 | MENOR | Timeouts definidos: API 60 s (A-006), descarga 120 s (A-029), extracción 300 s (A-046), UI 15 s (A-153), CSV asíncrono (A-104), paralelismo (A-036), ritmo (NFR-CUM-003) | Sin pool de conexiones BD, ajustes de memoria de workers OCR/multimodal ni parámetros de red |

---

## 🔢 Cálculo Objetivo del Nivel de Completitud (v1.0)

### **🎯 Metodología de Evaluación Objetiva**

**Base de Evaluación:**
- **Total de subcriterios evaluados:** 56 distribuidos en 3 categorías
- **Sistema de puntuación:** (Presencia + Completitud + Claridad) × Impacto Arquitectónico
- **Rango por criterio:** 3-18 puntos
- **Ponderación por importancia:** Críticos (3.0) + Importantes (2.0) + Menores (1.0)

### **📋 Tabla de Puntuaciones Detalladas**

La siguiente tabla muestra el cálculo transparente y objetiva del nivel de completitud basado en la evaluación sistemática de 56 subcriterios distribuidos en las tres categorías de importancia arquitectónica.

| Categoría         | Subcriterios | Puntuación Obtenida            | Puntuación Máxima | % Categoría                 | Peso    | Contribución                 |
| ----------------- | ------------ | ------------------------------ | ----------------- | --------------------------- | ------- | ---------------------------- |
| **🚨 Críticos**    | 20           | 287/360    | 360               | 79.7%    | 3.0     | 39.9    |
| **⚠️ Importantes** | 20           | 190/360 | 360               | 52.8% | 2.0     | 17.6 |
| **ℹ️ Menores**     | 16           | 105/288     | 288               | 36.5%     | 1.0     | 6.1     |
| **🎯 TOTAL**       | **56**       | **582/1008**  | **1008**          | **63.5%**    | **6.0** | **63.5**                     |

### **🔢 Fórmula de Cálculo Aplicada**

```
Puntuación_Ponderada_Total = 
    (Puntuación_Críticos × 3.0) + 
    (Puntuación_Importantes × 2.0) + 
    (Puntuación_Menores × 1.0)

Nivel_Completitud = Puntuación_Ponderada_Total / (3.0 + 2.0 + 1.0) × 100

Readiness_Score = 63.5%
```

### **📈 Distribución de Gaps por Categoría**

**Conteo de Gaps Identificados:**
```
🚨 GAPS CRÍTICOS:    3/20 subcriterios (15.0%)
⚠️ GAPS IMPORTANTES: 18/20 subcriterios (90.0%)  
ℹ️ GAPS MENORES:     16/16 subcriterios (100.0%)
```

### **🎯 Determinación del Estado General**

**Puntuación Final:** 63.5%  
**Estado Calculado:** ⚠️ PARCIALMENTE APTO - Requiere mejoras importantes

**Criterios de Determinación Automática:**
- ✅ **APTO PARA ARQUITECTURA:** ≥85% Y 0 gaps críticos
- ⚠️ **APTO CON RESERVAS:** ≥70% Y ≤2 gaps críticos  
- ⚠️ **PARCIALMENTE APTO:** ≥50%
- ❌ **NO APTO:** <50%

### **📊 Visualización de Preparación por Dimensión**

```
Criterios Críticos    [████████▒▒] 79.7%
Criterios Importantes [█████▒▒▒▒▒] 52.8%  
Criterios Menores     [████▒▒▒▒▒▒] 36.5%
────────────────────────────────────────────
COMPLETITUD GENERAL   [██████▒▒▒▒] 63.5%
```

### **🔍 Validación de Resultados**

**Criterios de Validación del Cálculo:**
1. ✅ Todos los 56 subcriterios fueron evaluados sistemáticamente
2. ✅ Se aplicó la matriz de puntuación objetiva (Presencia + Completitud + Claridad) × Impacto
3. ✅ La ponderación por importancia arquitectónica fue aplicada correctamente
4. ✅ Los conteos de gaps son consistentes con las puntuaciones obtenidas
5. ✅ El estado general se determinó siguiendo los criterios establecidos

**Transparencia del Proceso:**
- Metodología basada en criterios objetivos documentados en el paso 0.4 del workflow
- Puntuaciones calculadas matemáticamente sin interpretación subjetiva
- Fórmulas y criterios de determinación completamente transparentes
- Resultados auditables y reproducibles

### **🧮 Desarrollo del Cálculo**

**Paso 1 — Puntuación por categoría**
```
Puntuación_Críticos    = 287 / (20 × 18) × 100 = 287/360 × 100 = 79.7 %
Puntuación_Importantes = 190 / (20 × 18) × 100 = 190/360 × 100 = 52.8 %
Puntuación_Menores     = 105 / (16 × 18) × 100 = 105/288 × 100 = 36.5 %
```

**Paso 2 — Ponderación**
```
Puntuación_Ponderada_Total = (79.7 × 3.0) + (52.8 × 2.0) + (36.5 × 1.0)
                           = 239.2 + 105.6 + 36.5
                           = 381.2
```

**Paso 3 — Normalización**
```
Nivel_Completitud = 381.2 / (3.0 + 2.0 + 1.0) = 63.5 %
readiness_score   = 63.5 %
```
*(La puntuación ponderada ya está en escala porcentual, así que la división entre la suma de pesos da directamente el porcentaje final.)*

**Paso 4 — Conteo de gaps**
```
critical_gaps_count  = subcriterios C con puntuación < 12 = 3  → C2.3, C4.4, C5.3
important_gaps_count = subcriterios I con puntuación < 13 = 18 → I1.1, I1.2, I1.3, I1.4, I2.1, I2.2, I2.3, I2.4, I3.1, I3.2, I3.3, I3.4, I4.2, I4.3, I4.4, I5.2, I6.1, I6.2
minor_gaps_count     = subcriterios M con puntuación < 16 = 16 → todos (máximo obtenido: 12)
```

**Paso 5 — Estado general**
```
readiness_score = 63.5 % → no cumple ≥ 85 % ni ≥ 70 %; cumple ≥ 50 %
critical_gaps_count = 3 (> 2)
overall_status = "⚠️ PARCIALMENTE APTO - Requiere mejoras importantes"
```

### **⚖️ Observación sobre la Sensibilidad de la Métrica**

La fórmula **(Presencia + Completitud + Claridad) × Impacto** mide **relevancia × calidad**, no solo calidad documental. Esto tiene dos efectos en este proyecto:

1. **Techo estructural por impacto:** un subcriterio solo alcanza 18/18 con impacto 3. Con impacto 2 el máximo es 12 y con impacto 1 es 6. Por eso **ningún subcriterio menor puede superar el umbral de 16**: los 16 menores cuentan como gap aunque 8 estén en CUMPLE. En importantes, todo subcriterio de impacto ≤ 2 cuenta como gap aunque esté perfectamente documentado (p. ej. I1.1 e I1.3 en CUMPLE con 12/18).
2. **Calidad documental pura (referencial, no normativa):** si solo se promedia (P + C + Cl)/6 sin multiplicar por impacto, la completitud sería: críticos 88.3 %, importantes 77.5 %, menores 77.1 %, **ponderado 82.8 %**.

> El **resultado oficial** del workflow es **63.5 % — ⚠️ PARCIALMENTE APTO - Requiere mejoras importantes**. La cifra de calidad documental pura solo da contexto para interpretar el resultado: los faltantes reales se concentran en decisiones que el PRD delega a arquitectura (stack, despliegue, operación) y en información organizacional (equipo, dedicación, costo), no en la definición funcional, que es sobresaliente.

---

## 🎨 Verificación de Cobertura UX/UI en Documentación Comercial

> ⚠️ **Esta sección es INDEPENDIENTE del scoring de completitud PRD (56 subcriterios).**
> Su propósito es verificar si la documentación comercial (PRD, brief-alcance, épicas) contiene
> la información requerida por los checklists de los workflows `levantar-necesidades-ux` y
> `levantar-necesidades-ui`, para dar visibilidad sobre qué debe solicitarse, completarse
> o analizarse para cumplir con los requerimientos UX/UI más adelante.

### 📊 Resumen Ejecutivo UX/UI

| Indicador | UX | UI | Global |
|-----------|----|----|--------|
| **Cobertura** | 47.7% | 20.8% | 34.3% |
| **Ítems Encontrados** | 5 de 22 | 1 de 31 | 6 de 53 |
| **Ítems Parciales** | 11 | 8 | 19 |
| **Ítems No Encontrados** | 6 | 15 | 21 |
| **N/A** | 0 | 7 | 7 |

---

### 📋 Detalle de Cobertura UX (Checklist levantar-necesidades-ux)

| Sección | Ítem | Estado | Detalle | Documento Fuente |
|---------|------|--------|---------|------------------|
| §1 Contexto Negocio | ¿A qué se dedica la compañía? | ✅ | No hay compañía cliente: iniciativa propia del PO que lleva una tesis de maestría a un MVP. Aplicación web que procesa contratación pública colombiana (SECOP II + TVEC) y genera señales explicables y trazables | Brief (Resumen Ejecutivo, Stakeholders); PRD (encabezado); CONTEXTO |
| §1 Contexto Negocio | ¿Target (público objetivo)? | ✅ | Usuario de diseño = Analista que investiga contratación pública, con segmentos hipotéticos H1–H4 (periodista de datos, veedor, ONG/academia, control político). Organismos de control y ciudadano general quedan fuera. Hipótesis sin validar (D2/D5) | Brief (Actores del Sistema); PRD (Resumen) |
| §1 Contexto Negocio | ¿Usuarios con discapacidad? | ⚠️ | No se mencionan como segmento. Solo de forma indirecta: WCAG 2.1 AA (NFR-USA-004) y criterios de lector de pantalla en HU-069..072 | PRD NFR-USA-004; ÉPICA-006 |
| §1 Contexto Negocio | ¿Vital investigar con discapacidad? | ❌ | No se analiza la necesidad de investigar con usuarios con discapacidad (D2/D5 no la contemplan) | — |
| §2 Investigación | ¿Requiere investigación de usuarios? | ✅ | Validación con usuarios reales dentro del discovery: D2 (3–5 analistas: frecuencia, decisiones, valor, línea base manual) y D5; riesgo R4 mitigado con investigación; PRD supuesto 7 | Brief (D2, R4); PRD (Supuestos, Validaciones) |
| §2 Investigación | Tipo de investigación definido | ⚠️ | D2 trae pregunta guía y objetivo, pero no el método (entrevistas, observación, encuesta) ni el protocolo. Los 3 journeys del PRD son flujos funcionales, no journey maps de investigación. Sin arquetipos ni inmersión | Brief (D2); PRD §3 |
| §2 Investigación | Métodos especiales discapacidad | ❌ | No se definen métodos adaptados | — |
| §3 Referencias | Sitios web de referencia | ⚠️ | D3 (benchmark competitivo) enumera categorías a revisar pero no se ha ejecutado. Monitor Ciudadano, OCDS y Transparencia por Colombia aparecen como fuentes de información, no como referentes UX. La tesis trae mockups conceptuales propios | Brief (D3); CONTEXTO §4; TESIS §5.2 |
| §3 Referencias | Estructura de contenidos | ⚠️ | Estructura funcional inferible: lista de señales (inicio, A-172), Exploración, Ficha del contrato, Señal, Mis casos, operación del Administrador. Sin mapa de sitio ni arquitectura de información formal | PRD §3-4; epicas.md; ÉPICA-006; A-172 |
| §3 Referencias | Contenido interactivo | ⚠️ | Interactividad funcional: filtros con sugerencias (A-140), rangos predefinidos (A-143), estado en URL (A-151), gráfico del Benchmark 1 con tabla equivalente (A-156). No se pide contenido interactivo de experiencia | asunciones A-140, A-143, A-151, A-156 |
| §3 Referencias | Contenidos definidos | ✅ | Datos y textos definidos: campos de la ficha, benchmarks, fórmulas, fuente y fecha de corte, principio 'mostrar hechos, no acusar', texto de advertencia y formatos (A-132, A-152). Contenido generado por el sistema, sin producción editorial | Brief; asunciones A-132, A-152; PRD FRs |
| §4 Navegación | Wireframes/bocetos/flujos | ⚠️ | Mockups requeridos y planeados (D5) pero no existen. Hay flujos textuales (J1–J3, explorar → señal → caso → evidencia) y meta de ≤3 clics (NFR-USA-003). Mockups de la tesis conceptuales y desactualizados | PRD §3, NFR-USA-003, D5; Brief; TESIS §5.2 |
| §4 Navegación | Funciones de accesibilidad | ⚠️ | Solo contraste y teclado (WCAG 2.1 AA, NFR-USA-004), más lector de pantalla y foco visible en algunas HUs. Sin escalado de texto, modo nocturno, dictado, multi-idioma ni barra de accesibilidad | PRD NFR-USA-004; ÉPICA-006 HU-069/070/072 |
| §5 Interacciones | Interacciones/microinteracciones | ⚠️ | Comportamientos puntuales en HUs: indicador de carga (HU-069), sugerencias con Enter/Escape (HU-070), botón 'Volver' (A-154), sin autologin (A-170), edición concurrente (A-182). Dispersos, sin patrón global de feedback | ÉPICA-006 HU-069/070; A-154, A-170, A-182 |
| §5 Interacciones | Impacto en experiencia | ❌ | No se documenta el impacto esperado de las interacciones; solo metas de eficiencia (J1 10–15 min, ≥70 % de reducción, ≤3 clics) | PRD §3, NFR-USA-003 |
| §6 Validación | Técnica de validación definida | ⚠️ | Pruebas con prototipos/mockups (D5) con 3–5 analistas para validar el flujo y la usabilidad. Sin protocolo, tareas, métricas de usabilidad ni modalidad | Brief (D5); PRD (Validaciones) |
| §6 Validación | Métodos testeo discapacidad | ❌ | Sin pruebas con usuarios con discapacidad; solo QA funcional con teclado y lector de pantalla (HU-070 QA-17) | ÉPICA-006 HU-070 qa.md |
| §7 Personas | Personas identificadas | ⚠️ | Roles y perfiles (Analista, Administrador, segmentos H1–H4), sin personas UX formales ni validadas (0–2 contactos) | Brief (Actores); PRD |
| §7 Personas | Incluye demografía/objetivos/frustraciones | ⚠️ | La tabla de segmentos trae perfil, interacción esperada, punto de dolor y nivel técnico. Sin demografía (edad, ubicación, contexto, dispositivo) ni validación | Brief (tabla de Segmentos) |
| §8 Puntos Dolor | Puntos de dolor identificados | ✅ | Problemas 1–5 del Brief (vigilancia manual limitada, precio atrapado en documentos, sin referencia de mercado, difícil pasar de lo agregado al caso, hallazgos sin expediente) y dolor por segmento H1–H4. Son hipótesis | Brief (Planteamiento del Problema, Segmentos) |
| §8 Puntos Dolor | Clasificados impacto/frecuencia | ❌ | No clasificados; la frecuencia 'no se conoce todavía' (se medirá en D2). La matriz impacto/probabilidad solo existe para riesgos R1–R10 | Brief |
| §8 Puntos Dolor | Priorizados (P1/P2/P3) | ❌ | Sin priorización P1/P2/P3 de dolores; solo orden de segmentos H1–H4 y prioridad funcional de épicas | Brief; epicas.md |

**Resumen UX:** 47.7% de cobertura

**Resultado de la verificación UX (22 ítems):** ✅ 5 encontrados · ⚠️ 11 parciales · ❌ 6 no encontrados · 🚫 0 no aplica

**Hallazgos clave UX:**
- **Contexto y público:** bien definidos. Es una iniciativa propia (no hay compañía cliente) con un Analista como usuario de diseño y segmentos H1–H4. Todo es hipótesis hasta D2/D5.
- **Investigación y validación:** se exigen (D2 discovery con 3–5 analistas, D5 validación de mockups), pero faltan los métodos, protocolos, tareas y métricas de usabilidad.
- **Accesibilidad e inclusión:** limitada a WCAG 2.1 AA (contraste y teclado). No hay análisis de usuarios con discapacidad ni métodos de investigación o testeo adaptados. Es el bloque con más ítems ❌.
- **Artefactos UX inexistentes:** wireframes/mockups (D5 pendiente), arquitectura de información, personas formales y benchmark de referentes (D3 sin ejecutar).
- **Puntos de dolor:** identificados (5 problemas + dolor por segmento), pero sin clasificar por impacto/frecuencia ni priorizar.

#### 📊 Resumen de Cobertura UX por Sección

| Sección Checklist UX | Total Ítems | ✅ Encontrados | ⚠️ Parciales | ❌ No Encontrados | 🚫 N/A |
|---|---|---|---|---|---|
| §1 Contexto Negocio | 4 | 2 | 1 | 1 | 0 |
| §2 Investigación | 3 | 1 | 1 | 1 | 0 |
| §3 Referencias | 4 | 1 | 3 | 0 | 0 |
| §4 Navegación | 2 | 0 | 2 | 0 | 0 |
| §5 Interacciones | 2 | 0 | 1 | 1 | 0 |
| §6 Validación | 2 | 0 | 1 | 1 | 0 |
| §7 Personas | 2 | 0 | 2 | 0 | 0 |
| §8 Puntos Dolor | 3 | 1 | 0 | 2 | 0 |
| **TOTAL** | **22** | **5** | **11** | **6** | **0** |

**Cálculo:** cobertura_ux = (5 + 11 × 0,5) / (22 − 0) × 100 = **47.7 %**

---

### 📋 Detalle de Cobertura UI (Checklist levantar-necesidades-ui)

| Sección | Ítem | Estado | Detalle | Documento Fuente |
|---------|------|--------|---------|------------------|
| §1 Estándares | Manual imagen/estándar/DS | ❌ | No hay manual de marca, identidad visual, logo, paleta ni tipografía; solo el nombre del producto (HU-084 RN-09). Falta definir si existe identidad visual o quién la crea | PRD, Brief, asunciones, CONTEXTO (sin hallazgos) |
| §1 Estándares | UI KIT / Key Visual | ❌ | Sin UI kit ni key visual. Los mockups de la tesis (§5.2.1) son conceptuales; el Brief los trata como 'diseño conceptual de su momento' | TESIS §5.2.1; CONTEXTO |
| §2 Web | Procesos UX realizados | ⚠️ | UX planeada pero no realizada: D2 (discovery) y D5 (validación de mockups) pendientes. No hay brief UX ni artefactos UX | Brief (D2/D5, R4); PRD (Validaciones D5) |
| §2 Web | Evaluación heurística | ❌ | No se menciona. Lo más cercano: ≤3 clics (NFR-USA-003) y WCAG 2.1 AA (NFR-USA-004) | PRD §Usabilidad |
| §2 Web | Referencias gráficas (mín 3) | ⚠️ | Solo los 9 mockups conceptuales de la tesis (DataMonitor en Dash/Plotly) y la interfaz de SECOP II como contexto; no son referencias aprobadas para el MVP | TESIS §5.2.1, Figura 3 |
| §2 Web | Idiomas soportados | ⚠️ | Español implícito (correos en español HU-084 RN-09; formatos COP, DD/MM/AAAA, America/Bogota en A-132/A-152). Falta declarar explícitamente idioma único y sin i18n | HU-084; asunciones A-132, A-152 |
| §2 Web | Responsive + breakpoints | ⚠️ | NFR-USA-001: escritorio desde 1366×768, tablet desde 768 px, móvil desde 360 px; desktop-first. No se alinea con los breakpoints del estándar (<600, <768, <1024, >1440) | PRD NFR-USA-001; Brief |
| §2 Web | Navegadores garantizados | ✅ | 2 últimas versiones de Chrome, Edge, Firefox y Safari (NFR-USA-002); sin IE | PRD NFR-USA-002, Exclusiones técnicas |
| §2 Web | Frameworks visuales | ❌ | No definido; la tesis usaba Dash/Plotly pero no es obligatorio ('arquitectura a definir') | Brief; TESIS §5.2 |
| §2 Web | Preprocesadores CSS | ❌ | No se menciona estrategia CSS | — |
| §2 Web | Design tokens | ❌ | Sin tokens de color, tipografía ni espaciado; solo el contraste WCAG 2.1 AA | PRD NFR-USA-004 (indirecto) |
| §3 Mobile | Wireframes/bocetos | 🚫 | Exclusión explícita: sin app móvil nativa; el móvil se cubre con web responsive desde 360 px | PRD Exclusiones técnicas; Brief |
| §3 Mobile | Referencias gráficas (mín 3) | 🚫 | Sin app nativa | PRD Exclusiones técnicas |
| §3 Mobile | Idiomas soportados | 🚫 | Sin app nativa (idioma tratado en §2) | PRD Exclusiones técnicas |
| §3 Mobile | Framework mobile | 🚫 | Sin app nativa ni híbrida | PRD Exclusiones técnicas; CONTEXTO |
| §3 Mobile | Sistema operativo (iOS/Android) | 🚫 | Exclusión explícita: no hay app nativa iOS/Android | PRD Exclusiones técnicas |
| §3 Mobile | Design tokens + densidades | 🚫 | Sin app nativa | PRD Exclusiones técnicas |
| §4 Animaciones | Prototipo/gif/video/storyboard | ❌ | No se mencionan animaciones; probablemente no se requieran (producto analítico), pero no hay exclusión explícita | — |
| §4 Animaciones | Principios de animación | ❌ | No definidos | — |
| §4 Animaciones | Duración estándar | ❌ | No definida | — |
| §4 Animaciones | Tipo de suavizado | ❌ | No definido | — |
| §5 Design System | Problema que resolverá | ❌ | No se pide un Design System como entregable; producto único MVP. Falta confirmarlo como fuera de alcance | — |
| §5 Design System | Productos/plataformas + métricas | ❌ | Un solo producto; Express App solo comparte infraestructura, no UI | CONTEXTO §12 |
| §5 Design System | Referencias gráficas | ❌ | Sin referencias | — |
| §5 Design System | Config técnica (nav, fw, tokens) | ⚠️ | Solo navegadores (NFR-USA-002) y WCAG 2.1 AA (NFR-USA-004); faltan framework y tokens | PRD NFR-USA-002/004 |
| §5 Design System | Componentes (icono, ilustr, anim) | ⚠️ | Patrones funcionales en asunciones UI/UX: paginación 25/50/100 con estado en URL (A-151), formatos (A-152), gráfico de puntos con tabla equivalente (A-156), filtros con sugerencias (A-140), rangos de fecha (A-143). Sin iconos, ilustraciones ni animaciones | asunciones A-140, A-143, A-151, A-152, A-156 |
| §6 Iconografía | Concepto + librería + formato | ❌ | No se menciona iconografía, librería ni formato | — |
| §7 Mailings | Diseño cliente + referencias | ⚠️ | Correos transaccionales con asunto y contenido: invitación (HU-084 RN-09), recuperación y cambio de contraseña (FR-085, A-174), alertas de fuente (HU-100, A-189), suspensión (A-110). Falta el diseño visual (HTML/texto, plantilla, marca); no hay mailing de marketing | PRD FR-083/085; HU-084; HU-100; A-110, A-174, A-189 |
| §8 PDFs | Formato + impresión + librería | 🚫 | No se generan PDFs en el MVP: la exportación del expediente (FR-098) es Post-MVP (ÉPICA-009); solo CSV de auditoría (HU-113). Si D5 reincorpora FR-098 habrá que definirlo | PRD FR-098; epicas.md ÉPICA-009; HU-113 RN-05 |
| §9 Piezas Gráficas | Cantidad + concepto + canales + paleta | ❌ | No se mencionan piezas gráficas ni canales de difusión; probablemente no aplica (piloto por invitación), pero sin exclusión explícita | — |
| §10 Entregables | Entregables confirmados | ⚠️ | Confirmado: web desktop-first responsive como único canal; mobile nativo excluido; PDF de expediente Post-MVP; mockups para D5. Sin lista que confirme o excluya animaciones, Design System, iconografía, diseño de mailings y piezas gráficas, ni quién produce la identidad visual | PRD Exclusiones técnicas, Próximos pasos; Brief |

**Resumen UI:** 20.8% de cobertura

**Resultado de la verificación UI (31 ítems):** ✅ 1 encontrado · ⚠️ 8 parciales · ❌ 15 no encontrados · 🚫 7 no aplica

**Hallazgos clave UI:**
- **No hay identidad visual ni estándares gráficos:** faltan manual de marca, UI kit, key visual, design tokens, framework visual y estrategia CSS. Es el bloque más débil y condiciona todo el diseño UI.
- **Web:** solo los navegadores están completamente definidos (NFR-USA-002). Responsive está definido por NFR-USA-001 (1366/768/360 px) pero no se alinea con los breakpoints del estándar. El idioma español es implícito.
- **No aplica (7):** toda la sección Mobile (exclusión explícita de app nativa) y PDFs (la exportación del expediente FR-098 es Post-MVP).
- **Sin exclusión explícita:** animaciones, Design System, iconografía y piezas gráficas probablemente no se requieran en un MVP analítico por invitación, pero la documentación no lo confirma. Se cierran con una lista de entregables UI (§10).
- **Mailings:** el contenido de los correos transaccionales está definido; falta el diseño visual de la plantilla.

#### 📊 Resumen de Cobertura UI por Sección

| Sección Checklist UI | Total Ítems | ✅ Encontrados | ⚠️ Parciales | ❌ No Encontrados | 🚫 N/A |
|---|---|---|---|---|---|
| §1 Estándares | 2 | 0 | 0 | 2 | 0 |
| §2 Web | 9 | 1 | 4 | 4 | 0 |
| §3 Mobile | 6 | 0 | 0 | 0 | 6 |
| §4 Animaciones | 4 | 0 | 0 | 4 | 0 |
| §5 Design System | 5 | 0 | 2 | 3 | 0 |
| §6 Iconografía | 1 | 0 | 0 | 1 | 0 |
| §7 Mailings | 1 | 0 | 1 | 0 | 0 |
| §8 PDFs | 1 | 0 | 0 | 0 | 1 |
| §9 Piezas Gráficas | 1 | 0 | 0 | 1 | 0 |
| §10 Entregables | 1 | 0 | 1 | 0 | 0 |
| **TOTAL** | **31** | **1** | **8** | **15** | **7** |

**Cálculo:** cobertura_ui = (1 + 8 × 0,5) / (31 − 7) × 100 = **20.8 %**

**Cobertura global UX/UI** = (47.7 + 20.8) / 2 = **34.3 %**

> 🔎 **Sensibilidad:** 9 ítems UI ❌ de §4 Animaciones, §5 Design System, §6 Iconografía y §9 Piezas Gráficas probablemente no apliquen a un MVP analítico por invitación, pero la documentación no los excluye. Si el PO confirma esa exclusión en la lista de entregables (§10), la cobertura UI pasaría a **33.3 %** y la global a **40.5 %**.

---

### 🔗 Solapamientos entre Criterios PRD y Checklists UX/UI

> Los siguientes ítems son evaluados tanto en el scoring PRD (56 subcriterios) como en la verificación UX/UI.
> Se documentan para evitar la percepción de doble evaluación.

| Criterio PRD | Ítem UX/UI | Solapamiento |
|---|---|---|
| C1.1 Usuarios objetivo | UX §1 Target/público objetivo | Ambos evalúan definición de usuarios |
| C1.2 Objetivos de negocio | UX §1 Negocio de la compañía | Contexto de negocio |
| C4.2 Dispositivos y navegadores | UI §2 Navegadores garantizados | Navegadores soportados |
| C4.2 Dispositivos y navegadores | UI §2 Responsive + breakpoints | Dispositivos objetivo |
| C4.2 Dispositivos y navegadores | UI §3 Sistema operativo iOS/Android | Plataformas mobile |
| I2.1 Usabilidad | UX §4 Funciones de accesibilidad | Accesibilidad y usabilidad |
| I2.1 Usabilidad | UX §6 Técnica de validación | Validación con usuarios |
| M2.4 Mejoras UX | UX §5 Interacciones/microinteracciones | Mejoras de experiencia |
| M4.1 Elementos estéticos | UI §1 Manual imagen/estándar/DS | Estándares visuales |
| M4.2 Diseño responsivo | UI §2 Responsive + breakpoints | Breakpoints específicos |

#### 🔍 Consistencia de los resultados en los ítems solapados

| Criterio PRD | Resultado PRD | Ítem UX/UI | Resultado UX/UI | Consistencia |
|---|---|---|---|---|
| C1.1 Usuarios objetivo | ✅ CUMPLE (15/18) | UX §1 Target | ✅ Encontrado | ✅ Consistente |
| C1.2 Objetivos de negocio | ✅ CUMPLE (12/18) | UX §1 Negocio de la compañía | ✅ Encontrado | ✅ Consistente |
| C4.2 Dispositivos y navegadores | ✅ CUMPLE (12/18) | UI §2 Navegadores garantizados | ✅ Encontrado | ✅ Consistente |
| C4.2 Dispositivos y navegadores | ✅ CUMPLE (12/18) | UI §2 Responsive + breakpoints | ⚠️ Parcial | ⚠️ Diferencia de granularidad: para arquitectura, NFR-USA-001 (1366/768/360 px) es suficiente; el checklist UI exige los breakpoints estándar (<600/<768/<1024/>1440) |
| C4.2 Dispositivos y navegadores | ✅ CUMPLE (12/18) | UI §3 Sistema operativo | 🚫 No aplica | ✅ Consistente (app nativa excluida) |
| I2.1 Usabilidad | ⚠️ PARCIAL (5/18) | UX §4 Funciones de accesibilidad | ⚠️ Parcial | ✅ Consistente |
| I2.1 Usabilidad | ⚠️ PARCIAL (5/18) | UX §6 Técnica de validación | ⚠️ Parcial | ✅ Consistente |
| M2.4 Mejoras UX | ✅ CUMPLE (5/18) | UX §5 Interacciones/microinteracciones | ⚠️ Parcial | ⚠️ Diferencia de granularidad: el PRD valora que existan mejoras UX puntuales; el checklist UX exige un patrón global de microinteracciones |
| M4.1 Elementos estéticos | ❌ NO CUMPLE (1/18) | UI §1 Manual imagen/estándar/DS | ❌ No encontrado | ✅ Consistente |
| M4.2 Diseño responsivo | ✅ CUMPLE (6/18) | UI §2 Responsive + breakpoints | ⚠️ Parcial | ⚠️ Misma diferencia de granularidad que C4.2 (se resuelve con REC-UI-007) |

**Conclusión:** 7 de 10 solapamientos son consistentes. Las 3 diferencias no son contradicciones: el checklist UX/UI pide más detalle de diseño que el que necesita la arquitectura. No hay doble penalización: la verificación UX/UI no afecta el `readiness_score` del PRD.

---

### 🚨 Recomendaciones UX/UI Específicas y Accionables

> Para cada ítem con estado ❌ NO ENCONTRADO o ⚠️ PARCIAL se genera una recomendación estructurada
> con objetivo, pregunta, fuente, prioridad, acciones, esfuerzo y entregable.

#### **🔴 ACCIÓN INMEDIATA REQUERIDA (Prioridad Alta)**

> Bloquean la ejecución de los workflows `levantar-necesidades-ux` / `levantar-necesidades-ui`.

##### **REC-UX-001: Decidir la inclusión de usuarios con discapacidad**
- **Sección Checklist:** §1 Contexto del Negocio
- **Estado:** ⚠️ Parcial
- **Objetivo:** Definir si el producto debe diseñarse para usuarios con discapacidad más allá de WCAG 2.1 AA. Esto habilita decisiones de accesibilidad, investigación y testeo.
- **Pregunta:** ¿Entre los analistas objetivo (H1–H4) hay usuarios con discapacidad visual, motriz o cognitiva que deban considerarse explícitamente?
- **Fuente:** Product Owner
- **Prioridad:** 🔴 **Alta** - Condiciona el alcance de §2, §4 y §6 del levantamiento UX
- **Acciones:** 1) Revisar los segmentos H1–H4 con esta pregunta 2) Documentar la decisión ([Decisión]) en el Brief 3) Ajustar NFR-USA-004 si se amplía el alcance
- **Esfuerzo:** Bajo — decisión de 1 h
- **Entregable:** Decisión documentada de inclusión de accesibilidad
- **Dónde documentarse:** Brief-alcance

##### **REC-UX-003: Definir el método y protocolo de investigación D2**
- **Sección Checklist:** §2 Investigación de Usuarios
- **Estado:** ⚠️ Parcial
- **Objetivo:** Que el discovery con analistas produzca datos comparables (línea base manual, frecuencia, valor) y alimente personas y journey maps.
- **Pregunta:** ¿Qué método se usará en D2 (entrevistas semiestructuradas, observación contextual, encuesta) y con qué guion y entregables (arquetipos, journey map)?
- **Fuente:** Product Owner + UX
- **Prioridad:** 🔴 **Alta** - Bloquea el levantamiento UX: sin método no hay personas, journeys ni línea base (KPI de eficiencia)
- **Acciones:** 1) Elegir el método (recomendado: entrevista semiestructurada + observación de una tarea real) 2) Redactar el guion y el consentimiento 3) Definir los entregables: arquetipos, journey map y línea base de tiempo
- **Esfuerzo:** Medio — 1–2 días de preparación
- **Entregable:** Protocolo de investigación D2
- **Dónde documentarse:** Brief-alcance (actividad D2)

##### **REC-UX-008: Producir wireframes y flujos (D5)**
- **Sección Checklist:** §4 Navegación y Accesibilidad
- **Estado:** ⚠️ Parcial
- **Objetivo:** Materializar los journeys J1–J3 en wireframes navegables para la validación D5.
- **Pregunta:** ¿Cómo se ve el flujo explorar → señal → caso → evidencia en ≤3 clics (NFR-USA-003) en desktop, tablet y móvil?
- **Fuente:** UX + Product Owner
- **Prioridad:** 🔴 **Alta** - Bloquea la validación D5 y el levantamiento UI
- **Acciones:** 1) Wireframes de baja fidelidad de las vistas principales 2) Prototipo navegable del Journey 1 3) Revisión con el PO antes de D5
- **Esfuerzo:** Alto — 1–2 semanas
- **Entregable:** Wireframes + prototipo navegable
- **Dónde documentarse:** Insumos-cliente (artefacto D5)

##### **REC-UX-012: Definir el protocolo de validación con usuarios (D5)**
- **Sección Checklist:** §6 Validación con Usuarios
- **Estado:** ⚠️ Parcial
- **Objetivo:** Que D5 produzca evidencia accionable sobre si el flujo resuelve la tarea del analista.
- **Pregunta:** ¿Qué técnica (test de usabilidad moderado con prototipo), qué tareas, qué métricas (éxito, tiempo, SUS) y qué criterio de aprobación se usarán en D5?
- **Fuente:** UX + Product Owner
- **Prioridad:** 🔴 **Alta** - Bloquea el cierre de alcance previsto tras D5
- **Acciones:** 1) Elegir la técnica (recomendado: test moderado remoto con 3–5 analistas) 2) Definir 3–5 tareas basadas en J1–J3 3) Fijar métricas y umbral de aprobación
- **Esfuerzo:** Medio — 1 día
- **Entregable:** Protocolo de validación D5
- **Dónde documentarse:** Brief-alcance (actividad D5)

##### **REC-UX-014: Construir personas UX**
- **Sección Checklist:** §7 Personas de Usuario
- **Estado:** ⚠️ Parcial
- **Objetivo:** Pasar de segmentos hipotéticos H1–H4 a personas validadas que guíen el diseño.
- **Pregunta:** ¿Cuáles son las 2–3 personas principales (objetivos, tareas, frustraciones, contexto) según D2?
- **Fuente:** UX (con datos de D2)
- **Prioridad:** 🔴 **Alta** - Bloquea las decisiones de diseño centradas en el usuario
- **Acciones:** 1) Ejecutar D2 2) Sintetizar 2–3 personas 3) Validarlas con el PO
- **Esfuerzo:** Medio — 1–2 días después de D2
- **Entregable:** Fichas de personas
- **Dónde documentarse:** Insumos-cliente / Brief-alcance

##### **REC-UI-001: Definir identidad visual del producto**
- **Sección Checklist:** §1 Estándares Visuales
- **Estado:** ❌ No encontrado
- **Objetivo:** Contar con la base de marca (logo, paleta, tipografía) para todo el diseño UI.
- **Pregunta:** ¿Existe identidad visual para 'Seguimiento Compras Públicas'? Si no, ¿quién la crea y con qué lineamientos (sobria, institucional, neutral)?
- **Fuente:** Product Owner
- **Prioridad:** 🔴 **Alta** - Sin identidad no se puede iniciar el diseño UI de alta fidelidad
- **Acciones:** 1) Confirmar si hay identidad 2) Si no, definir lineamientos mínimos (logo, paleta accesible, tipografía) 3) Documentarlo como insumo
- **Esfuerzo:** Medio — 2–3 días
- **Entregable:** Guía de identidad mínima
- **Dónde documentarse:** Insumos-cliente

##### **REC-UI-003: Documentar los procesos UX y la ruta del brief UX**
- **Sección Checklist:** §2 Aplicaciones Web
- **Estado:** ⚠️ Parcial
- **Objetivo:** Que el levantamiento UI parta de los resultados UX (D2/D5).
- **Pregunta:** ¿Dónde quedarán los resultados de D2/D5 (personas, journeys, wireframes) para el levantamiento UI?
- **Fuente:** Product Owner
- **Prioridad:** 🔴 **Alta** - El checklist UI requiere la ruta del brief UX
- **Acciones:** 1) Definir la ruta del repositorio de artefactos UX 2) Ejecutar el levantamiento UX antes del UI
- **Esfuerzo:** Bajo
- **Entregable:** Ruta del brief UX
- **Dónde documentarse:** Brief-alcance

##### **REC-UI-008: Seleccionar el framework visual**
- **Sección Checklist:** §2 Aplicaciones Web
- **Estado:** ❌ No encontrado
- **Objetivo:** Habilitar el diseño de componentes y la estimación del frontend.
- **Pregunta:** ¿Qué framework UI se usará (p. ej. Tailwind + librería de componentes, Material, Bootstrap)?
- **Fuente:** Arquitecto + Product Owner
- **Prioridad:** 🔴 **Alta** - Decisión técnica que condiciona UI kit, tokens y estimación del frontend
- **Acciones:** 1) Evaluar 2–3 opciones según el stack 2) Registrar ADR 3) Comunicar a UX/UI
- **Esfuerzo:** Bajo — en arquitectura de solución
- **Entregable:** ADR de framework visual
- **Dónde documentarse:** PRD (restricciones técnicas) / arquitectura

##### **REC-UI-023: Confirmar la lista de entregables UI**
- **Sección Checklist:** §10 Entregables Esperados
- **Estado:** ⚠️ Parcial
- **Objetivo:** Cerrar de una vez el alcance UI: qué se entrega y qué queda excluido.
- **Pregunta:** ¿Cuáles de estos entregables se incluyen: Web (sí), Mobile nativo (no), Animaciones, Design System, Iconografía, Mailings, PDFs (Post-MVP), Piezas gráficas? ¿Quién produce la identidad visual?
- **Fuente:** Product Owner
- **Prioridad:** 🔴 **Alta** - Reclasifica ~9 ítems como N/A y define el alcance del trabajo UI
- **Acciones:** 1) Completar la lista de entregables 2) Registrar exclusiones en el PRD 3) Asignar responsable de identidad visual
- **Esfuerzo:** Bajo — 30 min
- **Entregable:** Lista de entregables UI confirmada
- **Dónde documentarse:** PRD (exclusiones) / Brief-alcance

#### **🟡 RESOLUCIÓN EN PREPARACIÓN (Prioridad Media)**

> Afectan la calidad del levantamiento, pero no lo bloquean.

##### **REC-UX-002: Definir si se investiga con usuarios con discapacidad**
- **Sección Checklist:** §1 Contexto del Negocio
- **Estado:** ❌ No encontrado
- **Objetivo:** Saber si D2/D5 deben incluir participantes con discapacidad.
- **Pregunta:** ¿Es vital incluir usuarios con discapacidad en el discovery (D2) y en la validación (D5)?
- **Fuente:** Product Owner
- **Prioridad:** 🟡 **Media** - Depende de REC-UX-001; afecta el reclutamiento de D2/D5
- **Acciones:** 1) Resolver REC-UX-001 2) Si aplica, agregar cuota de participantes en D2/D5 3) Documentar en las actividades de validación
- **Esfuerzo:** Bajo
- **Entregable:** Criterio de reclutamiento de D2/D5
- **Dónde documentarse:** Brief-alcance

##### **REC-UX-005: Ejecutar el benchmark de referentes (D3)**
- **Sección Checklist:** §3 Referencias y Contenido
- **Estado:** ⚠️ Parcial
- **Objetivo:** Contar con al menos 3 referentes de UX e interacción para visualización de contratación pública y análisis de precios.
- **Pregunta:** ¿Qué plataformas (SECOP/CCE, Monitor Ciudadano, OCDS, herramientas periodísticas) sirven de referencia de interacción y qué patrones se adoptan o evitan?
- **Fuente:** Product Owner + UX
- **Prioridad:** 🟡 **Media** - Mejora la calidad de los mockups D5 sin bloquearlos
- **Acciones:** 1) Ejecutar D3 sobre las categorías ya listadas 2) Capturar patrones (filtros, fichas, evidencia) 3) Seleccionar 3+ referencias para los mockups
- **Esfuerzo:** Medio — 1 día
- **Entregable:** Benchmark D3 con referentes y patrones
- **Dónde documentarse:** Insumos-cliente / Brief-alcance (D3)

##### **REC-UX-006: Formalizar la arquitectura de información**
- **Sección Checklist:** §3 Referencias y Contenido
- **Estado:** ⚠️ Parcial
- **Objetivo:** Consolidar la estructura de vistas que hoy se infiere de épicas y asunciones (señales, exploración, ficha, señal, casos, administración).
- **Pregunta:** ¿Cuál es el mapa de sitio y la jerarquía de navegación del producto, incluyendo las vistas administrativas con UI (Dominio 12)?
- **Fuente:** UX + Arquitecto
- **Prioridad:** 🟡 **Media** - Necesaria para los wireframes; se puede derivar de las épicas
- **Acciones:** 1) Derivar el mapa de sitio de ÉPICA-005/006/007/008 2) Decidir qué capacidades administrativas tienen UI 3) Validar con el PO
- **Esfuerzo:** Bajo — medio día
- **Entregable:** Mapa de sitio / arquitectura de información
- **Dónde documentarse:** PRD (sección de experiencia) / Épicas

##### **REC-UX-009: Definir funciones de accesibilidad adicionales**
- **Sección Checklist:** §4 Navegación y Accesibilidad
- **Estado:** ⚠️ Parcial
- **Objetivo:** Precisar qué funciones de accesibilidad se incluyen además de contraste y teclado.
- **Pregunta:** ¿Se requieren escalado de texto, modo oscuro, compatibilidad con dictado o lector de pantalla en todas las vistas, o barra de accesibilidad?
- **Fuente:** Product Owner + UX
- **Prioridad:** 🟡 **Media** - WCAG 2.1 AA ya cubre lo esencial; el resto depende de REC-UX-001
- **Acciones:** 1) Resolver REC-UX-001 2) Listar las funciones incluidas y excluidas 3) Actualizar NFR-USA-004
- **Esfuerzo:** Bajo
- **Entregable:** NFR de accesibilidad ampliado
- **Dónde documentarse:** PRD (NFR-USA)

##### **REC-UX-015: Completar la demografía y el contexto de uso**
- **Sección Checklist:** §7 Personas de Usuario
- **Estado:** ⚠️ Parcial
- **Objetivo:** Completar las personas con demografía, dispositivo y contexto de uso.
- **Pregunta:** ¿Qué edad, ubicación, dispositivo principal y contexto de uso (oficina, campo, redacción) tienen los analistas?
- **Fuente:** UX (D2)
- **Prioridad:** 🟡 **Media** - Complementa REC-UX-014
- **Acciones:** 1) Incluir preguntas de demografía en el guion de D2 2) Agregarlas a las personas
- **Esfuerzo:** Bajo
- **Entregable:** Personas completas
- **Dónde documentarse:** Brief-alcance

##### **REC-UX-016: Clasificar puntos de dolor por impacto y frecuencia**
- **Sección Checklist:** §8 Puntos de Dolor
- **Estado:** ❌ No encontrado
- **Objetivo:** Saber qué dolores atacar primero con evidencia.
- **Pregunta:** ¿Con qué frecuencia y con qué impacto sufre cada segmento los 5 problemas identificados?
- **Fuente:** UX + Product Owner (D2)
- **Prioridad:** 🟡 **Media** - La frecuencia se medirá en D2 (el Brief la declara desconocida)
- **Acciones:** 1) Medir la frecuencia e impacto en D2 2) Construir la matriz impacto × frecuencia
- **Esfuerzo:** Bajo
- **Entregable:** Matriz de puntos de dolor
- **Dónde documentarse:** Brief-alcance

##### **REC-UX-017: Priorizar puntos de dolor (P1/P2/P3)**
- **Sección Checklist:** §8 Puntos de Dolor
- **Estado:** ❌ No encontrado
- **Objetivo:** Alinear la priorización de épicas con los dolores validados.
- **Pregunta:** ¿Qué dolores son P1, P2 y P3 y coinciden con la priorización de épicas?
- **Fuente:** Product Owner
- **Prioridad:** 🟡 **Media** - Depende de REC-UX-016
- **Acciones:** 1) Priorizar con base en la matriz 2) Contrastar con la prioridad de épicas
- **Esfuerzo:** Bajo
- **Entregable:** Dolores priorizados
- **Dónde documentarse:** Brief-alcance

##### **REC-UI-002: Definir UI kit / key visual**
- **Sección Checklist:** §1 Estándares Visuales
- **Estado:** ❌ No encontrado
- **Objetivo:** Acelerar el diseño con un kit base coherente.
- **Pregunta:** ¿Se usará un UI kit existente (asociado al framework) o uno propio?
- **Fuente:** UX/UI + Arquitecto
- **Prioridad:** 🟡 **Media** - Se resuelve junto con REC-UI-008
- **Acciones:** 1) Elegir el kit según el framework 2) Personalizarlo con la identidad
- **Esfuerzo:** Bajo
- **Entregable:** UI kit base
- **Dónde documentarse:** Insumos-cliente

##### **REC-UI-005: Seleccionar referencias gráficas (mín. 3)**
- **Sección Checklist:** §2 Aplicaciones Web
- **Estado:** ⚠️ Parcial
- **Objetivo:** Orientar el estilo visual con referencias aprobadas.
- **Pregunta:** ¿Qué 3+ productos o dashboards sirven de referencia visual (no solo los mockups de la tesis)?
- **Fuente:** Product Owner + UX/UI
- **Prioridad:** 🟡 **Media** - Se alimenta del benchmark D3 (REC-UX-005)
- **Acciones:** 1) Derivar de D3 2) Aprobar 3+ referencias
- **Esfuerzo:** Bajo
- **Entregable:** Moodboard de referencias
- **Dónde documentarse:** Insumos-cliente

##### **REC-UI-007: Alinear breakpoints responsive**
- **Sección Checklist:** §2 Aplicaciones Web
- **Estado:** ⚠️ Parcial
- **Objetivo:** Que diseño y desarrollo usen los mismos cortes.
- **Pregunta:** ¿Se adoptan los breakpoints del estándar (<600, <768, <1024, >1440) o se mantienen 360/768/1366 de NFR-USA-001?
- **Fuente:** UX/UI + Arquitecto
- **Prioridad:** 🟡 **Media** - NFR-USA-001 existe pero no se alinea con el estándar de UI
- **Acciones:** 1) Definir la tabla de breakpoints 2) Actualizar NFR-USA-001
- **Esfuerzo:** Bajo
- **Entregable:** Tabla de breakpoints
- **Dónde documentarse:** PRD (NFR-USA-001)

##### **REC-UI-010: Definir design tokens**
- **Sección Checklist:** §2 Aplicaciones Web
- **Estado:** ❌ No encontrado
- **Objetivo:** Garantizar consistencia y contraste WCAG desde la base.
- **Pregunta:** ¿Cuáles son los tokens de color (con contraste AA), tipografía, espaciado y estados (incluidos niveles de confianza)?
- **Fuente:** UX/UI
- **Prioridad:** 🟡 **Media** - Depende de la identidad (REC-UI-001)
- **Acciones:** 1) Derivar de la identidad 2) Validar contraste AA 3) Publicar en formato JSON/CSS
- **Esfuerzo:** Medio — 1 día
- **Entregable:** Tokens de diseño
- **Dónde documentarse:** Insumos-cliente

##### **REC-UI-018: Completar la configuración técnica de UI**
- **Sección Checklist:** §5 Sistema de Diseño
- **Estado:** ⚠️ Parcial
- **Objetivo:** Unificar navegadores, framework y formato de tokens.
- **Pregunta:** ¿Cuál es el framework y el formato de tokens (JSON/CSS) además de los navegadores ya definidos?
- **Fuente:** Arquitecto + UX/UI
- **Prioridad:** 🟡 **Media** - Se resuelve con REC-UI-008 y REC-UI-010
- **Acciones:** 1) Consolidar en el ADR de frontend
- **Esfuerzo:** Bajo
- **Entregable:** Configuración técnica de UI
- **Dónde documentarse:** Arquitectura

##### **REC-UI-019: Definir el catálogo de componentes**
- **Sección Checklist:** §5 Sistema de Diseño
- **Estado:** ⚠️ Parcial
- **Objetivo:** Formalizar los patrones funcionales existentes (paginación, filtros, gráfico de puntos, formatos).
- **Pregunta:** ¿Qué componentes base se necesitan (tabla, filtros, ficha, tarjeta de señal, indicador de confianza, gráfico) y cómo se representan los estados?
- **Fuente:** UX/UI
- **Prioridad:** 🟡 **Media** - Los patrones existen en asunciones (A-140, A-143, A-151, A-152, A-156)
- **Acciones:** 1) Inventariar componentes desde las HUs 2) Diseñarlos sobre el UI kit
- **Esfuerzo:** Medio — 2 días
- **Entregable:** Catálogo de componentes
- **Dónde documentarse:** Épicas / Insumos-cliente

##### **REC-UI-020: Definir iconografía**
- **Sección Checklist:** §6 Iconografía
- **Estado:** ❌ No encontrado
- **Objetivo:** Coherencia visual y accesibilidad de iconos.
- **Pregunta:** ¿Qué librería de iconos (p. ej. la del framework) y formato (SVG) se usarán?
- **Fuente:** UX/UI
- **Prioridad:** 🟡 **Media** - Necesaria para estados y acciones; resolución sencilla
- **Acciones:** 1) Elegir la librería del framework 2) Formato SVG con texto alternativo
- **Esfuerzo:** Bajo
- **Entregable:** Decisión de iconografía
- **Dónde documentarse:** Insumos-cliente

#### **🟢 REFINAMIENTO POSTERIOR (Prioridad Baja)**

> Se pueden resolver durante la ejecución de los workflows UX/UI.

##### **REC-UX-004: Métodos de investigación adaptados a discapacidad**
- **Sección Checklist:** §2 Investigación de Usuarios
- **Estado:** ❌ No encontrado
- **Objetivo:** Garantizar que la investigación sea accesible si se incluyen usuarios con discapacidad.
- **Pregunta:** ¿Qué adaptaciones (lector de pantalla, sesiones remotas accesibles, tiempos extendidos) requiere la investigación?
- **Fuente:** UX
- **Prioridad:** 🟢 **Baja** - Solo aplica si REC-UX-002 resulta afirmativo
- **Acciones:** 1) Esperar la decisión de REC-UX-002 2) Definir adaptaciones del protocolo 3) Validar las herramientas de sesión remota
- **Esfuerzo:** Bajo
- **Entregable:** Anexo de accesibilidad del protocolo D2
- **Dónde documentarse:** Brief-alcance

##### **REC-UX-007: Confirmar el alcance de contenido interactivo**
- **Sección Checklist:** §3 Referencias y Contenido
- **Estado:** ⚠️ Parcial
- **Objetivo:** Delimitar si se requiere interactividad más allá de la funcional (filtros, gráficos, paginación).
- **Pregunta:** ¿Se requiere contenido interactivo adicional (visualizaciones exploratorias, tours guiados) o basta con la interactividad funcional definida?
- **Fuente:** Product Owner
- **Prioridad:** 🟢 **Baja** - La interactividad funcional ya está definida (A-140, A-143, A-151, A-156)
- **Acciones:** 1) Confirmar 'solo interactividad funcional' en el MVP 2) Registrar extras en el backlog Post-MVP
- **Esfuerzo:** Bajo
- **Entregable:** Decisión de alcance
- **Dónde documentarse:** PRD

##### **REC-UX-010: Definir el patrón global de microinteracciones y feedback**
- **Sección Checklist:** §5 Interacciones
- **Estado:** ⚠️ Parcial
- **Objetivo:** Unificar los comportamientos hoy dispersos en HUs (carga, sugerencias, estados vacíos, errores).
- **Pregunta:** ¿Cuál es el patrón estándar de feedback (carga, éxito, error, vacío, confirmación) en toda la aplicación?
- **Fuente:** UX
- **Prioridad:** 🟢 **Baja** - Se puede definir durante el diseño UI
- **Acciones:** 1) Inventariar las microinteracciones de las HUs 2) Definir el patrón global 3) Incluirlo en la guía de componentes
- **Esfuerzo:** Bajo
- **Entregable:** Guía de patrones de interacción
- **Dónde documentarse:** Épicas (criterios transversales)

##### **REC-UX-011: Documentar el impacto esperado en la experiencia**
- **Sección Checklist:** §5 Interacciones
- **Estado:** ❌ No encontrado
- **Objetivo:** Vincular las interacciones con resultados de experiencia medibles.
- **Pregunta:** ¿Qué impacto en la experiencia se espera de las interacciones clave (confianza en la evidencia, tiempo hasta la señal)?
- **Fuente:** UX + Product Owner
- **Prioridad:** 🟢 **Baja** - Ya existen metas de eficiencia (J1, NFR-USA-003)
- **Acciones:** 1) Derivar las metas de experiencia de los KPIs 2) Medirlas en D5
- **Esfuerzo:** Bajo
- **Entregable:** Metas de experiencia
- **Dónde documentarse:** PRD

##### **REC-UX-013: Métodos de testeo para discapacidad**
- **Sección Checklist:** §6 Validación con Usuarios
- **Estado:** ❌ No encontrado
- **Objetivo:** Asegurar que la validación cubra a usuarios con discapacidad si aplica.
- **Pregunta:** ¿Se incluirán pruebas con usuarios con discapacidad o auditoría de accesibilidad asistida?
- **Fuente:** UX
- **Prioridad:** 🟢 **Baja** - Depende de REC-UX-001/002; existe QA funcional con lector de pantalla
- **Acciones:** 1) Esperar la decisión de REC-UX-001 2) Si aplica, auditoría WCAG con herramientas y 1 usuario
- **Esfuerzo:** Bajo
- **Entregable:** Plan de testeo accesible
- **Dónde documentarse:** Brief-alcance

##### **REC-UI-004: Decidir si se hace evaluación heurística**
- **Sección Checklist:** §2 Aplicaciones Web
- **Estado:** ❌ No encontrado
- **Objetivo:** Detectar problemas de usabilidad en los mockups antes de D5.
- **Pregunta:** ¿Se hará una evaluación heurística (Nielsen) de los wireframes antes de la validación con usuarios?
- **Fuente:** UX
- **Prioridad:** 🟢 **Baja** - Complemento de bajo costo a D5
- **Acciones:** 1) Incluirla en el plan UX (recomendado) 2) Ejecutarla sobre el prototipo
- **Esfuerzo:** Bajo — medio día
- **Entregable:** Informe heurístico
- **Dónde documentarse:** Brief-alcance

##### **REC-UI-006: Declarar el idioma único**
- **Sección Checklist:** §2 Aplicaciones Web
- **Estado:** ⚠️ Parcial
- **Objetivo:** Evitar ambigüedad sobre i18n.
- **Pregunta:** ¿El producto es solo en español (es-CO) sin internacionalización en el MVP?
- **Fuente:** Product Owner
- **Prioridad:** 🟢 **Baja** - Hoy es implícito
- **Acciones:** 1) Declarar 'español es-CO, sin i18n en el MVP' en los NFR
- **Esfuerzo:** Bajo — 15 min
- **Entregable:** NFR de idioma
- **Dónde documentarse:** PRD (NFR-USA)

##### **REC-UI-009: Definir estrategia CSS / preprocesador**
- **Sección Checklist:** §2 Aplicaciones Web
- **Estado:** ❌ No encontrado
- **Objetivo:** Consistencia de estilos.
- **Pregunta:** ¿Se usará SASS/SCSS, CSS utility-first o CSS-in-JS?
- **Fuente:** Arquitecto
- **Prioridad:** 🟢 **Baja** - Consecuencia de REC-UI-008
- **Acciones:** 1) Decidir junto con el framework
- **Esfuerzo:** Bajo
- **Entregable:** Decisión en el ADR de frontend
- **Dónde documentarse:** Arquitectura

##### **REC-UI-011: Confirmar si hay animaciones (prototipo/storyboard)**
- **Sección Checklist:** §4 Animaciones
- **Estado:** ❌ No encontrado
- **Objetivo:** Cerrar el alcance de animaciones.
- **Pregunta:** ¿El MVP requiere animaciones más allá de transiciones estándar del framework?
- **Fuente:** Product Owner
- **Prioridad:** 🟢 **Baja** - Probablemente no aplica a un producto analítico
- **Acciones:** 1) Confirmar exclusión en la lista de entregables (REC-UI-023)
- **Esfuerzo:** Bajo
- **Entregable:** Decisión de alcance
- **Dónde documentarse:** PRD (exclusiones)

##### **REC-UI-012: Principios de animación**
- **Sección Checklist:** §4 Animaciones
- **Estado:** ❌ No encontrado
- **Objetivo:** Solo si se confirman animaciones.
- **Pregunta:** ¿Qué principios aplican (continuidad, jerarquía)?
- **Fuente:** UX/UI
- **Prioridad:** 🟢 **Baja** - Depende de REC-UI-011
- **Acciones:** 1) Resolver REC-UI-011
- **Esfuerzo:** Bajo
- **Entregable:** —
- **Dónde documentarse:** PRD

##### **REC-UI-013: Duración estándar de animaciones**
- **Sección Checklist:** §4 Animaciones
- **Estado:** ❌ No encontrado
- **Objetivo:** Solo si se confirman animaciones.
- **Pregunta:** ¿Qué duración estándar (p. ej. 150–250 ms)?
- **Fuente:** UX/UI
- **Prioridad:** 🟢 **Baja** - Depende de REC-UI-011
- **Acciones:** 1) Resolver REC-UI-011 2) Usar los valores por defecto del framework
- **Esfuerzo:** Bajo
- **Entregable:** —
- **Dónde documentarse:** PRD

##### **REC-UI-014: Tipo de suavizado**
- **Sección Checklist:** §4 Animaciones
- **Estado:** ❌ No encontrado
- **Objetivo:** Solo si se confirman animaciones.
- **Pregunta:** ¿Qué curva de suavizado (ease-in-out)?
- **Fuente:** UX/UI
- **Prioridad:** 🟢 **Baja** - Depende de REC-UI-011
- **Acciones:** 1) Resolver REC-UI-011
- **Esfuerzo:** Bajo
- **Entregable:** —
- **Dónde documentarse:** PRD

##### **REC-UI-015: Confirmar si se requiere un Design System**
- **Sección Checklist:** §5 Sistema de Diseño
- **Estado:** ❌ No encontrado
- **Objetivo:** Cerrar el alcance del Design System.
- **Pregunta:** ¿Se requiere un Design System formal o basta una guía de componentes sobre el UI kit?
- **Fuente:** Product Owner
- **Prioridad:** 🟢 **Baja** - Producto único MVP; un DS formal probablemente es innecesario
- **Acciones:** 1) Confirmar en la lista de entregables (REC-UI-023)
- **Esfuerzo:** Bajo
- **Entregable:** Decisión de alcance
- **Dónde documentarse:** PRD (exclusiones)

##### **REC-UI-016: Productos/plataformas y métricas del DS**
- **Sección Checklist:** §5 Sistema de Diseño
- **Estado:** ❌ No encontrado
- **Objetivo:** Solo si se requiere DS.
- **Pregunta:** ¿Qué productos cubriría y cómo se mediría su éxito?
- **Fuente:** Product Owner
- **Prioridad:** 🟢 **Baja** - Depende de REC-UI-015
- **Acciones:** 1) Resolver REC-UI-015
- **Esfuerzo:** Bajo
- **Entregable:** —
- **Dónde documentarse:** PRD

##### **REC-UI-017: Referencias gráficas del DS**
- **Sección Checklist:** §5 Sistema de Diseño
- **Estado:** ❌ No encontrado
- **Objetivo:** Solo si se requiere DS.
- **Pregunta:** ¿Qué sistemas de diseño de referencia se toman?
- **Fuente:** UX/UI
- **Prioridad:** 🟢 **Baja** - Depende de REC-UI-015
- **Acciones:** 1) Resolver REC-UI-015
- **Esfuerzo:** Bajo
- **Entregable:** —
- **Dónde documentarse:** Insumos-cliente

##### **REC-UI-021: Diseñar la plantilla de correos transaccionales**
- **Sección Checklist:** §7 Mailings
- **Estado:** ⚠️ Parcial
- **Objetivo:** Dar formato a los correos ya definidos (invitación, contraseña, alertas).
- **Pregunta:** ¿Los correos serán HTML con marca o texto plano? ¿Hay referencias de diseño?
- **Fuente:** Product Owner + UX/UI
- **Prioridad:** 🟢 **Baja** - El contenido ya está definido (HU-084, HU-100, A-174, A-189)
- **Acciones:** 1) Decidir HTML simple vs texto plano 2) Crear la plantilla base con la identidad
- **Esfuerzo:** Bajo
- **Entregable:** Plantilla de correo
- **Dónde documentarse:** Épicas (HU-084, HU-100)

##### **REC-UI-022: Confirmar que no hay piezas gráficas**
- **Sección Checklist:** §9 Piezas Gráficas
- **Estado:** ❌ No encontrado
- **Objetivo:** Cerrar el alcance de piezas de difusión.
- **Pregunta:** ¿El MVP requiere piezas gráficas (difusión del piloto, redes)?
- **Fuente:** Product Owner
- **Prioridad:** 🟢 **Baja** - Probablemente no aplica a un piloto por invitación
- **Acciones:** 1) Confirmar exclusión en REC-UI-023
- **Esfuerzo:** Bajo
- **Entregable:** Decisión de alcance
- **Dónde documentarse:** PRD (exclusiones)

**Recomendaciones UX:** 17 fichas (REC-UX-001 a REC-UX-017) — 🔴 5 Alta · 🟡 7 Media · 🟢 5 Baja

**Recomendaciones UI:** 23 fichas (REC-UI-001 a REC-UI-023) — 🔴 4 Alta · 🟡 7 Media · 🟢 12 Baja

---

### 📂 Información Faltante Agrupada por Documento Fuente

#### Información a completar en PRD:
REC-UX-006, REC-UX-007, REC-UX-009, REC-UX-011, REC-UI-006, REC-UI-007, REC-UI-008, REC-UI-011, REC-UI-012, REC-UI-013, REC-UI-014, REC-UI-015, REC-UI-016, REC-UI-022, REC-UI-023

#### Información a completar en Brief de Alcance:
REC-UX-001, REC-UX-002, REC-UX-003, REC-UX-004, REC-UX-005, REC-UX-012, REC-UX-013, REC-UX-014, REC-UX-015, REC-UX-016, REC-UX-017, REC-UI-003, REC-UI-004, REC-UI-023

#### Información a completar en Épicas:
REC-UX-006, REC-UX-010, REC-UI-019, REC-UI-021

#### Información que debe proporcionarse como insumo del cliente:
REC-UX-005, REC-UX-008, REC-UX-014, REC-UI-001, REC-UI-002, REC-UI-005, REC-UI-010, REC-UI-017, REC-UI-019, REC-UI-020

#### Decisiones técnicas a registrar en la arquitectura (ADR):
REC-UI-008, REC-UI-009, REC-UI-018

> Algunas recomendaciones aparecen en más de un documento porque requieren registro en ambos (p. ej. PRD y Brief).

### 🧾 Síntesis de la Verificación UX/UI

**Resumen ejecutivo UX/UI (independiente del readiness_score del PRD):**
- **Cobertura UX: 47,7 %** (22 ítems: 5 ✅ · 11 ⚠️ · 6 ❌). El contexto, el público objetivo, los contenidos y los puntos de dolor están documentados. Faltan los artefactos y métodos UX (personas, arquitectura de información, wireframes, protocolos D2/D5) y el bloque de accesibilidad e inclusión.
- **Cobertura UI: 20,8 %** (31 ítems: 1 ✅ · 8 ⚠️ · 15 ❌ · 7 🚫). Falta la identidad visual y los estándares gráficos (marca, UI kit, tokens, framework visual, iconografía). Mobile y PDFs no aplican.
- **Cobertura global UX/UI: 34,3 %.** Llegaría a ~40,5 % si se confirman como excluidos animaciones, Design System, iconografía formal y piezas gráficas (REC-UI-023).

**Lectura para la arquitectura:** los faltantes UX/UI **no bloquean la arquitectura de solución**. Solo dos decisiones UI la tocan directamente: el framework visual y la estrategia CSS (REC-UI-008/009/018), que se registran como ADR de frontend. El resto son insumos para los workflows `levantar-necesidades-ux` y `levantar-necesidades-ui`, que dependen de que se ejecuten D2 (discovery) y D5 (validación de mockups).

**Recomendaciones:** 40 fichas (17 UX + 23 UI). 9 son de prioridad alta: REC-UX-001, 003, 008, 012, 014 y REC-UI-001, 003, 008, 023.

---

## 📋 Recomendaciones Específicas y Accionables

### **🚨 ACCIÓN INMEDIATA REQUERIDA (CRÍTICOS)**

> No hay gaps CRÍTICOS según la fórmula. Esta sección agrupa los 3 subcriterios críticos con puntaje < 12 y las 3 dependencias externas que condicionan componentes concretos.

#### **REC-C001: Declarar supuesto de crecimiento y límites de escalabilidad (GAP-C001)**
- **Pregunta:** ¿Qué crecimiento debe soportar la plataforma a 12 y 36 meses (número de categorías, años de histórico, fuentes, analistas activos)? ¿Qué límite se acepta antes de rediseñar?
- **Tipo de información:** Proyección de negocio y supuesto de dimensionamiento
- **Fuente:** Product Owner (Negocio)
- **Prioridad:** ⏳ **CRÍTICO (no bloqueante)**
- **Impacto si no se resuelve:** El almacenamiento documental, la persistencia y el pipeline de extracción se dimensionan solo para el MVP, con riesgo de rediseño al ampliar categorías o años.
- **Acciones:** 1) El PO define un escenario de referencia (p. ej. ×5 categorías y ×2 años en 24 meses). 2) Arquitectura lo registra como supuesto y ADR de dimensionamiento. 3) Se valida que NFR-EVO-001/002 cubran el escenario.

#### **REC-C002: Precisar infraestructura existente, techo de costo y capacidad operativa (GAP-C002)**
- **Pregunta:** ¿Cuál es el costo mensual máximo aceptable de operación? ¿Qué planes y límites tienen Railway y PostgreSQL actuales? ¿Qué tiempo de reacción ante fallas puede garantizar el PO?
- **Tipo de información:** Restricción organizacional y operativa
- **Fuente:** Product Owner (Negocio/Técnico)
- **Prioridad:** ⏳ **CRÍTICO (no bloqueante)**
- **Impacto si no se resuelve:** No se puede justificar objetivamente la reutilización de infraestructura frente a servicios gestionados, ni el nivel de automatización operativa requerido.
- **Acciones:** 1) Fijar un techo de costo mensual de referencia. 2) Inventariar planes, versiones y límites de Railway/PostgreSQL. 3) Declarar la ventana de atención del operador único.

#### **REC-C003: Mapear dependencias entre épicas y secuencia de releases (GAP-C003)**
- **Pregunta:** ¿En qué orden se construyen y liberan las épicas e HUs? ¿Qué incremento mínimo demuestra el flujo extremo a extremo SECOP → señal → evidencia?
- **Tipo de información:** Planeación de producto
- **Fuente:** Product Owner + análisis (workflow de dependencias de HUs)
- **Prioridad:** ⏳ **CRÍTICO (no bloqueante)**
- **Impacto si no se resuelve:** Orden de construcción subóptimo y entregas incrementales sin valor demostrable.
- **Acciones:** 1) Ejecutar *analisis-dependencias-historias-usuario* en una nueva sesión. 2) Definir el release 1 como *walking skeleton* del flujo de extremo a extremo. 3) Validar la secuencia con el PO.

#### **REC-E001: Resolver INV-01, base tributaria del IVA en TVEC**
- **Pregunta:** ¿Los precios unitarios de TVEC incluyen IVA, y cómo se determina de forma confiable por orden o ítem?
- **Tipo de información:** Investigación de datos / regla de negocio
- **Fuente:** Investigación sobre datos TVEC + Colombia Compra Eficiente (documentación de acuerdos marco)
- **Prioridad:** ❌ **BLOQUEA EL COMPONENTE** (cierre analítico del Benchmark 1)
- **Impacto si no se resuelve:** Riesgo de violar NFR-CAL-006 (0 % de mezcla de IVA) o excluir TVEC del Benchmark 1.
- **Acciones:** 1) Revisar la documentación de los acuerdos marco de televisores. 2) Contrastar una muestra de órdenes con sus documentos. 3) Documentar la regla y actualizar A-049/A-120/A-122.

#### **REC-E002: Completar D4-4, precisión real de extracción**
- **Pregunta:** ¿Cuál es la precisión real global y por campo del extractor sobre la muestra validada, y qué umbral de aceptación automática se adopta?
- **Tipo de información:** Validación técnica
- **Fuente:** Product Owner (validación de las 228 filas de la plantilla D4)
- **Prioridad:** ⏳ **CONDICIONA COMPONENTE** (extracción IA y cola de revisión)
- **Impacto si no se resuelve:** No se puede calibrar la aceptación automática (A-194) ni dimensionar la cola de revisión humana.
- **Acciones:** 1) Completar la plantilla D4_plantilla_validacion_PO.xlsx. 2) Calcular la precisión con las fórmulas de A-203. 3) Fijar el umbral y convertir la muestra en *golden dataset*.

#### **REC-E003: Revisar ToS de Alkosto y Falabella**
- **Pregunta:** ¿Los términos de uso permiten la lectura automatizada de páginas públicas de producto en los términos de NFR-CUM-002 a 005?
- **Tipo de información:** Revisión jurídica / compliance
- **Fuente:** Product Owner + asesoría jurídica puntual
- **Prioridad:** ⏳ **BLOQUEA PRODUCCIÓN DE LA CAPTURA RETAIL** (no el MVP: existe carga manual y CSV)
- **Impacto si no se resuelve:** El Benchmark 2 depende solo de carga manual.
- **Acciones:** 1) Revisar los ToS vigentes. 2) Documentar la conclusión (NFR-CUM-006). 3) Si se restringe, priorizar el canal manual/CSV.

### **⚠️ RESOLUCIÓN EN DISCOVERY (IMPORTANTES)**

#### **REC-I001: Perfil técnico del mantenedor y estándares (GAP-I001)**
- **Pregunta:** ¿Qué lenguajes, frameworks y plataformas domina o prefiere el PO como mantenedor? ¿Qué tiempo objetivo se espera para cambios típicos (parámetro, conector, categoría)?
- **Objetivo:** Elegir un stack que una sola persona apoyada en agentes pueda mantener.
- **Fuente:** Product Owner (Técnico)
- **Prioridad:** Importante · **Impacto si no se resuelve:** stack difícil de mantener por un único operador.
- **Esfuerzo:** Bajo (2 h)
- **Entregable:** Sección "Perfil del mantenedor" en el Brief o PRD + estándares de código (workflow *generar-estandares-codigo*)

#### **REC-I002: Estrategia de pruebas y arnés de evaluación IA (GAP-I002)**
- **Pregunta:** ¿Qué niveles de prueba y cobertura se exigen? ¿Cómo se detecta una regresión de precisión al cambiar de modelo o prompt?
- **Objetivo:** Sostener NFR-CAL-001 (≥90 %) en el tiempo y reducir el retrabajo.
- **Fuente:** Arquitecto + PO
- **Prioridad:** Importante · **Impacto si no se resuelve:** degradación silenciosa de la precisión e incertidumbre en la estimación.
- **Esfuerzo:** Medio (1–2 días en el diseño)
- **Entregable:** Estrategia de pruebas en la arquitectura detallada + *golden dataset* versionado (D4-4) + mocks de Socrata/retail

#### **REC-I003: Equipo y dedicación (GAP-I003)**
- **Pregunta:** ¿Quién construye (agentes, PO, apoyo humano)? ¿Cuántas horas por semana dedica el PO a desarrollo, revisión humana, carga manual y operación?
- **Objetivo:** Estimar de forma realista y dimensionar la automatización operativa.
- **Fuente:** Product Owner (Negocio)
- **Prioridad:** Importante (impacto 3) · **Impacto si no se resuelve:** estimaciones irreales y sobrecarga del operador único.
- **Esfuerzo:** Bajo (1 h)
- **Entregable:** Tabla de capacidad del equipo en el Brief

#### **REC-I004: Despliegue, entornos y políticas de datos (GAP-I004)**
- **Pregunta:** ¿Se exige residencia de datos en Colombia o región específica? ¿Se autoriza enviar documentos públicos con datos personales a un proveedor IA externo? ¿Qué entornos se requieren?
- **Objetivo:** Habilitar la selección de nube, región y proveedor IA, y el diseño del pipeline.
- **Fuente:** PO (decisión) + Arquitecto (propuesta de entornos, CI/CD y rollback)
- **Prioridad:** Importante · **Impacto si no se resuelve:** selección de proveedor no conforme con la Ley 1581 y despliegues manuales riesgosos.
- **Esfuerzo:** Medio (decisión de 1 h + ADRs en el diseño)
- **Entregable:** ADR de entornos y despliegue + decisión documentada de residencia y uso de IA externa

#### **REC-I005: Modelo de datos lógico y máquina de estados (GAP-I005)**
- **Pregunta:** ¿Cuáles son las entidades canónicas, sus relaciones, versionado y estados a lo largo del pipeline?
- **Objetivo:** Base única de persistencia y trazabilidad coherente entre las 113 HUs.
- **Fuente:** Arquitecto (derivación de FRs y asunciones) + validación del PO
- **Prioridad:** Importante (se puede inferir) · **Impacto si no se resuelve:** inconsistencias entre HUs y retrabajo de persistencia.
- **Esfuerzo:** Medio (1–2 días)
- **Entregable:** Modelo lógico + diagrama de estados del ítem en la arquitectura de solución

#### **REC-I006: Clasificación de sensibilidad y cifrado (GAP-I006)**
- **Pregunta:** ¿Qué niveles de sensibilidad aplican y qué cifrado y controles corresponden a cada uno? ¿Qué garantías contractuales debe dar el proveedor IA (no retención, no entrenamiento, región)?
- **Objetivo:** Cumplir la Ley 1581 y guiar la selección de almacenamiento y proveedor IA/OCR.
- **Fuente:** Arquitecto + PO
- **Prioridad:** Importante · **Impacto si no se resuelve:** exposición de datos personales y proveedor no conforme.
- **Esfuerzo:** Bajo-Medio (medio día)
- **Entregable:** Tabla de clasificación de datos + requisitos al proveedor IA

#### **REC-I007: Orquestación e integración IA/OCR (GAP-I007)**
- **Pregunta:** ¿Cómo se programan, encolan, reintentan y reprocesan los jobs de manera idempotente? ¿Cómo se abstrae el proveedor IA para poder cambiarlo? ¿Cómo se detectan cambios de esquema en Socrata?
- **Objetivo:** Pipeline resiliente y desacoplado del proveedor.
- **Fuente:** Arquitecto + verificación técnica de A-014 (relación ítem↔orden TVEC)
- **Prioridad:** Importante · **Impacto si no se resuelve:** pipeline frágil, lock-in del proveedor IA y fallas silenciosas de ingesta.
- **Esfuerzo:** Medio (1–2 días)
- **Entregable:** ADR de orquestación + puerto/adaptador IA + validación de esquema en la ingesta

### **ℹ️ REFINAMIENTO POSTERIOR (MENORES)**

| Rec. | Gap | Pregunta / Acción | Fuente | Fase | Esfuerzo |
|---|---|---|---|---|---|
| REC-M001 | GAP-M001 | Definir OpenAPI de la API interna, JSON Schema de salida del extractor y catálogo de errores | Arquitecto | Durante diseño | Medio |
| REC-M002 | GAP-M002 | Definir tooltips, ayuda contextual y contenido del onboarding | UX/UI + PO | Posterior (D5) | Bajo |
| REC-M003 | GAP-M003 | Registrar mejoras UX opcionales en el backlog Post-MVP | PO | Posterior | Bajo |
| REC-M004 | GAP-M004 | Refinamientos visuales tras los mockups | UX/UI | Posterior (D5) | Bajo |
| REC-M005 | GAP-M005 | Runbooks mínimos: prueba de restauración, rotación de secretos, limpieza de temporales | Arquitecto | Durante diseño | Bajo |
| REC-M006 | GAP-M006 | Onboarding mínimo en producto | PO + UX | Posterior | Bajo |
| REC-M007 | GAP-M007 | SLA interno de atención de reportes de error | PO | Posterior | Bajo |
| REC-M008 | GAP-M008 | Configuración por ambiente y niveles o formato de log | Arquitecto | Durante diseño | Bajo |
| REC-M009 | GAP-M009 | Paleta, tipografía, iconografía y codificación visual de confianza | UX/UI | Posterior (D5) | Medio |
| REC-M010 | GAP-M010 | Caché, índices y precálculo de agregados | Desarrollo | Implementación | Bajo |
| REC-M011 | GAP-M011 | Pool de conexiones y memoria de workers | Desarrollo | Implementación | Bajo |

### **🗂️ Agrupación de Recomendaciones**

**Por stakeholder responsable:**

| Stakeholder | Recomendaciones |
|---|---|
| **Product Owner — Negocio** | REC-C001, REC-C002, REC-C003, REC-I003, REC-M003, REC-M007 |
| **Product Owner — Decisiones técnicas o regulatorias** | REC-I001, REC-I004 (residencia de datos y uso de IA externa), REC-E002, REC-E003 |
| **Investigación de datos** | REC-E001 (INV-01), verificación A-014 (en REC-I007) |
| **Arquitecto / Técnico** | REC-I002, REC-I004 (entornos y CI/CD), REC-I005, REC-I006, REC-I007, REC-M001, REC-M005, REC-M008 |
| **UX/UI** | REC-M002, REC-M004, REC-M006, REC-M009 |
| **Desarrollo** | REC-M010, REC-M011 |

**Por fase de resolución:**

| Fase | Recomendaciones |
|---|---|
| **Antes de arquitectura** | REC-C002, REC-I001, REC-I003, REC-I004 (decisión de residencia e IA externa) |
| **Durante el diseño de arquitectura** | REC-C001, REC-C003, REC-I002, REC-I004 (entornos), REC-I005, REC-I006, REC-I007, REC-M001, REC-M005, REC-M008 |
| **En paralelo / antes de cerrar componentes** | REC-E001 (Benchmark 1), REC-E002 (extracción IA), REC-E003 (captura retail) |
| **Posterior (UX/UI e implementación)** | REC-M002, REC-M003, REC-M004, REC-M006, REC-M007, REC-M009, REC-M010, REC-M011 |

**Por esfuerzo requerido:**

| Esfuerzo | Recomendaciones |
|---|---|
| **Bajo** (≤ medio día) | REC-C002, REC-I001, REC-I003, REC-I006, REC-M002 a M008, REC-M010, REC-M011 |
| **Medio** (1–3 días) | REC-C001, REC-C003, REC-I002, REC-I004, REC-I005, REC-I007, REC-M001, REC-M009, REC-E002, REC-E003 |
| **Alto** (≥ 1 semana) | REC-E001 (INV-01: depende de investigación externa) |

### **📊 Cronograma de Resolución**
- **Semana 1:** Sesión de decisiones del PO (REC-C002, REC-I001, REC-I003, REC-I004 decisión). Arranque de REC-E001 (INV-01) y REC-E002 (D4-4). REC-C003 (dependencias de HUs).
- **Semana 2:** Arquitectura de solución con REC-C001, REC-I005, REC-I006, REC-I007, REC-I002 y REC-I004 (entornos/CI-CD). Revisión de ToS retail (REC-E003).
- **Semana 3:** Cierre de INV-01 y D4-4 e incorporación al diseño del Benchmark 1 y del umbral de extracción. Recomendaciones menores de diseño (REC-M001, M005, M008).

---

## 🎯 Próximos Pasos Priorizados

### Acciones Inmediatas Recomendadas
1. **Sesión de decisiones del PO (antes de arquitectura, ~1 día):** declarar la composición del equipo y la dedicación semanal por actividad (GAP-I003), el perfil técnico y las tecnologías preferidas del mantenedor (GAP-I001), el techo de costo mensual y la disponibilidad operativa (GAP-C002), y la política de residencia de datos y uso de proveedores IA externos con documentos que contienen datos personales (GAP-I004/I006). Estas cuatro respuestas condicionan la selección de stack, nube y proveedor IA.
2. **Cerrar las dependencias externas abiertas (en paralelo a la arquitectura, 1–2 semanas):** resolver INV-01 (base tributaria del IVA en TVEC, que bloquea el cierre analítico del Benchmark 1), completar D4-4 (precisión real y umbral de aceptación automática sobre las 228 filas) y revisar los ToS de Alkosto y Falabella (bloquean la captura retail en producción).
3. **Incorporar a la arquitectura de solución los elementos inferibles (durante el diseño, 2–3 días):** derivar el modelo de datos lógico y la máquina de estados del ítem (GAP-I005), definir el patrón de orquestación de jobs y la abstracción del proveedor IA/OCR (GAP-I007), declarar el supuesto de crecimiento (GAP-C001) y la estrategia de pruebas con *golden dataset* de D4-4 (GAP-I002).

### Detalles de Recomendaciones

#### **🎯 Criterios de Éxito por Recomendación**

**CRÍTICAS:**
- ✅ Supuesto de crecimiento a 12 y 36 meses documentado y usado como ADR de dimensionamiento (REC-C001)
- ✅ Techo de costo mensual, límites de la infraestructura existente y ventana de atención del PO documentados (REC-C002)
- ✅ Mapa de dependencias entre épicas y release 1 (*walking skeleton*) aprobado por el PO (REC-C003)
- ✅ INV-01 resuelto con regla documentada y asunciones actualizadas (REC-E001)
- ✅ D4-4 cerrado con precisión global y por campo calculada y umbral de aceptación fijado (REC-E002)
- ✅ Conclusión documentada sobre los ToS de Alkosto y Falabella (REC-E003)

**IMPORTANTES:**
- ✅ Perfil técnico del mantenedor, capacidad del equipo y dedicación del PO registrados en el Brief (REC-I001, REC-I003)
- ✅ Decisión de residencia de datos y uso de IA externa documentada, con ADR de entornos, CI/CD y rollback (REC-I004)
- ✅ Modelo de datos lógico y máquina de estados del ítem validados por el PO (REC-I005)
- ✅ Clasificación de datos con cifrado por nivel y requisitos al proveedor IA definidos (REC-I006)
- ✅ ADR de orquestación de jobs, puerto/adaptador IA y validación de esquema de ingesta definidos (REC-I007)
- ✅ Estrategia de pruebas con *golden dataset* versionado (REC-I002)

**MENORES:**
- ✅ Las 11 recomendaciones menores registradas en el backlog o en la arquitectura detallada con fase asignada (REC-M001 a M011)

#### **⏰ Timeline Recomendado**
- **Inmediato (2 días):** Sesión de decisiones del PO (equipo, dedicación, perfil técnico, costo, residencia de datos, IA externa) y arranque de INV-01 y D4-4
- **Discovery (Semana 1):** Análisis de dependencias de HUs, investigación de INV-01, validación D4-4 y revisión de ToS retail
- **Pre-Arquitectura (Semana 2):** Arquitectura de solución que incorpora modelo de datos, orquestación, clasificación de datos, supuesto de crecimiento, entornos y estrategia de pruebas. Cierre de INV-01 y D4-4 en la semana 3 para completar el Benchmark 1 y la extracción.


---

##  Control de Versiones

| Versión | Fecha          | Autor       | Cambios                               |
| ------- | -------------- | ----------- | ------------------------------------- |
| 1.0     | 2026-10-05         | Juan Camilo | Validación inicial de completitud PRD |
| 1.1     | 2026-10-06         | Juan Camilo | Re-evaluación con el documento de resolución de gaps: 69.1% · 1 gap crítico · ⚠️ PARCIALMENTE APTO - Requiere mejoras importantes |
| 1.2     | 2026-10-06         | Juan Camilo | Re-evaluación con la adenda de dimensionamiento (S-DIM-01..06): 71.1% · 0 gaps críticos · ⚠️ APTO CON RESERVAS - Completar gaps críticos · validación obligatoria superada |

---

> **Método Ceiba validar prd** v6.1.96 | Modelo: Claude Opus 5.5 | Usuario: {Juan Camilo} | Fecha: {2026-10-05}