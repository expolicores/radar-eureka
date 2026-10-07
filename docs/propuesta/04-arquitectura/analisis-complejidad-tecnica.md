# Análisis de Complejidad Técnica

**Proyecto:** Seguimiento Compras Públicas
**Fecha:** 2026-10-06
**Arquitecto:** Juan Camilo
**Documento de Arquitectura:** docs/propuesta/04-arquitectura/arquitectura-solucion-comercial.md (v1.0, 2026-10-06) + adenda-dimensionamiento-arquitectura-mvp.md
**Documento de Tareas Técnicas:** docs/propuesta/04-arquitectura/tareas-tecnicas-arquitectura.md (138 tareas, 12 categorías)

---

## Resumen Ejecutivo

**Contexto del análisis.** Se evaluó la complejidad técnica del MVP de **Seguimiento Compras Públicas** a partir de la arquitectura de solución (v1.0, 2026-10-06), su adenda de dimensionamiento y el inventario de **138 tareas técnicas** en 12 categorías, con el PRD, las épicas y el brief de alcance como referencia. La solución es un monolito modular en Python y React desplegado en Railway sobre PostgreSQL y Cloudflare R2, con un pipeline asíncrono por etapas, extracción documental con IA multimodal (Anthropic Claude) y un núcleo determinístico de normalización, comparación y señales.

**Resultado principal.** La puntuación total es **26/45**, que produce un **FAC de 1.035** y un nivel de complejidad **Medio**, ligeramente por encima del valor central de la escala.

**Factores de mayor impacto.** Cinco factores alcanzan 4/5; los tres de mayor peso para el proyecto son:

1. **Lógica de Proceso Interno Compleja (4/5):** modelo analítico propio de señales con reglas encadenadas de precio derivado, base tributaria, emparejamiento, selección de comparables, estadísticos, confianza y reproducibilidad por versión de configuración.
2. **Complejidad del Prompt y Refinamiento (4/5):** más de ocho restricciones transversales por tarea para los agentes de desarrollo y prompts de extracción en el producto calibrados contra un golden dataset.
3. **Comunicación de Datos (4/5):** seis interfaces externas heterogéneas, algunas inestables o sujetas a reglas de cumplimiento.

Facilidad de Operación (4/5) y Verificación y Hardening (4/5) completan el grupo alto, mientras que Proceso Distribuido (2), Rendimiento (2), Tasa de Transacciones (1) y Legacy (1) moderan el resultado.

**Implicación para el proyecto.** La complejidad no proviene de la escala ni de la infraestructura, sino de la corrección analítica, de la integración con fuentes externas y del rigor operativo, de seguridad y de cumplimiento exigido a un sistema operado por una sola persona. El ajuste global del esfuerzo es moderado, pero su distribución es desigual: se concentra en los módulos de dominio analítico y de IA y en el trabajo transversal de operación y verificación. La incertidumbre de la estimación depende de los resultados de las pruebas de concepto y de los gates externos, por lo que el FAC debe revisarse cuando estos se cierren.

---

## Tabla de Evaluación de Factores

| # | Factor de Complejidad | Valor | Justificación |
|---|----------------------|-------|---------------|
| 1 | Comunicación de Datos | 4 | 6 interfaces externas funcionales y heterogéneas sobre HTTP (SoQL, descarga binaria, S3, LLM multimodal, retail JSON-LD, correo) con transformación y manejo de errores propios |
| 2 | Proceso Distribuido | 2 | Monolito modular en 3 procesos (web, worker, dispatch) coordinados por cola de jobs en PostgreSQL con coreografía, idempotencia y consistencia eventual; sin microservicios ni transacciones distribuidas |
| 3 | Objetivos de Rendimiento | 2 | Metas en segundos/minutos (≤ 3 s p95 con 20 concurrentes, extracción ≤ 5 min p95, recálculo ≤ 1 h) que exigen vistas materializadas, índices y pruebas de carga, sin latencias sub-segundo |
| 4 | Lógica de Proceso Interno Compleja | 4 | Modelo analítico propio de señales: precio derivado (6 condiciones), base tributaria, emparejamiento en 3 niveles, comparables escalonados, IQR + umbral, confianza compuesta y reproducibilidad por versión de configuración |
| 5 | Tasa de Transacciones | 1 | Volumen bajo: < 1.000 jobs/día (pico 20.000/día ≈ 14/min) y 20 usuarios concurrentes; decenas de transacciones/minuto en el pico, sin diseño de escalabilidad específico |
| 6 | Facilidad de Operación | 4 | CI/CD automatizado con aprobación manual, E2E, rollback ≤ 15 min y pipelines de evaluación IA; observabilidad (logs con correlation_id, Sentry, métricas, alertas funcionales, KPIs, costos); DR probado; sin autoescalado |
| 7 | Complejidad del Prompt y Refinamiento | 4 | Más de 8 restricciones transversales por tarea, lógica de dominio densa, 10 POC que definen el diseño y prompts de extracción multimodal en producto calibrados contra golden dataset (ratio esperado ≈ 3–4) |
| 8 | Verificación y Hardening | 4 | Cobertura ≥ 80 % en dominio, pruebas unitarias/propiedades/integración/E2E/autorización/términos prohibidos, autenticación propia, SSRF y archivos maliciosos, OWASP + ZAP como gate y cumplimiento Ley 1581 |
| 9 | Integración de Legacy o Código Existente | 1 | Código greenfield; solo se consumen plataformas de gobierno existentes (SECOP II/TVEC) vía API pública documentada con esquemas cambiantes y se reutilizan como insumo los spikes D1/D4/D6 |
| | **TOTAL** | **26/45** | |

