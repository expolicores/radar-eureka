# Historia #011: Clasificar contratos SECOP II y soportar contratos mixtos a nivel de ítem

**Estado:** Borrador (PO)  
**Release:** Release MVP  
**Épica:** [Universo de Compras Públicas de Televisores](../../../epicas.md#épica-001-universo-de-compras-públicas-de-televisores)  
**Feature:** Clasificar Ítems de Televisor  
**Prioridad:** Crítica  
**FRs relacionados:** FR-013, FR-015, FR-017

Escrita por el flujo generar-historias-usuario (Método Ceiba) — MVP propio, no comercial

---

## Historia de Usuario

**Como** Administrador del MVP,  
**Quiero** que cada contrato SECOP II candidato tenga una clasificación preliminar a partir de su texto y luego una clasificación confirmada a partir de sus ítems, de modo que en un contrato con varios bienes solo los televisores entren al análisis,  
**Para** descartar temprano los contratos que claramente no son compras de televisores y, en los contratos mixtos, analizar solo los ítems de televisor sin mezclar otros bienes.

## Descripción

En SECOP II los datos abiertos no traen ítems: el contrato se conoce primero por su objeto y descripción, y sus ítems aparecen después (por extracción documental o registro del Administrador). Por eso la clasificación del contrato tiene dos niveles:

1. **Preliminar (contrato):** reglas sobre el texto del contrato candidato. Descarta comodatos y contratos de solo servicios, envía a revisión los casos dudosos (CCTV, procesos por lotes, contratos que solo coinciden por UNSPSC) y deja como "Incluido preliminar" los que mencionan televisores.
2. **Confirmada por ítem:** cuando el contrato tiene ítems clasificados (HU-010), su resultado se deriva de ellos. Un contrato es mixto cuando combina televisores con otros bienes; solo sus ítems de televisor incluidos entran al análisis.

Cada ítem tiene un indicador `en_analisis` que dice si entra al análisis de precios. Es la regla única que usan las demás épicas.

---

## Criterios de Aceptación

### Escenario 1: Contrato con mención de televisor (preliminar)

- **Dado** que un contrato candidato tiene objeto "Adquisición de televisores 65 pulgadas para aulas" y aún no tiene ítems
- **Cuando** se ejecuta la clasificación de contratos
- **Entonces** queda `resultado = Incluido`, `nivel = Preliminar (contrato)`, criterio "C5 — El contrato menciona televisores; pendiente de confirmación por ítem", método "Regla", y `apto_gestion_documental = sí`

### Escenario 2: Comodato o arrendamiento

- **Dado** que un contrato candidato tiene objeto "Contrato de comodato de televisores para la sede"
- **Cuando** se clasifica
- **Entonces** queda "Excluido" con "C1 — El contrato no es una compra (comodato, arrendamiento o préstamo)" y `apto_gestion_documental = no`

### Escenario 3: Contrato de solo servicios

- **Dado** que un contrato candidato con UNSPSC `52161505` tiene objeto "Mantenimiento preventivo y correctivo de televisores y equipos audiovisuales"
- **Cuando** se clasifica
- **Entonces** queda "Excluido" con "C2 — Contrato de servicios, sin compra de bienes", porque contiene un término de servicio y ningún término de adquisición

### Escenario 4: Servicio con adquisición

- **Dado** que un contrato tiene objeto "Suministro e instalación de televisores para el hospital"
- **Cuando** se clasifica
- **Entonces** C2 no aplica (hay término de adquisición "suministro") y queda "Incluido" preliminar por C5

### Escenario 5: Posible CCTV

- **Dado** que un contrato tiene objeto "Adquisición de cámaras y televisores para el sistema de circuito cerrado"
- **Cuando** se clasifica
- **Entonces** queda "Requiere revisión" con "C3 — El contrato menciona televisores junto con CCTV o videovigilancia"

### Escenario 6: Proceso por lotes

- **Dado** que un contrato tiene objeto "Lote 2 equipos de cómputo" y descripción del proceso "Adquisición de equipos tecnológicos por lotes: lote 1 televisores, lote 2 equipos de cómputo"
- **Cuando** se clasifica
- **Entonces** queda "Requiere revisión" con "C4 — Proceso por lotes: verificar que el lote del contrato corresponda al televisor", porque el término de televisor solo aparece en la descripción del proceso

### Escenario 7: Solo coincide el UNSPSC

- **Dado** que un contrato candidato tiene UNSPSC `52161505` y objeto "Dotación de equipos para auditorio" sin términos de televisor ni de productos excluidos
- **Cuando** se clasifica
- **Entonces** queda "Requiere revisión" con "C7 — Solo coincide el código UNSPSC; el texto no menciona televisores"

### Escenario 8: Solo UNSPSC con producto excluido

- **Dado** que un contrato candidato tiene UNSPSC `52161505` y objeto "Suministro de videowall para centro de control"
- **Cuando** se clasifica
- **Entonces** queda "Excluido" con "C6 — Producto fuera de categoría sin mención de televisor"

### Escenario 9: Contrato mixto confirmado por ítems

- **Dado** que el contrato "Compra de 52 equipos de cómputo y 1 smart tv" tiene 3 ítems clasificados: "Computador de escritorio" (Excluido R2), "Impresora láser" (Excluido R2) y "Smart TV 50 pulgadas" (Incluido R10)
- **Cuando** cambia la clasificación de cualquiera de sus ítems
- **Entonces** el contrato queda "Incluido", `nivel = Confirmado por ítem`, criterio "C8 — Al menos un ítem es un televisor dentro del límite de categoría", `contrato_mixto = sí`, `items_tv_incluidos = 1`, `items_excluidos = 2`, y solo el ítem "Smart TV 50 pulgadas" queda `en_analisis = sí`

### Escenario 10: Ningún ítem es televisor

- **Dado** que todos los ítems clasificados de un contrato son "Excluido"
- **Cuando** se deriva la clasificación del contrato
- **Entonces** el contrato queda "Excluido", nivel "Confirmado por ítem", criterio "C9 — Ningún ítem del contrato es un televisor dentro del límite de categoría", y ninguno de sus ítems queda en análisis

### Escenario 11: Ítems pendientes de revisión sin ningún incluido

- **Dado** que un contrato tiene ítems en "Requiere revisión" y ninguno "Incluido"
- **Cuando** se deriva la clasificación
- **Entonces** el contrato queda "Requiere revisión", nivel "Confirmado por ítem", criterio "C10 — El contrato tiene ítems pendientes de revisión y ningún televisor confirmado"

### Escenario 12: Clasificación manual del contrato prevalece

- **Dado** que el contrato tiene una clasificación vigente con método "Manual" "Excluido"
- **Cuando** sus ítems cambian de clasificación
- **Entonces** el contrato conserva su clasificación manual y ninguno de sus ítems queda `en_analisis`, aunque estén "Incluido"

### Escenario 13: Ítems TVEC

- **Dado** que un ítem TVEC tiene clasificación vigente "Incluido"
- **Cuando** se calcula su indicador de análisis
- **Entonces** queda `en_analisis = sí` (los ítems TVEC no tienen contrato SECOP II); con "Excluido" o "Requiere revisión" queda `en_analisis = no`

### Escenario 14: Sin contratos pendientes

- **Dado** que no hay contratos candidatos en "Pendiente de clasificación"
- **Cuando** se ejecuta la clasificación de contratos
- **Entonces** termina sin cambios y registra "No hay contratos SECOP II pendientes de clasificación."

---

## Información Recopilada

### Usuario y Contexto

- **Tipo de usuario:** Administrador del MVP (PO); el sistema ejecuta la clasificación automáticamente.
- **Permisos requeridos:** rol Administrador para ejecución manual y cambio de listas.
- **Valor de negocio:** D1 encontró contratos mixtos ("52 equipos de cómputo + 1 televisor", "aires acondicionados y televisores"); analizar por contrato contaminaría las comparaciones. El descarte preliminar reduce el costo de obtener documentos de contratos que no son compras de televisores.

### Reglas de Negocio

- **RN-01 Contratos a clasificar:** contratos SECOP II con candidatura "Candidato" en "Pendiente de clasificación" (preliminar) y contratos con al menos un ítem clasificado (derivación).
- **RN-02 Texto evaluado:** `objeto` y `descripcion_proceso` normalizados (minúsculas, sin tildes, caracteres no alfanuméricos → espacio, espacios colapsados); campos nulos como texto vacío. Coincidencia por palabras completas; la última palabra del término admite sufijos "s" o "es".
- **RN-03 Listas (configurables y versionadas junto con las reglas de ítem; valores iniciales):** T = lista vigente de candidatura ("televisor", "smart tv", "tv"); NC = comodato, arrendamiento, alquiler, prestamo; SV = mantenimiento, reparacion, servicio, servicios, instalacion, montaje, soporte tecnico, diagnostico; AD (adquisición) = adquisicion, compra, compraventa, suministro, dotacion, adquirir; CC = cctv, circuito cerrado, videovigilancia, camaras de seguridad; PE = la lista de productos excluidos de la clasificación de ítems (videowall, video wall, pantalla modular, modulo led, senalizacion digital, digital signage, cartelera digital, monitor, cctv, circuito cerrado, videovigilancia, proyector, video beam, videobeam, pantalla interactiva, tablero interactivo, tactil, touch, inflable, solucion audiovisual, sistema audiovisual). Términos de 2 a 50 caracteres.
- **RN-04 Reglas preliminares en orden (la primera que se cumple decide):**

  | Código | Condición (sobre objeto + descripción) | Resultado |
  |---|---|---|
  | C1 | Contiene algún término NC | Excluido — El contrato no es una compra (comodato, arrendamiento o préstamo) |
  | C2 | Contiene algún término SV y ningún término AD | Excluido — Contrato de servicios, sin compra de bienes |
  | C3 | Contiene algún término T y algún término CC | Requiere revisión — El contrato menciona televisores junto con CCTV o videovigilancia |
  | C4 | Algún término T aparece en `descripcion_proceso`, ninguno en `objeto`, y el texto contiene la palabra "lote" o "lotes" | Requiere revisión — Proceso por lotes: verificar que el lote del contrato corresponda al televisor |
  | C5 | Contiene algún término T | Incluido (preliminar) — El contrato menciona televisores; pendiente de confirmación por ítem |
  | C6 | Contiene algún término PE | Excluido — Producto fuera de categoría sin mención de televisor |
  | C7 | Ninguna anterior | Requiere revisión — Solo coincide el código UNSPSC; el texto no menciona televisores |

- **RN-05 Derivación por ítems (cuando el contrato tiene al menos un ítem con clasificación vigente):** se ignoran los ítems sin clasificar.
  - ≥ 1 ítem "Incluido" → contrato "Incluido", criterio "C8 — Al menos un ítem es un televisor dentro del límite de categoría".
  - Todos los ítems clasificados "Excluido" → contrato "Excluido", criterio "C9 — Ningún ítem del contrato es un televisor dentro del límite de categoría".
  - En otro caso → "Requiere revisión", criterio "C10 — El contrato tiene ítems pendientes de revisión y ningún televisor confirmado".
  La derivación reemplaza a la preliminar (nivel "Confirmado por ítem") y se recalcula cada vez que cambia la clasificación de un ítem del contrato.
- **RN-06 Contrato mixto:** `contrato_mixto = sí` si tiene al menos un ítem con término de televisor y al menos un ítem "Excluido" por R2 (no es televisor). Se guardan `items_tv_incluidos`, `items_excluidos` e `items_en_revision`.
- **RN-07 Indicador `en_analisis` del ítem:** ítem SECOP II → sí solo si su clasificación vigente es "Incluido" **y** la clasificación vigente del contrato no es "Excluido". Ítem TVEC → sí solo si su clasificación vigente es "Incluido". Se recalcula ante cualquier cambio de clasificación del ítem o del contrato.
- **RN-08 `apto_gestion_documental` del contrato:** sí si la clasificación vigente del contrato es "Incluido" o "Requiere revisión"; no si es "Excluido". Contratos sin clasificar → no.
- **RN-09 Precedencia manual:** una clasificación vigente del contrato con método "Manual" no se reemplaza por la preliminar ni por la derivada; se registra el resultado derivado como información (`resultado_derivado`) sin cambiar la vigente.
- **RN-10 Registro:** cada clasificación del contrato agrega un evento con resultado, nivel, código y texto del criterio, términos coincidentes, método ("Regla" o "Derivado de ítems"), versión de reglas y fecha y hora. Los eventos no se modifican ni se eliminan. Solo se agrega evento si cambia el resultado, el nivel o el criterio.
- **RN-11 Disparo:** preliminar automática tras la marcación de candidatos; derivación automática ante cada cambio de clasificación de ítems; manual por comando ("clasificar contratos pendientes", "reclasificar todos los contratos").
- **RN-12 Resumen:** "Clasificación de contratos SECOP II: {n} evaluados. Incluidos: {n} (preliminar: {n}; confirmados: {n}). Excluidos: {n}. Requiere revisión: {n}. Mixtos: {n}. Omitidos por clasificación manual: {n}."

### Interfaz

No requiere interfaz gráfica. Comandos indicados en RN-11; resumen en consola o log (RN-12).

### Sistemas Externos (Si aplica)

No aplica.

---

## Contexto y Referencias

**Épica origen:** [Universo de Compras Públicas de Televisores](../../../epicas.md#épica-001-universo-de-compras-públicas-de-televisores)

**Exclusiones de la Épica:**
- NO incluye SECOP I (Adenda 1).
- NO incluye categorías distintas a televisores.
- NO incluye el dataset de Procesos (`p6dx-8zbt`) como unidad base.
- NO incluye adiciones, modificaciones ni ejecución del contrato (ciclo de vida).
- NO incluye scraping del portal SECOP.

**Historias relacionadas:** HU-008 (candidatos SECOP II), HU-010 (clasificación de ítems), HU-012 (sugerencia con IA), HU-013 (corrección manual).

---

## Supuestos

> Elementos inferidos por la IA que NO estaban explícitos en el PRD o la Épica. Todos los supuestos han sido resueltos: convertidos en reglas de negocio explícitas o eliminados mediante reformulación. Si aparece algún supuesto no resuelto, esta HU NO está lista para desarrollo.

- En SECOP II los ítems no existen en datos abiertos al momento de la ingesta → resuelto con dos niveles de clasificación (RN-04, RN-05).
- Un contrato con servicio y adquisición (ej. "suministro e instalación") no es de solo servicios → resuelto con la lista AD en C2.
- La regla única para saber qué entra al análisis → resuelto con el indicador `en_analisis` (RN-07).
- Los contratos excluidos no requieren documentos → resuelto con `apto_gestion_documental` (RN-08).

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
| 2026-10-02 | 1.0 | Historia generada desde Épica ÉPICA-001 | Juan Camilo (PO) |

---

> **Método Ceiba estimar hus** v6.1.95 | Modelo: claude-opus-5-5 | Usuario: Juan Camilo | Fecha: 2026-10-05
