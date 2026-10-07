# Historia #027: Detectar inconsistencias aritméticas en los datos extraídos y dirigirlas a revisión de calidad

**Estado:** Borrador (PO)  
**Release:** Release MVP  
**Épica:** [De Documentos a Datos Comparables](../../../epicas.md#épica-002-de-documentos-a-datos-comparables)  
**Feature:** Controlar la Calidad de la Extracción  
**Prioridad:** Crítica  
**FRs relacionados:** FR-031

Escrita por el flujo generar-historias-usuario (Método Ceiba) — MVP propio, no comercial

---

## Historia de Usuario

**Como** Administrador que actúa como Revisor en el MVP,  
**Quiero** que el sistema compruebe si cantidad × precio unitario coincide con el valor total del ítem y si la suma de los ítems coincide con el total publicado, cuando la información lo permita, y envíe las diferencias a revisión de calidad,  
**Para** detectar errores de lectura, de cantidad o de la propia tabla antes de que un dato llegue a una comparación, sin tratarlos como irregularidades.

## Descripción

D4 registró 33 inconsistencias, entre ellas errores aritméticos en tablas de los oferentes (ej. 4 × 1.020.000 registrado como 4.800.000). Estas diferencias pueden deberse a un error de extracción o a un error del documento; en ambos casos son una **señal de revisión de calidad o de evidencia, no una irregularidad**.

Esta HU aplica dos comprobaciones determinísticas sobre los ítems extraídos (HU-022), respetando la base tributaria de cada valor (HU-023): la del ítem (cantidad × precio unitario frente al valor total) y la de la tabla (suma de los valores totales de los ítems frente al total publicado de la tabla). Cada comprobación termina en "consistente", "inconsistente" o "no comprobable" con motivo. Una inconsistencia abierta envía el ítem a revisión (HU-026) hasta que el Administrador la resuelva (HU-028). No requiere interfaz gráfica.

---

## Criterios de Aceptación

### Escenario 1: Ítem consistente

- **Dado** que el ítem `CO1.PCCNTR.7654321-01` tiene cantidad 8, precio unitario explícito 2.150.000,00 y valor total 17.200.000,00, todos `con_iva`
- **Cuando** se ejecuta la comprobación aritmética
- **Entonces** la comprobación del ítem queda "consistente"

### Escenario 2: Error aritmético en la tabla del documento

- **Dado** que el ítem tiene cantidad 4, precio unitario 1.020.000,00 y valor total 4.800.000,00, todos con la misma base
- **Cuando** se ejecuta la comprobación aritmética
- **Entonces** la comprobación queda "inconsistente" con el detalle "4 × 1.020.000,00 = 4.080.000,00 ≠ 4.800.000,00 (diferencia 720.000,00; 17,65 %)", el ítem queda con "inconsistencia aritmética abierta" y pasa a revisión con el texto "Inconsistencia aritmética: revisión de calidad o de evidencia; no constituye una irregularidad"

### Escenario 3: Diferencia por redondeo dentro de la tolerancia

- **Dado** que la cantidad es 3, el precio unitario 3.333.333,00 y el total 10.000.000,00, con tolerancia configurada de 0,5 %
- **Cuando** se ejecuta la comprobación aritmética
- **Entonces** la comprobación queda "consistente" (diferencia 1,00; 0,00001 %)

### Escenario 4: Precio sin IVA, total con IVA y tasa publicada

- **Dado** que el precio unitario es 1.806.723,00 `sin_iva`, el total 17.200.000,00 `con_iva`, la cantidad 8 y la tasa publicada 19 %
- **Cuando** se ejecuta la comprobación aritmética
- **Entonces** se compara 8 × 1.806.723,00 × 1,19 = 17.200.002,96 con 17.200.000,00 y la comprobación queda "consistente"

### Escenario 5: Bases distintas sin tasa publicada

- **Dado** que el precio unitario es `sin_iva`, el total `con_iva` y el documento no publica la tasa de IVA
- **Cuando** se ejecuta la comprobación aritmética
- **Entonces** la comprobación queda "no comprobable" con el motivo "bases tributarias distintas sin tasa de IVA documentada"

### Escenario 6: Falta un dato

- **Dado** que el ítem no tiene valor total, o no tiene precio unitario explícito, o no tiene cantidad
- **Cuando** se ejecuta la comprobación aritmética
- **Entonces** la comprobación del ítem queda "no comprobable" con el motivo "faltan datos para comprobar"; si el precio unitario es derivado, el motivo es "precio derivado: consistente por construcción"

### Escenario 7: Suma de ítems frente al total de la tabla

- **Dado** que la tabla de la oferta contiene solo televisores, la extracción registró sus 2 ítems con totales 8.400.000,00 y 9.800.000,00 y el total publicado de la tabla es 19.200.000,00, todos con la misma base
- **Cuando** se ejecuta la comprobación aritmética
- **Entonces** la comprobación de la tabla queda "inconsistente" (18.200.000,00 ≠ 19.200.000,00) y ambos ítems quedan con "inconsistencia aritmética abierta"

### Escenario 8: Tabla con otros bienes

- **Dado** que la tabla incluye también computadores, que no se extraen
- **Cuando** se ejecuta la comprobación aritmética
- **Entonces** la comprobación de la tabla queda "no comprobable" con el motivo "la tabla incluye bienes que no son televisores"

### Escenario 9: Inconsistencia resuelta por el Administrador y nueva comprobación

- **Dado** que el Administrador corrige el valor total del ítem del Escenario 2 a 4.080.000,00 con evidencia
- **Cuando** se guarda la corrección
- **Entonces** la comprobación se repite, queda "consistente", la inconsistencia pasa a "resuelta" con usuario, fecha y acción, y el ítem deja de tener el motivo "inconsistencia aritmética"

### Escenario 10: Lenguaje de la inconsistencia

- **Dado** que se genera cualquier texto asociado a una inconsistencia
- **Cuando** se registra o se muestra
- **Entonces** el texto no contiene las palabras "sobreprecio", "corrupción", "fraude" ni "hallazgo fiscal"

---

## Información Recopilada

### Usuario y Contexto

- **Tipo de usuario:** Administrador que actúa como Revisor (en el MVP es el PO). La comprobación es automática.
- **Permisos requeridos:** Administrador y Analista consultan las comprobaciones; solo el Administrador resuelve (HU-028) o cambia la tolerancia.
- **Valor de negocio:** Evita que errores de lectura o de la tabla del documento produzcan comparaciones o señales infundadas.

### Reglas de Negocio

- **RN-01 — Momento:** se ejecuta tras la extracción, la base tributaria y el precio derivado de un proceso, y de nuevo tras cada corrección humana de cantidad, precio unitario, valor total, base o tasa del ítem.
- **RN-02 — Comprobación del ítem:** aplica cuando el ítem tiene cantidad, precio unitario **explícito** y valor total. Se calcula `esperado = cantidad × precio unitario` y se compara con el valor total. Si el precio unitario es derivado, el resultado es "no comprobable" con el motivo "precio derivado: consistente por construcción". Si falta alguno de los tres datos: "no comprobable", "faltan datos para comprobar".
- **RN-03 — Base tributaria en la comprobación del ítem:**
  - Misma base (incluido el caso de ambas `indeterminada`): comparación directa.
  - Precio `sin_iva` y total `con_iva` con tasa de IVA documentada: `esperado = cantidad × precio × (1 + tasa)`.
  - Precio `con_iva` y total `sin_iva` con tasa documentada: `esperado = cantidad × precio / (1 + tasa)`.
  - Bases distintas sin tasa documentada, o una base `indeterminada` y la otra determinada: "no comprobable", "bases tributarias distintas sin tasa de IVA documentada".
- **RN-04 — Tolerancia (configurable):** la comprobación es "consistente" si `|esperado − valor de referencia| ≤ máximo(tolerancia porcentual × valor de referencia, tolerancia mínima)`. Configuración inicial: 0,5 % y COP 100. Rango válido de la tolerancia porcentual: 0,0 % a 10,0 %; de la mínima: COP 0 a COP 100.000. Fuera de rango: "Valor fuera de rango para {parámetro}: debe estar entre {mín} y {máx}" y se conserva el anterior.
- **RN-05 — Comprobación de la tabla:** aplica cuando la extracción registró el total publicado de una tabla, con evidencia, e indicó que todas las filas de la tabla son ítems de televisor extraídos. Se compara la suma de los valores totales de esos ítems con el total de la tabla, en la misma base (si las bases difieren, se aplica RN-03 con la tasa documentada o queda "no comprobable"). Si la tabla incluye filas que no son televisores: "no comprobable", "la tabla incluye bienes que no son televisores". Si algún ítem de la tabla no tiene valor total: "no comprobable", "faltan datos para comprobar".
- **RN-06 — Resultado y detalle:** cada comprobación guarda resultado ("consistente", "inconsistente" o "no comprobable"), motivo si aplica, valores usados, fórmula aplicada, diferencia absoluta y porcentual (2 decimales) y evidencias de los valores. Formato del detalle de inconsistencia: "{cantidad} × {precio} = {esperado} ≠ {total} (diferencia {abs}; {pct} %)".
- **RN-07 — Efecto:** una comprobación "inconsistente" deja cada ítem involucrado con "inconsistencia aritmética abierta", que lo envía a revisión (HU-026) y lo deja no disponible para comparación hasta su resolución.
- **RN-08 — Resolución:** una inconsistencia pasa a "resuelta" cuando: a) una corrección del Administrador hace que la nueva comprobación sea "consistente" o "no comprobable", o b) el Administrador valida el ítem indicando que el error está en el documento y que los valores extraídos son fieles a él (comentario obligatorio). Se registran usuario, fecha, acción y comentario. En el caso b) la inconsistencia se conserva visible como "inconsistencia del documento" junto al ítem.
- **RN-09 — Lenguaje:** todo texto asociado se presenta como "Inconsistencia aritmética: revisión de calidad o de evidencia; no constituye una irregularidad". Ningún texto usa las palabras "sobreprecio", "corrupción", "fraude" ni "hallazgo fiscal".
- **RN-10 — Fuera de alcance:** los precios anormalmente bajos no se evalúan aquí (los trata la épica de señales).
- **RN-11 — Sin IA:** la comprobación es determinística y funciona con la extracción con IA desactivada.

### Interfaz

Sin interfaz gráfica obligatoria. Resultados y detalle disponibles para la revisión humana y para consultas; los mensajes de RN-04 se devuelven en la respuesta de la operación de configuración.

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

**Historias relacionadas:** HU-022 (valores y total de tabla), HU-023 (bases y tasa), HU-024 (precio derivado), HU-026 (envío a revisión), HU-028 (resolución).

---

## Supuestos

> Elementos inferidos por la IA que NO estaban explícitos en el PRD o la Épica. Todos los supuestos han sido resueltos: convertidos en reglas de negocio explícitas o eliminados mediante reformulación. Si aparece algún supuesto no resuelto, esta HU NO está lista para desarrollo.

- Tolerancia inicial configurable: el mayor entre 0,5 % y COP 100 → RN-04.
- La comprobación entre bases distintas solo se hace si la tasa de IVA está documentada → RN-03.
- La suma de ítems solo se comprueba si la tabla contiene únicamente televisores extraídos → RN-05.
- El Administrador puede cerrar una inconsistencia que proviene del propio documento, dejándola visible → RN-08.

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
