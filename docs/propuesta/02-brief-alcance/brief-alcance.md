---
nombre_proyecto: 'Seguimiento Compras Públicas'
fecha: '2026-10-01'
nombre_autor: 'Juan Camilo'
estado: 'Aprobado'
fecha_aprobacion: '2026-10-01'
adendas:
  - 'A1 (2026-10-02): resultados del spike D1 — incorpora TVEC, excluye SECOP I, regla de identificación'
  - 'A2 (2026-10-02): resultados del spike D6 — fuentes retail, adquisición progresiva, base propia de observaciones, carga manual'
  - 'A3 (2026-10-02): resultados del spike D4 — redefinición del KPI de cobertura, FR-026 pospuesto, precio unitario derivado'
stepsCompleted: ['step-01-init', 'step-02-validate-insumos', 'step-03-analysis', 'step-04-generate-brief', 'step-05-qa-loop', 'step-07-validation', 'step-08-approve']
lastStep: 'step-08-approve'
---

# Brief de Alcance: Seguimiento Compras Públicas

**Fecha:** 2026-10-01  
**Autor:** Juan Camilo  
**Estado:** Aprobado (2026-10-01) · **Adendas 1, 2 y 3** (2026-10-02)  
**Insumos analizados:** `# CONTEXTO DE INICIATIVA.md`, `TESIS (base teorica).md` (tesis "Plataforma de Visualización de Datos para Control Fiscal de Compras Públicas", Maestría en Gerencia de Transformación Digital y Analítica de Negocios, U. Externado, 2025)

> **Convención de este documento.** Cada afirmación relevante se etiqueta como:
> **[Hecho]** dato verificable en los insumos · **[Decisión]** ya tomada por el propietario · **[Hipótesis]** a validar con usuarios o datos · **[Supuesto]** asumido por el consultor a partir del análisis · **[Pregunta]** referencia a la tabla de Preguntas Abiertas.

---

## Resumen Ejecutivo

**Seguimiento Compras Públicas** es una aplicación web que procesa de forma masiva información pública de contratación estatal colombiana (SECOP II como fuente principal) y la convierte en **señales explicables y trazables** que dirigen la atención humana hacia los procesos que merecen ser investigados.

El problema no es la falta de información: la contratación es pública por ley (Ley 1712 de 2014, Ley 1150 de 2007). El problema es que su **volumen hace inviable la vigilancia manual proceso por proceso**, que es como hoy trabajan veedores, ciudadanos y periodistas. Como resultado, posibles sobreprecios, concentraciones de contratación y comportamientos atípicos pasan sin revisión.

La propuesta de valor es pasar de *"buscar manualmente contratos para luego analizarlos"* a *"procesar grandes cantidades de contratación y dirigir la atención humana hacia lo que merece investigarse"*. El producto **no acusa**: distingue explícitamente entre dato, indicador, anomalía, señal, evidencia y conclusión humana, y permite reconstruir de dónde sale cada resultado.

La iniciativa evoluciona una tesis de maestría (que llegó a formular un prototipo, no a construirlo) hacia un **MVP real y desplegable**. La **base determinística** (ingesta, exploración, fichas, comparación y señales sobre datos estructurados o ya extraídos) **funciona sin IA**; la **extracción con IA amplía la cobertura** sobre documentos no estructurados, y las capacidades de IA generativa/agéntica se incorporan solo donde demuestren valor adicional. El MVP se diseña para un **analista que investiga contratación pública** y se limita a una sola categoría: **televisores**. Su propósito es demostrar de extremo a extremo que el sistema puede pasar de SECOP a una señal investigable con evidencia trazable, antes de ampliarse a categorías más heterogéneas.

---

## Planteamiento del Problema

### Situación Actual

- **[Hecho]** SECOP II es el sistema oficial y transaccional de contratación estatal en Colombia. Toda entidad pública debe publicar sus procesos desde la apertura hasta la liquidación.
- **[Hecho]** La consulta ciudadana en SECOP II es por formulario de búsqueda (entidad, número de proceso, descripción, UNSPSC, región, estado, fechas, tipo de proceso) y luego ingreso **proceso por proceso** al detalle y sus documentos.
- **[Hecho]** Existen datos abiertos de SECOP II en datos.gov.co (la tesis referencia el dataset "SECOP II – Procesos de Contratación") y visualizaciones agregadas de Colombia Compra Eficiente. **No está validado** qué capacidades ofrecen hoy esas y otras herramientas frente a este problema; **no se afirma que no exista una solución** (ver análisis competitivo D3).
- **[Hecho]** Información crítica para detectar sobreprecios —**precios unitarios y cantidades**— frecuentemente no existe como campo estructurado: está dentro de documentos del proceso, a veces escaneados.
- **[Hecho]** Los hallazgos públicos conocidos de sobreprecio surgieron de investigación humana puntual (periodistas, un diputado, Contraloría), no de monitoreo sistemático. Casos citados en la tesis:
  - Cámara de Comercio de Tunja (2024): pantallas LED pagadas a COP 242.080.000 frente a cotización de COP 76.180.000.
  - Gobernación de Santander (2023): juegos de parqués a COP 795.000 c/u frente a precios de mercado de COP 20.000–50.000.
  - UNGRD – carrotanques La Guajira (2024): sobrecostos superiores a COP 7.760 millones.
  - Alcaldía de Sincelejo (pandemia): presuntos sobreprecios en 26.666 kits.

### Problemas Identificados

1. **Capacidad de vigilancia limitada por volumen.** La revisión es manual, un proceso a la vez; la mayoría de los procesos nunca se revisan. Frecuencia y esfuerzo actuales del analista: **no se conocen todavía**; se miden en discovery (D2) y sirven de línea base para el KPI de eficiencia.
2. **El precio unitario —la variable clave para detectar sobreprecio— está atrapado en documentos.** Sin extraerlo no es posible comparar contra referencias de mercado ni entre entidades.
3. **No se ha identificado ni validado todavía una referencia de precio de mercado confiable y comparable** integrada al análisis. Comparar contra retail requiere normalizar especificaciones, IVA, volumen, logística, garantías e instalación.
4. **Dificultad para pasar de lo agregado al caso.** Las visualizaciones existentes son agregadas; no permiten profundizar desde un indicador hasta el contrato, el proveedor y sus documentos con trazabilidad.
5. **Los hallazgos carecen de expediente reproducible.** Quien detecta una señal debe reconstruir manualmente la evidencia para presentarla a una veeduría, medio o ente de control.


### ¿Por Qué Resolver Esto Ahora?

- **[Hipótesis técnica — se valida en D4]** Las tecnologías actuales de IA generativa y multimodal podrían hacer viable lo que la tesis identificó como "reto tecnológico complejo": extraer ítems, cantidades y precios unitarios de documentos no estructurados, incluidos escaneados.
- **[Hecho]** El propietario busca un proyecto práctico y demostrable de ingeniería de producto, arquitectura, IA aplicada y sistemas agénticos.
- **[Supuesto]** La disponibilidad de datos abiertos de SECOP II vía API reduce el costo de ingesta frente al scraping con Selenium planteado en la tesis.

- **[Hecho]** No existe una fecha externa ni un evento que obligue a lanzar el MVP en una ventana determinada (PO, 2026-10-01). La urgencia no se usa como criterio de alcance.

---

## Solución Propuesta

Aplicación **web, desktop-first y responsive** **[Decisión]** que:

1. **Ingiere periódicamente** un subconjunto acotado de contratación pública desde fuentes abiertas y lo centraliza.
2. **Permite explorar** procesos, contratos, entidades y proveedores con consultas, filtros, tablas y visualizaciones (capacidad determinística, no requiere IA **[Decisión]**).
3. **Calcula indicadores y señales explicables** sobre la contratación —por ejemplo variación entre precio contratado y precio de referencia, `ID = (PE − PM) / PM` y su promedio por entidad, según la tesis— mostrando siempre fuente, fórmula, fecha de corte y datos usados.
4. **Permite profundizar** de lo agregado (entidad, sector, categoría) al caso individual y sus documentos.
5. **Incorpora IA solo donde agregue capacidad demostrable** **[Decisión]**. Primer incremento IA **[Decisión]**: **extracción inteligente** de ítems, cantidades, características y precios unitarios desde documentos contractuales, porque resuelve el cuello de botella identificado en la tesis y produce los datos estructurados que alimentan el resto de la plataforma. Siguiente incremento agéntico **[Decisión]**: **agente de investigación** con herramientas controladas (tool calling/MCP) que consume esos datos para investigar señales, comparar contratos, consultar antecedentes y explicar resultados.
6. **Ofrece un espacio de investigación personal** con registro/login **[Decisión]**: el analista guarda casos, los retoma, agrega notas y conserva las señales y evidencias relevantes. Flujo: *explorar → detectar señal → abrir caso → revisar evidencia → guardar/anotar → retomar investigación*.
7. **Produce resultados trazables** que el usuario puede revisar y llevar a una veeduría, medio u organismo de control, **sin que el sistema concluya que existe corrupción** **[Decisión]**.

