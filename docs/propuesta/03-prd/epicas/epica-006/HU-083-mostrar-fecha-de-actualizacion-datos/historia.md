# Historia #083: Mostrar la fecha de actualización de los datos en la exploración y en la ficha

**Estado:** Borrador (PO)  
**Release:** Release MVP  
**Épica:** [Exploración y Ficha del Contrato](../../../epicas.md#épica-006-exploración-y-ficha-del-contrato)  
**Feature:** Seguimiento del Procesamiento y Frescura de Datos  
**Prioridad:** Crítica  
**FRs relacionados:** FR-076

Escrita por el flujo generar-historias-usuario (Método Ceiba) — MVP propio, no comercial

---

## Historia de Usuario

**Como** Analista que investiga contratación pública,  
**Quiero** ver en la exploración, en la lista de señales y en la ficha del contrato la fecha de corte de los datos de cada fuente y la fecha del último cálculo de comparaciones,  
**Para** saber qué tan actual es la información que estoy usando y citarla correctamente cuando lleve un caso a revisión.

## Descripción

Esta HU agrega la indicación de **fecha de actualización de los datos** en tres vistas: "Exploración" (HU-069), "Señales" (HU-074) y la ficha del contrato (HU-076).

- En las vistas de listado se muestra la fecha de corte vigente de cada fuente pública (SECOP II y TVEC) y la fecha del último cálculo de comparaciones y señales.
- En la ficha se muestran la fecha de corte del registro (la fecha de corte de la fuente con la que se cargó o actualizó por última vez), la fecha de última actualización publicada por la fuente para ese registro y la fecha del último cálculo de comparación de sus ítems.

Las fechas provienen de los registros de ingesta y de cálculo de la plataforma; esta HU no ejecuta cargas ni recálculos.

---

## Criterios de Aceptación

### Escenario 1: Fecha de actualización en la exploración (happy path)

- **Dado** que existen cargas exitosas de SECOP II y TVEC y un cálculo de comparaciones
- **Cuando** el Analista abre "Exploración"
- **Entonces** sobre el listado ve "Datos actualizados al: SECOP II {fecha de corte} · TVEC {fecha de corte} · Comparaciones calculadas el {fecha}"

### Escenario 2: Fecha de actualización en la lista de señales

- **Dado** que el Analista abre "Señales"
- **Cuando** la lista se carga
- **Entonces** ve la misma indicación del Escenario 1 sobre la lista

### Escenario 3: Fecha de actualización en la ficha de un contrato SECOP II

- **Dado** que el Analista abre la ficha de un contrato SECOP II
- **Cuando** se carga la ficha
- **Entonces** en el encabezado ve "Fecha de corte de los datos: {fecha}", "Última actualización en la fuente: {fecha}" y "Comparación calculada el: {fecha}"

### Escenario 4: Ficha de una orden TVEC

- **Dado** que el Analista abre la ficha de una orden TVEC
- **Cuando** se carga la ficha
- **Entonces** ve "Fecha de corte de los datos: {fecha}" y "Comparación calculada el: {fecha}"; si la fuente no publica fecha de última actualización del registro, esa línea no se muestra

### Escenario 5: Fuente sin carga exitosa

- **Dado** que una fuente todavía no tiene ninguna carga exitosa
- **Cuando** se muestra la indicación en un listado
- **Entonces** para esa fuente aparece "{Fuente}: sin datos cargados todavía"

### Escenario 6: Comparaciones aún no calculadas

- **Dado** que todavía no se ha ejecutado ningún cálculo de comparaciones (o, en la ficha, ningún ítem del registro tiene comparación)
- **Cuando** se muestra la indicación
- **Entonces** aparece "Comparaciones: pendientes de cálculo" en los listados o "Comparación: pendiente" en la ficha

### Escenario 7: Última carga fallida

- **Dado** que la última ejecución de carga de una fuente falló
- **Cuando** se muestra la indicación
- **Entonces** se muestra la fecha de corte de la última carga exitosa, sin cambios, de modo que la fecha mostrada siempre corresponde a datos efectivamente disponibles

### Escenario 8: Ayuda sobre las fechas

- **Dado** que el Analista activa el ícono de información junto a la indicación
- **Cuando** se abre la ayuda
- **Entonces** ve: "Fecha de corte: fecha hasta la cual se consultaron los datos publicados por la fuente. Última actualización en la fuente: fecha en que la fuente modificó el registro por última vez. Comparación calculada: fecha del último cálculo de benchmarks y señales."

---

## Información Recopilada

### Usuario y Contexto

- **Tipo de usuario:** Analista que investiga contratación pública; el Administrador también ve la indicación.
- **Permisos requeridos:** Sesión iniciada con rol Analista o Administrador.
- **Valor de negocio:** La fecha de corte es parte de la trazabilidad de cualquier dato o señal; sin ella el analista no puede saber si la información está vigente ni citarla.

### Reglas de Negocio

- **RN-01 Fecha de corte por fuente (listados):** la fecha de corte de la última carga **exitosa** de cada fuente pública (SECOP II, TVEC), según el registro de ejecuciones de ingesta. Las cargas fallidas no la modifican.
- **RN-02 Fecha de corte del registro (ficha):** la fecha de corte con la que el registro se cargó o actualizó por última vez.
- **RN-03 Última actualización en la fuente (ficha):** SECOP II: campo `ultima_actualizacion` del contrato publicado; TVEC: el campo equivalente si la fuente lo publica; si no, la línea no se muestra.
- **RN-04 Fecha de cálculo de comparaciones:** listados: fecha y hora de finalización del último cálculo de comparaciones y señales; ficha: la fecha más reciente de cálculo entre los ítems del registro.
- **RN-05 Formatos:** fechas de corte y de última actualización en `DD/MM/AAAA`; fecha de cálculo en `DD/MM/AAAA HH:mm`; todas en hora de Colombia (UTC−5).
- **RN-06 Nulos:** fuente sin carga exitosa → "{Fuente}: sin datos cargados todavía"; sin cálculo → "pendientes de cálculo" / "pendiente"; registro sin `ultima_actualizacion` → no se muestra la línea.
- **RN-07 Ubicación:** en "Exploración" y "Señales", encima del listado y visible sin desplazamiento en escritorio desde 1366 × 768 px; en la ficha, en el encabezado. En móvil desde 360 px se muestra debajo del título en forma compacta, con la ayuda accesible.
- **RN-08 Actualización:** la indicación se obtiene con cada carga de la vista; no se actualiza mientras el Analista permanece en la vista.
- **RN-09 Rendimiento y accesibilidad (valores iniciales de diseño):** no agrega más de lo permitido por el objetivo de ≤ 3 segundos (p95) de las vistas; WCAG 2.1 AA: el texto es legible por lectores de pantalla, el ícono de ayuda tiene etiqueta "Información sobre las fechas" y se abre con teclado.

### Interfaz

- Línea "Datos actualizados al: SECOP II {fecha} · TVEC {fecha} · Comparaciones calculadas el {fecha y hora}" con ícono de ayuda, en "Exploración" y "Señales".
- Bloque en el encabezado de la ficha con "Fecha de corte de los datos", "Última actualización en la fuente" y "Comparación calculada el".
- Ventana de ayuda con el texto del Escenario 8.

### Sistemas Externos (Si aplica)

No consulta sistemas externos en tiempo real. Usa el registro de ejecuciones de ingesta de SECOP II (`jbjy-vk9h`) y TVEC, la fecha de corte de cada registro, el campo `ultima_actualizacion` publicado por SECOP II y el registro de cálculos de comparación de la plataforma.

---

## Contexto y Referencias

**Épica origen:** [Exploración y Ficha del Contrato](../../../epicas.md#épica-006-exploración-y-ficha-del-contrato)

**Exclusiones de la Épica:**
- NO incluye fichas de entidad ni de proveedor (candidatas, ÉPICA-009).
- NO incluye dashboards nacionales ni de otras categorías.
- NO incluye exploración pública anónima.
- NO incluye la consulta conversacional (chatbot).

**Historias relacionadas:** HU-069 (exploración), HU-074 (lista de señales), HU-076 (ficha del contrato)

---

## Supuestos

> Elementos inferidos por la IA que NO estaban explícitos en el PRD o la Épica. Todos los supuestos han sido resueltos: convertidos en reglas de negocio explícitas o eliminados mediante reformulación. Si aparece algún supuesto no resuelto, esta HU NO está lista para desarrollo.

- **Resuelto (RN-01 a RN-04):** la "fecha de actualización" se compone de la fecha de corte por fuente (de la última carga exitosa), la última actualización publicada por la fuente para el registro y la fecha del último cálculo de comparaciones.
- **Resuelto (RN-01, Escenario 7):** una carga fallida no cambia la fecha mostrada.

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