---

## Cálculo del Factor de Ajuste de Complejidad (FAC)

**Fórmula:** FAC = 0.775 + (0.01 × Puntuación Total)

**Cálculo:**
- Puntuación Total: 26
- FAC = 0.775 + (0.01 × 26) = **1.035**

### Interpretación del FAC

| Rango FAC | Nivel | Tu Proyecto |
|-----------|-------|-------------|
| 0.775 - 0.90 | Bajo |  |
| 0.90 - 1.00 | Medio-Bajo |  |
| 1.00 - 1.10 | Medio | **← AQUÍ (1.035)** |
| 1.10 - 1.20 | Medio-Alto |  |
| 1.20 - 1.225 | Alto |  |

**Nivel de Complejidad:** Medio

Con una puntuación de 26/45, el FAC de **1.035** ubica el proyecto en complejidad **Media**, ligeramente por encima del valor central (1.0 con 22,5 puntos). El resultado no es homogéneo: combina cinco factores altos (4/5) con cuatro factores bajos (1–2/5), y esa polarización es más informativa que el promedio.

**Implicaciones para la estimación:**

- El esfuerzo base estimado para las historias de usuario y las tareas técnicas debe ajustarse al alza en aproximadamente un **3,5 %** a nivel global.
- El ajuste global diluye la concentración de complejidad: el esfuerzo adicional no se reparte de forma uniforme, sino que se concentra en los módulos de Extracción, Catálogo de productos, Comparación y Señales, Identidad y Acceso y en el trabajo transversal de operación y CI/CD.
- Las historias de los módulos de Ingesta, Exploración e Investigación, de naturaleza más estándar, quedan cubiertas por el esfuerzo base con un margen bajo de ajuste.

**Áreas de mayor complejidad identificadas:**

- **Lógica de dominio (F4 = 4):** el modelo analítico propio de señales (precio derivado, base tributaria, emparejamiento en tres niveles, comparables escalonados, regla de señal híbrida, confianza compuesta y reproducibilidad por versión de configuración).
- **Prompt y refinamiento (F7 = 4):** más de ocho restricciones transversales por tarea y la ingeniería de prompts del propio producto, calibrada contra un golden dataset.
- **Comunicación de datos (F1 = 4):** seis interfaces externas heterogéneas, varias inestables o con reglas de cumplimiento.
- **Operación (F6 = 4) y verificación (F8 = 4):** cerca del 65 % del inventario de tareas técnicas (operación, seguridad y pruebas) para un sistema que debe ser operable por una sola persona y superar gates de seguridad y cumplimiento antes del piloto.

**Factores que reducen la complejidad:** el monolito modular sobre una sola base de datos (F2 = 2), las metas de rendimiento holgadas (F3 = 2), el bajo volumen transaccional (F5 = 1) y el carácter greenfield (F9 = 1) evitan que el FAC llegue al rango Medio-Alto.

**Factores que requieren atención:** F4 y F7 se refuerzan mutuamente, porque la lógica de dominio densa es precisamente la que más iteraciones exige a los agentes de desarrollo. Ambos dependen de los resultados de las pruebas de concepto (POC-003 y POC-008) y del gate D4-4, por lo que la incertidumbre de estimación es mayor en las releases R2 y R3.

---

## Detalle por Factor

### Factor 1: Comunicación de Datos

**Valor Asignado:** 4/5

