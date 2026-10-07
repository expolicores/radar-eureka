# Historia #026: Aplicar el umbral configurable de aceptación automática y dirigir a revisión los datos dudosos

**Estado:** Borrador (PO)  
**Release:** Release MVP  
**Épica:** [De Documentos a Datos Comparables](../../../epicas.md#épica-002-de-documentos-a-datos-comparables)  
**Feature:** Controlar la Calidad de la Extracción  
**Prioridad:** Crítica  
**FRs relacionados:** FR-028

Escrita por el flujo generar-historias-usuario (Método Ceiba) — MVP propio, no comercial

---

## Historia de Usuario

**Como** Administrador que actúa como Revisor en el MVP,  
**Quiero** configurar un umbral de aceptación automática por nivel de confianza, sin un valor fijo mientras no esté calibrado, y que el sistema acepte solo los ítems cuyos datos críticos lo superan y envíe los demás a revisión humana con el motivo,  
**Para** que ningún dato crítico de confianza baja o incierta llegue a una comparación sin revisión, y poder reducir la revisión manual cuando la calibración con la validación D4-4 lo justifique.

## Descripción

La decisión P-15 establece que no se fija un umbral arbitrario (ej. 0,9): el sistema soporta un umbral configurable cuyo valor se calibra con la validación manual D4-4, a partir de la relación observada entre la confianza del extractor y la corrección real. El puntaje de confianza del modelo no es una probabilidad calibrada de acierto.

Esta HU decide el estado de calidad de cada ítem extraído: "aceptado automáticamente" o "pendiente de revisión", con todos sus motivos. Mientras el umbral no tenga valor, ningún ítem se acepta automáticamente. Cuando el Administrador registra un valor (provisional o calibrado), debe indicar la fuente de la calibración. Los datos críticos son marca, modelo/referencia, tamaño, cantidad y precio unitario. Solo los ítems aceptados (automática o manualmente) quedan disponibles para comparación. La configuración puede hacerse sin interfaz gráfica.

---

## Criterios de Aceptación

### Escenario 1: Umbral sin valor (no calibrado)

- **Dado** que el umbral de aceptación no tiene valor y el ítem `CO1.PCCNTR.7654321-01` tiene información suficiente con confianzas de 0,95 en todos sus campos críticos
- **Cuando** se evalúa la aceptación del ítem
- **Entonces** el ítem queda "pendiente de revisión" con el motivo "umbral de aceptación no calibrado" y no está disponible para comparación

### Escenario 2: Ítem que supera el umbral

- **Dado** que el umbral global es 0,80 (estado "calibrado", fuente "D4-4, 228 filas, 2026-10-20") y el ítem tiene cantidad 0,90, precio unitario 0,85, tamaño 0,92, sin marca ni modelo extraídos, sin conflictos ni inconsistencias
- **Cuando** se evalúa la aceptación del ítem
- **Entonces** el ítem queda "aceptado automáticamente" y disponible para comparación; marca y modelo nulos no se evalúan

### Escenario 3: Un dato crítico bajo el umbral

- **Dado** que el umbral global es 0,80 y el precio unitario del ítem tiene confianza 0,60
- **Cuando** se evalúa la aceptación del ítem
- **Entonces** el ítem queda "pendiente de revisión" con el motivo "confianza bajo el umbral: precio unitario (0,60 < 0,80)"

### Escenario 4: Umbral específico por campo

- **Dado** que el umbral global es 0,80 y el umbral específico del precio unitario es 0,90, y el precio unitario tiene confianza 0,85
- **Cuando** se evalúa la aceptación del ítem
- **Entonces** el ítem queda "pendiente de revisión" con "confianza bajo el umbral: precio unitario (0,85 < 0,90)"

### Escenario 5: Precio derivado

- **Dado** que el umbral global es 0,70 y el precio unitario es derivado con confianza 0,68
- **Cuando** se evalúa la aceptación del ítem
- **Entonces** el ítem queda "pendiente de revisión" con "confianza bajo el umbral: precio unitario derivado (0,68 < 0,70)"

### Escenario 6: Otros motivos de revisión

- **Dado** que un ítem supera el umbral en todos sus campos críticos pero tiene "con conflicto entre documentos", o una inconsistencia aritmética, o "lote no determinado", o una "propuesta de reextracción"
- **Cuando** se evalúa la aceptación del ítem
- **Entonces** el ítem queda "pendiente de revisión" con el motivo correspondiente ("conflicto entre documentos", "inconsistencia aritmética", "lote no determinado" o "propuesta de reextracción"); si tiene varios, se registran todos

### Escenario 7: Campo no crítico bajo el umbral

- **Dado** que el umbral global es 0,80 y solo la resolución tiene confianza 0,40
- **Cuando** se evalúa la aceptación del ítem
- **Entonces** el ítem queda "aceptado automáticamente" y la resolución queda marcada "confianza baja"

### Escenario 8: Ítem con información insuficiente

- **Dado** que un ítem está en "información insuficiente" solo con motivos de causa fuente
- **Cuando** se evalúa la aceptación del ítem
- **Entonces** no se acepta ni se envía a revisión: queda "no comparable: información insuficiente"; si alguno de sus motivos es de causa procesamiento, queda "pendiente de revisión" con el motivo "posible pérdida de dato en el procesamiento"

### Escenario 9: Configuración del umbral con fuente obligatoria

- **Dado** que el Administrador registra el umbral global 0,80 con estado "calibrado" y fuente "D4-4, 228 filas, 2026-10-20"
- **Cuando** guarda la configuración
- **Entonces** se guarda con usuario, fecha, valor anterior, valor nuevo, estado y fuente; si omite la fuente, se rechaza con "Indique la fuente de calibración del umbral"; si el valor está fuera de 0,00–1,00 o tiene más de 2 decimales, se rechaza con "El umbral debe ser un número entre 0,00 y 1,00 con máximo 2 decimales"

### Escenario 10: Cambio de umbral reevalúa solo ítems no revisados

- **Dado** que el umbral cambia de "sin valor" a 0,80, y hay 40 ítems "pendiente de revisión" sin revisión humana y 10 ítems ya validados por el Administrador
- **Cuando** se guarda el nuevo umbral
- **Entonces** los 40 ítems se reevalúan con el nuevo umbral y los 10 validados conservan su estado

### Escenario 11: Leyenda de la confianza

- **Dado** que un usuario consulta la confianza de un dato extraído
- **Cuando** se muestra el valor
- **Entonces** se acompaña de la leyenda "Nivel de confianza del extractor; no es una probabilidad de acierto"

---

## Información Recopilada

### Usuario y Contexto

- **Tipo de usuario:** Administrador que actúa como Revisor (en el MVP es el PO). La evaluación es automática.
- **Permisos requeridos:** Solo el Administrador configura el umbral. Analista y Administrador consultan estados y confianzas.
- **Valor de negocio:** Protege la credibilidad de las señales (precisión ≥ 90 %, NFR-CAL-001) y permite medir y reducir la revisión manual con evidencia.

### Reglas de Negocio

- **RN-01 — Datos críticos:** marca, modelo/referencia, tamaño, cantidad y precio unitario (explícito o derivado). Solo se evalúan los que tienen valor; un campo crítico nulo no se evalúa aquí (su ausencia la trata HU-025).
- **RN-02 — Configuración del umbral:** umbral global y, opcionalmente, un umbral específico por cada dato crítico. Valor: número entre 0,00 y 1,00 con máximo 2 decimales, o "sin valor". Estado: "sin valor", "provisional" o "calibrado". Al registrar un valor (provisional o calibrado) es obligatoria la fuente de calibración (texto de 1 a 300 caracteres; ej. "D4-4, 228 filas, 2026-10-20"). Configuración inicial: global "sin valor" y sin umbrales específicos.
- **RN-03 — Mensajes de validación:** valor fuera de rango o con más de 2 decimales → "El umbral debe ser un número entre 0,00 y 1,00 con máximo 2 decimales"; valor sin fuente → "Indique la fuente de calibración del umbral". En ambos casos se conserva la configuración anterior.
- **RN-04 — Umbral aplicable a un campo:** el específico del campo si existe; si no, el global. Si el aplicable es "sin valor", el ítem no puede aceptarse automáticamente.
- **RN-05 — Comparación:** un campo supera el umbral si su confianza es mayor o igual que el umbral aplicable.
- **RN-06 — Decisión por ítem con información suficiente:** "aceptado automáticamente" si se cumplen todas: a) el umbral aplicable de cada dato crítico presente tiene valor; b) cada dato crítico presente supera su umbral; c) el ítem no está "con conflicto entre documentos"; d) no tiene inconsistencias aritméticas abiertas (HU-027); e) no está marcado "lote no determinado"; f) no tiene "propuesta de reextracción". En otro caso, "pendiente de revisión" con todos los motivos aplicables: "umbral de aceptación no calibrado", "confianza bajo el umbral: {campo} ({confianza} < {umbral})" (para precio derivado: "precio unitario derivado"), "conflicto entre documentos", "inconsistencia aritmética", "lote no determinado", "propuesta de reextracción".
- **RN-07 — Ítems con información insuficiente:** quedan "no comparable: información insuficiente" si todos sus motivos son de causa fuente; si alguno es de causa procesamiento, quedan "pendiente de revisión" con el motivo "posible pérdida de dato en el procesamiento".
- **RN-08 — Campos no críticos:** un campo no crítico con confianza menor que el umbral global (si tiene valor) se marca "confianza baja", sin cambiar el estado del ítem.
- **RN-09 — Disponibilidad para comparación:** solo los ítems "aceptado automáticamente" o aceptados por revisión humana (HU-028) quedan disponibles para comparación. "Pendiente de revisión" y "no comparable" no están disponibles.
- **RN-10 — Reevaluación:** al cambiar el umbral se reevalúan los ítems en "aceptado automáticamente", "pendiente de revisión" o "no comparable" que no tengan revisión humana. Los ítems validados, corregidos o rechazados por el Administrador no cambian. Un ítem también se reevalúa cuando cambia alguno de sus datos o motivos.
- **RN-11 — Registro:** cada cambio de configuración guarda usuario, fecha y hora, valores y estados anteriores y nuevos, y fuente. Cada decisión por ítem guarda estado, motivos, umbral y versión de configuración aplicados.
- **RN-12 — Leyenda:** toda presentación de un nivel de confianza se acompaña de "Nivel de confianza del extractor; no es una probabilidad de acierto".
- **RN-13 — Sin IA:** la decisión es determinística y funciona con la extracción con IA desactivada.

