# Historia #081: Ver el estado de procesamiento del contrato en la ficha

**Estado:** Borrador (PO)  
**Release:** Release MVP  
**Épica:** [Exploración y Ficha del Contrato](../../../epicas.md#épica-006-exploración-y-ficha-del-contrato)  
**Feature:** Seguimiento del Procesamiento y Frescura de Datos  
**Prioridad:** Crítica  
**FRs relacionados:** FR-075

Escrita por el flujo generar-historias-usuario (Método Ceiba) — MVP propio, no comercial

---

## Historia de Usuario

**Como** Analista que investiga contratación pública,  
**Quiero** ver en la ficha en qué etapa de procesamiento está el contrato (identificado, documentos obtenidos, extraído, revisado, comparado) y el estado de cada etapa,  
**Para** saber si la información que veo está completa o todavía en proceso, y no sacar conclusiones sobre un contrato a medio procesar.

## Descripción

Esta HU construye la sección **"Estado de procesamiento"** de la ficha del contrato (HU-076): una línea de etapas con las cinco etapas del flujo y el estado de cada una (Completada, En curso o pendiente, Incompleta, No aplica), con la fecha y un detalle breve. Además muestra un resumen del estado general en el encabezado de la ficha.

El estado se calcula a partir de los resultados ya registrados por los procesos de ingesta, clasificación, obtención de documentos, extracción, revisión humana y comparación; esta HU no ejecuta ni relanza ninguno de esos procesos. Los motivos de información insuficiente se detallan en HU-082.

---

## Criterios de Aceptación

### Escenario 1: Ver las etapas de un contrato completamente procesado (happy path)

- **Dado** que un contrato SECOP II pasó por todas las etapas
- **Cuando** el Analista abre la sección "Estado de procesamiento"
- **Entonces** ve las etapas "Identificado", "Documentos obtenidos", "Extraído", "Revisado" y "Comparado", cada una con el estado "Completada", su fecha y su detalle, y el encabezado de la ficha muestra "Estado: Comparado"

### Escenario 2: Contrato en una etapa intermedia

- **Dado** que un contrato tiene documentos obtenidos pero la extracción no ha terminado
- **Cuando** se muestra la sección
- **Entonces** "Identificado" y "Documentos obtenidos" aparecen "Completada", "Extraído" aparece "En curso o pendiente", "Revisado" y "Comparado" aparecen "En curso o pendiente", y el encabezado muestra "Estado: Documentos obtenidos"

### Escenario 3: Ítems pendientes de revisión humana

- **Dado** que la extracción terminó y hay ítems en la cola de revisión humana
- **Cuando** se muestra la etapa "Revisado"
- **Entonces** aparece "En curso o pendiente" con el detalle "{n} ítems pendientes de revisión humana"

### Escenario 4: Proceso sin documentos publicados

- **Dado** que la fuente no publicó documentos para el proceso
- **Cuando** se muestra la etapa "Documentos obtenidos"
- **Entonces** aparece "Incompleta" con el detalle "La fuente no ha publicado documentos para este proceso." y las etapas "Extraído", "Revisado" y "Comparado" aparecen "No aplica", con el enlace "Ver motivos" a la sección de motivos de información insuficiente

### Escenario 5: Extracción automática desactivada

- **Dado** que la extracción con IA está desactivada en la plataforma y el contrato tiene documentos sin extraer
- **Cuando** se muestra la etapa "Extraído"
- **Entonces** aparece "En curso o pendiente" con el detalle "La extracción automática de documentos está desactivada temporalmente; los datos ya extraídos y las comparaciones siguen disponibles."

### Escenario 6: Error en una etapa

- **Dado** que la descarga o la extracción de los documentos priorizados terminó con error en todos ellos
- **Cuando** se muestra la etapa correspondiente
- **Entonces** aparece "Incompleta" con el detalle "No se pudieron {obtener | leer} los documentos priorizados. El equipo de operación lo revisará."

### Escenario 7: Orden de compra TVEC

- **Dado** que la ficha es de una orden TVEC
- **Cuando** se muestra la sección
- **Entonces** "Identificado" aparece "Completada", "Documentos obtenidos" y "Extraído" aparecen "No aplica" con el detalle "Datos estructurados publicados por la TVEC", y "Revisado" y "Comparado" se calculan igual que para SECOP II

### Escenario 8: Comparación incompleta

- **Dado** que algunos ítems con precio unitario tienen comparación calculada y otros no
- **Cuando** se muestra la etapa "Comparado"
- **Entonces** aparece "En curso o pendiente" con el detalle "{a} de {b} ítems con precio unitario comparados"

### Escenario 9: Ningún ítem con precio unitario

- **Dado** que la extracción terminó pero ningún ítem tiene precio unitario
- **Cuando** se muestra la etapa "Comparado"
- **Entonces** aparece "No aplica" con el detalle "Ningún ítem tiene precio unitario para comparar." y el enlace "Ver motivos"

### Escenario 10: Clasificación en revisión

- **Dado** que el contrato es candidato y su clasificación aún no concluyó
- **Cuando** se muestra la etapa "Identificado"
- **Entonces** aparece "Completada" con el detalle "Candidato identificado el {fecha}; clasificación de ítems en revisión"

---

## Información Recopilada

### Usuario y Contexto

- **Tipo de usuario:** Analista que investiga contratación pública; el Administrador también puede consultar la sección.
- **Permisos requeridos:** Sesión iniciada con rol Analista o Administrador.
- **Valor de negocio:** Evita interpretar como "sin señal" un contrato que simplemente no ha terminado de procesarse, y muestra el límite que impone la fuente.

### Reglas de Negocio

- **RN-01 Etapas y orden:** 1) Identificado, 2) Documentos obtenidos, 3) Extraído, 4) Revisado, 5) Comparado.
- **RN-02 Estados posibles por etapa:** "Completada", "En curso o pendiente", "Incompleta" (terminó sin el resultado necesario, con motivo), "No aplica".
- **RN-03 Identificado:** siempre "Completada" para registros visibles del universo; fecha = fecha en que el registro se marcó como candidato. Detalle: "{n} ítems de televisor incluidos" o el texto del Escenario 10.
- **RN-04 Documentos obtenidos (SECOP II):** "Completada" si al menos un documento priorizado fue obtenido; "En curso o pendiente" si la lista de documentos aún no se ha consultado o hay documentos priorizados por descargar y ninguno descargado; "Incompleta" si la fuente no publicó documentos o si falló la obtención de todos los priorizados. Fecha = última obtención. Detalle: "{n} documentos priorizados de {m} publicados".
- **RN-05 Extraído (SECOP II):** "Completada" si terminó la extracción de todos los documentos priorizados obtenidos (con o sin datos encontrados); "En curso o pendiente" si queda al menos uno sin extraer (incluido el caso de extracción desactivada, Escenario 5); "Incompleta" si la extracción falló en todos; "No aplica" si la etapa anterior es "Incompleta". Fecha = última extracción.
- **RN-06 Revisado:** "Completada" si ningún ítem del contrato está pendiente de revisión humana (ítems aceptados automáticamente o validados); "En curso o pendiente" con el número de ítems pendientes; "En curso o pendiente" sin número mientras la extracción no ha terminado; "No aplica" si la etapa "Extraído" quedó "Incompleta" o "No aplica" (SECOP II), o si la extracción terminó sin ningún ítem.
- **RN-07 Comparado:** "Completada" si todos los ítems "incluido" con precio unitario tienen resultado de comparación calculado (aunque el Benchmark 2 resulte "no disponible"); "En curso o pendiente" con "{a} de {b}" si faltan; "En curso o pendiente" sin conteo mientras la extracción no ha terminado; "No aplica" si la etapa anterior aplicable quedó "Incompleta" o si, terminada la extracción, ningún ítem tiene precio unitario. Fecha = último cálculo.
- **RN-08 TVEC:** "Documentos obtenidos" y "Extraído" = "No aplica" con "Datos estructurados publicados por la TVEC".
- **RN-09 Estado general del encabezado:** nombre de la última etapa "Completada" de forma consecutiva desde la etapa 1, saltando las "No aplica" de TVEC. Si alguna etapa está "Incompleta", el encabezado agrega "— con información insuficiente" y el enlace "Ver motivos".
- **RN-10 Fechas y formato:** `DD/MM/AAAA HH:mm` en hora de Colombia; etapa sin fecha registrada → sin fecha (no se muestra "Sin dato").
- **RN-11 Cobertura:** la sección se muestra para el 100 % de las fichas de registros visibles del universo.
- **RN-12 Lenguaje:** ningún texto usa "sobreprecio", "corrupción", "fraude" ni "hallazgo fiscal".
- **RN-13 Rendimiento y accesibilidad (valores iniciales de diseño):** carga dentro del objetivo de la ficha de ≤ 3 segundos (p95) con 20 usuarios concurrentes; WCAG 2.1 AA: cada estado se comunica con texto e ícono (no solo color) y la línea de etapas se lee como lista ordenada; en móvil desde 360 px la línea de etapas se muestra en vertical.

