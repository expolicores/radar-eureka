# Historia #091: Crear un caso de investigación desde un contrato

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
**Quiero** crear un caso de investigación desde la ficha de un contrato, aunque ese contrato no tenga una señal,  
**Para** empezar a documentar una investigación a partir de un contrato que me interesa y conservar sus datos tal como los vi.

## Descripción

Además de crearse desde una señal (HU-090), un caso puede nacer desde la **ficha de un contrato** (FR-077), por ejemplo cuando el analista encuentra en la exploración un contrato relacionado o uno con información insuficiente que quiere seguir. El caso se crea con el contrato guardado como **instantánea** de solo lectura (FR-081), que no cambia si después se reprocesan documentos, se corrigen datos o se recalculan benchmarks.

Aplica a cualquier registro que tenga ficha de contrato en el producto: contratos de SECOP II y órdenes de compra de la TVEC. La acción "Crear caso" se agrega a la ficha del contrato (vista existente del producto). El caso es visible solo para su autor (HU-097).

---

## Criterios de Aceptación

### Escenario 1: Crear un caso desde la ficha de un contrato

- **Dado** que la analista está en la ficha del contrato `CO1.PCCNTR.5598765` del Municipio de Tunja
- **Cuando** pulsa "Crear caso", acepta o edita el título sugerido, escribe opcionalmente una descripción y pulsa "Crear"
- **Entonces** el sistema crea el caso con su autoría y fechas, guarda el contrato como primer elemento en forma de instantánea con fecha y hora, y muestra: "Caso creado con el contrato guardado." con el enlace "Abrir caso"

### Escenario 2: Título sugerido

- **Dado** que la analista pulsa "Crear caso" en la ficha de un contrato
- **Cuando** se abre el formulario
- **Entonces** el título aparece prellenado como "Contrato — {identificador de origen} — {entidad compradora}" (recortado a 120 caracteres si es más largo) y es editable

### Escenario 3: Título o descripción inválidos

- **Dado** que la analista está en el formulario de nuevo caso
- **Cuando** el título queda vacío o con menos de 3 o más de 120 caracteres tras quitar espacios al inicio y al final, o la descripción supera 1.000 caracteres
- **Entonces** el sistema no crea el caso y muestra según el caso: "Ingresa un título de 3 a 120 caracteres." o "La descripción admite máximo 1.000 caracteres."

### Escenario 4: Contenido de la instantánea del contrato

- **Dado** que se creó el caso desde el contrato
- **Cuando** se consulta la instantánea
- **Entonces** contiene todos los datos de la regla RN-04 y cada dato no disponible en la ficha queda como "No disponible"

### Escenario 5: Contrato sin ítems de televisor extraídos o con información insuficiente

- **Dado** que el contrato está en estado de procesamiento "documentos obtenidos" sin ítems extraídos, o tiene ítems marcados como "información insuficiente"
- **Cuando** la analista crea el caso
- **Entonces** el caso se crea; la instantánea registra el estado de procesamiento, "Sin ítems de televisor extraídos" cuando no hay ítems y, por cada ítem con información insuficiente, el motivo registrado

### Escenario 6: Contrato con señales

- **Dado** que el contrato tiene 2 señales vigentes
- **Cuando** la analista crea el caso desde la ficha
- **Entonces** la instantánea del contrato incluye un resumen de esas 2 señales (identificador, ítem, benchmark, desviación y nivel de confianza) sin guardarlas como elementos de tipo señal; el sistema muestra además el texto "Para conservar el detalle y la evidencia de una señal, guárdala en el caso desde su detalle."

### Escenario 7: Orden de compra de la TVEC

- **Dado** que la ficha corresponde a una orden de compra de la TVEC
- **Cuando** la analista crea el caso
- **Entonces** la instantánea registra fuente "TVEC", el identificador de la orden y los datos disponibles de la orden, con "No disponible" en los campos que no aplican a la TVEC

### Escenario 8: La instantánea no cambia después

- **Dado** que el caso tiene el contrato guardado con 0 ítems extraídos
- **Cuando** posteriormente se extraen 3 ítems de televisor y se genera una señal para ese contrato
- **Entonces** la instantánea del caso sigue mostrando 0 ítems y ninguna señal, con su fecha y hora de captura

### Escenario 9: Cancelar, doble envío y falla al guardar

- **Dado** que la analista abrió el formulario de nuevo caso
- **Cuando** cancela, pulsa "Crear" dos veces seguidas u ocurre un error interno al guardar
- **Entonces** al cancelar no se crea nada; con doble envío se crea un solo caso; ante error no queda caso ni instantánea parcial, el error se registra en el log de aplicación y se muestra "No pudimos crear el caso. Intenta de nuevo." conservando título y descripción

---

## Información Recopilada

### Usuario y Contexto