**Tareas Técnicas Relacionadas:**
- INT-001 a INT-014 (credenciales, Socrata, SECOP II, TVEC, Archivos Descarga, repositorio documental, almacén de objetos, ExtractorIA, artefactos de IA, control de costo, conectores Alkosto y Falabella, correo, pruebas de integración)
- LBC-BE-008 (puertos y cliente HTTP compartido)
- SEG-008 (protección SSRF en descargas)
- PIP-BE-005 (contract tests de datasets externos)
- POC-003, POC-007 (extracción multimodal, captura retail)
- INF-006, INF-008 (R2 y credenciales de mínimo privilegio)
- OBS-001, OBS-002 (Sentry, monitor externo)
- AMB-006 (adaptadores reales o fake por ambiente)

**Justificación Detallada:**
El sistema integra seis interfaces externas funcionalmente críticas, cada una con un estilo de integración distinto: (1) la API Socrata de datos.gov.co con consultas SoQL paginadas, marcas de agua con solape de 24 h, lista blanca de campos y la relación ítem-orden entre tres datasets más los anuales de Archivos Descarga (INT-002 a INT-005); (2) la descarga binaria desde community.secop.gov.co en streaming con cálculo de SHA-256, timeout de 120 s, ritmo controlado y protección SSRF sin seguir redirecciones (INT-006, SEG-008); (3) el almacén de objetos por API S3 (R2 en producción, MinIO en local) con escritura por hash sin sobrescritura, URL firmadas y tres juegos de credenciales de mínimo privilegio (INT-007, INF-008); (4) la API de Anthropic con mensajes multimodales, salida estructurada validada con Pydantic, timeout de 300 s, reintentos y registro de tokens y costo (INT-008); (5) la captura retail de Alkosto y Falabella con verificación de robots.txt en cada ejecución, sitemaps, extracción de JSON-LD, presupuesto y suspensión ante 403/429/CAPTCHA (INT-011, INT-012); y (6) el correo transaccional por API HTTP con reintentos (INT-013). Sentry y el monitor externo son interfaces de soporte de baja complejidad. Todas las interfaces usan HTTP/HTTPS y protocolos estándar y documentados (no hay SOAP, mainframes ni sockets binarios), y el patrón de puertos y adaptadores (ADR-005, LBC-BE-008) encapsula reintentos, ritmos y cumplimiento, lo que evita el nivel crítico. Sin embargo, la diversidad de paradigmas, la volatilidad de las fuentes externas (R-06, R-07, mitigada con contract tests en PIP-BE-005) y la exigencia de pruebas de integración con fallos inyectados para cada adaptador (INT-014) sitúan el factor en un nivel alto.

---

### Factor 2: Proceso Distribuido

**Valor Asignado:** 2/5

**Tareas Técnicas Relacionadas:**
- POC-001 (walking skeleton con 3 servicios desde la misma imagen)
- POC-002 (cola de jobs sobre PostgreSQL: SKIP LOCKED/Procrastinate, latido, huérfanos)
- LBC-BE-005 (esqueleto del worker, colas y apagado ordenado)
- LBC-BE-006 (dispatcher con idempotency_key por ventana)
- COM-002 (catálogo de tipos de job con payload versionado)
- COM-003 (encadenamiento por coreografía en la misma transacción)
- COM-004 (recálculo con agrupación y consistencia eventual)
- INF-003, INF-004, INF-005 (servicios web, worker y scheduler)
- OBS-006 (latido del worker y del dispatcher)
- PIP-INF-003 (despliegue sin interrupción de los 3 servicios)
- TST-009 (idempotencia ante reintentos y concurrencia)

**Justificación Detallada:**
Estructuralmente el sistema es un monolito modular (ADR-001): una base de código, una imagen Docker y una base de datos PostgreSQL, sin microservicios ni broker de mensajes. No obstante, se ejecuta como tres procesos independientes desde la misma imagen —servicio web, worker y dispatcher por cron— que se coordinan de forma asíncrona a través de una cola de jobs en PostgreSQL (ADR-002, ADR-004). Esto introduce problemas propios de los sistemas distribuidos que el código generado debe resolver correctamente: toma concurrente de jobs con SELECT … FOR UPDATE SKIP LOCKED o Procrastinate, cuatro colas con concurrencia configurable, latido y recuperación de jobs huérfanos (POC-002, LBC-BE-005); idempotencia por ventana del dispatcher (LBC-BE-006); encadenamiento por coreografía en el que cada etapa encola la siguiente en la misma transacción en que persiste su resultado (COM-003); recálculo con agrupación por alcance y consistencia eventual de hasta 1 hora mientras se sirven los resultados vigentes (COM-004, S-DIM-04); y apagado ordenado del worker para no perder jobs durante los despliegues (INF-004, POC-001). Al compartir una única base de datos, la consistencia se resuelve con transacciones locales, sin compensaciones, SAGA ni 2PC, y no existen cuatro o más servicios independientes, por lo que el factor no alcanza el nivel significativo. El pipeline asíncrono con semántica efectiva de exactamente una vez y consistencia eventual sí supera la complejidad de un monolito síncrono, lo que equivale a una orquestación simple de 2-3 servicios.

