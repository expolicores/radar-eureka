# Historia #079: Ver las señales que merecen revisión del contrato en la ficha

**Estado:** Borrador (PO)  
**Release:** Release MVP  
**Épica:** [Exploración y Ficha del Contrato](../../../epicas.md#épica-006-exploración-y-ficha-del-contrato)  
**Feature:** Consulta de la Ficha del Contrato  
**Prioridad:** Crítica  
**FRs relacionados:** FR-074

Escrita por el flujo generar-historias-usuario (Método Ceiba) — MVP propio, no comercial

---

## Historia de Usuario

**Como** Analista que investiga contratación pública,  
**Quiero** ver en la ficha las señales que merecen revisión de los ítems del contrato, con su benchmark, desviación, emparejamiento y nivel de confianza, y abrir el detalle de cada una,  
**Para** identificar rápidamente qué ítems del contrato merecen revisión y por qué, sin salir de la ficha.

## Descripción

Esta HU construye la sección **"Señales"** de la ficha del contrato (HU-076). Lista las señales vigentes de los ítems del contrato u orden, con un resumen de cada una y el acceso a su detalle completo (vista de señales con evidencia, provista por otra épica). La sección muestra siempre la advertencia de que una señal no constituye una conclusión ni una acusación.

También informa, sin generarlas como señales, las situaciones que la plataforma dirige a revisión de calidad (precios anormalmente bajos), para que el Analista no las confunda con señales.

---

## Criterios de Aceptación

### Escenario 1: Ver las señales del contrato (happy path)

- **Dado** que el contrato tiene ítems con señales vigentes
- **Cuando** el Analista abre la sección "Señales"
- **Entonces** ve el título "Señales que merecen revisión ({n})", la advertencia permanente y una fila por señal con los campos de RN-02, ordenadas por la prioridad de RN-03

### Escenario 2: Advertencia permanente

- **Dado** que la sección muestra al menos una señal
- **Cuando** el Analista la ve
- **Entonces** sobre la primera señal aparece "Una señal indica que un precio merece revisión. No constituye una conclusión ni una acusación sobre la entidad, el proveedor o las personas relacionadas."

### Escenario 3: Abrir el detalle de la señal

- **Dado** que el Analista ve una señal en la sección
- **Cuando** activa "Ver señal"
- **Entonces** se abre el detalle de esa señal, desde el cual la evidencia de origen queda a un clic

### Escenario 4: Ir al ítem de la señal

- **Dado** que el Analista ve una señal en la sección
- **Cuando** activa el nombre del ítem
- **Entonces** la ficha se desplaza a la tarjeta de ese ítem en "Ítems de televisor" y la resalta

### Escenario 5: Señal con comparación incompleta o precio derivado

- **Dado** que la señal se sustenta en una comparación con base tributaria indeterminada o en un precio unitario derivado
- **Cuando** se muestra la fila
- **Entonces** aparece la marca "IVA indeterminado — comparación incompleta" o "Precio derivado", según corresponda

### Escenario 6: Contrato sin señales

- **Dado** que ningún ítem del contrato tiene señal vigente y sus comparaciones ya se calcularon
- **Cuando** el Analista abre la sección
- **Entonces** ve "Este contrato no tiene señales que merezcan revisión con la información disponible." y no se muestra la advertencia

### Escenario 7: Comparaciones aún no calculadas

- **Dado** que ningún ítem del contrato tiene todavía comparación calculada
- **Cuando** el Analista abre la sección
- **Entonces** ve "Las señales se mostrarán cuando termine la comparación de los ítems de este contrato."

### Escenario 8: Precio anormalmente bajo en revisión de calidad

- **Dado** que un ítem tiene un precio anormalmente bajo dirigido a revisión de calidad
- **Cuando** se muestra la sección
- **Entonces** debajo de las señales aparece el bloque "En revisión de calidad ({n})" con el ítem y el texto "Precio muy por debajo de la referencia: se revisa como posible error de extracción, cantidad, producto o base tributaria. No es una señal."

---

## Información Recopilada

### Usuario y Contexto

- **Tipo de usuario:** Analista que investiga contratación pública; el Administrador también puede consultar la sección.
- **Permisos requeridos:** Sesión iniciada con rol Analista o Administrador.
- **Valor de negocio:** Conecta el contexto del contrato con las señales de sus ítems y con su evidencia, en el flujo *detectar señal → revisar comparación → revisar evidencia*.

### Reglas de Negocio

- **RN-01 Señales mostradas:** solo señales vigentes (último cálculo de comparación) de ítems del contrato u orden. Solo las desviaciones por encima de la referencia generan señal.
- **RN-02 Campos por señal:** ítem (producto normalizado o descripción original), benchmark usado ("Compras públicas" o "Mercado"), valor de referencia o "Referencia disponible ({n} obs.)", precio unitario contratado, desviación (con signo y una decimal), tipo de emparejamiento ("Mismo modelo" / "Producto equivalente"), nivel de confianza ("Alta" / "Media" / "Baja"), y acción "Ver señal".
- **RN-03 Orden:** nivel de confianza de mayor a menor; luego desviación de mayor a menor; luego orden del ítem en el contrato.
- **RN-04 Marcas:** "IVA indeterminado — comparación incompleta" si la comparación que sustenta la señal está marcada incompleta/no confiable por base tributaria; "Precio derivado" si el precio unitario del ítem es derivado.
- **RN-05 Advertencia:** texto del Escenario 2, visible siempre que la sección tenga al menos una señal, también en móvil.
- **RN-06 Estados:** sin señales con comparaciones calculadas (Escenario 6); sin comparaciones calculadas (Escenario 7). Si algunos ítems tienen comparación y otros no, se muestran las señales existentes y la nota "Algunos ítems aún no tienen comparación calculada."
- **RN-07 Revisión de calidad:** los precios anormalmente bajos no son señales; se muestran en el bloque "En revisión de calidad" con el texto del Escenario 8 y no cuentan en el título de señales.
- **RN-08 Lenguaje:** ningún texto usa "sobreprecio", "corrupción", "fraude" ni "hallazgo fiscal" aplicados al contrato, la entidad, el proveedor o personas.
- **RN-09 Formatos, rendimiento y accesibilidad (valores iniciales de diseño):** pesos `$ 3.900.000`, porcentajes `+35,2 %`; la sección carga dentro del objetivo de la ficha de ≤ 3 segundos (p95) con 20 usuarios concurrentes; WCAG 2.1 AA (teclado, foco visible, marcas con texto); en móvil desde 360 px cada señal se presenta como tarjeta con todos sus campos y acciones.

### Interfaz

- Sección "Señales que merecen revisión ({n})" con la advertencia y la lista de señales (tabla en escritorio, tarjetas en móvil).
- Por señal: nombre del ítem activable (lleva a su tarjeta), campos de RN-02, marcas de RN-04 y acción "Ver señal".
- Bloque "En revisión de calidad ({n})" cuando aplique.
- Mensajes de estado de RN-06.

### Sistemas Externos (Si aplica)

No consulta sistemas externos. Usa las señales vigentes y los resultados de revisión de calidad ya calculados por la plataforma.

---

## Contexto y Referencias

**Épica origen:** [Exploración y Ficha del Contrato](../../../epicas.md#épica-006-exploración-y-ficha-del-contrato)

**Exclusiones de la Épica:**
- NO incluye fichas de entidad ni de proveedor (candidatas, ÉPICA-009).
- NO incluye dashboards nacionales ni de otras categorías.
- NO incluye exploración pública anónima.
- NO incluye la consulta conversacional (chatbot).

**Historias relacionadas:** HU-074 (lista priorizada de señales), HU-076 (estructura de la ficha), HU-077 (ítems), HU-078 (benchmarks)

---

## Supuestos

> Elementos inferidos por la IA que NO estaban explícitos en el PRD o la Épica. Todos los supuestos han sido resueltos: convertidos en reglas de negocio explícitas o eliminados mediante reformulación. Si aparece algún supuesto no resuelto, esta HU NO está lista para desarrollo.

- **Resuelto (RN-07):** los precios anormalmente bajos se muestran en la ficha como "En revisión de calidad", explícitamente diferenciados de las señales.
- **Resuelto (RN-03):** las señales de la ficha se ordenan por confianza, desviación y orden del ítem.

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
| 2026-10-02 | 1.0 | Historia generada desde Épica ÉPICA-006 | Juan Camilo (PO) |

---

> **Método Ceiba estimar hus** v6.1.95 | Modelo: claude-opus-5-5 | Usuario: Juan Camilo | Fecha: 2026-10-05
