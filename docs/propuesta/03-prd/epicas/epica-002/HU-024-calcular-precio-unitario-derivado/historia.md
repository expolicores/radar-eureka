# Historia #024: Calcular el precio unitario derivado solo cuando se cumplen las seis condiciones

**Estado:** Borrador (PO)  
**Release:** Release MVP  
**Épica:** [De Documentos a Datos Comparables](../../../epicas.md#épica-002-de-documentos-a-datos-comparables)  
**Feature:** Extraer Datos de Ítems de Televisor  
**Prioridad:** Crítica  
**FRs relacionados:** FR-099, FR-100

Escrita por el flujo generar-historias-usuario (Método Ceiba) — MVP propio, no comercial

---

## Historia de Usuario

**Como** Analista que investiga contratación pública,  
**Quiero** que, cuando un documento publique el valor total y la cantidad de televisores pero no su precio unitario, el sistema calcule el precio unitario como valor total ÷ cantidad solo si se demuestran las seis condiciones aprobadas, y lo marque como derivado con su fórmula y su evidencia,  
**Para** ampliar la cobertura de precios comparables sin introducir precios distorsionados por otros bienes, servicios o valores no documentales.

## Descripción

La decisión D4-3 permite un precio unitario derivado (`valor total del ítem / cantidad`) en contratos de un solo tipo de televisor con valor global y cantidad conocida, siempre que se demuestren seis condiciones: (1) la cantidad está explícitamente documentada; (2) el valor usado corresponde exclusivamente a esos televisores; (3) todos son del mismo producto/modelo o de una referencia inequívocamente homogénea; (4) no hay otros bienes mezclados; (5) no hay instalación, transporte, soporte, obra, accesorios ni otros servicios incluidos sin discriminar; (6) la base tributaria no introduce una incompatibilidad conocida. Nunca se usa `valor total del contrato / cantidad` en un contrato mixto, ni el valor del contrato publicado en datos abiertos (FR-100), que en D4 no coincidía con la oferta aceptada (ej. 89,8 M frente a 61,0 M).

Esta HU evalúa las seis condiciones con la evidencia que reporta la extracción (HU-022), calcula el precio cuando todas se cumplen y lo guarda con `precio_unitario_tipo = derivado`, la fórmula, los valores usados, sus ubicaciones y una confianza menor que la de sus insumos. El cálculo y la decisión son determinísticos. No requiere interfaz gráfica.

---

## Criterios de Aceptación

### Escenario 1: Precio derivado con las seis condiciones cumplidas

- **Dado** que el ítem `CO1.PCCNTR.6100001-01` no tiene precio unitario explícito, tiene cantidad 8 (contrato, página 1, confianza 0,90) y valor total del ítem 17.200.000,00 `con_iva` (aceptación de oferta, página 2, confianza 0,85), y las seis condiciones están reportadas como "cumple" con evidencia
- **Cuando** se evalúa el precio derivado
- **Entonces** el precio unitario queda 2.150.000,00 con `precio_unitario_tipo = derivado`, indicador de derivado "sí", fórmula "17.200.000,00 / 8", valor total usado 17.200.000,00, cantidad usada 8, documentos y ubicaciones de ambos insumos, base `con_iva` heredada y confianza 0,68 (0,85 × 0,80)

### Escenario 2: Contrato mixto

- **Dado** que el valor total documentado de 45.000.000 incluye 10 computadores y 2 televisores, y la cantidad de televisores es 2
- **Cuando** se evalúa el precio derivado
- **Entonces** no se calcula precio derivado; la condición 4 queda "no cumple" con la evidencia, y el ítem pasa a la evaluación de información insuficiente con el motivo "condiciones de precio derivado no cumplidas: 2, 4"

### Escenario 3: Valor que incluye instalación sin discriminar

- **Dado** que el valor total del ítem dice "suministro e instalación de 6 televisores 55 pulgadas con soporte de pared"
- **Cuando** se evalúa el precio derivado
- **Entonces** no se calcula; las condiciones 2 y 5 quedan "no cumple"

### Escenario 4: Televisores de modelos distintos en el mismo valor

- **Dado** que un valor total cubre 4 televisores de 43 pulgadas y 2 de 65 pulgadas
- **Cuando** se evalúa el precio derivado
- **Entonces** no se calcula; la condición 3 queda "no cumple"

### Escenario 5: Condición no determinable

- **Dado** que la extracción reporta la condición 5 como "no determinable" porque el documento no dice si el valor incluye transporte
- **Cuando** se evalúa el precio derivado
- **Entonces** no se calcula; la condición 5 queda "no determinable" y el motivo es "condiciones de precio derivado no cumplidas: 5 (no determinable)"

### Escenario 6: Condición reportada como cumplida sin evidencia

- **Dado** que la condición 2 viene como "cumple" pero sin texto ni ubicación de soporte
- **Cuando** se evalúa el precio derivado
- **Entonces** la condición 2 se trata como "no determinable" y no se calcula el precio

### Escenario 7: Intento de usar el valor de datos abiertos

- **Dado** que el ítem no tiene valor total documental y el contrato tiene `valor_del_contrato` = 89.800.000 en datos abiertos con cantidad 8
- **Cuando** se evalúa el precio derivado
- **Entonces** no se calcula precio derivado (no hay valor total documental) y el valor de datos abiertos no se usa en ningún cálculo

### Escenario 8: Existe precio unitario explícito

- **Dado** que el ítem ya tiene un precio unitario explícito
- **Cuando** se evalúa el precio derivado
- **Entonces** no se calcula precio derivado y el precio queda `explicito`

### Escenario 9: Base tributaria incompatible

- **Dado** que el valor total tiene base `indeterminada` con el motivo "declaraciones tributarias contradictorias"
- **Cuando** se evalúa el precio derivado
- **Entonces** la condición 6 queda "no cumple" y no se calcula; si en cambio la base es `indeterminada` por "sin declaración tributaria en el documento", la condición 6 puede cumplirse y el precio derivado hereda la base `indeterminada`

### Escenario 10: Recalculo tras corrección humana

- **Dado** que el Administrador corrige la cantidad de un ítem con precio derivado de 8 a 10
- **Cuando** se guarda la corrección
- **Entonces** el precio derivado se recalcula a 1.720.000,00 con la nueva fórmula "17.200.000,00 / 10" y el valor anterior queda en el historial del ítem

### Escenario 11: Redondeo

- **Dado** que el valor total es 10.000.000,00 y la cantidad es 3
- **Cuando** se calcula el precio derivado
- **Entonces** el precio unitario es 3.333.333,33 (redondeo a 2 decimales, mitad hacia arriba)

---

## Información Recopilada

### Usuario y Contexto

- **Tipo de usuario:** Analista (ve el precio derivado marcado y su fórmula). El cálculo es automático; el Administrador puede corregir insumos (HU-028).
- **Permisos requeridos:** Analista y Administrador consultan; el factor de confianza lo configura el Administrador.
- **Valor de negocio:** Sube la disponibilidad de precios unitarios donde la fuente solo publica el total, sin sacrificar comparabilidad (epic: 100 % de los derivados con valor total, cantidad, fórmula, fuente, ubicación e indicador).

### Reglas de Negocio

- **RN-01 — Cuándo se evalúa:** cuando el ítem no tiene precio unitario explícito y tiene valor total del ítem y cantidad no nulos, ambos con evidencia documental. Si falta cualquiera de los dos, no se evalúa (el motivo lo asigna HU-025). Si hay precio unitario explícito, nunca se deriva.
- **RN-02 — Las seis condiciones (D4-3):** cada una se registra como "cumple", "no cumple" o "no determinable", con texto y ubicación de soporte:
  1. La cantidad está explícitamente documentada (tiene evidencia propia; no se infiere de otro valor).
  2. El valor usado corresponde exclusivamente a esos televisores.
  3. Todos los televisores incluidos son del mismo producto/modelo o de una referencia inequívocamente homogénea (mismo tamaño, resolución y tecnología, y misma marca y modelo cuando se publican).
  4. No hay otros bienes mezclados en el valor.
  5. No hay instalación, transporte, soporte, obra, accesorios ni otros servicios incluidos sin discriminar.
  6. La base tributaria no introduce una incompatibilidad conocida.
- **RN-03 — Origen de la evaluación:** las condiciones 2 a 5 provienen de la extracción (HU-022), que las reporta con su soporte. La condición 1 se verifica de forma determinística (la cantidad tiene evidencia propia en un documento). La condición 6 se verifica de forma determinística: "no cumple" si la base del valor total es `indeterminada` con el motivo "declaraciones tributarias contradictorias" o si la extracción reporta que el valor combina partes con bases distintas; en otro caso "cumple". Una condición reportada como "cumple" sin texto o sin ubicación de soporte se trata como "no determinable".
- **RN-04 — Decisión:** se calcula el precio derivado solo si las seis condiciones están en "cumple". En otro caso no se calcula y se entrega a HU-025 el motivo "condiciones de precio derivado no cumplidas: {números}", agregando "(no determinable)" a las que estén en ese estado.
- **RN-05 — Fórmula y redondeo:** `precio unitario derivado = valor total del ítem / cantidad`, en pesos colombianos, redondeado a 2 decimales con redondeo de la mitad hacia arriba.
- **RN-06 — Prohibiciones (FR-099, FR-100):** nunca se usa el `valor_del_contrato` de datos abiertos como valor total, ni ningún valor sin evidencia documental. Nunca se divide el valor total de un contrato entre la cantidad de televisores si el contrato contiene otros bienes o servicios (la condición 4 o la 5 queda "no cumple").
- **RN-07 — Datos guardados:** `precio_unitario_tipo = derivado`, indicador de derivado "sí", precio calculado, fórmula en texto con los valores ("17.200.000,00 / 8"), valor total usado, cantidad usada, documento, versión y ubicación de cada insumo, resultado y soporte de cada condición, etapa del precio heredada del valor total, base tributaria heredada del valor total y confianza.
- **RN-08 — Confianza (configurable):** `confianza del derivado = mínimo(confianza del valor total, confianza de la cantidad) × factor de derivación`, redondeada a 2 decimales con redondeo de la mitad hacia arriba (ej. 0,085 → 0,09). Configuración inicial del factor: 0,80; rango válido 0,10 a 0,99 (fuera de rango: "El factor de derivación debe estar entre 0,10 y 0,99" y se conserva el anterior). Así el derivado siempre tiene menor confianza que sus insumos y que un precio explícito con la misma evidencia.
- **RN-09 — Recalculo:** si el Administrador corrige la cantidad, el valor total o una condición del ítem (HU-028), la evaluación se repite: el precio derivado se recalcula, se crea o se elimina según el nuevo resultado, y el valor anterior se conserva en el historial del ítem con fecha y usuario.
- **RN-10 — Sin IA:** la evaluación y el cálculo son determinísticos sobre los datos ya extraídos y funcionan con la extracción con IA desactivada.

### Interfaz

Sin interfaz gráfica obligatoria. El precio derivado, su indicador, su fórmula y sus insumos quedan disponibles para las vistas de ficha y señal y para consultas del Administrador.

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

**Historias relacionadas:** HU-022 (insumos y condiciones), HU-023 (base tributaria), HU-025 (información insuficiente), HU-026 (umbral de confianza), HU-028 (corrección y recalculo).

---

## Supuestos

> Elementos inferidos por la IA que NO estaban explícitos en el PRD o la Épica. Todos los supuestos han sido resueltos: convertidos en reglas de negocio explícitas o eliminados mediante reformulación. Si aparece algún supuesto no resuelto, esta HU NO está lista para desarrollo.

- La confianza del derivado es el mínimo de la confianza de sus insumos por un factor configurable (inicial 0,80) → RN-08.
- Las condiciones 2 a 5 las reporta la extracción con su soporte; 1 y 6 se verifican de forma determinística → RN-03.
- Una base `indeterminada` por ausencia de declaración no es incompatibilidad; sí lo es la contradicción de declaraciones → RN-03.
- Redondeo a 2 decimales, mitad hacia arriba → RN-05.

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
