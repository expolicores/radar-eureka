# Historia #071: Filtrar la exploración por fechas, rango de valor y UNSPSC

**Estado:** Borrador (PO)  
**Release:** Release MVP  
**Épica:** [Exploración y Ficha del Contrato](../../../epicas.md#épica-006-exploración-y-ficha-del-contrato)  
**Feature:** Búsqueda y Filtrado de Compras  
**Prioridad:** Crítica  
**FRs relacionados:** FR-071

Escrita por el flujo generar-historias-usuario (Método Ceiba) — MVP propio, no comercial

---

## Historia de Usuario

**Como** Analista que investiga contratación pública,  
**Quiero** acotar la exploración por un rango de fechas de compra, por un rango de valor del contrato u orden y por códigos UNSPSC,  
**Para** enfocar la revisión en un período, un tamaño de compra o una categoría de clasificación concretos.

## Descripción

Esta HU agrega al panel de filtros de la vista "Exploración" (HU-069) tres criterios: **Fechas**, **Rango de valor** y **UNSPSC**. Funcionan en los modos "Contratos" e "Ítems de televisor" y se combinan con los demás filtros (Y entre criterios distintos, O entre valores del mismo criterio).

La fecha usada es la fecha de la compra: fecha de firma del contrato en SECOP II y fecha de la orden en la TVEC. El rango de valor se aplica sobre el **valor del contrato u orden publicado en datos abiertos**, que es un dato de referencia del contrato y nunca un sustituto del precio unitario del ítem. El UNSPSC se aplica sobre el código de categoría principal del contrato SECOP II; la TVEC no publica ese código.

---

## Criterios de Aceptación

### Escenario 1: Filtrar por un rango de fechas (happy path)

- **Dado** que el Analista está en la exploración
- **Cuando** ingresa "Desde" 01/01/2025 y "Hasta" 31/12/2025 y pulsa "Aplicar"
- **Entonces** el listado muestra solo los registros cuya fecha de compra está entre esas dos fechas, ambas incluidas, y aparece la etiqueta "Fechas: 01/01/2025 – 31/12/2025"

### Escenario 2: Usar un rango predefinido

- **Dado** que el Analista está en la exploración
- **Cuando** elige "Últimos 12 meses"
- **Entonces** se aplica "Desde" = fecha de hoy menos 12 meses + 1 día y "Hasta" = hoy, y la etiqueta muestra "Fechas: Últimos 12 meses ({desde} – {hasta})"

### Escenario 3: Solo una de las dos fechas

- **Dado** que el Analista ingresa solo "Desde" o solo "Hasta"
- **Cuando** pulsa "Aplicar"
- **Entonces** el filtro se aplica abierto por el otro extremo y la etiqueta muestra "Fechas: desde {fecha}" o "Fechas: hasta {fecha}"

### Escenario 4: Fecha inicial posterior a la final

- **Dado** que el Analista ingresa "Desde" 01/06/2026 y "Hasta" 01/01/2026
- **Cuando** pulsa "Aplicar"
- **Entonces** el filtro no se aplica y se muestra "La fecha inicial no puede ser posterior a la fecha final."

### Escenario 5: Fecha inválida o futura

- **Dado** que el Analista ingresa una fecha que no existe (ej. 31/02/2026), con formato distinto de DD/MM/AAAA, o posterior a hoy
- **Cuando** pulsa "Aplicar"
- **Entonces** el filtro no se aplica y se muestra "Ingresa una fecha válida con formato DD/MM/AAAA." o "La fecha no puede ser posterior a hoy.", según el caso

### Escenario 6: Filtrar por rango de valor

- **Dado** que el Analista está en la exploración
- **Cuando** ingresa "Valor mínimo" 10.000.000 y "Valor máximo" 50.000.000 y pulsa "Aplicar"
- **Entonces** el listado muestra solo los registros cuyo valor del contrato u orden está entre esos valores, ambos incluidos, y aparece la etiqueta "Valor: $ 10.000.000 – $ 50.000.000"

### Escenario 7: Valor mínimo mayor que el máximo o valor no válido

- **Dado** que el Analista ingresa un mínimo mayor que el máximo, un valor negativo, con decimales, con letras o de más de 12 dígitos
- **Cuando** pulsa "Aplicar"
- **Entonces** el filtro no se aplica y se muestra "El valor mínimo no puede ser mayor que el valor máximo." o "Ingresa un valor en pesos, solo con números enteros (máximo 12 dígitos).", según el caso

### Escenario 8: Filtrar por UNSPSC

- **Dado** que el Analista está en la exploración
- **Cuando** ingresa "52161505" (o "V1.52161505") en "UNSPSC" y lo agrega
- **Entonces** el listado muestra solo los contratos SECOP II cuyo código de categoría principal es 52161505, aparece la etiqueta "UNSPSC: 52161505" y se muestra la nota "Los registros de la TVEC no publican código UNSPSC y no aparecen cuando este filtro está activo."

### Escenario 9: Código UNSPSC inválido

- **Dado** que el Analista ingresa un código que no tiene 8 dígitos (ej. "5216150" o "52161505X")
- **Cuando** intenta agregarlo
- **Entonces** no se agrega y se muestra "Ingresa un código UNSPSC de 8 dígitos (ej. 52161505)."

### Escenario 10: Código UNSPSC sin registros en el universo

- **Dado** que el Analista ingresa un código de 8 dígitos válido que ningún registro del universo tiene como categoría principal
- **Cuando** lo agrega
- **Entonces** el filtro se aplica y el listado muestra el estado "No encontramos resultados con los filtros aplicados."

### Escenario 11: Registros sin fecha, sin valor o sin UNSPSC

- **Dado** que un registro no tiene fecha de compra, valor o UNSPSC publicados
- **Cuando** está activo el filtro correspondiente
- **Entonces** ese registro no aparece en los resultados; cuando el filtro no está activo, el registro sí aparece

### Escenario 12: Combinar fechas, valor y UNSPSC con otros filtros

- **Dado** que el Analista aplicó fechas, rango de valor, UNSPSC y un filtro de otra HU (ej. entidad)
- **Cuando** el listado se actualiza
- **Entonces** solo aparecen los registros que cumplen todos los criterios a la vez, en la página 1

---

## Información Recopilada

### Usuario y Contexto

- **Tipo de usuario:** Analista que investiga contratación pública; el Administrador puede usar los mismos filtros.
- **Permisos requeridos:** Sesión iniciada con rol Analista o Administrador.
- **Valor de negocio:** Permite revisar períodos concretos (por ejemplo, los últimos 12 meses del recorrido principal del analista), compras de cierto tamaño o categorías de clasificación.

### Reglas de Negocio

- **RN-01 Fecha de compra:** SECOP II = `fecha_de_firma` del contrato; TVEC = fecha de la orden de compra. En modo "Ítems de televisor" se usa la fecha del contrato u orden al que pertenece el ítem.
- **RN-02 Formato y rango de fechas:** formato `DD/MM/AAAA`, también seleccionable en un calendario; el rango es inclusivo en ambos extremos y se evalúa en hora de Colombia (UTC−5). "Hasta" no puede ser posterior a la fecha de hoy. No hay fecha mínima bloqueante; debajo del campo se muestra la ayuda "Histórico disponible desde {fecha de compra más antigua del universo}".
- **RN-03 Rangos predefinidos:** "Últimos 30 días" (hoy − 29 días a hoy), "Últimos 6 meses" (hoy − 6 meses + 1 día a hoy), "Últimos 12 meses" (hoy − 12 meses + 1 día a hoy) y "Año en curso" (01/01 del año actual a hoy). El rango predefinido se recalcula con la fecha del día cada vez que se carga la exploración, también desde una URL guardada.
- **RN-04 Valor del contrato u orden:** SECOP II = `valor_del_contrato` publicado en datos abiertos; TVEC = valor total de la orden. Este valor es dato de referencia del contrato y no representa el precio unitario de ningún ítem. En modo "Ítems de televisor" el filtro se evalúa con el valor del contrato u orden del ítem.
- **RN-05 Formato del valor:** pesos colombianos, enteros ≥ 0, máximo 12 dígitos (hasta 999.999.999.999). El campo acepta solo dígitos y muestra separadores de miles con punto mientras se escribe. Rango inclusivo; se puede ingresar solo el mínimo o solo el máximo.
- **RN-06 Formato UNSPSC:** exactamente 8 dígitos. Se acepta el prefijo "V1." de SECOP II y se normaliza al código de 8 dígitos ("V1.52161505" → "52161505"). Se comparan contra el código de categoría principal (`codigo_de_categoria_principal`) del contrato. Hasta 5 códigos a la vez, combinados con O; un sexto código no se agrega y se muestra "Puedes agregar hasta 5 códigos UNSPSC."
- **RN-07 Sugerencias UNSPSC:** al enfocar el campo se listan los códigos presentes en el universo con su número de contratos, ordenados de mayor a menor, como atajo de selección.
- **RN-08 TVEC y UNSPSC:** las órdenes TVEC no tienen código UNSPSC; con el filtro UNSPSC activo no aparecen y se muestra la nota del Escenario 8.
- **RN-09 Nulos:** con un filtro de fechas, valor o UNSPSC activo, se excluyen los registros sin el dato correspondiente.
- **RN-10 Validación antes de aplicar:** fechas y valores se aplican con el botón "Aplicar" de su sección (o Enter en el campo) solo si pasan las validaciones; los mensajes de error aparecen junto al campo y el listado no cambia. Los rangos predefinidos y los códigos UNSPSC se aplican al elegirlos o agregarlos.
- **RN-11 Combinación y persistencia:** Y con los demás criterios; vuelve a la página 1 en cada cambio; los valores se guardan en la URL de la exploración y se restauran al recargar o volver de la ficha.
- **RN-12 Tiempo de respuesta:** aplicar cualquiera de estos filtros responde en ≤ 3 segundos (p95) con el volumen del MVP y 20 usuarios concurrentes (objetivo inicial de diseño, configurable y recalibrable).
- **RN-13 Accesibilidad (WCAG 2.1 AA, valor inicial de diseño):** campos con etiqueta visible y formato indicado ("DD/MM/AAAA", "en pesos"); el calendario es operable con teclado; los mensajes de error se asocian al campo y se anuncian a lectores de pantalla.

### Interfaz

- Sección "Fechas de compra": campos "Desde" y "Hasta" con calendario, botones de rangos predefinidos ("Últimos 30 días", "Últimos 6 meses", "Últimos 12 meses", "Año en curso"), botón "Aplicar" y ayuda de histórico disponible.
- Sección "Valor del contrato u orden": campos "Valor mínimo" y "Valor máximo" con prefijo "$", botón "Aplicar" y ayuda "Valor publicado en datos abiertos; no es el precio unitario del ítem."
- Sección "UNSPSC": campo para el código, lista de sugerencias "{código} ({n} contratos)" y lista de códigos agregados con botón "Quitar".
- Etiquetas sobre el listado: "Fechas: …", "Valor: …", "UNSPSC: …" y la nota informativa de TVEC cuando aplica.
- En tablet y móvil, las secciones están dentro del panel plegable "Filtros ({n})".

### Sistemas Externos (Si aplica)

No consulta sistemas externos en tiempo real. Usa `fecha_de_firma`, `valor_del_contrato` y `codigo_de_categoria_principal` de SECOP II (`jbjy-vk9h`) y la fecha y el valor total de las órdenes TVEC (`rgxm-mmea`), ya ingeridos.

---

## Contexto y Referencias

**Épica origen:** [Exploración y Ficha del Contrato](../../../epicas.md#épica-006-exploración-y-ficha-del-contrato)

**Exclusiones de la Épica:**
- NO incluye fichas de entidad ni de proveedor (candidatas, ÉPICA-009).
- NO incluye dashboards nacionales ni de otras categorías.
- NO incluye exploración pública anónima.
- NO incluye la consulta conversacional (chatbot).

**Historias relacionadas:** HU-069 (vista de exploración), HU-070, HU-072 (otros filtros), HU-075 (filtros en la lista de señales)

---

## Supuestos

> Elementos inferidos por la IA que NO estaban explícitos en el PRD o la Épica. Todos los supuestos han sido resueltos: convertidos en reglas de negocio explícitas o eliminados mediante reformulación. Si aparece algún supuesto no resuelto, esta HU NO está lista para desarrollo.

- **Resuelto (RN-04):** el rango de valor se aplica al valor del contrato u orden publicado en datos abiertos, presentado como dato de referencia y nunca como precio unitario.
- **Resuelto (RN-06, RN-08):** el filtro UNSPSC usa la categoría principal de SECOP II; las órdenes TVEC, que no publican UNSPSC, quedan fuera cuando el filtro está activo.
- **Resuelto (RN-03):** rangos de fechas predefinidos (30 días, 6 meses, 12 meses, año en curso) recalculados cada día.

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