**Diferenciador esperado [Hipótesis]:** "evidencia antes que acusación". Señales explicables + trazabilidad + profundización hasta el documento, sobre un volumen que una persona no puede revisar manualmente. Se confirma contra el análisis competitivo (D3).

**Principio de presentación [Decisión]:** *mostrar hechos y datos públicos, no realizar acusaciones*. La plataforma muestra proveedor, entidad, contrato, objeto, valores, documentos, comparaciones, indicadores, señales, fuentes y evidencia, pero **nunca** etiqueta a una empresa o persona como corrupta, responsable de sobreprecio, fraudulenta o equivalente.


---

## Actores del Sistema

### Usuario de Diseño del MVP [Decisión]

> **Analista que investiga contratación pública** y necesita pasar de un volumen amplio de contratos a un caso concreto que merezca revisión, acompañado de datos, comparaciones y evidencia trazable.

- Se define por la **tarea**, no por el segmento. Puede representar a periodistas de datos, veedores, investigadores académicos u otros actores que hagan esta tarea.
- **No se diseñan experiencias diferentes por segmento** en el MVP.
- Accede mediante **registro/login** y trabaja sobre sus propios casos y notas **[Decisión]**.
- **[Hecho]** Hoy hay **0–2 contactos** utilizables que analicen contratación de forma recurrente. Acceso inicial: academia y red profesional (gestión pública, transformación digital, analítica, contratación).
- **[Decisión]** La validación con usuarios reales es parte del discovery: Brief → PRD inicial → prototipo/mockups → validación con 3–5 usuarios → ajustes → desarrollo. La búsqueda de usuarios corre en paralelo; los 3–5 usuarios deben conseguirse **antes de cerrar el alcance para desarrollo**, no antes del PRD inicial.

### Segmentos que el perfil puede representar (hipótesis a validar en discovery)

| Prioridad | Actor (hipótesis) | Perfil e interacción esperada | Punto de dolor | Nivel técnico |
|---|---|---|---|---|
| H1 | **Periodista de investigación / periodismo de datos** | Busca historias con evidencia sólida; necesita detectar casos, profundizar y exportar evidencia. | Encontrar el caso entre miles; construir evidencia defendible. | Medio–alto |
| H2 | **Veedor ciudadano organizado** | Vigila entidades o sectores específicos de su territorio. | Revisión manual en SECOP; falta de recursos técnicos (Transparencia por Colombia, 2024). | Bajo–medio |
| H3 | **Organizaciones de transparencia (ONG, academia)** | Análisis agregado, informes periódicos, patrones por sector o entidad. | Procesamiento masivo y repetible. | Alto |
| H4 | **Control político (concejales, diputados y sus UTL)** | Debates de control con casos concretos. Señal en insumos: el caso parqués de Santander lo destapó un diputado. | Encontrar casos con evidencia rápida. | Medio |
| — | **Organismos de control** | Mencionados como "potenciales". **[Supuesto]** Fuera del MVP: ciclos de venta y requisitos institucionales largos. | — | — |
| — | **Ciudadano general** | Consulta ocasional. **[Supuesto]** Fuera del MVP como usuario primario: baja frecuencia de uso, difícil de medir valor. | — | Bajo |
| Sistema | **Propietario / administrador** | Configura ingesta, fuentes, recortes, catálogo de señales y monitorea costos. | — | Alto |

El discovery debe confirmar cuál de estos segmentos adopta efectivamente el producto.

La frecuencia del problema, las decisiones que toma el analista y el valor que recibe se validan en discovery (D2).

---

## Objetivos y Métricas de Éxito

### Objetivos de Negocio

**Prioridad cuando haya conflicto [Decisión]:** construir un **producto real que genere valor para usuarios**. El portafolio es consecuencia, no criterio de funcionalidades; el potencial de negocio no condiciona el MVP. Orden: *problema real → producto útil → usuarios → evidencia de valor → modelo de sostenibilidad/negocio*. El modelo de monetización (comercial, freemium, institucional, bien público u otro) **no se cierra todavía**.

1. **Demostrar la hipótesis de valor:** una persona identifica casos que merecen revisión de forma significativamente más eficiente que con el análisis manual contrato por contrato.
2. **Lanzar un MVP desplegado y usado** por usuarios reales mediante una URL, con sus principales drivers de costo identificados.
3. **Validar si la IA aporta capacidad adicional demostrable** frente a la base determinística.
4. **Servir como proyecto demostrable** de producto, arquitectura, IA aplicada y desarrollo asistido por agentes, sin sacrificar decisiones de producto **[Decisión]**.


### KPIs Críticos

**Criterio general [Decisión]:** el éxito **no** se mide por número de funcionalidades ni por casos de corrupción descubiertos. Se mide por la capacidad de transformar contratación dispersa en **señales investigables, comparables y trazables con mucho menor esfuerzo humano**. El MVP se considera validado técnicamente si ejecuta de extremo a extremo: SECOP → contrato/documento → identificar televisor → extraer especificaciones, cantidad y precio unitario → normalizar producto → encontrar referencias comparables → calcular diferencia → generar señal → presentar evidencia trazable.

| Dimensión | KPI | Meta inicial (3 meses) |
|---|---|---|
| Extracción | Precisión en campos críticos extraídos (marca, modelo/referencia, tamaño, cantidad, precio unitario, cuando estén disponibles) sobre una muestra **diversa de ≥ 50 contratos/documentos** validados manualmente, sin limitarse a casos fáciles | **≥ 90 %** |
| Cobertura | **[Reemplazado por la Adenda 3]** Tres indicadores sobre SECOP II: disponibilidad en la fuente (se reporta), cobertura de extracción (meta ≥ 80 %, provisional) y cobertura efectiva end-to-end (se reporta). TVEC aparte. Se mide separado de la precisión | Ver Adenda 3 |
| Trazabilidad | % de señales que permiten regresar al contrato, documento/dato y referencias usadas | **100 %** |
| Comparabilidad | Toda comparación se clasifica como *mismo modelo*, *producto equivalente* o *insuficiente/no confiable* | **100 %** de las comparaciones clasificadas |
| Eficiencia | Reducción del tiempo humano promedio por caso (contrato → comparación revisable) con la plataforma vs. línea base manual medida con casos reales. El procesamiento automático no cuenta como tiempo humano mientras no requiera intervención del analista | **≥ 70 %** (provisional; se recalibra tras medir la línea base) |
| Validación humana | Usuarios del perfil de diseño que prueban casos generados | **≥ 3 usuarios** |
| Validación humana | % de señales calificadas como "suficientemente sustentadas para merecer revisión" (aunque luego no haya irregularidad) | **≥ 70 %** |

_La metodología exacta de cálculo de precisión se define en el PRD, para que los campos ausentes o no aplicables no distorsionen el indicador._

---

## Alcance del MVP

### Funcionalidades Core (Imprescindibles)

**Principios ya definidos [Decisión]:** La **base determinística** (ingesta, exploración, fichas, comparación y señales sobre datos estructurados o ya extraídos) **funciona sin IA**; la **extracción con IA amplía la cobertura** sobre documentos no estructurados; recorte pequeño (no plataforma nacional); evidencia antes que acusación; arquitectura evolutiva; web desktop-first.

**Recorte del MVP [Decisión]:** una sola categoría, **televisores**, sin restricción territorial ni por entidad salvo necesidad técnica. Razones: bien estandarizable, con marca/modelo/especificaciones identificables, referencias públicas de precio y características técnicas comparables. Reduce el dominio y permite construir y validar el mecanismo de normalización y comparación.

**Objetivo de demostración de extremo a extremo [Decisión]:**

SECOP → identificar contrataciones de televisores → obtener contratos y documentos relevantes → identificar los bienes adquiridos → extraer características, cantidades y precios → normalizar productos comparables → obtener referencias de comparación → calcular diferencias → detectar señales que merezcan revisión → presentar evidencia y trazabilidad.

**Funcionalidades core — solo las necesarias para el flujo principal [Decisión]**, en orden del flujo:

