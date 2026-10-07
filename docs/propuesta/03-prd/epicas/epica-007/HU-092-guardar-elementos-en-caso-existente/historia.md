# Historia #092: Guardar señales, contratos y evidencias en un caso existente

**Estado:** Borrador (PO)  
**Release:** Release MVP  
**Épica:** [Espacio de Investigación del Analista](../../../epicas.md#épica-007-espacio-de-investigación-del-analista)  
**Feature:** Crear y Organizar Casos de Investigación  
**Prioridad:** Crítica  
**FRs relacionados:** FR-078, FR-081

Escrita por el flujo generar-historias-usuario (Método Ceiba) — MVP propio, no comercial

---

## Historia de Usuario

**Como** Analista,  
**Quiero** guardar en uno de mis casos varias señales, contratos y evidencias individuales a medida que los encuentro,  
**Para** reunir en un solo lugar todo lo que sustenta mi investigación, conservado tal como lo vi.

## Descripción

Un caso reúne varios elementos (FR-078) de tres tipos: **señal**, **contrato** y **evidencia**. Una evidencia es una pieza individual que sustenta una señal: (a) el **documento de origen** de un dato extraído (documento, página u hoja y celda), o (b) una **observación de referencia** usada en un benchmark (compra pública comparable u observación retail). Cada elemento se guarda como **instantánea** de solo lectura (FR-081), que no cambia aunque luego se recalculen benchmarks o se corrijan datos.

La acción "Guardar en caso" se agrega al detalle de la señal, a la ficha del contrato y a cada evidencia mostrada en el detalle de la señal (vistas existentes del producto). Permite elegir uno de los casos propios o crear uno nuevo. La creación de casos está en HU-090 y HU-091; la vista del caso, en HU-096.

---

## Criterios de Aceptación

### Escenario 1: Guardar una señal en un caso existente

- **Dado** que la analista tiene el caso "Compra TV 65 Gobernación" y está en el detalle de otra señal vigente
- **Cuando** pulsa "Guardar en caso", elige ese caso y pulsa "Guardar"
- **Entonces** el sistema agrega la señal al caso como instantánea con fecha y hora, actualiza la fecha de última actualización del caso y muestra: "Señal guardada en el caso «Compra TV 65 Gobernación»." con el enlace "Abrir caso"

### Escenario 2: Guardar un contrato en un caso existente

- **Dado** que la analista está en la ficha del contrato `CO1.PCCNTR.5598765`
- **Cuando** lo guarda en el caso "Compra TV 65 Gobernación"
- **Entonces** el sistema agrega el contrato como instantánea (RN-05) y muestra: "Contrato guardado en el caso «Compra TV 65 Gobernación»."

### Escenario 3: Guardar el documento de origen como evidencia

- **Dado** que en el detalle de una señal se muestra la evidencia de origen del precio unitario (`oferta_economica.pdf`, página 3)
- **Cuando** la analista pulsa "Guardar en caso" en esa evidencia y elige un caso
- **Entonces** el sistema agrega un elemento de tipo evidencia con los datos de RN-06 (a) y muestra: "Evidencia guardada en el caso «{título}»."

### Escenario 4: Guardar una observación de referencia como evidencia

- **Dado** que en el detalle de una señal se muestra una observación de referencia de Alkosto registrada manualmente
- **Cuando** la analista la guarda en un caso
- **Entonces** el sistema agrega un elemento de tipo evidencia con los datos de RN-06 (b), incluida la marca de observación manual, y muestra el mensaje del Escenario 3

### Escenario 5: Crear un caso nuevo desde el selector

- **Dado** que la analista abre "Guardar en caso"
- **Cuando** elige "Crear caso nuevo", escribe un título válido y pulsa "Guardar"
- **Entonces** el sistema crea el caso con ese elemento como primer elemento y muestra: "Caso creado con el elemento guardado."

### Escenario 6: La analista no tiene casos

- **Dado** que la analista no tiene ningún caso
- **Cuando** abre "Guardar en caso"
- **Entonces** el selector muestra "Aún no tienes casos." y solo la opción "Crear caso nuevo"

### Escenario 7: Elemento ya guardado en ese caso

- **Dado** que la señal ya está guardada en el caso "Compra TV 65 Gobernación"
- **Cuando** la analista intenta guardarla otra vez en el mismo caso
- **Entonces** el sistema no crea otra instantánea y muestra: "Este elemento ya está guardado en el caso «Compra TV 65 Gobernación»."

### Escenario 8: El mismo elemento en casos distintos

- **Dado** que la señal ya está guardada en el caso A
- **Cuando** la analista la guarda en el caso B
- **Entonces** el caso B recibe su propia instantánea con la fecha y los valores del momento, y la instantánea del caso A no cambia

### Escenario 9: Caso con el máximo de elementos

- **Dado** que el caso ya tiene 100 elementos (valor inicial configurable)
- **Cuando** la analista intenta guardar uno más
- **Entonces** el sistema no lo agrega y muestra: "El caso alcanzó el máximo de 100 elementos guardados. Crea un caso nuevo para continuar."

### Escenario 10: El elemento dejó de estar disponible

- **Dado** que la señal o la evidencia que la analista está viendo fue recalculada y ya no existe
- **Cuando** intenta guardarla
- **Entonces** el sistema no agrega nada y muestra: "Este elemento ya no está disponible. Actualiza la página para ver la información vigente."

### Escenario 11: Falla al guardar o doble envío

- **Dado** que la analista pulsa "Guardar"
- **Cuando** ocurre un error interno o la solicitud se envía dos veces
- **Entonces** ante error no queda instantánea parcial, se registra en el log de aplicación y se muestra "No pudimos guardar el elemento. Intenta de nuevo."; ante doble envío se guarda una sola instantánea

---

## Información Recopilada

### Usuario y Contexto

- **Tipo de usuario:** Analista (también el Administrador, sobre sus propios casos)
- **Permisos requeridos:** sesión activa; solo puede guardar en casos de los que es autor
- **Valor de negocio:** construye el expediente de la investigación (Journeys 1 y 2), conservando la evidencia reproducible que sustenta cada señal

### Reglas de Negocio

- **RN-01 — Tipos de elemento:** `señal`, `contrato` y `evidencia` (subtipos `documento_origen` y `observacion_referencia`).
- **RN-02 — Casos elegibles:** el selector muestra solo los casos del usuario de la sesión, ordenados por fecha de última actualización descendente, con título y fecha de última actualización, y la opción "Crear caso nuevo". El servidor rechaza cualquier intento de guardar en un caso ajeno con "No encontramos este caso."
- **RN-03 — Crear caso desde el selector:** título obligatorio de 3 a 120 caracteres tras quitar espacios al inicio y al final ("Ingresa un título de 3 a 120 caracteres."); sin descripción en este formulario.
- **RN-04 — Instantánea de señal:** fecha y hora de captura e identificador de la señal; ítem (descripción, marca, modelo/referencia, tamaño, cantidad, precio unitario, tipo `explicito` o `derivado`, base tributaria); contrato (identificador de origen, entidad, proveedor, fuente, fecha, valor de referencia, URL pública); cada benchmark con estado (referencia estadística, referencia disponible / evidencia limitada, o no disponible / evidencia insuficiente), valor de referencia, número de observaciones y fuentes y ventana aplicada; cada referencia u observación usada (origen, precio, fecha, vendedor, método de adquisición, indicador manual, URL o referencia); fórmula, desviación porcentual, tipo de emparejamiento, regla que priorizó la señal y nivel de confianza; evidencia de origen (identificador de documento, nombre, página u hoja y celda, hash, URL original); fecha de corte; y la advertencia "Esta señal no constituye una conclusión ni una acusación; indica un caso que merece revisión."
- **RN-05 — Instantánea de contrato:** fecha y hora de captura; fuente, identificador de origen, número de proceso y URL pública; entidad, proveedor, objeto, modalidad, valor como dato de referencia, fechas, departamento y municipio; estado de procesamiento y motivos de información insuficiente; ítems de televisor extraídos (o "Sin ítems de televisor extraídos"); resumen de señales vigentes (identificador, ítem, benchmark, desviación, nivel de confianza, o "Sin señales"); documentos conocidos (nombre, tipo, identificador); fecha de corte.
- **RN-06 — Instantánea de evidencia:**
  - **(a) `documento_origen`:** identificador del documento, nombre, tipo de archivo, página u hoja y celda, hash, URL original, fuente, fecha de descarga, el dato extraído que respalda (campo y valor, ej. "precio unitario: $4.250.000") y el contrato y la señal desde donde se guardó.
  - **(b) `observacion_referencia`:** origen (SECOP II, TVEC o retail con la tienda), producto, marca/modelo, vendedor, precio, información de IVA, fecha de observación, método de adquisición, indicador de observación manual, URL o referencia, identificador de la evidencia adjunta cuando exista, y la señal desde donde se guardó.
- **RN-07 — Datos ausentes:** se guardan como "No disponible"; nunca se infieren.
- **RN-08 — Inmutabilidad:** las instantáneas son de solo lectura; ningún recálculo, reprocesamiento, corrección o cambio de configuración las modifica. La copia del documento referenciada por identificador y hash es la conservada por el sistema como evidencia.
- **RN-09 — Duplicados:** un mismo elemento (mismo tipo e identificador; para `documento_origen`, mismo documento y misma página u hoja y celda) no se guarda dos veces en el mismo caso. Sí puede estar en varios casos, cada uno con su propia instantánea.
- **RN-10 — Máximo de elementos:** parámetro configurable `max_elementos_por_caso`, inicial **100**, rango 10 a 500. Si se reduce por debajo de los elementos de un caso existente, ese caso conserva sus elementos pero no admite nuevos.
- **RN-11 — Fecha de última actualización:** se actualiza con cada elemento agregado.
- **RN-12 — Atomicidad e idempotencia:** cada guardado se completa entero o no deja rastro; un doble envío produce una sola instantánea.
- **RN-13 — Lenguaje:** los textos generados por el sistema nunca usan "sobreprecio", "corrupción", "fraude" ni "hallazgo fiscal".

### Interfaz

- Botón "Guardar en caso" en el detalle de la señal, en la ficha del contrato y junto a cada evidencia del detalle de la señal (documento de origen y cada observación de referencia).
- Selector modal: lista de casos propios (título y "Actualizado el dd/mm/aaaa hh:mm"), opción "Crear caso nuevo" con campo Título, botones "Guardar" (deshabilitado mientras se procesa) y "Cancelar". Estado vacío del Escenario 6.
- Mensajes de confirmación con enlace "Abrir caso". WCAG 2.1 AA; funcional en 768 px y 360 px.

### Sistemas Externos (Si aplica)

No aplica. Los datos provienen de las señales, fichas y evidencias ya disponibles en el sistema.

---

## Contexto y Referencias

**Épica origen:** [Espacio de Investigación del Analista](../../../epicas.md#épica-007-espacio-de-investigación-del-analista)

**Exclusiones de la Épica:**
- NO incluye casos compartidos ni colaboración entre analistas.
- NO incluye login social (Google, Microsoft) ni SSO.
- NO incluye exportación del expediente (candidata, ÉPICA-009).
- NO incluye publicación de casos ni un canal de denuncia a entes de control.

**Historias relacionadas:** HU-090, HU-091 (crear caso), HU-096 (abrir y retomar), HU-097 (privacidad)

---

## Supuestos

> Elementos inferidos por la IA que NO estaban explícitos en el PRD o la Épica. Todos los supuestos han sido resueltos: convertidos en reglas de negocio explícitas o eliminados mediante reformulación. Si aparece algún supuesto no resuelto, esta HU NO está lista para desarrollo.

- "Evidencia" se define como el documento de origen de un dato o una observación de referencia de un benchmark (RN-06).
- Se fija un máximo configurable de 100 elementos por caso y se rechazan duplicados en un mismo caso (RN-09, RN-10).
- Quitar elementos de un caso no está en los FRs de la épica y queda fuera del MVP.

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
| 2026-10-02 | 1.0 | Historia generada desde Épica ÉPICA-007 | Juan Camilo (PO) |

---

> **Método Ceiba estimar hus** v6.1.95 | Modelo: claude-opus-5-5 | Usuario: Juan Camilo | Fecha: 2026-10-05
