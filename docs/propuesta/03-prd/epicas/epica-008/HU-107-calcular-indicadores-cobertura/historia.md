# Historia #107: Calcular los tres indicadores de cobertura sobre SECOP II, con TVEC aparte

**Estado:** Borrador (PO)  
**Release:** Release MVP  
**Épica:** [Operación, Calidad y Medición del MVP](../../../epicas.md#épica-008-operación-calidad-y-medición-del-mvp)  
**Feature:** Medir KPIs del MVP  
**Prioridad:** Alta  
**FRs relacionados:** FR-091 (relacionados: FR-030, FR-075, FR-092, FR-099; NFR-CAL-003)

Escrita por el flujo generar-historias-usuario (Método Ceiba) — MVP propio, no comercial

---

## Historia de Usuario

**Como** Administrador del MVP (el PO),  
**Quiero** calcular la disponibilidad en la fuente, la cobertura de extracción y la cobertura efectiva end-to-end de los contratos SECOP II, y ver la TVEC por separado,  
**Para** distinguir cuándo la fuente no publica el dato de cuándo el producto no extrae un dato que sí estaba publicado, sin ocultar qué parte del universo termina siendo analizable.

## Descripción

La decisión D4-1 (Adenda 3, NFR-CAL-003) reemplazó el KPI de cobertura del Brief por **tres indicadores**, medidos sobre los contratos/ítems candidatos de **SECOP II** del alcance; **la TVEC se reporta aparte** porque ya trae información estructurada:

| Indicador | Definición | Meta |
|---|---|---|
| (a) Disponibilidad en la fuente | % de contratos/ítems candidatos cuyos documentos publicados contienen la información mínima para intentar el análisis (cantidad + precio unitario explícito o derivable) | Se reporta, sin meta (D4: ~44–50 % de los contratos en categoría) |
| (b) Cobertura de extracción | contratos elegibles extraídos correctamente y llevados automáticamente hasta información suficiente para comparar / contratos elegibles con información realmente disponible en la fuente | ≥ 80 %, provisional, sujeta a calibración con D4-4; no se reduce automáticamente |
| (c) Cobertura efectiva end-to-end | % del universo total de contratos/ítems candidatos que llega automáticamente a una comparación utilizable | Se reporta siempre |

Como (a) y (b) dependen de saber qué publica realmente la fuente, se calculan sobre los contratos de la **muestra de validación** con veredicto manual por contrato (HU-104 y HU-105). El indicador (c) se calcula sobre **todo el universo** con los estados de procesamiento del sistema.

**Implementación sin UI permitida:** comando, script, consulta o reporte (texto, CSV o JSON).

---

## Criterios de Aceptación

### Escenario 1: Disponibilidad en la fuente

- **Dado** que la muestra tiene 50 contratos con veredicto: 36 son compra de televisor en categoría y, de ellos, 17 tienen información mínima en la fuente
- **Cuando** el Administrador calcula la cobertura
- **Entonces** obtiene disponibilidad en la fuente 34,0 % (17/50) sobre contratos candidatos de la muestra, disponibilidad 47,2 % (17/36) sobre contratos en categoría (comparable con D4), y estado "Se reporta (sin meta)"

### Escenario 2: Cobertura de extracción

- **Dado** que de los 17 contratos elegibles, 14 tienen al menos un ítem de televisor con cantidad y precio unitario aceptados automáticamente y validados como `correcto`, 2 llegaron a información suficiente solo tras corrección humana y 1 no llegó
- **Cuando** el Administrador calcula la cobertura
- **Entonces** obtiene cobertura de extracción 82,4 % (14/17), estado "Cumple (meta provisional 80,0 %)", y el desglose "con intervención humana: 2; no alcanzados: 1"

### Escenario 3: Cobertura de extracción por debajo de la meta

- **Dado** que de 17 contratos elegibles solo 12 cumplen el numerador
- **Cuando** se calcula la cobertura
- **Entonces** obtiene 70,6 % (12/17), estado "No cumple" y la nota "Meta provisional sujeta a calibración con D4-4. Si la evidencia muestra que no es técnicamente razonable, se propone una recalibración explícita; no se reduce automáticamente."

### Escenario 4: Muestra insuficiente para (a) y (b)

- **Dado** que solo 30 contratos de la muestra tienen veredicto completo
- **Cuando** se calcula la cobertura
- **Entonces** (a) y (b) se calculan y muestran, pero el estado de (b) es "Muestra insuficiente: 30 de 50 contratos con veredicto." y no dice "Cumple"

### Escenario 5: Cobertura efectiva end-to-end

- **Dado** que el universo SECOP II del alcance tiene 355 contratos candidatos y 470 ítems candidatos, y 98 contratos (con 121 ítems) tienen al menos un ítem de televisor que llegó automáticamente a una comparación utilizable
- **Cuando** se calcula la cobertura
- **Entonces** obtiene end-to-end por contrato 27,6 % (98/355) y por ítem 25,7 % (121/470), con estado "Se reporta"

### Escenario 6: Embudo de pérdidas del universo

- **Dado** el universo del Escenario 5
- **Cuando** se calcula la cobertura
- **Entonces** el reporte muestra, por contrato, cuántos quedan en cada etapa: candidatos (355) → confirmados como compra de televisor → con documentos obtenidos → con al menos un ítem con información suficiente → con comparación utilizable (98), y la pérdida absoluta y porcentual entre etapas, incluido el número de contratos marcados "información insuficiente" con su motivo

### Escenario 7: Comparaciones incompletas por base tributaria

- **Dado** que 40 contratos adicionales tienen una comparación con emparejamiento válido pero marcada incompleta/no confiable por base tributaria indeterminada
- **Cuando** se calcula la cobertura
- **Entonces** esos 40 no entran al numerador principal del end-to-end; el reporte muestra además la variante "incluyendo comparaciones incompletas por base tributaria": 38,9 % (138/355)

### Escenario 8: Llegada con intervención humana

- **Dado** que 15 contratos llegaron a comparación utilizable solo después de una corrección humana de clasificación o de datos extraídos
- **Cuando** se calcula el end-to-end
- **Entonces** no cuentan en el numerador principal y se informan como "con intervención humana: 15"

### Escenario 9: TVEC reportada aparte

- **Dado** que la TVEC tiene 1.150 ítems candidatos, 1.020 confirmados como televisor y 870 con comparación utilizable
- **Cuando** se calcula la cobertura
- **Entonces** el reporte muestra una sección "TVEC (reporte aparte)" con esos conteos y end-to-end TVEC 75,7 % (870/1.150), y ninguna cifra TVEC entra en los indicadores (a), (b) o (c) de SECOP II

### Escenario 10: Sin veredictos en la muestra

- **Dado** que ningún contrato de la muestra tiene veredicto por contrato
- **Cuando** se calcula la cobertura
- **Entonces** (a) y (b) muestran "Sin datos: no hay contratos con veredicto en la muestra." y (c) y TVEC se calculan normalmente

### Escenario 11: Universo vacío

- **Dado** que no hay contratos candidatos SECOP II en el alcance
- **Cuando** se calcula la cobertura
- **Entonces** (c) muestra "—" con el texto "Sin contratos candidatos SECOP II en el alcance." y no hay división por cero

### Escenario 12: Corte histórico

- **Dado** que el Administrador calcula la cobertura en dos fechas distintas
- **Cuando** consulta el historial
- **Entonces** ve ambos cortes con fecha y hora, fecha de corte de los datos, versión de configuración y todos los indicadores; los cortes no cambian después

### Escenario 13: Usuario sin rol Administrador

- **Dado** que un usuario con rol Analista está autenticado
- **Cuando** intenta calcular o consultar la cobertura
- **Entonces** recibe "Acción no permitida: esta operación requiere el rol Administrador."

---

## Información Recopilada

### Usuario y Contexto

- **Tipo de usuario:** Administrador (en el MVP, el PO).
- **Permisos requeridos:** rol Administrador.
- **Valor de negocio:** mide el producto (extracción) separado del límite de la fuente, y mantiene visible qué fracción del universo termina siendo analizable; es la decisión D4-1 aplicada.

### Reglas de Negocio

- **RN-01 — Universo SECOP II del alcance:** contratos SECOP II marcados como candidatos (por UNSPSC `52161505` y/o términos de búsqueda), con fecha de firma desde el inicio de la ventana histórica configurada (configuración inicial: 2023-01-01) hasta la fecha de corte de los datos. Ítems candidatos = ítems asociados a esos contratos. TVEC nunca entra a este universo.
- **RN-02 — Veredicto por contrato (muestra):** un contrato de la muestra tiene veredicto completo si ES_COMPRA_TV_EN_CATEGORIA = `no`, o si ES_COMPRA_TV_EN_CATEGORIA = `si` y EXISTE_INFO_MINIMA tiene `si` o `no`. "Información mínima" = cantidad + precio unitario explícito o derivable según las 6 condiciones del precio derivado (FR-099).
- **RN-03 — (a) Disponibilidad en la fuente:** principal = contratos con veredicto (`si`, `si`) / contratos de la muestra con veredicto completo. Complementaria = mismo numerador / contratos con ES_COMPRA_TV_EN_CATEGORIA = `si`. Estado fijo "Se reporta (sin meta)".
- **RN-04 — (b) Cobertura de extracción:** elegibles = contratos de la muestra con veredicto (`si`, `si`). Un elegible cuenta en el numerador si al menos uno de sus ítems de televisor: (1) llegó a "información suficiente para comparar" (cantidad y precio unitario `explicito` o `derivado`, sin marca de información insuficiente); (2) su cantidad y su precio unitario tienen resultado de validación vigente `correcto`; y (3) ni su clasificación ni su cantidad ni su precio unitario pasaron por la cola de revisión humana ni fueron corregidos manualmente. Los elegibles que cumplen (1) y (2) solo con intervención humana se informan como "con intervención humana"; el resto como "no alcanzados".
- **RN-05 — Meta y estados de (b):** meta configurable, decimal de 0,0 a 100,0 %, **configuración inicial: 80,0 %** (provisional). Estados en orden: "Sin datos: no hay contratos con veredicto en la muestra." (0 elegibles y 0 con veredicto); "Muestra insuficiente: {n} de {mínimo} contratos con veredicto." si los contratos con veredicto completo son menos que el mínimo de muestra (configuración inicial: 50); "Cumple (meta provisional {m} %)" si el porcentaje redondeado a 1 decimal es ≥ meta; "No cumple" con la nota de recalibración del Escenario 3. Si hay contratos con veredicto pero 0 elegibles: "—" con "Sin contratos elegibles en la muestra."
- **RN-06 — (c) Cobertura efectiva end-to-end:** por contrato = contratos del universo con al menos un ítem de televisor con comparación utilizable alcanzada automáticamente / contratos candidatos del universo. Por ítem = ítems con comparación utilizable alcanzada automáticamente / ítems candidatos del universo. "Comparación utilizable" = al menos un benchmark (compras públicas o mercado) con referencia agregada o "referencia disponible", emparejamiento *mismo modelo* o *producto equivalente* y no marcada incompleta/no confiable. "Automáticamente" = sin corrección humana de clasificación ni de datos extraídos de ese ítem. Variantes informativas: "incluyendo comparaciones incompletas por base tributaria" y "con intervención humana". Estado fijo "Se reporta".
- **RN-07 — Embudo (por contrato):** etapas: candidatos → confirmados como compra de televisor → con documentos obtenidos → con al menos un ítem con información suficiente → con comparación utilizable automática. Por etapa: conteo, pérdida absoluta y porcentual respecto a la etapa anterior; en la etapa de información suficiente, conteo por motivo de "información insuficiente".
- **RN-08 — TVEC aparte:** sección separada con ítems candidatos TVEC, confirmados como televisor, con comparación utilizable (misma definición de RN-06) y end-to-end TVEC por ítem. No se suma ni se promedia con SECOP II.
- **RN-09 — Formato:** porcentajes con 1 decimal (redondeo a la mitad hacia arriba), siempre con numerador y denominador. Denominador 0 → "—" con texto explicativo, nunca error.
- **RN-10 — Corte histórico:** cada cálculo se guarda como corte inmutable con fecha y hora (UTC−05:00), usuario, fecha de corte de los datos SECOP II y TVEC, versión de configuración y todos los indicadores, variantes, embudo y sección TVEC. Cálculo a demanda; no modifica datos.
- **RN-11 — Mensajes:** "Sin datos: no hay contratos con veredicto en la muestra."; "Sin contratos elegibles en la muestra."; "Sin contratos candidatos SECOP II en el alcance."; "Acción no permitida: esta operación requiere el rol Administrador."

### Interfaz

No requiere interfaz gráfica. Mínimo aceptable: comando "calcular cobertura" que entrega el reporte (texto, CSV o JSON) con las secciones (a), (b), (c), embudo y TVEC, y comando "historial de cobertura".

### Sistemas Externos (Si aplica)

No aplica (usa datos ya ingeridos y procesados).

---

## Contexto y Referencias

**Épica origen:** [Operación, Calidad y Medición del MVP](../../../epicas.md#épica-008-operación-calidad-y-medición-del-mvp)

**Exclusiones de la Épica:**
- NO incluye analítica de uso avanzada ni embudos de producto.
- NO incluye facturación ni gestión de planes.
- NO incluye administración multi-organización.

**Historias relacionadas:** HU-104 (muestra), HU-105 (veredictos por contrato), HU-106 (precisión), HU-108 (trazabilidad y comparabilidad).

---

## Supuestos

> Elementos inferidos por la IA que NO estaban explícitos en el PRD o la Épica. Todos los supuestos han sido resueltos: convertidos en reglas de negocio explícitas o eliminados mediante reformulación. Si aparece algún supuesto no resuelto, esta HU NO está lista para desarrollo.

- (a) y (b) se calculan sobre la muestra con veredicto manual, porque solo una verificación humana distingue "la fuente no publica" de "no se extrajo"; (c) se calcula sobre todo el universo → resuelto en RN-02 a RN-06.
- La disponibilidad se reporta sobre candidatos (texto de NFR-CAL-003) y, como complemento, sobre contratos en categoría (comparable con la cifra de D4) → resuelto en RN-03.
- Un contrato cuenta como cubierto si al menos uno de sus ítems de televisor llega al resultado → resuelto en RN-04 y RN-06.
- "Comparación utilizable" excluye en la cifra principal las comparaciones incompletas/no confiables (ej. por IVA indeterminado mientras INV-01 está pendiente), que se informan en una variante → resuelto en RN-06.
- El "embudo" de pérdidas es del procesamiento de datos, no analítica de uso de producto (excluida por la épica) → resuelto en RN-07.

---

## Validación INVEST

- [x] **Independiente:** Esta HU puede implementarse sin dependencias bloqueantes de otras HU
- [x] **Negociable:** Describe QUÉ se necesita, no CÓMO implementarlo (detalles técnicos son negociables)
- [x] **Valiosa:** Aporta valor tangible al negocio o usuario final (beneficio claro)
- [x] **Estimable:** El equipo puede estimar esfuerzo (scope claro, no ambiguo)
- [x] **Pequeña:** Completable en pocos días/persona (no excede 1 sprint)
- [x] **Testeable:** Criterios de aceptación permiten verificar cuándo está terminada

## Validación Anti-Ambigüedad

- [x] **Auto-contenida:** Un desarrollador puede implementar esta HU leyendo SOLO este archivo
- [x] **Reglas completas:** Todas las reglas de negocio incluyen formatos, rangos, límites y comportamiento ante nulos
- [x] **Errores explícitos:** El comportamiento ante cada tipo de error está documentado (mensaje, acción, redirección)
- [x] **Edge cases cubiertos:** Criterios de aceptación incluyen casos borde y estados vacíos
- [x] **Supuestos resueltos:** No quedan supuestos pendientes de validación
- [x] **Datos claros:** Origen, formato y proveedor de cada dato están especificados

---

## Definición de Terminado (Inicial)

- [ ] Funcionalidad implementada según criterios de aceptación
- [ ] Validaciones funcionando correctamente
- [ ] Mensajes de usuario implementados
- [ ] Pruebas funcionales pasando

---

## Registro de Cambios

| Fecha | Versión | Descripción | Autor |
|-------|---------|-------------|-------|
| 2026-10-02 | 1.0 | Historia generada desde Épica ÉPICA-008 | Juan Camilo (PO) |

---

> **Método Ceiba estimar hus** v6.1.95 | Modelo: claude-opus-5-5 | Usuario: Juan Camilo | Fecha: 2026-10-05
