# ÉPICA-005: Señales que Merecen Revisión, con Evidencia

**Volver a:** [Índice de Épicas](../../epicas.md)

---

## Resumen

Es el corazón de la propuesta de valor: compara el precio unitario de cada televisor contra el **Benchmark 1 (compras públicas: SECOP II + TVEC)** y el **Benchmark 2 (mercado: Alkosto y Falabella)**, con reglas de temporalidad, base tributaria y emparejamiento, y produce una **"señal que merece revisión"** cuando la desviación al alza lo justifica según una estrategia híbrida configurable (atípicos Q3 + 1,5 × IQR con muestra suficiente y homogénea; si no, +30 % mismo modelo / +50 % equivalente). Los precios anormalmente bajos van a revisión de calidad. Cada señal guarda una instantánea de evidencia completa e inmutable, con confianza explicable (un precio `derivado` reduce la confianza), navegación hasta el documento y la página de origen, y advertencia de no conclusión. El Benchmark 2 se degrada a "no disponible" sin bloquear el Benchmark 1. Incluye la calificación de señales por los Analistas (KPI de validación humana) y el mecanismo de reporte y gestión de errores.

Todos los valores de ventanas, mínimos, umbrales, penalizaciones de confianza, tarifa de IVA y base tributaria de la TVEC son **parámetros configurables** con configuración inicial; no son verdades fijas.

**Prioridad:** Crítica  
**FRs cubiertos:** FR-054 a FR-070  
**Total HU:** 15 historias  
**Estado:** ✅ Generadas y Aprobadas

---

## Features y Historias de Usuario

### Feature 1: Selección de Comparables

- [HU-054: Seleccionar comparables públicos del Benchmark 1 con ventana temporal configurable](./HU-054-seleccionar-comparables-benchmark-1/historia.md) — FR-055, FR-062
- [HU-055: Seleccionar observaciones retail del Benchmark 2 cercanas a la fecha de la compra](./HU-055-seleccionar-observaciones-benchmark-2/historia.md) — FR-056, FR-062
- [HU-056: Homologar la base tributaria (IVA) y marcar comparaciones incompletas](./HU-056-homologar-base-tributaria-iva/historia.md) — FR-057

### Feature 2: Cálculo de Benchmarks

- [HU-057: Calcular el Benchmark 1 – Contratación pública y la desviación del precio contratado](./HU-057-calcular-benchmark-1-compras-publicas/historia.md) — FR-054, FR-058, FR-059, FR-061
- [HU-058: Calcular el Benchmark 2 – Mercado con degradación a "no disponible"](./HU-058-calcular-benchmark-2-mercado/historia.md) — FR-058, FR-059, FR-060, FR-061

### Feature 3: Generación y Confianza de Señales

- [HU-059: Generar la «señal que merece revisión» por desviación al alza con regla híbrida configurable](./HU-059-generar-senal-desviacion-al-alza/historia.md) — FR-063
- [HU-060: Dirigir los precios anormalmente bajos a la cola de revisión de calidad](./HU-060-enviar-precios-bajos-revision-calidad/historia.md) — FR-063
- [HU-061: Calcular el nivel de confianza de la comparación y de la señal](./HU-061-calcular-confianza-de-la-senal/historia.md) — FR-068

### Feature 4: Presentación de Evidencia Trazable

- [HU-062: Registrar la evidencia completa y reproducible de cada señal](./HU-062-registrar-evidencia-de-la-senal/historia.md) — FR-065
- [HU-063: Ver el detalle de una señal con su comparación, su evidencia y la advertencia de no conclusión](./HU-063-ver-detalle-de-la-senal/historia.md) — FR-065, FR-067, FR-062, FR-059, FR-060
- [HU-064: Navegar desde la señal hasta el contrato, el documento y la página de origen, y cada observación de referencia](./HU-064-navegar-a-evidencia-de-origen/historia.md) — FR-066
- [HU-065: Garantizar lenguaje no acusatorio en todos los textos generados por el sistema](./HU-065-garantizar-lenguaje-no-acusatorio/historia.md) — FR-064

### Feature 5: Validación Humana de Señales

- [HU-066: Calificar una señal como suficientemente sustentada para merecer revisión](./HU-066-calificar-senal-sustentada/historia.md) — FR-069
- [HU-067: Reportar un error en un dato o en una señal](./HU-067-reportar-error-dato-o-senal/historia.md) — FR-070
- [HU-068: Gestionar los reportes de error y registrar su resolución](./HU-068-gestionar-reportes-de-error/historia.md) — FR-070

---

## Matriz de Trazabilidad

| HU | FR | Rol Principal | Valor de Negocio |
|---|---|---|---|
| HU-054 | FR-055, FR-062 | Analista | Comparables públicos correctos por emparejamiento y ventana (±6/±12 meses configurable), con origen SECOP II/TVEC |
| HU-055 | FR-056, FR-062 | Analista | Nunca juzgar una compra antigua con un precio actual (±30 días configurable); origen y método de cada observación retail |
| HU-056 | FR-057 | Analista | 0 comparaciones mezclando IVA sin marca; TVEC indeterminada hasta INV-01 |
| HU-057 | FR-054, FR-058, FR-059, FR-061 | Analista | Distribución, mediana y desviación del Benchmark 1; evidencia limitada por debajo del mínimo (≥ 5) |
| HU-058 | FR-058, FR-059, FR-060, FR-061 | Analista | Referencia de mercado (≥ 3 de 2 fuentes) o "no disponible" sin bloquear el Benchmark 1 |
| HU-059 | FR-063 | Analista | Priorización de casos con regla híbrida configurable, solo al alza |
| HU-060 | FR-063 | Administrador | Precios anormalmente bajos a revisión de calidad, nunca como señal |
| HU-061 | FR-068 | Analista | Confianza explicable; precio derivado reduce la confianza |
| HU-062 | FR-065 | Analista | Trazabilidad 100 % y reproducibilidad por versión de señal |
| HU-063 | FR-065, FR-067, FR-062, FR-059, FR-060 | Analista | Evaluar la señal en una vista, con advertencia de no conclusión |
| HU-064 | FR-066 | Analista | Evidencia de origen en ≤ 3 clics |
| HU-065 | FR-064 | Administrador | 0 textos acusatorios generados por el sistema (verificable) |
| HU-066 | FR-069 | Analista | Insumo del KPI ≥ 70 % de señales sustentadas |
| HU-067 | FR-070 | Analista | Mecanismo de corrección accesible desde la señal |
| HU-068 | FR-070 | Administrador | Gestión trazable de los reportes de error |

---

## Exclusiones Explícitas de Esta Épica

- NO incluye señales que no son de precio (concentración, contratación directa, presupuesto vs. contratado): candidatas post-MVP (ÉPICA-009).
- NO incluye rankings de entidades ni de proveedores.
- NO incluye conclusiones automáticas ni lenguaje acusatorio.
- NO incluye detección proactiva con alertas automáticas.
- NO incluye contraste con antecedentes de Contraloría o prensa (RAG).

---

**Última actualización:** 2026-10-02  
**Generado por:** Workflow generar-historias-usuario

> **Método Ceiba generar hus** v6.1.95 | Modelo: claude-opus-5-5 | Usuario: Juan Camilo | Fecha: 2026-10-02