---

### Factor 3: Objetivos de Rendimiento

**Valor Asignado:** 2/5

**Tareas Técnicas Relacionadas:**
- DAT-011 (vistas materializadas, índices compuestos, pg_trgm, tsvector; EXPLAIN ANALYZE)
- OBS-007 (duración y p95 por endpoint)
- TST-010 (pruebas de rendimiento y capacidad: 20 concurrentes y 20.000 jobs/24 h)
- COM-004 (recálculo ≤ 1 h)
- POC-002 (20.000 jobs en ≤ 24 h sin contención)
- POC-005 (procesamiento documental dentro de 1 vCPU / 2 GB; p95 por tipo)
- INT-006 (descarga en streaming sin cargar archivos completos en memoria)
- INF-004 (límites de CPU/RAM del worker)
- LBC-FE-004 (tabla con paginación del servidor)

**Justificación Detallada:**
Las metas de rendimiento definidas en la arquitectura son holgadas y se expresan en segundos, minutos u horas: búsquedas, filtros, ficha y detalle de señal en ≤ 3 s p95 con 20 usuarios concurrentes (NFR-PER-001 a 003); extracción asíncrona en ≤ 5 min p95 por documento (NFR-PER-004); recálculo de benchmarks y señales en ≤ 1 h (S-DIM-04); reprocesamiento de 20.000 jobs en ≤ 24 h manteniendo la web disponible (QS-13); carga histórica en ≤ 7 días (NFR-DAT-004) y rollback en ≤ 15 min (QS-14). Con el volumen del MVP (miles de filas) estas metas se cumplen sin caché ni motor de búsqueda (ADR-013). Aun así, el proyecto contiene trabajo concreto de rendimiento que justifica el extremo superior del rango bajo-moderado: diseño de vistas materializadas con REFRESH CONCURRENTLY, índices compuestos, pg_trgm y búsqueda de texto completo en español verificados con EXPLAIN ANALYZE (DAT-011); medición del p95 por endpoint (OBS-007); pruebas de carga con k6 o Locust sin ambiente de staging (TST-010); procesamiento documental pesado (LibreOffice, PyMuPDF, descompresión) dentro de un worker de 1 vCPU / 2 GB y descargas en streaming (POC-005, INT-006); y la garantía de que un reprocesamiento masivo no degrade la única réplica web que comparte la base de datos. No existen requisitos de latencia inferiores a 500 ms ni percentiles estrictos de alta concurrencia, por lo que el factor no alcanza el nivel significativo.

---

### Factor 4: Lógica de Proceso Interno Compleja

**Valor Asignado:** 4/5

**Tareas Técnicas Relacionadas:**
- POC-008 (reglas de normalización y emparejamiento con datos reales)
- POC-004 (detección determinística de páginas que requieren lectura visual)
- POC-006 (minimización de datos personales antes de la IA)
- TST-004 (casos de referencia de las reglas analíticas)
- DOC-009 (documentación de reglas analíticas determinísticas versionadas)
- DAT-005 (catálogo: productos normalizados, emparejamientos, reglas de equivalencia)
- DAT-007 (benchmarks, señales versionadas, calificación, reporte de errores)
- COM-004 (recálculo con agrupación por alcance y versión de configuración)
- INT-010 (prorrateo de costo de IA, tope y pausa)
- SEG-010, SEG-012 (clasificación L1/L2/L3; plantillas y términos prohibidos)
- LBC-BE-003, LBC-BE-009, DAT-016 (solo inserción, ConfigurationVersion, configuración v1)