1. **Ingesta periódica e identificación** de contrataciones de televisores en SECOP II desde datos abiertos, con **3 años de histórico** **[Decisión]**. Límite de la categoría **[Decisión]**: *televisores comerciales de consumo masivo comparables por marca, modelo y/o especificaciones técnicas equivalentes*.
   - **Incluye:** LED, QLED, OLED y tecnologías equivalentes de consumo; Smart TV y convencionales; todos los tamaños; compras de una o varias unidades del mismo producto.
   - **Excluye:** pantallas LED modulares, videowalls, señalización digital especializada, monitores de computador, proyectores, pantallas interactivas/táctiles, soluciones audiovisuales integrales, contratos donde el televisor es inseparable de instalación/obra/servicios sin costo discriminable, y kits donde no se pueda determinar razonablemente el precio unitario del televisor.
2. **Exploración y búsqueda** de procesos y contratos con filtros (entidad, proveedor, modalidad, fechas, UNSPSC, región, valor).
3. **Ficha de proceso/contrato** con datos clave, enlace a la fuente oficial y documentos.
4. **Extracción inteligente desde documentos** **[Decisión]**: ítems, cantidades, características y precios unitarios desde documentos contractuales del recorte, con trazabilidad al documento y página de origen y revisión humana. Es la capacidad IA del primer incremento.
5. **Comparación de precios con dos benchmarks explícitos** **[Decisión]**. Una desviación **no** se denomina sobreprecio, corrupción ni hallazgo fiscal: el sistema genera una **"señal que merece revisión"**, y el analista revisa contrato, cantidades, especificaciones, documentos y referencias antes de concluir.
   - **Benchmark 1 – Contratación pública** (principal para el histórico de 3 años): la adquisición se compara contra la distribución de precios de otras compras públicas comparables (mismo modelo o equivalencia técnica, período cercano, cantidades, características y condiciones que afecten razonablemente el precio, cuando estén disponibles) para identificar valores atípicos.
   - **Benchmark 2 – Mercado** (contratos recientes, productos aún disponibles comercialmente y precios verificables): fuentes retail iniciales **Alkosto (principal) y Falabella (secundaria)**, solo con vendedor = la tienda **[Adenda 2]**. Mercado Libre y Éxito quedan fuera inicialmente. TVEC y otras fuentes públicas comparables pueden complementar la referencia, indicando siempre si la observación es de contratación pública o de retail. Una sola observación retail **no** se denomina "precio de mercado" (ver A2.6). Si no hay referencia retail confiable, el Benchmark 2 se marca como no disponible y el Benchmark 1 sigue disponible (A2.7).
   - **Regla temporal:** *pasado → compras públicas vs. compras públicas*; *presente/futuro → compras públicas vs. compras públicas + mercado*. Un precio actual **no** se usa para juzgar una compra antigua.
   - **Histórico propio de mercado:** desde que entra en operación, el sistema guarda cada consulta de precio con producto/modelo, características relevantes, precio, fuente, fecha de consulta, URL o referencia de origen, información para determinar el IVA y metadatos para reproducir y auditar la comparación.
   - **Prioridad de emparejamiento:** 1) **mismo modelo exacto** (marca + referencia); 2) **producto equivalente** por tamaño, resolución, tecnología de pantalla, marca cuando sea relevante, funciones Smart, generación/año aproximado y demás características necesarias. La equivalencia tiene **menor nivel de confianza** y muestra sus criterios.
   - **Referencia estadística:** se conservan todas las observaciones y se calcula una referencia apropiada (ej. mediana), con trazabilidad a cada fuente. La definición matemática final se hace en PRD/diseño analítico.
   - **IVA:** se compara **precio final con IVA** cuando ambos valores puedan llevarse a esa base. Nunca con IVA vs. sin IVA en silencio; si la base no se puede determinar, la comparación se marca como **incompleta/no confiable**.
6. **Trazabilidad y nivel de confianza por señal:** fuente, fórmula, datos usados, fecha de corte, tipo de comparación (mismo modelo / equivalente / insuficiente), base tributaria y advertencia de que no constituye conclusión.
7. **Base propia de observaciones de mercado** **[Decisión — Adenda 2]**: toda observación de precio se normaliza y se guarda con su trazabilidad mínima y su método de adquisición, sin importar cómo se obtuvo. Incluye **carga manual o semiautomática** como mecanismo válido de discovery/MVP, identificada explícitamente como manual.
8. **Cuenta y espacio de investigación** **[Decisión]**: registro/login; guardar casos de interés y consultarlos después; notas asociadas al análisis; conservar señales y evidencias relevantes de cada investigación.

### Candidatas a Validar en el PRD

No son core del MVP salvo que el PRD demuestre que son necesarias para el flujo principal **[Decisión]**:

- **Fichas de entidad y de proveedor** con indicadores agregados y su contratación.
- **Señales que no son de precio**: concentración de contratos en un proveedor, peso de la contratación directa y diferencias entre presupuesto y valor contratado.
- **Exportación de expediente de caso** (resumen, datos, señales y enlaces a evidencia).

### Fuera de Alcance (Post-MVP)

- Aplicación móvil nativa **[Decisión]**.
- **SECOP I** como fuente de datos **[Decisión — Adenda 1]**.
- **Mercado Libre y Éxito** como fuentes retail iniciales **[Decisión — Adenda 2]**. No es una exclusión definitiva: pueden entrar si aparece un mecanismo adecuado y autorizado.
- Vendedores terceros de marketplace en el Benchmark 2 **[Decisión — Adenda 2]**.
- Exploración pública anónima sin autenticación **[Decisión]**: se evalúa después; las capacidades de investigación personal siempre requieren usuario.
- Publicación abierta de investigaciones, señalamientos, rankings de riesgo de proveedores o conclusiones sobre personas naturales **[Decisión]**: requieren revisión jurídica previa.
- Definición del modelo de monetización **[Decisión]**.
- Categorías distintas a televisores: computadores, refrigerios, kits alimentarios y otras **[Decisión]**. Se evalúan después de demostrar el modelo con televisores.
- Fuentes externas de precios históricos de mercado (archivos web, sitios de seguimiento de precios) **[Decisión]**.
- Cobertura nacional de toda la contratación colombiana **[Decisión]**.
- Detección proactiva/autónoma periódica con agentes que investigan sin pregunta del usuario **[Decisión: no asumir en MVP]**.
- Incorporación de todas las fuentes candidatas: Contraloría, Transparencia por Colombia, Monitor Ciudadano, prensa, información fiscal **[Decisión: no asumir]**.
- **[Supuesto]** Base de conocimiento RAG sobre informes de control y prensa (antecedentes).
- Scraping como mecanismo principal de obtención de datos, y evasión o resolución automatizada de CAPTCHA cuando exista una fuente oficial programática **[Decisión]**.
- **[Supuesto]** Plan de capacitación y apropiación de la tesis (Six Stage Training Model): se reemplaza por onboarding mínimo en producto.
- **[Supuesto]** Chatbot conversacional general **[Decisión: no convertir en chatbot]**.
- **[Supuesto]** Canal de denuncia directa a entes de control.
- **[Supuesto]** Integración funcional con Express App **[Decisión: producto independiente]**.

---

## Visión Post-MVP

### Roadmap de Funcionalidades Futuras

Orden **[Hipótesis]**, sujeto a resultados del MVP:

1. Ampliar a nuevas categorías, de menor a mayor heterogeneidad (ej. computadores; luego kits alimentarios y refrigerios), y a más años de histórico.
2. **[Decisión]** Investigación asistida por agente (siguiente incremento agéntico tras la extracción): el usuario formula una pregunta ("analiza la contratación de esta entidad en los últimos tres años") y el agente decide qué consultar, calcula, compara períodos y presenta síntesis con evidencia.
3. Base de conocimiento (RAG) con informes de Contraloría, Transparencia por Colombia, Monitor Ciudadano y antecedentes periodísticos, para contrastar señales con casos similares.
4. Detección proactiva: análisis periódico de nueva contratación con alertas de señales relevantes.
5. Referencias de precio adicionales, incluidas fuentes externas de precios históricos de mercado.
6. Seguimiento a lo largo del ciclo de vida del contrato (adiciones, prórrogas, liquidación).
7. Segmentos adicionales: organismos de control y pilotos con entidades (recomendación de la tesis).

---

## Restricciones

### Restricciones de Negocio

