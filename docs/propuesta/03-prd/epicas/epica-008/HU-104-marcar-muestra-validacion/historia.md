# Historia #104: Marcar contratos y documentos de la muestra de validación manual

**Estado:** Borrador (PO)  
**Release:** Release MVP  
**Épica:** [Operación, Calidad y Medición del MVP](../../../epicas.md#épica-008-operación-calidad-y-medición-del-mvp)  
**Feature:** Gestionar Revisión y Muestra de Validación  
**Prioridad:** Alta  
**FRs relacionados:** FR-092 (relacionados: FR-024, FR-091, FR-094; NFR-CAL-001)

Escrita por el flujo generar-historias-usuario (Método Ceiba) — MVP propio, no comercial

---

## Historia de Usuario

**Como** Administrador del MVP (el PO),  
**Quiero** marcar contratos o documentos de SECOP II como parte de la muestra de validación manual de la extracción y ver la composición de esa muestra,  
**Para** medir la precisión y la cobertura sobre una muestra diversa de al menos 50 contratos/documentos, sin limitarme a los casos fáciles.

## Descripción

La precisión de la extracción **no puede medirla el mismo sistema que extrae** (D4): requiere que una persona verifique, campo por campo, una muestra de contratos o documentos. NFR-CAL-001 exige **≥ 90 % de precisión en campos críticos sobre una muestra diversa de ≥ 50 contratos/documentos**. Esta HU permite construir esa muestra:

- Marcar uno o varios **contratos** SECOP II candidatos (incluye todos sus ítems de televisor, los campos extraídos de todos sus documentos y el veredicto por contrato que alimenta la cobertura).
- Marcar uno o varios **documentos** SECOP II (incluye solo los campos extraídos de ese documento; alimenta la precisión, no la cobertura).
- Retirar un elemento solo si todavía no tiene resultados de validación (para que la muestra no se "limpie" a conveniencia).
- Consultar la **composición** de la muestra, con advertencias de concentración.

El registro de los valores verificados se hace en HU-105.

**Implementación sin UI permitida:** comando o script con lista de identificadores, consulta o interfaz administrativa mínima.

---

## Criterios de Aceptación

### Escenario 1: Marcar contratos en lote

- **Dado** que CO1.PCCNTR.4838434, CO1.PCCNTR.5030063 y CO1.PCCNTR.4946355 son contratos candidatos de SECOP II que no están en la muestra
- **Cuando** el Administrador los marca con la etiqueta de lote "D4-4"
- **Entonces** los tres quedan en la muestra con tipo "contrato", lote "D4-4", fecha y hora y usuario, y la respuesta lista cada id con resultado "Marcado"

### Escenario 2: Marcar un documento

- **Dado** que DOC-30542 es un documento registrado de un contrato candidato SECOP II que no está en la muestra
- **Cuando** el Administrador lo marca con lote "2026-10-S1"
- **Entonces** el documento queda en la muestra con tipo "documento" y su resultado es "Marcado"

### Escenario 3: Resultado mixto en un lote

- **Dado** que el Administrador envía CO1.PCCNTR.4838434 (ya en la muestra), CO1.PCCNTR.9999999 (no existe) y CO1.PCCNTR.5375159 (candidato no marcado)
- **Cuando** marca el lote
- **Entonces** la respuesta es, por id: "Ya en la muestra", "Rechazado: el contrato 'CO1.PCCNTR.9999999' no existe en el universo de candidatos SECOP II." y "Marcado"; solo CO1.PCCNTR.5375159 cambia

### Escenario 4: Elementos que no pueden integrar la muestra

- **Dado** que el Administrador está autenticado
- **Cuando** intenta marcar la orden TVEC 98765
- **Entonces** el resultado es "Rechazado: solo contratos o documentos de SECOP II sujetos a extracción pueden integrar la muestra."

### Escenario 5: Documento ya incluido por su contrato

- **Dado** que CO1.PCCNTR.5030063 está en la muestra y DOC-30610 pertenece a ese contrato
- **Cuando** el Administrador marca DOC-30610
- **Entonces** el resultado es "Ya en la muestra: el documento DOC-30610 está incluido a través del contrato CO1.PCCNTR.5030063." y no se crea un registro nuevo

### Escenario 6: Marcar el contrato de un documento ya marcado

- **Dado** que DOC-30542 está en la muestra individualmente y pertenece a CO1.PCCNTR.5100200
- **Cuando** el Administrador marca CO1.PCCNTR.5100200
- **Entonces** el contrato queda marcado, DOC-30542 conserva su marca y sus campos se cuentan una sola vez en la muestra

### Escenario 7: Lote inválido o vacío

- **Dado** que el Administrador está autenticado
- **Cuando** marca sin etiqueta de lote, con una etiqueta de 2 caracteres, envía una lista vacía o una lista de 201 identificadores
- **Entonces** no se marca ninguno y recibe, respectivamente, "Debe indicar una etiqueta de lote de 3 a 50 caracteres." (para los dos primeros), "Debe indicar al menos un identificador." o "Se permiten como máximo 200 identificadores por operación."

### Escenario 8: Retirar un elemento sin resultados de validación

- **Dado** que CO1.PCCNTR.5375159 está en la muestra y no tiene resultados de validación
- **Cuando** el Administrador lo retira con el motivo "Marcado por error, es un contrato de mantenimiento duplicado"
- **Entonces** deja de estar en la muestra, se registra un evento de auditoría "Retiro de muestra de validación" con usuario, fecha y hora, id y motivo, y la respuesta es "CO1.PCCNTR.5375159 fue retirado de la muestra."

### Escenario 9: Retirar un elemento con resultados de validación

- **Dado** que CO1.PCCNTR.4838434 ya tiene al menos un resultado de validación registrado
- **Cuando** el Administrador intenta retirarlo
- **Entonces** sigue en la muestra y recibe "No se puede retirar CO1.PCCNTR.4838434 de la muestra: ya tiene resultados de validación registrados."

### Escenario 10: Composición de la muestra

- **Dado** que la muestra tiene 45 contratos y 8 documentos marcados individualmente cuyos contratos no están marcados
- **Cuando** el Administrador consulta la composición
- **Entonces** obtiene: elementos de muestra 53; contratos 45; documentos individuales 8; "Muestra mínima: 53/50 — Cumple"; y la distribución por año de firma, entidad, tipo de documento, necesidad de OCR o lectura multimodal, resultado del extractor y estado de validación (RN-08)

### Escenario 11: Muestra por debajo del mínimo

- **Dado** que la muestra tiene 30 elementos
- **Cuando** el Administrador consulta la composición
- **Entonces** ve "Muestra mínima: 30/50 — No cumple"

### Escenario 12: Advertencias de diversidad

- **Dado** que 31 de 45 contratos de la muestra (68,9 %) son de 2023 y ningún contrato de la muestra tiene resultado del extractor "información insuficiente" o "sin precio"
- **Cuando** el Administrador consulta la composición
- **Entonces** ve las advertencias "La muestra está concentrada: 68,9 % de los contratos corresponde a año de firma 2023." y "La muestra no incluye contratos con información insuficiente o sin precio extraído."

### Escenario 13: Muestra vacía

- **Dado** que no hay elementos marcados
- **Cuando** el Administrador consulta la composición
- **Entonces** recibe "La muestra de validación está vacía." y "Muestra mínima: 0/50 — No cumple"

### Escenario 14: Usuario sin rol Administrador

- **Dado** que un usuario con rol Analista está autenticado
- **Cuando** intenta marcar, retirar o consultar la muestra
- **Entonces** recibe "Acción no permitida: esta operación requiere el rol Administrador." y nada cambia

---

## Información Recopilada

### Usuario y Contexto

- **Tipo de usuario:** Administrador (en el MVP, el PO, que también es el validador manual).
- **Permisos requeridos:** rol Administrador.
- **Valor de negocio:** sin una muestra validada no se puede demostrar el KPI de precisión (≥ 90 %) ni separar "la fuente no publica el dato" de "el producto no lo extrae" (cobertura D4-1).

### Reglas de Negocio

- **RN-01 — Elementos admitidos:** (a) **contrato**: identificador `id_contrato` de SECOP II (formato `CO1.PCCNTR.{dígitos}`) que exista en el universo de candidatos SECOP II del alcance, cualquiera sea su resultado de clasificación o extracción; (b) **documento**: `id_documento` registrado de un contrato candidato SECOP II, aunque no tenga datos extraídos. Ítems y órdenes TVEC no se admiten (no hay extracción documental).
- **RN-02 — Alcance de cada marca:** un contrato marcado incluye todos sus ítems de televisor, los campos extraídos de todos sus documentos y el veredicto por contrato usado en la cobertura. Un documento marcado incluye solo los campos extraídos de ese documento y no aporta veredicto por contrato.
- **RN-03 — Lote:** cada operación de marcado lleva una etiqueta de lote obligatoria de 3 a 50 caracteres (letras, números, espacios, guiones y guion bajo), que se guarda con cada elemento. Identificadores por operación: 1 a 200. Se quitan espacios y se ignoran identificadores repetidos dentro de la misma operación.
- **RN-04 — Resultado por identificador:** cada identificador se procesa por separado y devuelve uno de: "Marcado"; "Ya en la muestra" (sin cambios; si es un documento cubierto por su contrato, con el texto "Ya en la muestra: el documento {id} está incluido a través del contrato {c}."); o "Rechazado: {motivo}". Un rechazo no impide marcar los demás.
- **RN-05 — Sin doble conteo:** si un documento está marcado individualmente y también lo está su contrato, sus campos se cuentan una sola vez. "Elementos de muestra" = contratos marcados + documentos marcados individualmente cuyo contrato no está marcado.
- **RN-06 — Retiro:** solo si el elemento no tiene ningún resultado de validación registrado (HU-105). Requiere motivo de 10 a 500 caracteres. Se registra en el log de auditoría con tipo "Retiro de muestra de validación", usuario, fecha y hora, id y motivo. Los resultados de validación nunca se borran por un retiro.
- **RN-07 — Auditoría del marcado:** cada operación de marcado registra un evento "Marcado de muestra de validación" con usuario, fecha y hora, lote e identificadores marcados. Si la auditoría no se puede registrar, la operación no se aplica y responde "No fue posible registrar la auditoría; la operación no se aplicó. Intente de nuevo."
- **RN-08 — Composición:** elementos de muestra; contratos; documentos individuales; indicador "Muestra mínima: {n}/{mínimo} — Cumple | No cumple" (mínimo configurable, entero de 1 a 1.000; **configuración inicial: 50**, NFR-CAL-001); distribución (conteo y porcentaje con 1 decimal) por año de firma, entidad compradora, tipo de documento, requiere OCR o lectura multimodal (sí/no), resultado del extractor (precio explícito, precio derivado, información insuficiente, sin precio, fuera de categoría u otro valor registrado) y estado de validación (sin validar, parcial, completa); y lotes con su cantidad.
- **RN-09 — Advertencias de diversidad (no bloqueantes):** (a) si más de un umbral de concentración configurable (decimal de 10,0 a 100,0 %; **configuración inicial: 50,0 %**) de los contratos de la muestra comparte el mismo año de firma o la misma entidad: "La muestra está concentrada: {p} % de los contratos corresponde a {dimensión} {valor}."; (b) si ningún contrato de la muestra tiene resultado "información insuficiente" ni "sin precio": "La muestra no incluye contratos con información insuficiente o sin precio extraído." Con 0 contratos no se calculan advertencias.
- **RN-10 — Sin efectos colaterales:** marcar o retirar no modifica datos extraídos, clasificación, cola de revisión, señales ni KPIs ya calculados.
- **RN-11 — Mensajes:**
  - "Rechazado: el contrato '{id}' no existe en el universo de candidatos SECOP II."
  - "Rechazado: el documento '{id}' no existe o no pertenece a un contrato candidato SECOP II."
  - "Rechazado: solo contratos o documentos de SECOP II sujetos a extracción pueden integrar la muestra."
  - "Debe indicar una etiqueta de lote de 3 a 50 caracteres."
  - "Debe indicar al menos un identificador."
  - "Se permiten como máximo 200 identificadores por operación."
  - "{id} fue retirado de la muestra."
  - "{id} no está en la muestra."
  - "No se puede retirar {id} de la muestra: ya tiene resultados de validación registrados."
  - "Debe indicar un motivo de retiro de 10 a 500 caracteres."
  - "La muestra de validación está vacía."
  - "Acción no permitida: esta operación requiere el rol Administrador."

### Interfaz

No requiere interfaz gráfica. Mínimo aceptable: comando "marcar muestra" con lote y lista de identificadores (o archivo de texto con un identificador por línea), comando "retirar de muestra" con motivo y comando o consulta "composición de muestra" con el contenido de RN-08 y RN-09.

### Sistemas Externos (Si aplica)

No aplica.

---

## Contexto y Referencias

**Épica origen:** [Operación, Calidad y Medición del MVP](../../../epicas.md#épica-008-operación-calidad-y-medición-del-mvp)

**Exclusiones de la Épica:**
- NO incluye analítica de uso avanzada ni embudos de producto.
- NO incluye facturación ni gestión de planes.
- NO incluye administración multi-organización.

**Historias relacionadas:** HU-105 (registrar resultados de validación), HU-106 (precisión), HU-107 (cobertura), HU-112 (auditoría).

---

## Supuestos

> Elementos inferidos por la IA que NO estaban explícitos en el PRD o la Épica. Todos los supuestos han sido resueltos: convertidos en reglas de negocio explícitas o eliminados mediante reformulación. Si aparece algún supuesto no resuelto, esta HU NO está lista para desarrollo.

- Un contrato marcado aporta precisión y cobertura; un documento marcado solo aporta precisión → resuelto en RN-02.
- Para evitar sesgo de selección, un elemento con resultados de validación no puede retirarse → resuelto en RN-06.
- "Diversa" se apoya en una composición visible y en advertencias no bloqueantes (concentración > 50 % configurable, ausencia de casos difíciles) → resuelto en RN-08 y RN-09.
- El marcado y el retiro se registran en el log de auditoría → resuelto en RN-06 y RN-07.

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