**Justificación Detallada:**
El núcleo del producto es un modelo analítico propio de detección de señales de precio, derivado de la tesis base, compuesto por numerosas reglas determinísticas encadenadas (DOC-009, TST-004): precio derivado bajo seis condiciones estrictas con detección de inconsistencias aritméticas (FR-099); homologación de la base tributaria con estado indeterminado que se propaga y nunca se mezcla en silencio, con base TVEC parametrizable mientras INV-01 siga abierto (A-121); normalización a un esquema común (marca, modelo, tamaño, resolución, tecnología, Smart, generación) y emparejamiento en tres niveles con reglas de equivalencia versionadas y un piso de criterios no configurable (POC-008, DAT-005, A-078); selección escalonada de comparables por ventanas de ±6 y ±12 meses con mínimos de observaciones para el Benchmark 1, y precio efectivo/condicionado con filtro de vendedor para el Benchmark 2; estadísticos (mediana, Q1, Q3, IQR) con regla de señal híbrida (IQR más umbral porcentual) solo por desviación al alza; nivel de confianza compuesto y estados explícitos de degradación (insuficiente, retenida, no disponible); y reproducibilidad del 100 % de los cálculos referenciando la versión de configuración, con recálculo agrupado por alcance (DAT-007, COM-004, LBC-BE-009, QS-03). Se suman heurísticas determinísticas para la detección de páginas visuales (POC-004), la minimización de datos personales (POC-006) y el control de costo de IA (INT-010). Un error conceptual en estas reglas genera falsos positivos con riesgo reputacional y legal (R-03, R-04, OC-2), lo que exige casos de referencia aprobados por el PO, pruebas basadas en propiedades y umbrales de cobertura más altos para el dominio. El factor no llega al nivel crítico porque las matemáticas son estadística estándar (cuartiles, IQR, porcentajes) y no un algoritmo de optimización o matemática intensiva: la complejidad reside en el número de reglas y su interacción, no en una fórmula novedosa.

---

### Factor 5: Tasa de Transacciones

**Valor Asignado:** 1/5

**Tareas Técnicas Relacionadas:**
- POC-002 (20.000 jobs en ≤ 24 h sin contención en la cola sobre PostgreSQL)
- DAT-014 (carga histórica por lotes acotados)
- TST-010 (pruebas de capacidad: 20 usuarios concurrentes y 20.000 jobs/24 h)
- INF-004, LBC-BE-005 (concurrencia configurable por cola en el worker)
- DAT-011 (estructuras de lectura para exploración)
- COM-004 (recálculo agrupado por alcance)

**Justificación Detallada:**
La adenda de dimensionamiento (S-DIM-03) fija la operación normal en menos de 1.000 operaciones de datos o jobs por día (menos de una por minuto), con picos de reprocesamiento de hasta 20.000 operaciones en un día (unas 14 por minuto) y una carga histórica ejecutable durante varios días. El tráfico interactivo es de 20 usuarios concurrentes (NFR-PER-003), del orden de decenas de solicitudes por minuto, sobre un universo de unos 355 contratos SECOP II y 1.150 líneas TVEC, con un escenario a 24 meses de 5 categorías y 50 usuarios (S-DIM-01). El pico combinado se ubica en el extremo inferior del rango de 10 a 100 transacciones por minuto, y la propia arquitectura concluye que no se requieren broker, streaming ni autoescalado (ADR-002, ADR-004). El trabajo asociado se limita a verificar que la cola en tabla soporte 20.000 jobs en 24 horas sin contención (POC-002), configurar la concurrencia por cola (LBC-BE-005, INF-004), procesar la carga histórica por lotes (DAT-014) y ejecutar la prueba de capacidad (TST-010). No se requieren particionamiento, réplicas de lectura ni sharding, por lo que el factor se valora en el nivel bajo.

---

### Factor 6: Facilidad de Operación

**Valor Asignado:** 4/5

**Tareas Técnicas Relacionadas:**
- PIP-INF-001 a PIP-INF-004 (protección de rama, Railway como código, CD con aprobación, rollback)
- PIP-BE-001 a PIP-BE-005, PIP-FE-001 (CI backend/frontend, imagen única, E2E, evaluación de IA, contract tests)
- INF-001 a INF-013 (Railway, PostgreSQL, R2, imagen, DNS, correo, límites de facturación, costos)
- AMB-001 a AMB-006 (local, CI efímero, producción, catálogo de configuración, secretos, adaptadores por ambiente)
- OBS-001 a OBS-010 (Sentry, monitor, logs, métricas, alertas, health checks, p95, KPIs, costos, tablero)
- DAT-012, DAT-013, DAT-015 (respaldo externo cifrado, prueba de restauración, purga por retención)
- DOC-005 (runbook operativo)
- SEG-013, SEG-016 (gestión de secretos, análisis de dependencias e imagen)
- LBC-BE-006 (recuperación automática de jobs huérfanos)