- **Tipo de usuario:** Analista (también el Administrador, sobre sus propios casos)
- **Permisos requeridos:** sesión activa; funciones de investigación
- **Valor de negocio:** permite iniciar investigaciones desde la exploración (Journey 2) y no solo desde señales, sin perder el estado del contrato observado

### Reglas de Negocio

- **RN-01 — Datos del caso:** identificador no secuencial ni adivinable; autor; título obligatorio (3 a 120 caracteres tras quitar espacios al inicio y al final, puede repetirse); descripción opcional (máximo 1.000 caracteres, texto plano); fecha de creación; fecha de última actualización.
- **RN-02 — Elemento inicial:** el caso se crea con exactamente un elemento de tipo `contrato`.
- **RN-03 — Registros admitidos:** contratos de SECOP II y órdenes de compra de la TVEC que tengan ficha en el producto.
- **RN-04 — Contenido de la instantánea de contrato:** fecha y hora de captura y:
  - **Identificación:** fuente (SECOP II o TVEC), identificador de origen, número de proceso cuando exista y URL pública del proceso u orden.
  - **Datos clave:** entidad compradora, proveedor, objeto, modalidad, valor del contrato u orden (como dato de referencia, no como precio unitario), fechas disponibles (firma u orden, inicio, fin), departamento y municipio.
  - **Procesamiento:** estado (identificado, documentos obtenidos, extraído, revisado, comparado) y motivos de información insuficiente.
  - **Ítems de televisor extraídos:** por ítem, descripción, marca, modelo/referencia, tamaño, cantidad, precio unitario, tipo de precio unitario (`explicito` o `derivado`) y base tributaria; o el texto "Sin ítems de televisor extraídos".
  - **Resumen de señales vigentes:** por señal, identificador, ítem, benchmark usado, desviación y nivel de confianza; o "Sin señales".
  - **Documentos:** lista de documentos del proceso conocidos por el sistema (nombre, tipo e identificador).
  - **Fecha de corte** de los datos.
- **RN-05 — Datos ausentes:** se registran como "No disponible"; nunca se infieren.
- **RN-06 — Inmutabilidad:** la instantánea es de solo lectura y no la modifican extracciones, correcciones, recálculos ni cambios de configuración posteriores.
- **RN-07 — Señales en el contrato:** el resumen de señales es parte de la instantánea del contrato; no crea elementos de tipo señal (para eso, HU-092).
- **RN-08 — Atomicidad e idempotencia:** caso e instantánea se crean juntos o no se crean; doble envío produce un solo caso.
- **RN-09 — Lenguaje:** los textos generados por el sistema nunca usan "sobreprecio", "corrupción", "fraude" ni "hallazgo fiscal".
- **RN-10 — Privacidad:** el caso es visible y modificable solo por su autor.
- **RN-11 — Datos personales excluidos:** la instantánea no incluye datos bancarios ni documentos de identidad de representantes legales, supervisores u ordenadores del gasto (el sistema no los almacena).

### Interfaz

- Botón "Crear caso" en la ficha del contrato.
- Formulario modal "Nuevo caso" igual al de creación desde señal: Título (prellenado, contador), Descripción (opcional, contador), resumen del contrato que se guardará (fuente, identificador, entidad, número de ítems y de señales), "Crear" y "Cancelar".
- Mensaje de confirmación con enlace "Abrir caso"; texto informativo del Escenario 6 cuando el contrato tiene señales.
- WCAG 2.1 AA; funcional en 768 px y 360 px.

### Sistemas Externos (Si aplica)

No aplica. Los datos provienen de la ficha del contrato ya disponible en el sistema.

---

## Contexto y Referencias

**Épica origen:** [Espacio de Investigación del Analista](../../../epicas.md#épica-007-espacio-de-investigación-del-analista)

**Exclusiones de la Épica:**
- NO incluye casos compartidos ni colaboración entre analistas.
- NO incluye login social (Google, Microsoft) ni SSO.
- NO incluye exportación del expediente (candidata, ÉPICA-009).
- NO incluye publicación de casos ni un canal de denuncia a entes de control.

**Historias relacionadas:** HU-090 (crear caso desde señal), HU-092 (guardar elementos en un caso existente), HU-096 (abrir y retomar), HU-097 (privacidad)

---

## Supuestos

> Elementos inferidos por la IA que NO estaban explícitos en el PRD o la Épica. Todos los supuestos han sido resueltos: convertidos en reglas de negocio explícitas o eliminados mediante reformulación. Si aparece algún supuesto no resuelto, esta HU NO está lista para desarrollo.

- "Contrato" incluye las órdenes de compra de la TVEC con ficha (RN-03).
- La instantánea del contrato toma los datos que FR-074 y FR-075 definen para la ficha (RN-04).
- Las señales del contrato se resumen en su instantánea pero no se guardan como elementos de señal (RN-07).

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