- **[Hecho]** Infraestructura actual de otro producto del propietario (Express App): Railway, PostgreSQL, backend desplegado y recursos de Google. Gasto conjunto ≈ **COP 100.000/mes**.
- **[Decisión]** **Presupuesto, costo operativo, fecha objetivo, dedicación semanal y ventana de urgencia no son restricciones de diseño** en esta etapa (PO, 2026-10-01). No se usan para recortar funcionalidades; el plan se deriva del producto y no al revés.
- **[Decisión]** Aunque no hay tope, la arquitectura debe **identificar los principales drivers de costo** (IA, procesamiento, almacenamiento, búsqueda, cloud, licencias) y evitar decisiones innecesariamente costosas.
- **[Decisión]** Producto **independiente** de Express App; sin acoplamiento funcional; no reutilizar tecnología solo porque exista.
- **[Hecho]** Construcción con agentes del Método Ceiba; el propietario decide producto y hace revisión técnica.
- **[Decisión]** Solo fuentes públicas de contratación y otras fuentes públicas autorizadas. Los nombres de proveedores se muestran cuando ya son información pública del proceso contractual, bajo el principio *mostrar hechos, no acusar*.
- **[Hecho]** No hay acompañamiento jurídico permanente durante el MVP.
- **[Supuesto]** Regulatorio: tratamiento de datos de personas naturales contratistas y de los usuarios registrados (Ley 1581 de 2012).


### Preferencias y Restricciones Técnicas

- **[Decisión]** Canal: aplicación **web**; sin app móvil nativa (reduce complejidad, evita tiendas, permite despliegues rápidos y pruebas por URL).
- **[Decisión]** Experiencia **desktop-first + responsive**: dashboards, tablas, filtros, comparación, análisis documental e interacción agéntica requieren desktop; tablet y móvil con experiencia funcional adaptada.
- **[Decisión]** La **base determinística** (ingesta, exploración, fichas, comparación y señales sobre datos estructurados o ya extraídos) **funciona sin IA**; la **extracción con IA amplía la cobertura** sobre documentos no estructurados. Con la IA deshabilitada el producto sigue operando, con menor cobertura.
- **[Decisión]** Tecnología **no cerrada**: las tecnologías de la tesis (Python, Dash, PostgreSQL, SQL, Selenium, AWS EC2, ETL tradicional) no son obligatorias; se permite replantear la arquitectura.
- **[Decisión]** Evaluar, cuando aporten valor: Microsoft Foundry, modelos generativos, agentes, tool calling, MCP, RAG, Azure AI Search / Foundry IQ, capacidades multimodales, extracción inteligente. El interés en Foundry/Azure es **técnico y de portafolio**, pero **cada componente se justifica técnicamente**: no se elige Foundry o Azure solo para demostrar su uso. Puede usarse si aporta valor en agentes, modelos, herramientas, conocimiento, evaluación u observabilidad. No se asumen créditos de Azure/Foundry.
- **[Decisión]** Arquitectura **híbrida permitida**: infraestructura existente u otros servicios cuando resulte más razonable.
- **[Decisión] Orden de preferencia para obtener datos** (SECOP y fuentes comerciales; versión de la Adenda 2): **1) API/dataset oficial autorizado → 2) feed, catálogo, sitemap u otro mecanismo público estructurado → 3) lectura automatizada permitida de datos estructurados publicados en páginas → 4) exploración de nuevas fuentes → 5) carga manual o semiautomática** como mecanismo temporal del MVP. No se evade CAPTCHA, bloqueo, autenticación ni otra restricción técnica. Antes de producción se revisan los términos de uso de las fuentes comerciales. **La falta de automatización completa de una fuente no bloquea el MVP.**
- **[Decisión]** El web scraping con Python/Selenium de la tesis es un **antecedente tecnológico, no una restricción** del MVP.
- **[Decisión]** El sistema **no se diseña alrededor de la evasión ni de la resolución automatizada de CAPTCHA** cuando exista una fuente oficial programática.
- **[Hecho — validado en D1]** SECOP II dispone de Datos Abiertos y APIs de consulta (ver Adenda 1).
- **[Hecho — corregido en D6]** Mercado Libre tiene API, pero el spike D6 no encontró hoy un mecanismo de consulta de publicaciones suficientemente operativo y confiable para el MVP: la búsqueda respondió 403 (ver Adenda 2).
- **[Decisión]** Aplicación con **registro/login** y datos por usuario (casos, notas, evidencias guardadas).
- **[Decisión]** Arquitectura evolutiva: simple para el MVP, extensible a nuevas fuentes, análisis y capacidades IA.


---

## Supuestos y Riesgos

### Supuestos Críticos

1. **[Supuesto]** Los datos abiertos de SECOP II (datos.gov.co) cubren los campos estructurados necesarios (entidad, proveedor, modalidad, fechas, valores, UNSPSC) con calidad suficiente para el MVP, sin depender del scraping del portal transaccional. **No validado**: la estructura estudiada en la tesis no se asume vigente; se valida en el spike D1.
2. **[Supuesto]** Los documentos del proceso (pliegos, estudios previos, anexos económicos, contratos) son accesibles de forma automatizada para el recorte elegido.
3. **[Supuesto]** En televisores es posible identificar el "mismo bien" o un bien equivalente (marca, modelo, tamaño, resolución, tecnología) entre procesos con precisión suficiente para comparar precios unitarios.
4. **[Supuesto de la tesis, no validado]** Ciudadanos y veedurías tienen interés activo y usarán la plataforma.
5. **[Supuesto de la tesis, a NO asumir]** Los datos publicados por las entidades son precisos y libres de errores significativos. La tesis cita estudios sobre calidad de datos abiertos de contratación; deben esperarse errores, duplicados y campos incompletos.
6. **[Supuesto]** El MVP es operable por una persona (propietario) apoyado en agentes de desarrollo.
7. **[Supuesto]** El volumen de contrataciones de televisores en SECOP II, con documentos que contengan ítems y precios unitarios, es suficiente para generar comparaciones y señales con sentido. Se valida en la exploración de datos.
8. **[Supuesto — actualizado en D6]** Alkosto y Falabella publican sitemaps y datos estructurados de producto (precio, marca, SKU/EAN, vendedor) en páginas permitidas por su `robots.txt`, consultables sin evasión. **Pendiente:** revisión de términos de uso antes de producción. Mientras no haya automatización viable, la carga manual o semiautomática alimenta la base de observaciones.
9. **[Supuesto]** En la mayoría de contratos de televisores es posible determinar si el valor incluye IVA, a partir de campos de SECOP o de los documentos.

### Actividades de Validación (Discovery y Spikes)

| # | Actividad | Qué debe responder | Momento |
|---|---|---|---|
| D1 | **Spike técnico SECOP II / datos.gov.co** (primer spike del proyecto) | Datasets relevantes y sus campos; cómo identificar contratación de televisores; qué está estructurado y qué requiere documentos; cómo relacionar procesos, contratos, proveedores y documentos; mecanismos de consulta/API (Datos Abiertos y APIs de SECOP) y sus límites; si los documentos del proceso se obtienen por un mecanismo oficial o solo desde el portal; volumen y calidad; viabilidad del histórico de 3 años. | ✅ **Completado** (2026-10-02; ver Adenda 1) |
| D2 | **Discovery con analistas** (3–5 usuarios del perfil de diseño) | *"¿Con qué frecuencia investigas contratación pública y cuánto tiempo toma hoy pasar de una sospecha o pregunta inicial a un caso suficientemente documentado para decidir si merece una investigación más profunda?"* Además: decisiones que toma y valor esperado. Establece la **línea base manual** del KPI de eficiencia. | En paralelo; antes de cerrar alcance para desarrollo |
| D3 | **Análisis competitivo / benchmark** | Qué capacidades ya existen y cuál es el vacío real. Revisar: herramientas oficiales de SECOP / Colombia Compra Eficiente, datos.gov.co, plataformas de organismos de control, iniciativas de transparencia y contratación abierta, herramientas periodísticas o académicas, soluciones privadas de inteligencia de contratación pública. | Antes de cerrar el PRD |
| D4 | **Spike de extracción** (riesgo R1) | Precisión, cobertura y costo por documento de la extracción sobre una muestra real de contratos de televisores. | Tras D1 |
| D6 | **Spike de fuentes de precios de mercado** | Por fuente (Mercado Libre, Alkosto, Éxito, Falabella, acuerdos marco u otras): mecanismo disponible según el orden API → integración pública → scraping; campos (modelo, características, precio, IVA); límites de uso, autenticación y términos; estabilidad. Define qué fuentes entran al Benchmark 2. | ✅ **Completado con decisiones de adquisición progresiva** (2026-10-02; ver Adenda 2) |
| D5 | **Validación de mockups** | Si el flujo explorar → señal → caso → evidencia resuelve la tarea del analista. | Antes de cerrar alcance para desarrollo |