**Justificación Detallada:**
Cerca del 43 % del inventario (unas 60 tareas) corresponde a operación. El CI/CD es completamente automatizado: CI en cada PR para backend y frontend con lint, tipado, import-linter, pruebas unitarias y de integración y verificación de tipos OpenAPI (PIP-BE-001, PIP-FE-001); imagen única construida una vez por commit (PIP-BE-002); etapa E2E (PIP-BE-003); CD con aprobación manual, migración pre-deploy y healthcheck (PIP-INF-003); rollback en ≤ 15 min (PIP-INF-004); configuración de Railway como código (PIP-INF-002); y pipelines especializados de evaluación de IA contra el golden dataset y de contract tests semanales de datasets externos (PIP-BE-004, PIP-BE-005). La observabilidad incluye logs JSON con correlation_id que permiten rastrear un flujo completo (sustituto ligero del tracing distribuido), Sentry en los tres componentes con depuración de datos personales, monitor externo de disponibilidad, métricas de jobs desde PostgreSQL, p95 por endpoint, latido del worker y del dispatcher, alertas funcionales por correo con deduplicación, KPIs del MVP, costos por componente y un tablero de administración (OBS-001 a OBS-010). La continuidad se cubre con backup nativo diario más pg_dump semanal cifrado en un bucket independiente, prueba de restauración documentada con RPO/RTO ≤ 24 h y un runbook que incluye la migración a otro PaaS (DAT-012, DAT-013, DOC-005). Existen además mecanismos automáticos que se acercan al nivel crítico: recuperación de jobs huérfanos, suspensión automática de fuentes retail, pausa de la cola de IA al alcanzar el tope de costo, purga por retención, escaneo de secretos y vulnerabilidades en CI y auditoría de cada acción. El requisito de que todo sea operable por una sola persona con unas 8 h/semana y sin on-call (OC-4) convierte esta automatización en obligatoria. El factor no alcanza el nivel crítico porque no hay autoescalado (una réplica por servicio, DT-04), ni infraestructura self-healing más allá de la que ofrece el PaaS, ni tracing distribuido, y el cumplimiento regulatorio (OWASP, Ley 1581, términos de uso) se verifica en buena parte de forma manual mediante gates previos al piloto.

---

### Factor 7: Complejidad del Prompt y Refinamiento

**Valor Asignado:** 4/5

**Tareas Técnicas Relacionadas:**
- POC-003 (extracción multimodal de extremo a extremo y calibración del umbral)
- INT-008, INT-009 (adaptador ExtractorIA; prompts de extracción y clasificación, esquema de salida versionado)
- PIP-BE-004, TST-005, DOC-007 (evaluación contra golden dataset, puerta de calidad y ciclo de cambio de artefactos de IA)
- DOC-004 (guía de desarrollo y de agentes del Método Ceiba)
- COM-001, COM-005, LBC-BE-001 (fronteras de módulos, convenciones de API, import-linter)
- DOC-009, TST-004 (reglas analíticas y casos de referencia como contexto de prompts)
- POC-001 a POC-010 (decisiones de diseño aún abiertas)

**Justificación Detallada:**
La complejidad de prompt se manifiesta en dos frentes. En el desarrollo asistido por los agentes del Método Ceiba, cada tarea debe respetar más de ocho restricciones transversales verificadas en CI o en revisión: fronteras de módulos y capas con import-linter (LBC-BE-001, COM-001); hechos de solo inserción con config_version_id (ADR-012); jobs con idempotency_key y correlation_id encadenados en la misma transacción (COM-002, COM-003); montos COP enteros y zona horaria America/Bogota; estados explícitos ante falta de datos; lista blanca de campos y logs sin datos L3 (SEG-009, SEG-010); términos prohibidos y plantillas centralizadas (SEG-012); errores RFC 9457, OpenAPI como contrato y rol declarado por ruta (COM-005, SEG-004); e identificadores en inglés con campos SECOP sin transformar. A ello se suma la lógica analítica del factor 4, que requiere prompts con abundante contexto y casos de referencia (TST-004, DOC-009), y diez pruebas de concepto cuyos resultados condicionan el diseño. En el producto, el diseño de los prompts de extracción multimodal y de clasificación es una actividad de ingeniería de prompts iterativa y medida (POC-003, INT-009): esquema estructurado con ítems, atributos, cantidad, precio, IVA, etapa del precio, localizador y confianza; calibración del umbral por campo; verificación de localizadores; límite de páginas visuales y minimización de datos personales. Cada cambio pasa por el golden dataset con una puerta de calidad que falla si un campo crítico cae más de 2 p.p. o queda bajo el 90 % (TST-005, PIP-BE-004, QS-05), con el riesgo R-01 de no alcanzar la precisión. La arquitectura monolítica, los puertos con fakes, la guía para agentes (DOC-004), los ADR y las historias pequeñas mitigan la ambigüedad, por lo que no se esperan fallos sistemáticos ni la necesidad de un framework de agentes complejo; aun así, se estima una razón de iteraciones por código aceptado cercana a 3–4 en los módulos de Extracción, Catálogo y Comparación.

