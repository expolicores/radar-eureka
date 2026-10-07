# Historia #037: Configurar las reglas de equivalencia por categoría

**Estado:** Borrador (PO)  
**Release:** Release MVP  
**Épica:** [Normalización y Emparejamiento de Televisores](../../../epicas.md#épica-003-normalización-y-emparejamiento-de-televisores)  
**Feature:** Emparejar por Equivalencia Técnica  
**Prioridad:** Crítica  
**FRs relacionados:** FR-038, FR-040

Escrita por el flujo generar-historias-usuario (Método Ceiba) — MVP propio, no comercial

---

## Historia de Usuario

**Como** Administrador (PO),  
**Quiero** definir y versionar, por categoría de bien, qué características deben coincidir para considerar dos productos equivalentes y con qué tolerancia,  
**Para** que la equivalencia se base en criterios explícitos, validados por mí, que no se puedan rebajar sin control ni trazabilidad.

## Descripción

La equivalencia técnica (FR-038) depende de reglas de dominio que el PO debe validar (factor crítico de la épica). Esta HU crea el **conjunto de reglas de equivalencia** por categoría (en el MVP solo `televisor`), con su configuración inicial, sus validaciones y su historial de versiones. El emparejamiento de equivalentes (HU-038) siempre usa la versión vigente.

Para cumplir FR-040, la configuración tiene un **piso no configurable** (criterios núcleo que no se pueden quitar ni relajar), cada cambio exige justificación y queda auditado, y los cambios solo se aplican hacia adelante con una nueva versión. NFR-EVO-002: agregar una categoría futura es crear su conjunto de reglas, sin cambiar el modelo de datos.

Capacidad administrativa: puede implementarse con archivo de configuración, script o interfaz mínima; no requiere pantalla.

---

## Criterios de Aceptación

### Escenario 1: Configuración inicial de la categoría televisor

- **Dado** que el sistema se instala por primera vez
- **Cuando** se carga la configuración inicial
- **Entonces** existe el conjunto de reglas `televisor` versión 1, vigente, con los criterios: tamaño (exacto, tolerancia 0", obligatorio), resolución (exacto, obligatorio), tecnología (exacto, obligatorio), Smart (exacto, obligatorio), generación (tolerancia ±1 año, solo si ambos conocidos) y marca (exacto, solo si ambos conocidos)

### Escenario 2: Cambio válido con justificación

- **Dado** que el Administrador cambia la tolerancia de generación de ±1 a 0 años con la justificación "Calibración con muestra revisada de octubre"
- **Cuando** guarda el cambio
- **Entonces** se crea la versión 2 vigente, la versión 1 pasa a `vigente = no` con fecha de fin, y se registra usuario, fecha y hora, valores anteriores y nuevos y la justificación

### Escenario 3: Cambio sin justificación

- **Dado** que el Administrador intenta guardar un cambio con justificación vacía o de menos de 10 caracteres
- **Cuando** guarda
- **Entonces** el cambio se rechaza con "Configuración inválida: la justificación es obligatoria (mínimo 10 caracteres)" y la versión vigente no cambia

### Escenario 4: Intento de relajar un criterio núcleo

- **Dado** que el Administrador intenta cambiar tamaño o resolución a "solo si ambos conocidos" o "no evaluado", eliminarlos, o poner una tolerancia de tamaño mayor a 1 pulgada
- **Cuando** guarda
- **Entonces** el cambio se rechaza con "Configuración inválida: {criterio} es un criterio núcleo y no puede relajarse por debajo del piso" y no se crea versión

### Escenario 5: Valores fuera de dominio

- **Dado** que el Administrador define una tolerancia negativa, una tolerancia en un criterio de modo exacto, un atributo inexistente en el esquema común o un modo no reconocido
- **Cuando** guarda
- **Entonces** el cambio se rechaza con "Configuración inválida: {detalle}"

### Escenario 6: Usuario sin permiso

- **Dado** que un Analista intenta modificar las reglas de equivalencia
- **Cuando** guarda
- **Entonces** el cambio se rechaza por falta de permiso y no se registra versión

### Escenario 7: Consultar versiones

- **Dado** que existen varias versiones del conjunto `televisor`
- **Cuando** el Administrador consulta las reglas
- **Entonces** obtiene la versión vigente y el historial completo (número de versión, criterios, fechas de inicio y fin, usuario y justificación)

### Escenario 8: Categoría sin reglas

- **Dado** que existe un producto de una categoría sin conjunto de reglas vigente
- **Cuando** el emparejamiento de equivalentes consulta las reglas
- **Entonces** se responde que no hay reglas vigentes y ningún producto de esa categoría puede emparejarse como equivalente (motivo `SIN_REGLAS_EQUIVALENCIA`)

### Escenario 9: Efecto prospectivo del cambio

- **Dado** que se crea una nueva versión de reglas
- **Cuando** se ejecuta el siguiente emparejamiento
- **Entonces** los pares de equivalencia se recalculan con la nueva versión y los pares calculados con la versión anterior pasan a `vigente = no` conservando la versión con la que se calcularon

---

## Información Recopilada

### Usuario y Contexto

- **Tipo de usuario:** Administrador (en el MVP, el PO).
- **Permisos requeridos:** solo el rol Administrador crea o modifica reglas; consultar las reglas vigentes está disponible para Administrador y para los procesos del sistema.
- **Valor de negocio:** evita falsos positivos por equivalencias laxas (riesgo R2) y deja explícito qué se considera comparable.

### Reglas de Negocio

**RN-01 — Estructura del conjunto de reglas.** Por categoría: `categoria`, `version` (entero desde 1), `vigente` (sí/no), `fecha_inicio`, `fecha_fin` (nula si vigente), `usuario`, `justificacion`, y una lista de criterios. Cada criterio tiene:
- `atributo`: uno de los atributos del esquema común (`tamano_pulgadas`, `resolucion`, `tecnologia`, `smart`, `generacion`, `marca`).
- `modo`: `EXACTO` (valores iguales) o `TOLERANCIA` (diferencia absoluta ≤ tolerancia; solo para atributos numéricos `tamano_pulgadas` y `generacion`).
- `tolerancia`: número ≥ 0; obligatorio en `TOLERANCIA`, nulo en `EXACTO`.
- `obligatoriedad`: `OBLIGATORIO` (ambos valores deben ser conocidos y cumplir), `SI_AMBOS_CONOCIDOS` (se evalúa solo si ambos son no nulos; si alguno es nulo queda `NO_EVALUADO`) o `NO_EVALUADO` (no se considera).

**RN-02 — Configuración inicial `televisor` v1 (configurable, a validar por el PO).**

| Atributo | Modo | Tolerancia | Obligatoriedad |
|---|---|---|---|
| `tamano_pulgadas` | EXACTO | — | OBLIGATORIO |
| `resolucion` | EXACTO | — | OBLIGATORIO |
| `tecnologia` | EXACTO | — | OBLIGATORIO |
| `smart` | EXACTO | — | OBLIGATORIO |
| `generacion` | TOLERANCIA | 1 año | SI_AMBOS_CONOCIDOS |
| `marca` | EXACTO | — | SI_AMBOS_CONOCIDOS |

**RN-03 — Piso no configurable (FR-040).** Para `televisor`: `tamano_pulgadas` y `resolucion` siempre son `OBLIGATORIO`; la tolerancia de tamaño (si se usa `TOLERANCIA`) no puede superar 1 pulgada. Un conjunto de reglas debe tener al menos 3 criterios `OBLIGATORIO`. Cualquier cambio que viole el piso se rechaza.

**RN-04 — Validaciones.** Se rechaza con "Configuración inválida: {detalle}": atributo inexistente o repetido; modo no reconocido; `TOLERANCIA` en un atributo no numérico; tolerancia negativa, nula en `TOLERANCIA` o informada en `EXACTO`; tolerancia de generación mayor a 3 años; justificación vacía o de menos de 10 caracteres ("la justificación es obligatoria (mínimo 10 caracteres)"); violación del piso ("{criterio} es un criterio núcleo y no puede relajarse por debajo del piso").

**RN-05 — Versionado.** Todo cambio aceptado crea una versión nueva (`version` + 1) que pasa a vigente; la anterior queda `vigente = no` con `fecha_fin`. Las versiones nunca se modifican ni se borran. Hay exactamente una versión vigente por categoría con reglas.

**RN-06 — Auditoría.** Cada intento de cambio, aceptado o rechazado, se registra con usuario, fecha y hora, categoría, valores anteriores y propuestos, justificación y resultado (aceptado / rechazado con motivo).

**RN-07 — Efecto prospectivo.** Una nueva versión no modifica los pares ya calculados: el siguiente emparejamiento recalcula con la versión vigente y deja los pares anteriores como `vigente = no`, cada uno con la versión de reglas con que se calculó.

**RN-08 — Categorías.** Las reglas se definen por categoría; nunca se aplican entre categorías distintas. Una categoría sin conjunto vigente no admite equivalencias (`SIN_REGLAS_EQUIVALENCIA`). Agregar una categoría es crear su conjunto de reglas (con su propio piso definido en esa configuración), sin cambios al modelo de datos.

### Interfaz

Sin interfaz gráfica obligatoria. Puede implementarse con archivo de configuración versionado, script o interfaz administrativa mínima, siempre que se apliquen las validaciones, el versionado y la auditoría. Los mensajes de rechazo se devuelven en la salida de la herramienta usada.

### Sistemas Externos (Si aplica)

No aplica.

---

## Contexto y Referencias

**Épica origen:** [Normalización y Emparejamiento de Televisores](../../../epicas.md#épica-003-normalización-y-emparejamiento-de-televisores)

**Exclusiones de la Épica:**
- NO incluye un catálogo maestro de fabricantes ni una integración con bases de datos de productos (GS1, fabricantes).
- NO incluye la equivalencia entre categorías distintas.
- NO incluye la estimación de precio por depreciación o antigüedad del modelo.

**Historias relacionadas:** HU-038 (usa estas reglas), HU-041 (verifica que no se usen criterios por debajo de los configurados).

---

## Supuestos

> Elementos inferidos por la IA que NO estaban explícitos en el PRD o la Épica. Todos los supuestos han sido resueltos: convertidos en reglas de negocio explícitas o eliminados mediante reformulación. Si aparece algún supuesto no resuelto, esta HU NO está lista para desarrollo.

- **S-01 (Resuelto → RN-02):** la configuración inicial de equivalencia (tamaño, resolución, tecnología y Smart obligatorios y exactos; generación ±1 año y marca solo si ambos se conocen) es una propuesta configurable que el PO debe validar; exigir tecnología puede reducir los equivalentes de SECOP II cuando el documento no la indica.
- **S-02 (Resuelto → RN-03):** se define un piso no configurable (tamaño y resolución obligatorios, tolerancia de tamaño ≤ 1", ≥ 3 criterios obligatorios) para que FR-040 no dependa solo de la disciplina operativa.
- **S-03 (Resuelto → RN-04, RN-07):** todo cambio exige justificación y se aplica solo hacia adelante con una versión nueva.

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
| 2026-10-02 | 1.0 | Historia generada desde Épica ÉPICA-003 | Juan Camilo (PO) |

---

> **Método Ceiba estimar hus** v6.1.95 | Modelo: claude-opus-5-5 | Usuario: Juan Camilo | Fecha: 2026-10-05