### Revisión Crítica de la Tesis — Elementos que No Deben Asumirse

| Elemento de la tesis | Por qué no se asume | Implicación para el MVP |
|---|---|---|
| "El sistema detecta sobreprecios de forma automática, masiva y autónoma" | Contradice el principio "evidencia antes que acusación". Una diferencia de precio no implica sobreprecio ni corrupción. | El sistema genera **señales** con trazabilidad; la conclusión es humana. |
| Web scraping con Python/Selenium de SECOP y fuentes comerciales | Antecedente tecnológico, no restricción **[Decisión]**. Es frágil y costoso de mantener, y existen Datos Abiertos/APIs de SECOP (validado en D1). | Orden de adquisición progresiva de la Adenda 2 (API oficial → mecanismo público estructurado → lectura permitida de datos estructurados → exploración → carga manual). Sin evasión de CAPTCHA, bloqueo ni autenticación. |
| Mercado Libre / Google Shopping como "precio de mercado" | Precio retail ≠ precio institucional: difieren especificación, volumen, IVA, logística, garantía, instalación. Riesgo de falsos positivos. | **Resuelto:** dos benchmarks (compras públicas y mercado multifuente), mismo modelo vs. equivalente, mediana, IVA y temporalidad explícitos. |
| Volumen citado: 50–150 procesos nuevos y 100–300 documentos diarios | **[Supuesto]** Parece bajo para toda la contratación nacional; requiere verificación con los datos. | Validar volumen real de televisores en el spike D1. |
| Python + Dash + PostgreSQL en AWS EC2 | Diseño conceptual de su momento; no es obligatorio para el nuevo MVP. | Arquitectura a definir en fase de arquitectura. |
| Plan de capacitación como parte de la solución | Válido para adopción a escala, excesivo para un MVP de validación. | Fuera de alcance; onboarding mínimo. |
| Usuario "ciudadano en general" | Demasiado amplio para validar valor. | **Resuelto:** usuario de diseño = analista que investiga contratación pública. |
| Ecuación 2 (promedio simple de variaciones por entidad) | Un promedio simple sin ponderar por valor ni controlar por categoría puede distorsionar y castigar entidades injustamente. | Definir metodología de indicadores en el PRD con revisión explícita. |

### Riesgos Principales

| # | Riesgo | Impacto | Probabilidad | Mitigación |
|---|---|---|---|---|
| R1 | **Extracción de precios unitarios** de documentos (formatos heterogéneos, escaneados, ítems agrupados en kits) con precisión insuficiente o costo de IA alto. | Alto: es la base de la señal de sobreprecio. | Alta | Spike técnico sobre una muestra del recorte; medir precisión y costo por documento; revisión humana; MVP con señales sobre datos estructurados como red de seguridad. |
| R2 | **Falsos positivos por mala comparabilidad** de precios (bienes no equivalentes, referencia retail inadecuada). | Alto: destruye credibilidad y genera riesgo legal. | Alta | Recorte a bienes homogéneos; reglas explícitas de comparabilidad; mostrar incertidumbre; lenguaje de "señal", no de "hallazgo". |
| R3 | **Riesgo legal y reputacional** por asociar nombres de entidades o proveedores (incluidas personas naturales) a señales de posible irregularidad. | Alto | Media | Principio *mostrar hechos, no acusar*; solo fuentes públicas; lenguaje de "señal que merece revisión"; sin etiquetas sobre personas o empresas; trazabilidad a fuente oficial; mecanismo de corrección; política de tratamiento de datos (Ley 1581/2012). Rankings de riesgo, señalamientos o publicación abierta de investigaciones quedan fuera del MVP hasta tener revisión jurídica. Sin acompañamiento jurídico permanente, el riesgo residual se mantiene. |
| R4 | **Usuario de diseño no validado**: hoy hay 0–2 contactos que analicen contratación; se puede construir algo que nadie adopte. | Alto | Alta | Validación con mockups antes de cerrar alcance para desarrollo; búsqueda de usuarios en paralelo desde ya; criterio de salida: 3–5 analistas reales. |
| R8 | **Volumen o calidad insuficiente en televisores**: pocos contratos, televisores mezclados con otros bienes en un mismo proceso, o precios unitarios ausentes en los documentos. | Alto: sin datos no hay señal demostrable. | Media | Exploración de datos al inicio (conteo de procesos, % con documentos que tengan ítems y precios); ampliar histórico o los límites de la categoría si el volumen no alcanza. |
| R9 | **No hay referencia de mercado histórica** para contratos de hasta 3 años atrás: las tiendas muestran precio actual y los modelos se descontinúan. La mayoría de comparaciones históricas con mercado podrían quedar como *no confiables*. | Alto: debilita la pata de mercado de la triangulación en el histórico. | Alta (mitigado por diseño) | **[Decisión]** El histórico usa como señal principal el Benchmark 1 (compras públicas vs. compras públicas); el benchmark de mercado aplica a contratos recientes y al histórico propio de precios que el sistema empieza a guardar desde que arranca. Fuentes externas de precios históricos quedan fuera del MVP. |
| R10 | **Obtención de precios retail**: términos de uso, bloqueos anti-bot, cambios de estructura de las páginas y costo de mantenimiento de la captura. | Medio | Media | **[Decisión — Adenda 2]** Adquisición progresiva con carga manual como respaldo: la falta de automatización no bloquea el MVP. Sin evasión de restricciones; captura poco frecuente; evidencia por observación; revisión de términos de uso antes de producción. Si no hay referencia retail confiable, el Benchmark 2 se marca como no disponible y nunca se relaja la comparabilidad para forzarla. Residual: términos de uso aún no verificados y acceso que puede cambiar sin aviso. |
| R5 | **Alcance inflado**: la visión amplia de la tesis y el interés de portafolio, sin presupuesto ni fecha que actúen como freno. | Medio: retrasa la llegada a usuarios reales y la evidencia de valor. | Alta | Los límites son de producto: una categoría (televisores), una capacidad IA en el primer incremento, KPIs de validación como criterio de salida y la regla "si no ayuda al analista a llegar a un caso con evidencia, no entra en el MVP". |
| R6 | **Costos de IA, búsqueda y almacenamiento** desproporcionados frente al valor (ej. servicios de búsqueda gestionados con costo fijo mensual). No hay tope definido. | Medio | Media | La arquitectura identifica drivers de costo; estimación por documento y por consulta; justificar técnicamente cada servicio administrado. |
| R7 | **Calidad y disponibilidad de datos abiertos** (campos incompletos, cambios de esquema, interrupciones de la API). | Medio | Media | Validaciones de calidad en ingesta; versionado de cortes; mostrar fecha de actualización. |

---

## Stakeholders

### Patrocinador Ejecutivo

**[Supuesto — confirmar]** Juan Camilo Sierra Nossa, autor de la tesis y propietario de la iniciativa. Actúa como **Product Owner**: responsable de las decisiones de producto y de la revisión técnica **[Hecho]**. Involucramiento alto y continuo.

### Stakeholders Clave

| Rol | Actor | Responsabilidad |
|---|---|---|
| Decisor de producto, alcance y presupuesto | Propietario / PO | Aprueba Brief, PRD, alcance y costos. |
| Ejecutores | Agentes del Método Ceiba (producto, funcional, arquitectura, diseño, estimación, desarrollo) | Producen artefactos; **no asumen decisiones críticas** cuando falte información **[Decisión]**. |
| Validadores / usuarios piloto | Por conseguir: 3–5 analistas de contratación (hoy 0–2 contactos, vía academia y red profesional) | Validan problema, flujo, señales y usabilidad sobre mockups, antes de cerrar el alcance para desarrollo. |
| Aliados institucionales | **Ninguno confirmado** (PO, 2026-10-01). Hay contactos potenciales en redes académicas y profesionales, que no se registran como aliados hasta que haya participación concreta. | El MVP **no** se diseña suponiendo apoyo de universidad, organismo de control, medio, entidad pública u otra organización. |


---

## Preguntas Abiertas

Ninguna. Brief completado y aprobado el 2026-10-01.

---

## Adenda 1 — Resultados del Spike D1 (2026-10-02)

**Origen:** [Spike D1 — SECOP II / datos.gov.co](../03-prd/insumos/D1-spike-secop-datos-abiertos.md). Esta adenda **complementa** el Brief aprobado; cuando hay conflicto, prevalece la adenda.