---

### Factor 8: Verificación y Hardening

**Valor Asignado:** 4/5

**Tareas Técnicas Relacionadas:**
- SEG-001 a SEG-019 (identidad y sesión propias, autorización, protección web, evidencia segura, archivos, SSRF, lista blanca, clasificación de datos, proveedor de IA, términos prohibidos, secretos, hardening, 2FA, dependencias, Ley 1581, ToS retail, OWASP/ZAP)
- TST-001 a TST-012 (unitarias y de propiedades, integración, corpus, casos de referencia, golden dataset, E2E, autorización, términos prohibidos, resiliencia, rendimiento, accesibilidad y navegadores, cobertura)
- PIP-BE-001, PIP-FE-001 (gates de CI)
- PIP-BE-004, PIP-BE-005 (evaluación de IA y contract tests)
- INT-014 (pruebas de adaptadores con fallos inyectados)
- POC-005 (archivos malformados y zip bombs)

**Justificación Detallada:**
El 22 % del inventario (31 tareas) es de seguridad y pruebas. La cobertura objetivo es de al menos 80 % en el dominio y las reglas determinísticas, verificada en CI (TST-012). La estrategia de pruebas incluye pruebas unitarias y basadas en propiedades con Hypothesis (TST-001), integración contra PostgreSQL y MinIO reales (TST-002), adaptadores con fallos inyectados (INT-014), E2E con Playwright en cuatro motores de navegador y accesibilidad con axe (TST-006, TST-011), rendimiento (TST-010), resiliencia e idempotencia (TST-009), golden dataset de IA (TST-005), contract tests de fuentes externas (PIP-BE-005) y casos de referencia aprobados por el PO (TST-004). Hay pruebas automatizadas de reglas de dominio críticas: matriz de autorización sobre el 100 % de las rutas y de propietario en casos y notas (TST-007), términos prohibidos que hacen fallar el CI (TST-008), ausencia de campos sensibles en el esquema (SEG-009), logs sin datos L3 (SEG-010) y tablas de hechos sin UPDATE/DELETE (LBC-BE-003). En seguridad, la autenticación y la sesión son propias (Argon2id, rotación, expiraciones; SEG-001 a SEG-003, ADR-014, R-10), con protección SSRF (SEG-008), rechazo de archivos maliciosos (SEG-007), CSRF, CSP y HSTS (SEG-005), URL firmadas (SEG-006), escaneo de secretos, dependencias e imagen (SEG-013, SEG-016), contenedor no root (SEG-014) y una revisión OWASP Top 10 con escaneo dinámico ZAP como gate de apertura del piloto con cero hallazgos altos o críticos (SEG-019). En cumplimiento, se exigen la política de la Ley 1581 con transferencia internacional (SEG-017), las condiciones del proveedor de IA (SEG-011) y la revisión de términos de uso del retail (SEG-018), en un producto con riesgo reputacional y legal por nombrar a terceros (R-09). El factor no alcanza el nivel crítico porque la cobertura objetivo es inferior al 90 %, no hay fuzz testing formal (aunque las pruebas de propiedades y de archivos malformados se le acercan), no existe revisión de seguridad por pares obligatoria con un solo mantenedor y no aplican regulaciones de tipo PCI o HIPAA.

---

### Factor 9: Integración de Legacy o Código Existente

**Valor Asignado:** 1/5

**Tareas Técnicas Relacionadas:**
- POC-003, POC-004, POC-007 (reutilizan los aprendizajes de los spikes D4 y D6)
- INT-002 a INT-006 (API Socrata y descargas de las plataformas SECOP II y TVEC)
- PIP-BE-005 (contract tests ante cambios de esquema de los datasets)
- SEG-009 (lista blanca de campos ante columnas nuevas o sensibles)