### Interfaz

Sin interfaz gráfica obligatoria para la configuración (archivo o tabla de configuración, comando o vista administrativa mínima). Estados, motivos y confianzas quedan disponibles para la revisión humana (HU-028), la cola de revisión y las vistas de otras épicas. Los mensajes de RN-03 se devuelven en la respuesta de la operación.

### Sistemas Externos (Si aplica)

No aplica.

---

## Contexto y Referencias

**Épica origen:** [De Documentos a Datos Comparables](../../../epicas.md#épica-002-de-documentos-a-datos-comparables)

**Exclusiones de la Épica:**
- NO incluye el agente de investigación (siguiente incremento agéntico, post-MVP).
- NO incluye la extracción y comparación de precios de múltiples oferentes (FR-026, pospuesta por D4).
- NO incluye la extracción de cláusulas contractuales, garantías ni condiciones de entrega.
- NO incluye procesar todos los documentos de cada proceso, solo los priorizados.
- NO incluye la extracción de categorías distintas a televisores.
- NO incluye la base de conocimiento RAG sobre los documentos.

**Historias relacionadas:** HU-022 (confianza por campo, conflictos, reextracción), HU-024 (confianza del derivado), HU-025 (información insuficiente), HU-027 (inconsistencias), HU-028 (revisión humana).

---

## Supuestos

> Elementos inferidos por la IA que NO estaban explícitos en el PRD o la Épica. Todos los supuestos han sido resueltos: convertidos en reglas de negocio explícitas o eliminados mediante reformulación. Si aparece algún supuesto no resuelto, esta HU NO está lista para desarrollo.

- Mientras el umbral no tenga valor, ningún ítem se acepta automáticamente (todos van a revisión del PO) → RN-02, RN-04, RN-06.
- Además del umbral global se permiten umbrales específicos por dato crítico → RN-02.
- Al registrar un valor es obligatorio indicar la fuente de calibración → RN-02.
- Los ítems pendientes de revisión no están disponibles para comparación → RN-09.
- Los ítems insuficientes solo por causas de fuente no se envían a revisión → RN-07.

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
| 2026-10-02 | 1.0 | Historia generada desde Épica ÉPICA-002 | Juan Camilo (PO) |

---

> **Método Ceiba estimar hus** v6.1.95 | Modelo: claude-opus-5-5 | Usuario: Juan Camilo | Fecha: 2026-10-05