### A1.1 Fuentes de datos del MVP [Decisión]

| Fuente | Datasets | Rol en el MVP |
|---|---|---|
| **SECOP II** | Contratos Electrónicos `jbjy-vk9h`; Archivos Descarga (`dmgg-8hin` desde 2025 e históricos por año) | Contratos de televisores y sus documentos. Ítems, cantidades, precios unitarios y modelo se obtienen por **extracción desde documentos**. |
| **TVEC — Tienda Virtual del Estado Colombiano** (incorporada) | Ítems `usqp-5nsn` / `3hdv-smhz`; Consolidado de órdenes `rgxm-mmea` | **Compras públicas con ítem, precio unitario, cantidad y fecha ya estructurados** (~1.146 líneas de televisores desde 2023; 36 % con código de modelo). Alimenta el **Benchmark 1** y la comparación de **mismo modelo** sin extracción con IA. |

- La TVEC es compra pública: entra al Benchmark 1 al mismo nivel que SECOP II, siempre con la fuente identificada en cada observación.
- **Pendiente para el PRD:** determinar si los precios TVEC incluyen IVA. Mientras no se determine, sus comparaciones se marcan como **incompletas/no confiables** en ese aspecto, según la regla de IVA del Brief.
- Ambas fuentes se obtienen por **API oficial** (nivel 1 del orden de preferencia). No se requiere scraping.

### A1.2 SECOP I fuera del MVP [Decisión]

Los ~240 contratos de televisores en SECOP I desde 2023 no se incorporan al MVP. Se evalúan post-MVP.

### A1.3 Identificación de televisores [Decisión]

- **Candidatos:** código UNSPSC `52161505` **y/o** búsqueda de texto ("televisor", "smart tv", "tv") en objeto o descripción del contrato (SECOP II) y en la descripción del ítem (TVEC).
- **Unidad de análisis = ítem de televisor**, no el contrato: hay contratos mixtos (ej. computadores + 1 televisor; aires acondicionados + televisores).
- **[Consecuencia del Brief aprobado]** Cada candidato se confirma a nivel de ítem contra el **límite de categoría** ya aprobado (inclusiones y exclusiones), porque la búsqueda textual trae falsos positivos (ej. contratos de ecoturismo o mesa de ayuda que mencionan un televisor).

### A1.4 Datos personales [Decisión]

El dataset de contratos incluye banco, tipo y número de cuenta, y documentos de identidad de representantes legales, supervisores y ordenadores del gasto. **Estos campos no se ingieren ni se muestran** (minimización de datos, Ley 1581/2012).

### A1.5 Efecto sobre supuestos, riesgos y KPIs

| Elemento | Efecto |
|---|---|
| Supuesto 1 (campos estructurados SECOP II) | **Validado parcialmente:** sí para entidad, proveedor, modalidad, fechas, valores y UNSPSC; no para ítems y precios unitarios. |
| Supuesto 2 (documentos accesibles) | **Validado** en muestra: URL oficial de descarga, sin CAPTCHA, histórico disponible por año. |
| Supuesto 7 / Riesgo R8 (volumen suficiente) | **Mitigado:** SECOP II aporta ~100 contratos por año; con TVEC la densidad del Benchmark 1 se multiplica. |
| Riesgo R1 (extracción) | **Se mantiene para SECOP II:** ~28 % de los PDF muestreados sin capa de texto y especificaciones sin modelo en documentos de la entidad. Se dimensiona en D4. |
| KPI de cobertura (≥ 60 %) | **[Propuesta del consultor — confirmar en PRD]** Medir la cobertura **sobre SECOP II**, que es donde actúa la extracción, y reportar TVEC aparte. Así los ítems ya estructurados de TVEC no inflan el indicador. |

---

## Adenda 2 — Resultados del Spike D6 (2026-10-02)

**Origen:** [Spike D6 — Fuentes de precios de mercado](../03-prd/insumos/D6-spike-fuentes-precios-mercado.md). **Prevalece** sobre cualquier contenido anterior del Brief, incluida la Adenda 1, cuando exista contradicción.

### A2.1 Fuentes retail del MVP [Decisión]

Fuentes retail iniciales del **Benchmark 2 – Mercado**:
- **Alkosto:** fuente principal.
- **Falabella:** fuente secundaria.

Quedan fuera **inicialmente**:
- **Mercado Libre:** aunque existe una API, D6 no encontró hoy un mecanismo de consulta suficientemente operativo y confiable para el MVP.
- **Éxito:** el mecanismo técnico encontrado usa una ruta `/api/` desautorizada por su `robots.txt`.

Estas exclusiones **no son definitivas**: una fuente puede incorporarse si aparece un mecanismo adecuado y autorizado. **TVEC y otras fuentes públicas comparables** pueden complementar la referencia, indicando siempre si la observación proviene de contratación pública o de retail.

### A2.2 Adquisición progresiva de precios [Decisión]

La ausencia de automatización completa de una fuente **no bloquea el MVP**. Orden práctico:

1. API/dataset oficial autorizado.
2. Feed, catálogo, sitemap u otro mecanismo público estructurado.
3. Lectura automatizada permitida de datos estructurados publicados en páginas.
4. Exploración de nuevas fuentes.
5. Carga manual o semiautomática como mecanismo temporal del MVP.

**No se evade** CAPTCHA, bloqueo, autenticación ni otra restricción técnica. **Antes de producción** se revisan los términos de uso de las fuentes comerciales utilizadas.

### A2.3 Base propia de observaciones de mercado [Decisión]

Se desacoplan conceptualmente **A. la adquisición** de la observación de precio y **B. su uso** para comparar y generar señales. Toda observación, sin importar cómo se obtuvo, se normaliza y se guarda en la **base propia de referencias**.

**Registro mínimo:** producto · marca/modelo · SKU/EAN cuando exista · vendedor · **precio efectivo** · fuente · URL/referencia · fecha de observación · información disponible sobre IVA · evidencia · **método de adquisición** (API / dataset / feed / sitemap-datos estructurados / extracción web / manual).

La **captura manual es válida** durante discovery/MVP, siempre que conserve trazabilidad y se identifique explícitamente como manual.

### A2.4 Vendedores marketplace [Decisión]

En el MVP solo se aceptan observaciones retail en las que el **vendedor es directamente la tienda seleccionada**. Se excluyen vendedores terceros para reducir variaciones por garantía, procedencia, estado, logística, reputación y condiciones particulares.

### A2.5 Precio efectivo [Decisión]

La referencia usa el **precio efectivo de venta disponible al consumidor** en la fecha de captura. El precio tachado o anterior puede guardarse como evidencia, pero no es la referencia principal. Los precios sujetos a tarjeta específica, cupón, financiación, membresía u otra condición especial **se identifican** y no se tratan automáticamente como precio general de mercado.

### A2.6 Robustez de la referencia [Decisión]

Una sola observación retail válida **no** se denomina automáticamente "precio de mercado". Con evidencia limitada se muestra como **"referencia de mercado disponible"**, junto con el número de fuentes u observaciones y el nivel de confianza. Con suficientes observaciones comparables se puede construir una **referencia estadística agregada**.

### A2.7 Estrategia de degradación [Decisión]

La ausencia de Benchmark 2 **no bloquea** el análisis de un contrato. Si no existe referencia retail confiable:
- **Benchmark 1 – compras públicas:** permanece disponible.
- **Benchmark 2 – mercado:** se marca como **no disponible / evidencia insuficiente**.

**Nunca** se reduce artificialmente el criterio de comparabilidad para producir obligatoriamente una referencia de mercado.

### A2.8 Resultado de D6 [Decisión]

**D6 = completado con decisiones de adquisición progresiva.** No es criterio de salida de D6 automatizar el 100 % de las fuentes. D6 determina qué fuentes se usan hoy, cuáles requieren integración posterior, cuáles se alimentan manualmente, cuáles se excluyen y qué trazabilidad conserva cada observación. La automatización de la adquisición de precios puede evolucionar **sin modificar el modelo funcional de comparación**.

---

## Adenda 3 — Resultados del Spike D4 (2026-10-02)

**Origen:** [Spike D4 — Extracción documental](../03-prd/insumos/D4-spike-extraccion-documental.md). **Prevalece** sobre el contenido anterior del Brief y de las Adendas 1 y 2 cuando exista contradicción. D4 encontró evidencia que contradecía la meta de cobertura aprobada: en ~45–50 % de los contratos SECOP II en categoría, **la fuente no publica** el precio unitario.