**Justificación Detallada:**
El proyecto es greenfield: el repositorio, el monolito modular y la SPA se crean desde cero (LBC-BE-001, LBC-FE-001), sin obligación de reutilizar el stack de la tesis (Python/Dash/Selenium/EC2) y sin acoplamiento funcional con Express App, de modo que no hay código heredado que modificar o extender. Se asigna un valor bajo, y no nulo, por dos fuentes de contexto preexistente que el agente debe comprender: (1) las plataformas de gobierno SECOP II y TVEC, sistemas existentes fuera del control del equipo, consumidas mediante la API Socrata pública y documentada, pero con esquemas que pueden cambiar sin aviso (R-06, PIP-BE-005), campos sensibles que deben excluirse (SEG-009), datasets de Archivos Descarga particionados por año (INT-005), una relación ítem-orden poco evidente en la TVEC (INT-004) y semántica tributaria aún abierta (INV-01); y (2) los spikes D1, D4 y D6, prototipos en Python cuyos hallazgos reutilizan las pruebas de concepto (POC-003, POC-004, POC-007) como insumo de aprendizaje y no como código a mantener. No se asigna un valor mayor porque no existe código legacy con deuda técnica que integrar y la complejidad de integración con estas fuentes ya está contabilizada en el Factor 1.

---

## Conclusiones

### Principales hallazgos

1. **Complejidad media con perfil polarizado.** El FAC de 1.035 resulta de cinco factores altos (F1, F4, F6, F7, F8) y cuatro bajos (F2, F3, F5, F9). Las decisiones de arquitectura —monolito modular, PostgreSQL como único motor de datos, cola de jobs sin broker, metas de rendimiento holgadas y proyecto greenfield— contienen eficazmente la complejidad estructural.
2. **El riesgo técnico está en la corrección, no en la escala.** La lógica analítica (F4) y la ingeniería de prompts (F7) se refuerzan mutuamente: las reglas de dominio más densas son las que más iteraciones exigen a los agentes de desarrollo y las que más impacto reputacional tienen ante un error (R-01, R-03, R-04).
3. **El trabajo no funcional es una parte mayoritaria del inventario.** Operación, seguridad y pruebas suman cerca del 65 % de las tareas técnicas, como consecuencia directa de operar con una sola persona sin on-call (OC-4) y de los gates de seguridad y cumplimiento previos al piloto (OC-5).
4. **La incertidumbre se concentra en las POC y los gates externos.** POC-002 (cola de jobs), POC-003 (extracción multimodal), POC-008 (emparejamiento), D4-4 (umbral de extracción) e INV-01 (IVA en TVEC) pueden mover los factores F2, F4 y F7.

### Recomendaciones basadas en los factores de mayor complejidad

- **F4 — Lógica de dominio:** construir los casos de referencia (TST-004) y la documentación de reglas (DOC-009) antes de implementar los módulos de Catálogo y Comparación, y usarlos como especificación ejecutable en los prompts de los agentes. Mantener las reglas como funciones puras con pruebas basadas en propiedades.
- **F7 — Prompt y refinamiento:** priorizar la guía de desarrollo para agentes (DOC-004) y los contratos de `import-linter` (LBC-BE-001, COM-001) al inicio de R1, de modo que las restricciones transversales queden verificadas por herramientas y no dependan del prompt. Tratar POC-003 y el golden dataset (TST-005) como prerrequisito de cualquier trabajo de Extracción en R2.
- **F1 — Comunicación de datos:** implementar primero los puertos con sus fakes (LBC-BE-008) y las pruebas de integración con fallos inyectados (INT-014) para cada adaptador; activar temprano los contract tests de los datasets (PIP-BE-005).
- **F6 — Operación:** adelantar al walking skeleton (POC-001, R1) el pipeline de CD, el healthcheck, el respaldo externo y las alertas básicas, en lugar de dejarlos para el cierre del MVP.
- **F8 — Verificación y hardening:** priorizar la revisión humana del código generado en los módulos de Identidad y Acceso y en la autorización por propietario, y programar la revisión OWASP/ZAP (SEG-019) con holgura antes de la apertura del piloto.

### Consideraciones para la planificación y la estimación

- Aplicar el **FAC de 1.035** como ajuste global al esfuerzo base, complementado con una ponderación diferencial por módulo: mayor contingencia en Extracción, Catálogo, Comparación y Señales e Identidad y Acceso, y menor en Ingesta, Exploración e Investigación.
- Planificar las POC de alta prioridad (POC-001, 002, 003, 007 y 008) al inicio, antes de comprometer la estimación de las releases R2 a R4.
- Reservar capacidad explícita para la revisión humana del código generado por agentes en los módulos con F4 y F7 altos, considerando la dedicación parcial del PO (~8 h/semana).
- Revisar este análisis al cierre de las POC y de los gates D4-4 e INV-01, y ante cualquier activación de los disparadores de revisión arquitectónica (más categorías, usuarios o volumen).

---

> **Método Ceiba analizar complejidad técnica** v6.1.97 | Modelo: Claude Opus 5.5 | Usuario: Juan Camilo | Fecha: 2026-10-06
