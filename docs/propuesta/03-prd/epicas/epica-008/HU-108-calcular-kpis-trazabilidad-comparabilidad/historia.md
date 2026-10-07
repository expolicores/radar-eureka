# Historia #108: Verificar trazabilidad de señales, clasificación de comparaciones y base tributaria

**Estado:** Borrador (PO)  
**Release:** Release MVP  
**Épica:** [Operación, Calidad y Medición del MVP](../../../epicas.md#épica-008-operación-calidad-y-medición-del-mvp)  
**Feature:** Medir KPIs del MVP  
**Prioridad:** Alta  
**FRs relacionados:** FR-091 (relacionados: FR-024, FR-039, FR-057, FR-065; NFR-CAL-004, NFR-CAL-005, NFR-CAL-006)

Escrita por el flujo generar-historias-usuario (Método Ceiba) — MVP propio, no comercial

---

## Historia de Usuario

**Como** Administrador del MVP (el PO),  
**Quiero** calcular los KPIs de trazabilidad de las señales, de clasificación de las comparaciones y de coherencia de la base tributaria, con la lista de los casos que incumplen,  
**Para** demostrar que el 100 % de las señales lleva a su evidencia, que el 100 % de las comparaciones está clasificado y que ninguna mezcla valores con y sin IVA sin advertirlo, y corregir cualquier excepción antes de mostrarla a los analistas.

## Descripción

Tres KPIs del Brief son verificables de forma determinística sobre los datos del sistema:

| KPI | Meta | Fuente |
|---|---|---|
| Trazabilidad: % de señales que permiten regresar al contrato, al documento o dato de origen y a cada referencia usada | 100 % | NFR-CAL-004 |
| Comparabilidad: % de comparaciones clasificadas como *mismo modelo*, *producto equivalente* o *insuficiente/no confiable* | 100 % | NFR-CAL-005 |
| Base tributaria: % de comparaciones que mezclan valores con y sin IVA (o de base indeterminada) sin estar marcadas como incompletas/no confiables | 0 % | NFR-CAL-006 |

Esta HU recorre las señales y comparaciones vigentes, verifica cada condición, calcula los tres indicadores, lista cada incumplimiento con su motivo y guarda el resultado como corte histórico. No corrige nada: solo mide y señala.

**Implementación sin UI permitida:** comando, script, consulta o reporte (texto, CSV o JSON).

---

## Criterios de Aceptación

### Escenario 1: Todos los KPIs cumplen

- **Dado** que hay 120 señales vigentes, todas con sus vínculos completos, y 1.400 comparaciones vigentes, todas clasificadas y sin mezcla de bases no marcada
- **Cuando** el Administrador calcula los KPIs
- **Entonces** obtiene trazabilidad 100,0 % (120/120) "Cumple", comparabilidad 100,0 % (1.400/1.400) "Cumple" y base tributaria 0,0 % (0/1.400) "Cumple"

### Escenario 2: Señal sin ubicación de la evidencia

- **Dado** que la señal SEN-0042 (ítem SECOP II) tiene documento de origen del precio pero sin página, hoja ni celda
- **Cuando** se calculan los KPIs
- **Entonces** SEN-0042 cuenta como no trazable, la trazabilidad es 99,2 % (119/120) "No cumple" y la lista de incumplimientos muestra "SEN-0042: falta la ubicación (página, hoja o celda) del precio en el documento DOC-30542."

### Escenario 3: Copia de evidencia faltante o alterada

- **Dado** que la señal SEN-0050 usa el documento DOC-30611 cuya copia conservada no existe, y SEN-0051 usa DOC-30700 cuya copia tiene un hash distinto del registrado
- **Cuando** se calculan los KPIs
- **Entonces** ambas son no trazables con los motivos "falta la copia conservada del documento DOC-30611." y "el hash de la copia del documento DOC-30700 no coincide con el registrado."

### Escenario 4: Referencia usada sin trazabilidad

- **Dado** que la señal SEN-0060 usa 6 observaciones y una de ellas (OBS-7781, retail manual) no tiene evidencia adjunta
- **Cuando** se calculan los KPIs
- **Entonces** SEN-0060 es no trazable con el motivo "la observación OBS-7781 no tiene evidencia adjunta."

### Escenario 5: Señal de un ítem TVEC

- **Dado** que la señal SEN-0070 corresponde a un ítem TVEC con identificador de orden e ítem de origen existentes
- **Cuando** se verifica su trazabilidad
- **Entonces** no se le exige documento ni página: el dato de origen es el registro TVEC, y la señal es trazable si cumple las demás condiciones

### Escenario 6: Comparación sin clasificar

- **Dado** que la comparación CMP-9001 no tiene tipo de emparejamiento, y CMP-9002 tiene el valor no permitido "similar"
- **Cuando** se calculan los KPIs
- **Entonces** ambas cuentan como no clasificadas, la comparabilidad baja a 99,9 % (1.398/1.400) "No cumple" y la lista muestra "CMP-9001: sin clasificación." y "CMP-9002: clasificación no válida 'similar'."

### Escenario 7: Distribución de la clasificación

- **Dado** que de 1.400 comparaciones, 310 son mismo modelo, 780 producto equivalente y 310 insuficiente/no confiable
- **Cuando** se calculan los KPIs
- **Entonces** el reporte incluye la distribución 22,1 % / 55,7 % / 22,1 %, separada por benchmark (compras públicas / mercado)

### Escenario 8: Mezcla de bases tributarias no marcada

- **Dado** que la comparación CMP-9100 compara un precio contratado con IVA contra observaciones TVEC de base indeterminada y no está marcada incompleta/no confiable
- **Cuando** se calculan los KPIs
- **Entonces** el indicador de base tributaria es 0,1 % (1/1.400) "No cumple" y la lista muestra "CMP-9100: combina bases con IVA e indeterminada sin marca de comparación incompleta/no confiable."

### Escenario 9: Mezcla de bases correctamente marcada

- **Dado** que la comparación CMP-9101 combina bases con IVA e indeterminada y está marcada incompleta/no confiable
- **Cuando** se calculan los KPIs
- **Entonces** no cuenta como incumplimiento de base tributaria

### Escenario 10: Sin señales ni comparaciones

- **Dado** que no hay señales ni comparaciones vigentes
- **Cuando** se calculan los KPIs
- **Entonces** los tres indicadores muestran "—" con estado "Sin datos: no hay señales vigentes." o "Sin datos: no hay comparaciones vigentes.", sin error

### Escenario 11: Exportar incumplimientos y corte histórico

- **Dado** que hay incumplimientos
- **Cuando** el Administrador exporta la lista y luego consulta el historial
- **Entonces** obtiene un CSV con una fila por incumplimiento (KPI, id, motivo) y el historial muestra cada corte con fecha y hora, totales, indicadores y estados

### Escenario 12: Usuario sin rol Administrador

- **Dado** que un usuario con rol Analista está autenticado
- **Cuando** intenta calcular o consultar estos KPIs
- **Entonces** recibe "Acción no permitida: esta operación requiere el rol Administrador."

---

## Información Recopilada

### Usuario y Contexto

- **Tipo de usuario:** Administrador (en el MVP, el PO).
- **Permisos requeridos:** rol Administrador.
- **Valor de negocio:** la credibilidad de las señales depende de que todas sean verificables y comparables en la misma base; este control detecta excepciones antes de que lleguen a los analistas.

### Reglas de Negocio

- **RN-01 — Población:** señales vigentes (no reemplazadas por un recálculo posterior) y comparaciones vigentes (cada cálculo de benchmark de compras públicas o de mercado para un ítem). Las instantáneas guardadas en casos de investigación no se incluyen.
- **RN-02 — Señal trazable:** cumple **todas** las condiciones:
  1. El contrato SECOP II o la orden TVEC referenciados existen.
  2. Dato de origen del precio: para ítems SECOP II, documento existente con ubicación (página, o hoja y celda), copia conservada del archivo y hash de la copia igual al registrado; para ítems TVEC, identificadores de orden e ítem de origen existentes.
  3. Cada observación usada como referencia existe y tiene fuente, fecha de observación y URL o referencia; las observaciones retail tienen además método de adquisición y evidencia adjunta, y las de compras públicas su identificador de origen.
  4. La señal registra la fórmula, la referencia y la versión de configuración con que se calculó.
  Cada condición incumplida genera un motivo; una señal puede tener varios.
- **RN-03 — Comparación clasificada:** su tipo de emparejamiento es exactamente uno de `mismo modelo`, `producto equivalente`, `insuficiente/no confiable`. Vacío u otro valor = no clasificada.
- **RN-04 — Incumplimiento de base tributaria:** comparación cuyos valores (precio contratado y observaciones usadas) no tienen todos la misma base determinada (`con IVA` o `sin IVA`), es decir, combinan bases distintas o alguna `indeterminada`, y **no** está marcada incompleta/no confiable. Una comparación en la que todos los valores tienen la misma base determinada nunca es incumplimiento.
- **RN-05 — Fórmulas y estados:** trazabilidad = señales trazables / señales vigentes (meta 100,0 %); comparabilidad = comparaciones clasificadas / comparaciones vigentes (meta 100,0 %); base tributaria = comparaciones con incumplimiento / comparaciones vigentes (meta 0,0 %). "Cumple" solo si el conteo de incumplimientos es exactamente 0 (no se usa el porcentaje redondeado). Porcentajes con 1 decimal. Denominador 0 → "—" y "Sin datos: no hay señales vigentes." o "Sin datos: no hay comparaciones vigentes.".
- **RN-06 — Distribución de clasificación:** conteo y porcentaje por tipo de emparejamiento, total y por benchmark.
- **RN-07 — Lista de incumplimientos:** por KPI, el id de la señal o comparación y su motivo con los textos de los escenarios 2, 3, 4, 6 y 8; exportable en CSV UTF-8 con columnas `kpi`, `id`, `motivo`.
- **RN-08 — Corte histórico:** cada cálculo se guarda inmutable con fecha y hora (UTC−05:00), usuario, versión de configuración, totales, indicadores, estados, distribución y lista de incumplimientos. A demanda; no modifica datos.
- **RN-09 — Lenguaje:** los textos del reporte hablan de "señales que merecen revisión"; nunca usan "sobreprecio", "corrupción", "fraude" ni "hallazgo fiscal".
- **RN-10 — Mensajes:** los de RN-05 y RN-07, y "Acción no permitida: esta operación requiere el rol Administrador."

### Interfaz

No requiere interfaz gráfica. Mínimo aceptable: comando "calcular KPIs de trazabilidad y comparabilidad" con reporte (texto, CSV o JSON), exportación de incumplimientos e historial de cortes.

### Sistemas Externos (Si aplica)

No aplica (no consulta las fuentes: verifica las copias y registros internos).

---

## Contexto y Referencias

**Épica origen:** [Operación, Calidad y Medición del MVP](../../../epicas.md#épica-008-operación-calidad-y-medición-del-mvp)

**Exclusiones de la Épica:**
- NO incluye analítica de uso avanzada ni embudos de producto.
- NO incluye facturación ni gestión de planes.
- NO incluye administración multi-organización.

**Historias relacionadas:** HU-107 (cobertura), HU-110 (validación humana y eficiencia).

---

## Supuestos

> Elementos inferidos por la IA que NO estaban explícitos en el PRD o la Épica. Todos los supuestos han sido resueltos: convertidos en reglas de negocio explícitas o eliminados mediante reformulación. Si aparece algún supuesto no resuelto, esta HU NO está lista para desarrollo.

- La trazabilidad verifica también la copia conservada y su hash (FR-024), no solo la existencia del vínculo → resuelto en RN-02.
- Para ítems TVEC el "dato de origen" es el registro TVEC, sin documento ni página → resuelto en RN-02.
- Los KPIs se miden sobre señales y comparaciones vigentes, no sobre instantáneas de casos → resuelto en RN-01.

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
