# Historia #103: Consultar la cola de revisión humana

**Estado:** Borrador (PO)  
**Release:** Release MVP  
**Épica:** [Operación, Calidad y Medición del MVP](../../../epicas.md#épica-008-operación-calidad-y-medición-del-mvp)  
**Feature:** Gestionar Revisión y Muestra de Validación  
**Prioridad:** Alta  
**FRs relacionados:** FR-090 (relacionados: FR-015, FR-016, FR-028, FR-031, FR-032, FR-063)

Escrita por el flujo generar-historias-usuario (Método Ceiba) — MVP propio, no comercial

---

## Historia de Usuario

**Como** Administrador del MVP que actúa como Revisor (el PO),  
**Quiero** ver en una sola cola, con filtros y orden, todos los elementos que esperan revisión humana (clasificaciones dudosas, extracciones de baja confianza, inconsistencias aritméticas y precios anormalmente bajos),  
**Para** organizar mi sesión semanal de revisión, atender primero lo más antiguo o lo menos confiable y no dejar elementos olvidados.

## Descripción

Varios procesos del MVP dirigen elementos a revisión humana: la clasificación de candidatos que queda en "requiere revisión" (FR-015), los datos extraídos con confianza por debajo del umbral de aceptación o, sin calibración, con confianza baja o incierta (FR-028), las inconsistencias aritméticas (FR-031) y los precios anormalmente bajos, que no generan señal y van a revisión de calidad (FR-063).

Esta HU expone la **consulta unificada de la cola**: resumen con conteos, listado filtrable y ordenable, y exportación. **No incluye** las acciones de resolución (confirmar o corregir clasificación, validar, corregir o rechazar datos extraídos), que pertenecen a FR-016 y FR-032; la cola solo refleja su resultado (el elemento pasa a "Resuelto").

Las inconsistencias y los precios bajos son **señales de revisión de calidad o evidencia, no irregularidades**.

**Implementación sin UI permitida:** la cola puede consultarse con comando, script, consulta a base de datos, archivo CSV o vista administrativa mínima.

---

## Criterios de Aceptación

### Escenario 1: Resumen de la cola

- **Dado** que hay 12 elementos pendientes: 3 de clasificación dudosa, 6 de extracción de baja confianza, 2 de inconsistencia aritmética y 1 de precio anormalmente bajo, y el más antiguo ingresó hace 9 días
- **Cuando** el Administrador consulta el resumen de la cola
- **Entonces** obtiene total pendiente 12, el conteo por tipo (3, 6, 2, 1) y "elemento pendiente más antiguo: 9 días"

### Escenario 2: Listado por defecto

- **Dado** que existen elementos pendientes y resueltos
- **Cuando** el Administrador consulta la cola sin filtros
- **Entonces** obtiene solo los elementos en estado Pendiente, ordenados del más antiguo al más reciente por fecha de ingreso, en páginas de 50, cada uno con los campos de RN-03

### Escenario 3: Filtrar por tipo y fuente

- **Dado** que hay elementos de SECOP II y de TVEC
- **Cuando** el Administrador filtra por tipo "Extracción de baja confianza" y fuente "SECOP II"
- **Entonces** obtiene solo los elementos que cumplen ambos filtros

### Escenario 4: Ordenar por confianza

- **Dado** que hay 6 elementos de extracción de baja confianza con confianzas 0,41; 0,55; 0,60; 0,62; sin valor numérico ("incierta"); 0,30
- **Cuando** el Administrador ordena por confianza ascendente
- **Entonces** el orden es 0,30; 0,41; 0,55; 0,60; 0,62 y al final el elemento sin valor numérico

### Escenario 5: Consultar elementos resueltos

- **Dado** que un elemento de extracción fue corregido por el Revisor el 2026-09-30
- **Cuando** el Administrador filtra por estado "Resuelto"
- **Entonces** el elemento aparece con fecha de resolución, usuario que resolvió y resultado de la resolución ("Corregido")

### Escenario 6: Un elemento resuelto sale de los pendientes

- **Dado** que un elemento de clasificación dudosa está Pendiente
- **Cuando** el Revisor confirma la clasificación mediante el flujo de corrección de clasificación
- **Entonces** el elemento pasa a estado Resuelto y deja de contarse en el resumen de pendientes

### Escenario 7: Sin duplicados en la cola

- **Dado** que ya existe un elemento Pendiente de "Extracción de baja confianza" para el campo precio unitario del ítem 1 del contrato CO1.PCCNTR.5030063
- **Cuando** una nueva extracción vuelve a dejar ese mismo campo con baja confianza
- **Entonces** no se crea un segundo elemento; el existente actualiza su valor actual, su confianza y su fecha de última detección, y conserva su fecha de ingreso original

### Escenario 8: Reingreso tras una resolución

- **Dado** que un elemento de inconsistencia aritmética de un ítem fue Resuelto
- **Cuando** una nueva extracción del mismo ítem vuelve a detectar una inconsistencia aritmética
- **Entonces** se crea un nuevo elemento Pendiente con nueva fecha de ingreso; el resuelto se conserva sin cambios

### Escenario 9: Cola vacía

- **Dado** que no hay elementos pendientes
- **Cuando** el Administrador consulta la cola o el resumen
- **Entonces** recibe "No hay elementos pendientes de revisión." y el resumen muestra total 0, conteos en 0 y "elemento pendiente más antiguo: —"

### Escenario 10: Filtros sin resultados

- **Dado** que existen elementos pendientes, ninguno de TVEC con tipo "Inconsistencia aritmética"
- **Cuando** el Administrador aplica esos filtros
- **Entonces** recibe "No hay elementos que cumplan los filtros."

### Escenario 11: Filtros inválidos

- **Dado** que el Administrador está autenticado
- **Cuando** filtra por el tipo "Sobreprecio", por el rango de fechas 2026-09-30 a 2026-09-01, o pide una página de 600 elementos
- **Entonces** no obtiene resultados y recibe, respectivamente, "El tipo 'Sobreprecio' no es válido. Tipos válidos: Clasificación dudosa, Extracción de baja confianza, Inconsistencia aritmética, Precio anormalmente bajo.", "La fecha inicial no puede ser posterior a la fecha final." o "El tamaño de página debe estar entre 1 y 500."

### Escenario 12: Exportar la cola filtrada

- **Dado** que el filtro aplicado devuelve 130 elementos
- **Cuando** el Administrador exporta el resultado
- **Entonces** obtiene un archivo CSV en UTF-8 con encabezado y 130 filas con los campos de RN-03, sin paginación

### Escenario 13: Usuario sin rol Administrador

- **Dado** que un usuario con rol Analista está autenticado
- **Cuando** intenta consultar o exportar la cola
- **Entonces** no obtiene datos y recibe "Acción no permitida: esta operación requiere el rol Administrador."

---

## Información Recopilada

### Usuario y Contexto

- **Tipo de usuario:** Administrador que actúa como Revisor (P-08: en el MVP, el PO). Los analistas piloto no hacen limpieza de datos.
- **Permisos requeridos:** rol Administrador.
- **Valor de negocio:** la revisión humana es la que convierte extracciones dudosas en datos comparables; una cola visible y ordenada reduce el tiempo de la sesión semanal del Journey 3 (30–60 minutos) y evita elementos olvidados.

### Reglas de Negocio

- **RN-01 — Tipos de elemento:**

  | Tipo | Origen | Granularidad |
  |---|---|---|
  | Clasificación dudosa | Candidato con resultado de clasificación "requiere revisión" | un elemento por ítem candidato |
  | Extracción de baja confianza | Dato extraído con confianza menor que el umbral de aceptación automática vigente o, si el umbral está "sin calibrar", dato crítico (marca, modelo/referencia, tamaño, cantidad, precio unitario) con confianza baja o incierta | un elemento por ítem y campo |
  | Inconsistencia aritmética | cantidad × precio unitario ≠ total del ítem, o suma de ítems ≠ total esperado | un elemento por ítem (o por contrato si es de suma) |
  | Precio anormalmente bajo | Desviación por debajo de la referencia dirigida a revisión de calidad | un elemento por ítem y benchmark |

- **RN-02 — Estados:** Pendiente → Resuelto. El paso a Resuelto lo producen los flujos de resolución (corrección de clasificación y validación/corrección/rechazo de datos extraídos), que informan fecha y hora, usuario y resultado (Confirmado, Corregido, Rechazado, Validado o Descartado). Esta HU no permite resolver ni reabrir elementos. Un elemento Resuelto es inmutable.
- **RN-03 — Campos de cada elemento:** id del elemento; tipo; estado; motivo (texto del proceso que lo generó, máximo 500 caracteres); fuente (SECOP II / TVEC); id de contrato SECOP II u orden TVEC; número de ítem; descripción del ítem (máximo 200 caracteres); campo afectado (solo extracción; "—" en otros tipos); valor actual ("—" si no hay); confianza (decimal 0,00–1,00 o "incierta"; "—" si no aplica); documento de origen y ubicación (página, hoja o celda; "—" si no aplica); fecha de ingreso; fecha de última detección; antigüedad en días (enteros completos desde la fecha de ingreso); y, si está Resuelto, fecha de resolución, usuario y resultado.
- **RN-04 — Unicidad:** no puede haber dos elementos Pendientes con el mismo tipo, ítem y campo (o benchmark, para precio bajo). Una nueva detección sobre un elemento Pendiente existente actualiza valor actual, confianza, motivo y fecha de última detección, y conserva la fecha de ingreso. Si el elemento anterior está Resuelto, se crea uno nuevo.
- **RN-05 — Filtros (combinables con Y):** tipo (uno o varios de RN-01); estado (por defecto Pendiente; también Resuelto o Todos); fuente; id de contrato u orden (coincidencia exacta); campo afectado; rango de fecha de ingreso (`AAAA-MM-DD`, ambos extremos incluidos).
- **RN-06 — Orden:** por defecto, fecha de ingreso ascendente (más antiguo primero); alternativas: confianza ascendente (los elementos con confianza "incierta" o sin confianza van al final), antigüedad descendente, tipo y contrato. Empates: por id del elemento ascendente.
- **RN-07 — Paginación:** tamaño de página entero de 1 a 500; por defecto 50. La exportación CSV (UTF-8, separador coma, con encabezado) incluye todo el resultado filtrado sin paginar.
- **RN-08 — Resumen:** total pendiente, conteo pendiente por tipo (los 4 tipos siempre presentes, aunque sean 0) y antigüedad en días del pendiente más antiguo ("—" si no hay).
- **RN-09 — Lenguaje:** los motivos y textos de la cola describen "revisión de calidad o evidencia"; nunca usan "sobreprecio", "corrupción", "fraude" ni "hallazgo fiscal".
- **RN-10 — Mensajes:**
  - "No hay elementos pendientes de revisión."
  - "No hay elementos que cumplan los filtros."
  - "El tipo '{x}' no es válido. Tipos válidos: Clasificación dudosa, Extracción de baja confianza, Inconsistencia aritmética, Precio anormalmente bajo."
  - "La fecha inicial no puede ser posterior a la fecha final."
  - "La fecha '{x}' no tiene el formato AAAA-MM-DD."
  - "El tamaño de página debe estar entre 1 y 500."
  - "Acción no permitida: esta operación requiere el rol Administrador."

### Interfaz

No requiere interfaz gráfica. Mínimo aceptable: comando o consulta "cola de revisión" con los filtros, orden y paginación de RN-05 a RN-07, comando "resumen de cola" (RN-08) y exportación CSV. Cada elemento debe traer los identificadores necesarios (contrato u orden, ítem, documento y ubicación) para abrirlo en el flujo de resolución.

### Sistemas Externos (Si aplica)

No aplica.

---

## Contexto y Referencias

**Épica origen:** [Operación, Calidad y Medición del MVP](../../../epicas.md#épica-008-operación-calidad-y-medición-del-mvp)

**Exclusiones de la Épica:**
- NO incluye analítica de uso avanzada ni embudos de producto.
- NO incluye facturación ni gestión de planes.
- NO incluye administración multi-organización.

**Historias relacionadas:** HU-102 (umbral de aceptación automática), HU-104 (muestra de validación).

---

## Supuestos

> Elementos inferidos por la IA que NO estaban explícitos en el PRD o la Épica. Todos los supuestos han sido resueltos: convertidos en reglas de negocio explícitas o eliminados mediante reformulación. Si aparece algún supuesto no resuelto, esta HU NO está lista para desarrollo.

- Los precios anormalmente bajos (FR-063) forman parte de la misma cola como cuarto tipo → resuelto en RN-01.
- La cola solo se consulta; la resolución pertenece a los flujos de FR-016 y FR-032 → resuelto en RN-02.
- Una nueva detección no duplica un elemento pendiente → resuelto en RN-04.
- El orden por defecto es el más antiguo primero → resuelto en RN-06.

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