### Interfaz

- Resumen en el encabezado de la ficha: "Estado: {etapa}" (+ "— con información insuficiente" y "Ver motivos" cuando aplique).
- Sección "Estado de procesamiento": línea de cinco etapas (horizontal en escritorio, vertical en móvil), cada una con nombre, estado (texto + ícono), fecha y detalle.
- Enlace "Ver motivos" hacia la sección de motivos de información insuficiente.

### Sistemas Externos (Si aplica)

No consulta sistemas externos. Usa los registros de ingesta, clasificación, documentos, extracción, revisión humana y comparación ya almacenados por la plataforma, y el indicador de configuración de extracción con IA activada/desactivada.

---

## Contexto y Referencias

**Épica origen:** [Exploración y Ficha del Contrato](../../../epicas.md#épica-006-exploración-y-ficha-del-contrato)

**Exclusiones de la Épica:**
- NO incluye fichas de entidad ni de proveedor (candidatas, ÉPICA-009).
- NO incluye dashboards nacionales ni de otras categorías.
- NO incluye exploración pública anónima.
- NO incluye la consulta conversacional (chatbot).

**Historias relacionadas:** HU-076 (estructura de la ficha), HU-080 (documentos), HU-082 (motivos de información insuficiente)

---

## Supuestos

> Elementos inferidos por la IA que NO estaban explícitos en el PRD o la Épica. Todos los supuestos han sido resueltos: convertidos en reglas de negocio explícitas o eliminados mediante reformulación. Si aparece algún supuesto no resuelto, esta HU NO está lista para desarrollo.

- **Resuelto (RN-02 a RN-07):** cada etapa tiene cuatro estados posibles con reglas explícitas de cálculo.
- **Resuelto (RN-08):** para las órdenes TVEC, "Documentos obtenidos" y "Extraído" no aplican.
- **Resuelto (RN-09):** el estado general es la última etapa completada consecutivamente.

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