### A3.1 Cobertura: tres indicadores [Decisión D4-1]

Reemplaza la definición anterior del KPI de cobertura (≥ 60 %). Se mide sobre los contratos/ítems candidatos de SECOP II del alcance; **TVEC se reporta aparte** porque ya trae información estructurada.

| Indicador | Definición | Meta |
|---|---|---|
| **Disponibilidad en la fuente** | % de contratos/ítems candidatos cuyos documentos publicados contienen la información mínima para intentar el análisis: cantidad + precio unitario explícito o derivable según A3.3 | **Se reporta**, sin meta de producto inicial; mide el límite de la fuente |
| **Cobertura de extracción** | contratos elegibles extraídos correctamente / contratos elegibles con información realmente disponible en la fuente | **≥ 80 %**, provisional y sujeta a calibración con D4-4. Si la evidencia muestra que no es técnicamente razonable, se propone una recalibración explícita; no se reduce automáticamente |
| **Cobertura efectiva end-to-end** | % del universo total de contratos/ítems candidatos que llega automáticamente a una comparación utilizable | **Se reporta siempre**, aunque la pérdida se deba a la fuente |

Así se distingue *la fuente no publica el dato* de *el producto no extrae un dato que sí estaba publicado*, sin ocultar qué parte del universo termina siendo analizable.

### A3.2 Múltiples oferentes pospuesto [Decisión D4-2]

La extracción y comparación de precios de múltiples oferentes de un proceso (FR-026) queda **fuera del core del MVP** (D4: ~10 % de los procesos la publica). Se registra como capacidad futura y se reincorpora si aparece una fuente o tipo documental donde sea sistemática. No bloquea el flujo SECOP/TVEC → extracción del bien adjudicado → normalización → benchmark → señal → evidencia.

### A3.3 Precio unitario derivado [Decisión D4-3]

Se permite `precio unitario derivado = valor total del ítem / cantidad` **solo** si se demuestra que: (1) la cantidad está explícitamente documentada; (2) el valor corresponde exclusivamente a esos televisores; (3) todos son del mismo producto/modelo o de una referencia inequívocamente homogénea; (4) no hay otros bienes mezclados; (5) no hay instalación, transporte, soporte, obra, accesorios ni otros servicios incluidos sin discriminar; (6) la base tributaria no introduce una incompatibilidad conocida.

- **Nunca** se usa `valor total del contrato / cantidad` en un contrato mixto.
- **Nunca** se usa el valor del contrato de datos abiertos como sustituto del valor documental del ítem (D4: no coincide necesariamente con la oferta aceptada).
- Se guarda como `precio_unitario_tipo = derivado`, con valor total usado, cantidad usada, fórmula, documento fuente, página/hoja/celda, nivel de confianza e indicador de derivado.
- Tiene **menor confianza** que un precio explícito, y esa condición se propaga a la comparación y a la señal.

### A3.4 Precisión y calibración [Decisión D4-4]

La validación manual de las 228 filas campo por campo continúa en paralelo, con prioridad: precio unitario, cantidad, tamaño, modelo/referencia, marca y demás atributos. Alimenta la precisión por campo y global, los falsos positivos, los campos no encontrados, la cobertura real y la **calibración del umbral de aceptación automática**, que sale de la relación observada entre la confianza del extractor y la corrección real. No se fija un valor arbitrario (ej. 0,9).

### A3.5 Efecto sobre supuestos y riesgos

| Elemento | Efecto |
|---|---|
| Supuesto 7 / R8 (volumen) | ~28 % de los candidatos SECOP II no son compras de TV y ~44–50 % de los que sí lo son publican precio unitario: el aporte efectivo de SECOP II es del orden de ~110–130 contratos. **La TVEC es la base principal del Benchmark 1.** |
| R1 (extracción) | La extracción multimodal es viable (evidencia 100 %, imágenes legibles); el riesgo dominante es la **disponibilidad en la fuente**, no la extracción. Precisión pendiente de D4-4. |
| Hipótesis técnica de "¿Por qué ahora?" | Confirmada parcialmente: la lectura multimodal funciona donde el dato existe; ~52 % de los contratos la necesitó. |

---

## Próximos Pasos

Una vez aprobado este Brief de Alcance, **no se pasa directamente al PRD** **[Decisión]**:

1. ✅ **Spike D1 (SECOP II / datos.gov.co)** completado (Adenda 1) y ✅ **spike D6 (fuentes de precios de mercado)** completado con decisiones de adquisición progresiva (Adenda 2). Sus informes son **insumos obligatorios del PRD**: [D1](../03-prd/insumos/D1-spike-secop-datos-abiertos.md) · [D6](../03-prd/insumos/D6-spike-fuentes-precios-mercado.md).
2. **Desarrollo de PRD (Product Requirements Document)** con los resultados de D1 y D6
   - Descomposición en requerimientos funcionales (RF001-RF0XX)
   - Especificación de requerimientos no funcionales (RNF001-RNF0XX)
   - Definición de flujos de negocio detallados
   - Identificación de actores del sistema
   - Especificación de integraciones requeridas
   - Definición de volúmenes y escala esperada

---

_Este Brief de Alcance sirve como documento fundacional estratégico. NO incluye especificaciones técnicas detalladas (RFs, RNFs, flujos, actores, integraciones), que se desarrollarán en el PRD una vez aprobado este documento._

---

## Anexo: Registro de Decisiones del Discovery

Preguntas resueltas durante la elaboración del Brief, conservadas para trazabilidad.

