# Historia #090: Crear un caso de investigación desde una señal

**Estado:** Borrador (PO)  
**Release:** Release MVP  
**Épica:** [Espacio de Investigación del Analista](../../../epicas.md#épica-007-espacio-de-investigación-del-analista)  
**Feature:** Crear y Organizar Casos de Investigación  
**Prioridad:** Crítica  
**FRs relacionados:** FR-077, FR-081

Escrita por el flujo generar-historias-usuario (Método Ceiba) — MVP propio, no comercial

---

## Historia de Usuario

**Como** Analista,  
**Quiero** crear un caso de investigación desde el detalle de una señal que merece revisión, guardando esa señal con su evidencia tal como la vi,  
**Para** continuar la investigación después sin perder la comparación ni la evidencia, aunque los benchmarks se recalculen.

## Descripción

Último paso del Journey 1: tras revisar una señal y su evidencia, el analista crea un **caso** (contenedor privado de su investigación). El caso nace con la señal guardada como **instantánea**: una copia de solo lectura de los datos de la señal, sus referencias y su evidencia en el momento de guardarla (FR-081). Si después se recalculan los benchmarks, se reprocesan documentos o se corrigen datos, la instantánea del caso no cambia.

La acción "Crear caso" se agrega al detalle de la señal (vista existente del producto). La creación desde un contrato está en HU-091; guardar elementos en un caso existente, en HU-092. El caso es visible solo para su autor (HU-097).

---

## Criterios de Aceptación

### Escenario 1: Crear un caso desde una señal

- **Dado** que la analista está en el detalle de una señal vigente del contrato `CO1.PCCNTR.5512345` de la Gobernación de Santander
- **Cuando** pulsa "Crear caso", acepta o edita el título sugerido, escribe opcionalmente una descripción y pulsa "Crear"
- **Entonces** el sistema crea el caso con su autoría, fecha de creación y fecha de última actualización, guarda la señal como primer elemento del caso en forma de instantánea con fecha y hora, y muestra: "Caso creado con la señal guardada." con el enlace "Abrir caso"

### Escenario 2: Título sugerido

- **Dado** que la analista pulsa "Crear caso" en una señal
- **Cuando** se abre el formulario
- **Entonces** el título aparece prellenado como "Señal — {entidad compradora} — {fecha de firma dd/mm/aaaa}" (recortado a 120 caracteres si es más largo) y es editable; si la fecha de firma no está disponible, se usa "Señal — {entidad compradora}"

### Escenario 3: Título inválido

- **Dado** que la analista está en el formulario de nuevo caso
- **Cuando** deja el título vacío, con menos de 3 o más de 120 caracteres (tras quitar espacios al inicio y al final)
- **Entonces** el sistema no crea el caso y muestra: "Ingresa un título de 3 a 120 caracteres."

### Escenario 4: Descripción demasiado larga

- **Dado** que la analista está en el formulario de nuevo caso
- **Cuando** la descripción supera 1.000 caracteres
- **Entonces** el sistema no crea el caso y muestra: "La descripción admite máximo 1.000 caracteres."

### Escenario 5: Contenido de la instantánea

- **Dado** que se creó el caso desde la señal
- **Cuando** se consulta la instantánea guardada
- **Entonces** contiene todos los datos de la regla RN-05 (ítem, contrato, benchmarks, referencias y observaciones, fórmula, desviación, tipo de emparejamiento, base tributaria, nivel de confianza, fecha de corte, evidencia de origen y advertencia), y cada dato que no estaba disponible en la señal queda registrado como "No disponible" en lugar de omitirse

### Escenario 6: Señal con Benchmark 2 no disponible

- **Dado** que la señal tiene el Benchmark 2 marcado como "no disponible / evidencia insuficiente" o como "referencia de mercado disponible" por debajo del mínimo de observaciones
- **Cuando** se crea el caso
- **Entonces** la instantánea conserva exactamente ese estado y su texto, sin convertirlo en "precio de mercado"

### Escenario 7: La instantánea no cambia tras un recálculo

- **Dado** que el caso tiene la señal guardada con desviación +42 % y nivel de confianza "Medio"
- **Cuando** el sistema recalcula los benchmarks y la señal pasa a +35 % y confianza "Alto", o deja de existir
- **Entonces** la instantánea del caso sigue mostrando +42 % y "Medio" con su fecha y hora de captura

### Escenario 8: La señal dejó de estar disponible antes de confirmar

- **Dado** que la analista abrió el formulario de nuevo caso y, mientras tanto, la señal fue recalculada y ya no existe
- **Cuando** pulsa "Crear"
- **Entonces** el sistema no crea el caso y muestra: "Esta señal ya no está disponible. Actualiza la página para ver la información vigente."

### Escenario 9: Cancelar

- **Dado** que la analista abrió el formulario de nuevo caso
- **Cuando** pulsa "Cancelar" o cierra el formulario
- **Entonces** no se crea ningún caso y permanece en el detalle de la señal

### Escenario 10: Doble envío

- **Dado** que la analista pulsa "Crear" dos veces seguidas
- **Cuando** el sistema procesa las solicitudes
- **Entonces** se crea un solo caso con una sola instantánea

### Escenario 11: Falla al guardar

- **Dado** que ocurre un error interno al guardar el caso o la instantánea
- **Cuando** la analista pulsa "Crear"
- **Entonces** no queda ningún caso ni instantánea parcial, el error se registra en el log de aplicación y se muestra: "No pudimos crear el caso. Intenta de nuevo."; el formulario conserva el título y la descripción

---

## Información Recopilada

### Usuario y Contexto

- **Tipo de usuario:** Analista (también disponible para el Administrador, sobre sus propios casos)
- **Permisos requeridos:** sesión activa; funciones de investigación (rol `Analista` o `Administrador`)
- **Valor de negocio:** convierte una señal en una investigación persistente, que es el resultado del flujo que valida la hipótesis (*explorar → detectar señal → revisar evidencia → guardar caso → continuar investigación*)

### Reglas de Negocio

- **RN-01 — Datos del caso:** identificador no secuencial ni adivinable; autor (usuario de la sesión); título; descripción opcional; fecha de creación; fecha de última actualización (cambia con cada elemento o nota que se agregue, edite o elimine).
- **RN-02 — Título:** obligatorio; se eliminan espacios al inicio y al final; 3 a 120 caracteres; texto libre. Puede repetirse entre casos del mismo autor.
- **RN-03 — Descripción:** opcional; máximo 1.000 caracteres; texto plano (no se interpreta formato ni código); vacío se guarda como sin descripción.
- **RN-04 — Elemento inicial:** el caso se crea con exactamente un elemento de tipo `señal`. No existe la creación de un caso vacío desde esta acción.
- **RN-05 — Contenido de la instantánea de señal:** fecha y hora de captura e identificador de la señal, más:
  - **Ítem:** descripción, marca, modelo/referencia, tamaño en pulgadas, cantidad, precio unitario, tipo de precio unitario (`explicito` o `derivado`) y base tributaria (con IVA, sin IVA o indeterminada).
  - **Contrato:** identificador de origen, entidad compradora, proveedor, fuente (SECOP II o TVEC), fecha de firma o de la orden, valor del contrato como dato de referencia y URL pública del proceso.
  - **Benchmarks:** por cada benchmark (1 – Contratación pública y 2 – Mercado): estado (referencia estadística, referencia disponible / evidencia limitada, o no disponible / evidencia insuficiente), valor de referencia cuando exista, número de observaciones y de fuentes, y ventana temporal aplicada.
  - **Referencias y observaciones usadas:** por cada una, origen (SECOP II, TVEC o retail con la tienda), precio, fecha, vendedor cuando aplique, método de adquisición, indicador de observación manual y URL o referencia.
  - **Cálculo:** fórmula, desviación porcentual, tipo de emparejamiento (mismo modelo o producto equivalente), regla que priorizó la señal (valores atípicos o umbral porcentual) y nivel de confianza.
  - **Evidencia de origen del precio:** identificador del documento, nombre, página u hoja y celda, hash y URL original de la copia conservada por el sistema.
  - **Fecha de corte** de los datos y **advertencia** que acompaña a la señal: "Esta señal no constituye una conclusión ni una acusación; indica un caso que merece revisión."
- **RN-06 — Datos ausentes:** un dato que la señal no tenía se guarda como "No disponible"; nunca se completa con estimaciones ni con el valor del contrato de datos abiertos.
- **RN-07 — Inmutabilidad:** la instantánea es de solo lectura; no la modifican recálculos de benchmarks, reprocesamiento de documentos, correcciones de datos ni cambios de configuración. Solo guarda valores, no referencias vivas, salvo el vínculo a la copia conservada del documento (identificador y hash), que tampoco cambia.
- **RN-08 — Validez al confirmar:** la señal se verifica como vigente en el momento de pulsar "Crear" y la instantánea se toma de los valores de ese momento (Escenario 8).
- **RN-09 — Atomicidad e idempotencia:** caso e instantánea se crean juntos o no se crean; un doble envío produce un solo caso.
- **RN-10 — Lenguaje:** los textos generados por el sistema en el caso (títulos sugeridos, etiquetas, mensajes) nunca usan "sobreprecio", "corrupción", "fraude" ni "hallazgo fiscal"; se habla de "señal que merece revisión". El texto que escribe el analista en título y descripción es libre.
- **RN-11 — Privacidad:** el caso es visible y modificable solo por su autor.

### Interfaz

- Botón "Crear caso" en el detalle de la señal, visible con sesión activa.
- Formulario modal "Nuevo caso" con: Título (prellenado según Escenario 2, contador de caracteres), Descripción (opcional, contador hasta 1.000), resumen de la señal que se guardará (contrato, ítem, desviación y nivel de confianza), botones "Crear" (deshabilitado mientras se procesa) y "Cancelar".
- Mensaje de confirmación con enlace "Abrir caso".
- Errores junto a cada campo. WCAG 2.1 AA y navegación por teclado; funcional en 768 px y 360 px.

### Sistemas Externos (Si aplica)

No aplica. Los datos provienen de la señal ya calculada y de la evidencia conservada por el sistema.

---

## Contexto y Referencias

**Épica origen:** [Espacio de Investigación del Analista](../../../epicas.md#épica-007-espacio-de-investigación-del-analista)

**Exclusiones de la Épica:**
- NO incluye casos compartidos ni colaboración entre analistas.
- NO incluye login social (Google, Microsoft) ni SSO.
- NO incluye exportación del expediente (candidata, ÉPICA-009).
- NO incluye publicación de casos ni un canal de denuncia a entes de control.

**Historias relacionadas:** HU-091 (crear caso desde contrato), HU-092 (guardar elementos en un caso existente), HU-096 (abrir y retomar un caso), HU-097 (privacidad)

---

## Supuestos

> Elementos inferidos por la IA que NO estaban explícitos en el PRD o la Épica. Todos los supuestos han sido resueltos: convertidos en reglas de negocio explícitas o eliminados mediante reformulación. Si aparece algún supuesto no resuelto, esta HU NO está lista para desarrollo.

- El caso tiene título (3 a 120) y descripción opcional (hasta 1.000), con título sugerido (RN-02, RN-03, Escenario 2).
- El contenido de la instantánea se define a partir de los datos que FR-065 asocia a la señal (RN-05).
- Renombrar o eliminar casos no está en los FRs de la épica y queda fuera del MVP.

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
