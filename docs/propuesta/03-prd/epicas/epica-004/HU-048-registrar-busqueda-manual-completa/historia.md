# Historia #048: Registrar una búsqueda manual con todas las ofertas comparables y sus términos

**Estado:** Borrador (PO)  
**Release:** Release MVP  
**Épica:** [Referencias de Mercado Trazables](../../../epicas.md#épica-004-referencias-de-mercado-trazables)  
**Feature:** Cargar Observaciones Manual y Semiautomáticamente  
**Prioridad:** Crítica  
**FRs relacionados:** FR-051, FR-049, FR-050

Escrita por el flujo generar-historias-usuario (Método Ceiba) — MVP propio, no comercial

---

## Historia de Usuario

**Como** Administrador de la plataforma,  
**Quiero** registrar en una sola carga manual todas las ofertas comparables que encontré en una búsqueda, junto con los términos de búsqueda usados,  
**Para** evitar el sesgo de selección: que una referencia elegida a mano no fabrique ni esconda una señal por haber guardado solo la oferta más barata o la más cara.

## Descripción

D6 propuso, y el PRD adoptó (FR-051), un **protocolo contra el sesgo de selección** para la carga manual: registrar **todas** las ofertas comparables encontradas en una búsqueda, no solo una, junto con los términos usados. Esta HU implementa la **búsqueda manual** como una unidad de carga atómica:

- Encabezado de la búsqueda: fuente, producto buscado, términos usados, fecha y hora, número de resultados revisados, evidencia de la página de resultados y declaración de completitud.
- Lista de ofertas encontradas: cada una se registra como **observación** (con el mismo registro mínimo de la carga manual individual) o como **oferta descartada** con su motivo (ej. vendedor tercero, accesorio o combo).
- Las observaciones creadas quedan con `canal_carga = busqueda`, `protocolo_busqueda = registrado` y vinculadas a la búsqueda, de modo que cualquier consumidor pueda ver con qué términos se encontraron.

Una búsqueda sin ofertas comparables también se registra: es evidencia de que no se encontró referencia de mercado.

---

## Criterios de Aceptación

### Escenario 1: Registrar una búsqueda con varias ofertas

- **Dado** que el Administrador buscó en Alkosto "televisor samsung 55 4k" y revisó 12 resultados
- **Cuando** registra la búsqueda con esos términos, 12 resultados revisados, una captura de la página de resultados, la declaración de completitud marcada, 3 ofertas comparables completas y 1 oferta descartada por ser un combo
- **Entonces** el sistema crea la búsqueda con su `id_busqueda`, crea 3 observaciones con `metodo_adquisicion = manual`, `canal_carga = busqueda`, `protocolo_busqueda = registrado`, `id_contexto = id_busqueda` y `registrado_por` = el Administrador, guarda la oferta descartada con su motivo y responde `"Búsqueda registrada: {id_busqueda}. Observaciones creadas: 3. Ofertas descartadas: 1."`

### Escenario 2: Una oferta inválida rechaza toda la búsqueda

- **Dado** que una búsqueda contiene 4 ofertas y la tercera no tiene evidencia
- **Cuando** el Administrador la envía
- **Entonces** no se guarda ni la búsqueda ni ninguna observación, y se devuelven los errores identificados por oferta: `"Oferta 3: La observación requiere al menos una evidencia."`

### Escenario 3: Búsqueda sin ofertas comparables

- **Dado** que el Administrador buscó "LG OLED77C4PSA" en Falabella y no encontró ofertas comparables entre 5 resultados revisados
- **Cuando** registra la búsqueda con 0 ofertas
- **Entonces** se guarda la búsqueda con resultado "sin ofertas comparables" y 0 observaciones, y se responde `"Búsqueda registrada: {id_busqueda}. Observaciones creadas: 0. Ofertas descartadas: 0."`

### Escenario 4: Sin términos de búsqueda, sin evidencia de resultados o sin declaración

- **Dado** que el Administrador envía una búsqueda sin términos, sin la captura de la página de resultados o sin marcar la declaración de completitud
- **Cuando** el sistema valida
- **Entonces** no se guarda y se devuelve, según el caso, `"Registre al menos un término de búsqueda."`, `"Adjunte la evidencia de la página de resultados."` o `"Confirme que registró todas las ofertas comparables encontradas."`

### Escenario 5: Más ofertas que resultados revisados

- **Dado** que el Administrador indica 2 resultados revisados
- **Cuando** registra 3 ofertas (entre comparables y descartadas)
- **Entonces** no se guarda y se devuelve `"El número de ofertas registradas (3) no puede superar el total de resultados revisados (2)."`

### Escenario 6: Oferta descartada por vendedor tercero

- **Dado** que en la búsqueda de Falabella una oferta es de "ElectroMundo Store"
- **Cuando** el Administrador la registra como oferta descartada con motivo "vendedor tercero", su URL y su vendedor
- **Entonces** la oferta queda en la búsqueda como descartada, no se crea observación y su precio (si se registra) no se usa en ningún cálculo; si en cambio la registra como oferta comparable, se rechaza la búsqueda con `"Oferta {n}: Solo se aceptan observaciones cuyo vendedor sea directamente la tienda Falabella. Vendedor recibido: ElectroMundo Store."`

### Escenario 7: Dos ofertas con la misma URL

- **Dado** que dos ofertas de la misma búsqueda tienen la misma URL de producto
- **Cuando** el Administrador envía la búsqueda
- **Entonces** no se guarda y se devuelve `"Oferta {n}: Observación duplicada en la búsqueda: {url}."`

### Escenario 8: Consultar la búsqueda de origen de una observación

- **Dado** que existe una observación creada en una búsqueda
- **Cuando** cualquier consumidor la lee
- **Entonces** la observación incluye `etiqueta_origen = "Observación manual"`, `protocolo_busqueda = registrado`, el `id_busqueda`, los términos de búsqueda y el número de ofertas comparables y descartadas de esa búsqueda

### Escenario 9: Doble envío de la misma búsqueda

- **Dado** que el Administrador registró una búsqueda hace 2 minutos
- **Cuando** envía de nuevo la misma búsqueda (misma fuente, términos, fecha, ofertas y evidencias)
- **Entonces** no se crea nada y se devuelve `"Esta búsqueda ya fue registrada hace menos de 10 minutos ({id_busqueda})."`

### Escenario 10: Usuario sin rol Administrador

- **Dado** que un Analista intenta registrar una búsqueda
- **Cuando** envía la operación
- **Entonces** se rechaza con `"Operación permitida solo para el rol Administrador."`

---

## Información Recopilada

### Usuario y Contexto

- **Tipo de usuario:** Administrador (en el MVP, el PO).
- **Permisos requeridos:** rol Administrador autenticado para registrar y consultar búsquedas.
- **Valor de negocio:** referencias manuales defendibles ante el Analista y ante terceros: se ve qué se buscó y todo lo que se encontró.

### Reglas de Negocio

**RN-01 — Encabezado de la búsqueda.**

| Campo | Obligatorio | Formato y límites | Mensaje de error |
|---|---|---|---|
| Fuente | Sí | Fuente del catálogo con carga manual habilitada | `"La fuente {fuente} no está habilitada para el método manual."` |
| Producto buscado | Sí | 3 a 200 caracteres (ej. "Samsung 55 UN55DU7000") | `"Indique el producto buscado (3 a 200 caracteres)."` |
| Términos de búsqueda | Sí | 1 a 10 términos, cada uno de 2 a 200 caracteres, en el orden en que se usaron | `"Registre al menos un término de búsqueda."` / `"Cada término debe tener entre 2 y 200 caracteres (máximo 10 términos)."` |
| Fecha y hora de la búsqueda | Sí | Hora de Colombia; no futura; antigüedad máxima igual a la de la carga manual (inicial: 7 días, configurable) | `"La fecha de la búsqueda no puede ser futura."` / `"La fecha de la búsqueda no puede tener más de {N} días de antigüedad."` |
| Resultados revisados | Sí | Entero de 0 a 1.000 | `"Resultados revisados debe ser un entero entre 0 y 1.000."` |
| Evidencia de la página de resultados | Sí | 1 a 5 archivos PNG, JPG/JPEG o PDF de máximo 10 MB cada uno | `"Adjunte la evidencia de la página de resultados."` |
| Declaración de completitud | Sí | Marcada: "Registré todas las ofertas comparables encontradas, no solo la de mayor o menor precio" | `"Confirme que registró todas las ofertas comparables encontradas."` |
| Nota | No | Hasta 1.000 caracteres | `"La nota admite máximo 1.000 caracteres."` |

**RN-02 — Ofertas comparables.** De 0 a 50 ofertas por búsqueda. Cada oferta comparable tiene los mismos campos, validaciones y mensajes de la carga manual individual: descripción (3–300), marca (1–60), modelo (2–60), SKU y EAN opcionales (EAN con dígito de control válido), tamaño/resolución/tecnología/Smart opcionales, vendedor aceptado de la fuente, precio efectivo entero de 1 a 999.999.999 COP, precio anterior opcional mayor que el efectivo, condición especial obligatoria (con detalle si no es "ninguna"), referencia de origen (URL o texto), condición de IVA, 1 a 5 evidencias (PNG, JPG o PDF, ≤ 10 MB) y declaración de precio por unidad. La fecha de observación de cada oferta es la fecha de la búsqueda. Los errores se prefijan con `"Oferta {n}: "` (n = posición en la lista, desde 1).

**RN-03 — Ofertas descartadas.** De 0 a 50 por búsqueda. Campos: URL o referencia (obligatoria), vendedor (obligatorio, 1–100), precio observado (opcional, solo informativo), motivo (obligatorio): `vendedor_tercero` | `no_comparable` (accesorio, combo, otro producto o modelo distinto) | `sin_precio_visible` | `otro` (con detalle obligatorio de 3 a 300 caracteres). Las ofertas descartadas no son observaciones y no se usan en ningún cálculo. Motivo ausente: `"Oferta descartada {n}: indique el motivo de descarte."` Motivo `otro` sin detalle válido: `"Oferta descartada {n}: describa el motivo (3 a 300 caracteres)."`

**RN-04 — Consistencia de conteos.** (ofertas comparables + ofertas descartadas) ≤ resultados revisados. Si no se cumple: `"El número de ofertas registradas ({suma}) no puede superar el total de resultados revisados ({total})."`

**RN-05 — Atomicidad.** La búsqueda se valida completa. Si el encabezado o cualquier oferta tiene un error, no se guarda nada y se devuelven todos los errores encontrados. Si todo es válido, se guardan en una sola operación la búsqueda, sus ofertas descartadas y sus observaciones.

**RN-06 — Duplicados.** Dos ofertas (comparables o descartadas) de la misma búsqueda no pueden tener la misma URL: `"Oferta {n}: Observación duplicada en la búsqueda: {url}."` Doble envío: si el mismo usuario envía una búsqueda idéntica (fuente, términos, fecha, ofertas y hashes de evidencias) a otra registrada por él en los 10 minutos anteriores, no se crea nada: `"Esta búsqueda ya fue registrada hace menos de 10 minutos ({id_busqueda})."`

**RN-07 — Campos asignados por el sistema.** Búsqueda: `id_busqueda`, `registrada_por` (usuario autenticado; un valor enviado se ignora), `fecha_registro`, resultado (`con ofertas comparables` | `sin ofertas comparables`), conteos. Cada observación: `metodo_adquisicion = manual`, `canal_carga = busqueda`, `protocolo_busqueda = registrado`, `id_contexto = id_busqueda`, `registrado_por`, `es_manual = sí`, `etiqueta_origen = "Observación manual"`, `estado = vigente`, `apta_para_referencia` (sí solo si condición = ninguna).

**RN-08 — Inmutabilidad y entrega.** La búsqueda y sus ofertas descartadas no se modifican ni se eliminan. Si una observación de la búsqueda se anula, la búsqueda conserva el vínculo y muestra la observación como anulada. Toda entrega de una observación con `protocolo_busqueda = registrado` incluye `id_busqueda`, términos de búsqueda y conteos de la búsqueda.

**RN-09 — Consulta.** El Administrador puede consultar una búsqueda por `id_busqueda` (encabezado, evidencias, ofertas descartadas y observaciones con su estado) y listar búsquedas por fuente y rango de fechas, ordenadas por fecha descendente. Sin resultados: `"No hay búsquedas manuales para los filtros indicados."`

**RN-10 — Evento auditable.** Cada búsqueda registrada genera el evento `carga_manual_busqueda` con usuario, fecha y hora, `id_busqueda` y número de observaciones creadas.

### Interfaz

Puede implementarse como formulario administrativo mínimo con lista de ofertas o como comando/script que recibe un documento estructurado con el encabezado y las ofertas, más los archivos de evidencia (nota del Dominio 12 del PRD). En cualquier forma devuelve los mensajes definidos aquí.

### Sistemas Externos (Si aplica)

No hay integración: el Administrador busca en la tienda por su cuenta y registra lo encontrado.

---

## Contexto y Referencias

**Épica origen:** [Referencias de Mercado Trazables](../../../epicas.md#épica-004-referencias-de-mercado-trazables)

**Exclusiones de la Épica:**
- NO incluye Mercado Libre ni Éxito como fuentes automáticas (Adenda 2); solo carga manual si el Administrador lo decide.
- NO incluye vendedores terceros de marketplace.
- NO incluye fuentes externas de precios históricos (archivos web, sitios de seguimiento).
- NO incluye evasión de CAPTCHA, bloqueos ni autenticación.
- NO incluye alertas de cambio de precio para usuarios.

**Historias relacionadas:** HU-042 (base), HU-043 (anulación), HU-044 (vendedor), HU-045 (precio efectivo), HU-046 (condiciones especiales), HU-047 (carga individual), HU-049 (carga por archivo con agrupación por búsqueda).

---

## Supuestos

> Elementos inferidos por la IA que NO estaban explícitos en el PRD o la Épica. Todos los supuestos han sido resueltos: convertidos en reglas de negocio explícitas o eliminados mediante reformulación. Si aparece algún supuesto no resuelto, esta HU NO está lista para desarrollo.

1. **Búsqueda atómica:** todas las ofertas se aceptan o ninguna, para no romper la completitud del protocolo. Resuelta (RN-05).
2. **Registro de ofertas descartadas** (terceros, combos, otros productos) como parte del protocolo, sin convertirlas en observaciones. Resuelta (RN-03).
3. **Evidencia de la página de resultados y declaración de completitud** obligatorias. Resuelta (RN-01).
4. **Búsqueda sin ofertas** se registra como evidencia de ausencia de referencia. Resuelta (Escenario 3).
5. **Límites:** 1–10 términos, 0–50 ofertas por tipo, 0–1.000 resultados revisados. Resuelta (RN-01 a RN-03).

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
| 2026-10-02 | 1.0 | Historia generada desde Épica ÉPICA-004 | Juan Camilo (PO) |

---

> **Método Ceiba estimar hus** v6.1.95 | Modelo: claude-opus-5-5 | Usuario: Juan Camilo | Fecha: 2026-10-05