| # | Sección Destino | Pregunta | Estado | Respuesta |
|---|-----------------|----------|--------|-----------|
| 1 | Actores del Sistema | ¿Qué segmento (H1 periodistas de datos, H2 veedores organizados, H3 ONG/academia, H4 control político) puedes **alcanzar con 3–5 personas reales en las próximas semanas** para probar el MVP? Ese será el usuario primario. ¿Tienes nombres concretos? | ✅ Resuelta | PO (2026-10-01): usuario de diseño = analista que investiga contratación pública y necesita pasar de un volumen amplio de contratos a un caso concreto con datos, comparaciones y evidencia trazable. Sin experiencias por segmento. Contactos utilizables hoy: 0–2. Validación con 3–5 usuarios sobre mockups, antes de cerrar alcance para desarrollo; no bloquea el PRD inicial. |
| 2 | Planteamiento del Problema | Para ese usuario: ¿cada cuánto investiga contratación (casos/semana o mes)? ¿Cuántas horas le toma hoy llegar a un caso relevante y armar la evidencia? ¿Qué herramientas usa hoy (SECOP, datos.gov.co, Excel, otras)? | ✅ Resuelta | No se sabe todavía (PO, 2026-10-01). No se inventan cifras. Se registra como pregunta de discovery (D2) y sirve como línea base del KPI de eficiencia. |
| 3 | Solución Propuesta | ¿Has evaluado herramientas existentes (tableros de Colombia Compra Eficiente, plataformas de analítica de la Contraloría, Monitor Ciudadano, iniciativas de periodismo de datos)? ¿Qué no resuelven que este MVP sí resolvería? | ✅ Resuelta | No validado (PO, 2026-10-01). No se afirma que no exista una solución. Se registra el análisis competitivo como actividad de discovery (D3). |
| 4 | Alcance del MVP | ¿Qué recorte prefieres: (a) una categoría de bienes homogéneos (ej. equipos de cómputo, pantallas, mobiliario, kits alimentarios), (b) un territorio, (c) un tipo de entidad? ¿Hay un caso o tema con el que quieras demostrar valor primero? | ✅ Resuelta | PO (2026-10-01): una sola categoría, **televisores**, sin restricción territorial ni por entidad. Computadores, refrigerios y kits quedan fuera del MVP. Objetivo: demostrar de extremo a extremo SECOP → identificación → documentos → extracción → normalización → comparación → señal → evidencia. Caso demostrativo: se elige tras explorar calidad de datos. |
| 5 | Alcance del MVP | ¿Cuánto histórico necesita el MVP: 1, 3 o 5 años? ¿Basta con actualización diaria o semanal? (Impacta volumen, costo y alcance de las señales.) | ✅ Resuelta | PO (2026-10-01): 3 años de histórico. Comparación con temporalidad: precio en fecha X ↔ referencia de mercado cercana a X. Un precio actual no se usa para juzgar compras antiguas; si no hay referencia histórica confiable, se indica. |
| 6 | Alcance del MVP | ¿La comparación **precio contratado vs precio de mercado** es imprescindible para el primer MVP, o aceptarías validar primero con señales sobre datos estructurados y comparación de precios unitarios **entre entidades**? ¿Qué pierde el usuario sin ella? | ✅ Resuelta | PO (2026-10-01): la comparación con mercado se mantiene como parte central de la propuesta de valor, pero no es la única referencia. Triangulación: contratado vs. mercado + contratado vs. compras públicas comparables (entidades, contratos, períodos). Si la referencia de mercado es costosa o ambigua en una categoría, se arranca con comparación entre compras públicas y se incorpora mercado después. |
| 7 | Alcance del MVP / Riesgos | ¿Qué referencia aceptarías como "precio de mercado": precios de Acuerdos Marco / Tienda Virtual del Estado, precios del mismo bien en otras entidades, marketplaces, o combinación? ¿Cómo tratar IVA, volumen, logística, garantía e instalación? | ✅ Resuelta | PO (2026-10-01): varias fuentes retail públicas (Alkosto, Éxito, Falabella, Mercado Libre, otras verificables) + fuentes públicas/acuerdos marco comparables. Prioridad: mismo modelo exacto → producto equivalente (menor confianza, criterios visibles). Referencia estadística (ej. mediana) con trazabilidad a cada observación. Precio final con IVA; si la base no se puede determinar, comparación marcada como incompleta/no confiable. Fórmula final en PRD. |
| 8 | Alcance del MVP | ¿Cuál es la **única** capacidad IA a demostrar en el MVP: (a) extracción de ítems/cantidades/precios unitarios desde documentos, o (b) investigación asistida por agente? ¿Qué te haría concluir que la IA "sí aportó"? | ✅ Resuelta | PO (2026-10-01): primer incremento = extracción inteligente de ítems, cantidades, características y precios unitarios desde documentos contractuales. Siguiente incremento = agente de investigación. La IA aporta si reduce de forma medible el trabajo manual de documento → información comparable → señal investigable, con trazabilidad a la evidencia. Umbrales numéricos se definen en #9. |
| 9 | Objetivos y Métricas | ¿Qué resultado medible en 3 meses te diría que el MVP funciona? (ej. # usuarios activos semanales, # casos exportados, tiempo por caso vs manual, % de señales calificadas como relevantes, precisión de extracción.) ¿Qué umbral lo declara fracaso? | ✅ Resuelta | PO (2026-10-01): extracción ≥ 90 % sobre muestra diversa de ≥ 50 contratos/documentos validados manualmente; cobertura automática ≥ 60 %, medida separada de la precisión; reducción de tiempo humano por caso ≥ 70 % (provisional, se recalibra con la línea base manual; el procesamiento automático no cuenta como tiempo humano). Metodología de precisión se define en el PRD. |
| 10 | Objetivos y Métricas | Cuando choquen, ¿qué gana: producto con usuarios, proyecto demostrable/portafolio, o futuro negocio (ej. servicio a medios, ONG o entes)? ¿Hay intención de monetizar o es un bien público? | ✅ Resuelta | PO (2026-10-01): prioridad = producto real con valor para usuarios. Portafolio es consecuencia; el negocio no condiciona el MVP. Modelo de monetización no se cierra todavía. |
| 11 | Restricciones de Negocio | ¿Tope de costo operativo mensual del MVP (infra + IA + búsqueda) en COP? ¿Límite estricto o flexible? ¿Hay presupuesto de desarrollo más allá de tu tiempo (terceros, licencias)? | ✅ Resuelta | No aplica como restricción en este ejercicio (PO, 2026-10-01): no hay tope de costo ni de presupuesto. La arquitectura debe identificar los drivers de costo y evitar decisiones innecesariamente costosas. |
| 12 | Restricciones de Negocio | ¿Fecha objetivo para tener el MVP con usuarios piloto? ¿Qué la condiciona? ¿Cuántas horas por semana puedes dedicar como PO y revisor técnico? | ✅ Resuelta | No aplica como restricción en este ejercicio (PO, 2026-10-01): sin fecha objetivo ni horas por semana como criterio de alcance. El plan se deriva del producto. |
| 13 | Restricciones Técnicas | ¿Tienes créditos, suscripción o acuerdo con Microsoft/Azure (Foundry, AI Search) u otro proveedor que cambie la ecuación de costo? ¿El interés en Foundry es por valor técnico, por aprendizaje/portafolio, o ambos? | ✅ Resuelta | PO (2026-10-01): sin créditos asumidos. Interés técnico y de portafolio, pero cada componente se justifica técnicamente; no se elige Foundry/Azure solo para demostrar su uso. Arquitectura híbrida permitida. |
| 14 | Restricciones Técnicas | ¿El MVP es de acceso público abierto o requiere registro? ¿Necesitas funciones por usuario (guardar casos, notas, listas de seguimiento)? | ✅ Resuelta | PO (2026-10-01): web con registro/login. El analista guarda casos, los retoma, agrega notas y conserva señales y evidencias. La exploración pública anónima se evalúa después. |
| 15 | ¿Por Qué Ahora? | ¿Hay una ventana que haga urgente el lanzamiento (ej. calendario electoral territorial, Ley de Garantías, convocatorias, aliados interesados, publicación)? ¿Qué se pierde si el MVP sale 2–3 meses después? | ✅ Resuelta | No aplica como restricción en este ejercicio (PO, 2026-10-01): no hay fecha ni evento externo que obligue a lanzar en una ventana. |
| 16 | Stakeholders | ¿Hay aliados (U. Externado, ONG, medios, veedurías) que actúen como validadores, usuarios piloto o difusores? Nombre, rol y nivel de compromiso. | ✅ Resuelta | PO (2026-10-01): ningún aliado institucional confirmado; 0–2 contactos para discovery, a ampliar. No se diseña suponiendo apoyo institucional. |
| 17 | Riesgos | ¿El MVP mostrará públicamente nombres de proveedores (incluidas personas naturales) asociados a señales? ¿Puedes contar con revisión jurídica del lenguaje, términos de uso y tratamiento de datos? | ✅ Resuelta | PO (2026-10-01): solo fuentes públicas; los nombres de proveedores se muestran cuando ya son información pública. Principio: mostrar hechos, no acusar; sin etiquetas sobre personas o empresas. Rankings, señalamientos o publicación de investigaciones requieren revisión jurídica previa. Sin acompañamiento jurídico permanente en el MVP. |
| 18 | Supuestos | ¿Ya exploraste los datasets abiertos de SECOP II (procesos y contratos) en datos.gov.co? ¿Encontraste limitaciones de campos, calidad o acceso a documentos? | ✅ Resuelta | PO (2026-10-01): la estructura actual no está validada. Se registra la exploración de SECOP II / datos.gov.co como primer spike técnico (D1), con su alcance de preguntas. |
| 19 | Alcance del MVP | ¿Qué entra en "televisores"? ¿Solo televisores (incl. Smart TV), o también **pantallas LED/LCD de uso institucional, video walls, monitores de señalización digital y pantallas interactivas**? (El caso de Tunja fueron *pantallas LED*.) ¿Se incluyen procesos donde el televisor viene **con instalación, soporte o mezclado con otros bienes** (ej. dotación de aulas)? | ✅ Resuelta | PO (2026-10-01): televisores comerciales de consumo masivo comparables por marca, modelo y/o especificaciones. Incluye LED/QLED/OLED, Smart y convencionales, todos los tamaños, una o varias unidades. Excluye pantallas modulares, videowalls, señalización digital, monitores, proyectores, pantallas interactivas, soluciones audiovisuales integrales, contratos con instalación/obra/servicios no discriminables y kits sin precio unitario determinable. |
| 20 | Alcance del MVP / Riesgos | Para contratos de 1 a 3 años atrás casi nunca habrá precio retail de la fecha. ¿Aceptas que en el histórico la **señal principal sea la comparación entre compras públicas**, y que la comparación con mercado aplique sobre todo a contratos recientes y a partir de capturas periódicas desde el arranque del MVP? ¿O quieres evaluar fuentes de histórico de precios (archivos web, sitios de seguimiento de precios) aunque aumenten costo y complejidad? | ✅ Resuelta | PO (2026-10-01): opción A. Dos benchmarks explícitos: (1) contratación pública, principal para el histórico; (2) mercado, para contratos recientes y productos disponibles. El sistema construye su propio histórico de precios de mercado desde que arranca (producto, características, precio, fuente, fecha, URL, IVA, metadatos de auditoría). Fuentes históricas externas fuera del MVP. Las desviaciones se presentan como "señal que merece revisión". |
