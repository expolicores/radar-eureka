# Historia #046: Identificar y marcar precios sujetos a condiciones especiales

**Estado:** Borrador (PO)  
**Release:** Release MVP  
**Épica:** [Referencias de Mercado Trazables](../../../epicas.md#épica-004-referencias-de-mercado-trazables)  
**Feature:** Aplicar Reglas de Precio de Referencia  
**Prioridad:** Crítica  
**FRs relacionados:** FR-046

Escrita por el flujo generar-historias-usuario (Método Ceiba) — MVP propio, no comercial

---

## Historia de Usuario

**Como** Administrador de la plataforma,  
**Quiero** que el sistema identifique y marque los precios sujetos a tarjeta específica, cupón, financiación, membresía u otra condición especial,  
**Para** que esos precios no se traten como precio general de mercado y no generen referencias engañosamente bajas.

## Descripción

Las tiendas publican con frecuencia precios que solo obtiene un subconjunto de compradores (ej. precio con la tarjeta de crédito de la tienda, con cupón o con membresía). La Adenda 2 (A2.5) exige identificarlos y no tratarlos automáticamente como precio general de mercado. Esta HU define:

1. Cómo se registra la condición especial en carga manual.
2. Cómo la detecta la captura automática (mapeo por conector y lista configurable de palabras clave).
3. Qué pasa cuando conviven un precio general y uno condicionado, y cuando solo existe el condicionado.
4. Cómo se entrega la marca a los consumidores (la observación con condición especial queda con `apta_para_referencia = no`).

---

## Criterios de Aceptación

### Escenario 1: Carga manual de un precio general

- **Dado** que el Administrador registra una observación manual con `condicion_especial = ninguna`
- **Cuando** el sistema la guarda
- **Entonces** la observación queda con `apta_para_referencia = sí` y sin detalle de condición

### Escenario 2: Carga manual de un precio condicionado

- **Dado** que el Administrador registra una observación manual con `condicion_especial = membresia` y detalle "Precio para afiliados del programa de fidelización"
- **Cuando** el sistema la guarda
- **Entonces** queda guardada con `apta_para_referencia = no` y se entrega a los consumidores con la marca `"Precio sujeto a condición especial: membresía"`

### Escenario 3: Carga manual sin seleccionar condición o sin detalle

- **Dado** que el Administrador envía una observación manual sin `condicion_especial`, o con una condición distinta de `ninguna` sin detalle
- **Cuando** el sistema la valida
- **Entonces** no se guarda y se devuelve `"Campo obligatorio ausente: condicion_especial."` o `"Describa la condición especial (3 a 300 caracteres)."`, respectivamente

### Escenario 4: Captura con precio general y precio condicionado

- **Dado** que una página de Falabella publica un precio general de 2.099.900 COP y un precio de 1.899.900 COP rotulado "Precio CMR"
- **Cuando** la captura automática crea la observación
- **Entonces** la observación queda con `precio_efectivo = 2099900`, `condicion_especial = ninguna`, `apta_para_referencia = sí`, y en `precios_condicionados_evidencia` se guarda {precio 1899900, tipo `tarjeta_especifica`, rótulo "Precio CMR"}, que nunca se usa como referencia

### Escenario 5: Captura con solo precio condicionado

- **Dado** que una página publica únicamente un precio de 1.649.900 COP rotulado "Con cupón TVFEST"
- **Cuando** la captura automática crea la observación
- **Entonces** la observación queda con `precio_efectivo = 1649900`, `condicion_especial = cupon`, `condicion_especial_detalle = "Con cupón TVFEST"` y `apta_para_referencia = no`

### Escenario 6: Varias condiciones sobre el único precio

- **Dado** que el único precio publicado tiene el rótulo "Con tarjeta de la tienda y cupón"
- **Cuando** se detectan dos tipos de condición (`tarjeta_especifica` y `cupon`)
- **Entonces** la observación queda con `condicion_especial = otra`, `condicion_especial_detalle = "tarjeta_especifica, cupon: Con tarjeta de la tienda y cupón"` y `apta_para_referencia = no`

### Escenario 7: Texto de financiación fuera del rótulo del precio

- **Dado** que una página muestra un único precio general de 1.899.900 COP y, en otra parte de la página (fuera del rótulo del precio), el texto "Paga hasta en 12 cuotas"
- **Cuando** la captura automática evalúa condiciones
- **Entonces** no se marca condición especial: `condicion_especial = ninguna` y `apta_para_referencia = sí`

### Escenario 8: Cambio de la lista de palabras clave

- **Dado** que el Administrador agrega la palabra clave "Puntos Colombia" al tipo `membresia`
- **Cuando** guarda la configuración
- **Entonces** el cambio aplica solo a capturas posteriores, las observaciones existentes no cambian y queda registrado un evento con usuario, fecha y hora, valor anterior y nuevo

### Escenario 9: Usuario sin rol Administrador modifica la configuración

- **Dado** que un Analista intenta modificar la lista de palabras clave
- **Cuando** ejecuta la operación
- **Entonces** se rechaza con `"Operación permitida solo para el rol Administrador."`

---

## Información Recopilada

### Usuario y Contexto

- **Tipo de usuario:** Administrador (carga manual y configuración); los conectores aplican la detección automáticamente.
- **Permisos requeridos:** rol Administrador para cargar observaciones y modificar la configuración de palabras clave.
- **Valor de negocio:** evita referencias de mercado artificialmente bajas que esconderían o fabricarían señales.

### Reglas de Negocio

**RN-01 — Tipos de condición.** `condicion_especial` ∈ {`ninguna`, `tarjeta_especifica`, `cupon`, `financiacion`, `membresia`, `otra`}. Es obligatorio en toda observación. Si es distinto de `ninguna`, `condicion_especial_detalle` es obligatorio (3 a 300 caracteres). Mensajes: `"Campo obligatorio ausente: condicion_especial."`, `"condicion_especial no es un valor permitido."`, `"Describa la condición especial (3 a 300 caracteres)."`

**RN-02 — Carga manual.** El Administrador debe elegir explícitamente el tipo de condición, incluida `ninguna`; no hay valor por defecto. Las observaciones manuales condicionadas se guardan (sirven como evidencia) con `apta_para_referencia = no`.

**RN-03 — Detección automática.** Se evalúa **solo el rótulo o la descripción asociada a cada elemento de precio** de la oferta de la propia tienda (no el resto del texto de la página), en este orden:
1. **Mapeo del conector:** campos de precio que el conector de la fuente conoce como condicionados (ej. en Falabella, el precio asociado a la tarjeta CMR → `tarjeta_especifica`).
2. **Palabras clave configurables por tipo** (configuración inicial, editable por el Administrador):

| Tipo | Palabras clave iniciales |
|---|---|
| `tarjeta_especifica` | "con tarjeta", "tarjeta de crédito", "tarjeta de la tienda", "CMR", "Banco Falabella", "tarjeta Alkosto" |
| `cupon` | "cupón", "código promocional", "código de descuento" |
| `financiacion` | "a crédito", "financiado", "financiación", "precio a cuotas" |
| `membresia` | "membresía", "afiliado", "socio", "suscripción" |

La comparación ignora mayúsculas y tildes y busca la palabra o frase completa. Un precio sin coincidencias es general.

**RN-04 — Convivencia de precios.** Si existe al menos un precio general vigente de la propia tienda: `precio_efectivo` es el general (regla de precio efectivo: el menor precio general vigente), `condicion_especial = ninguna`, y cada precio condicionado se guarda en `precios_condicionados_evidencia` como lista de {precio en COP, tipo, rótulo leído (máximo 300 caracteres)}. Esa lista es solo evidencia y nunca se usa en cálculos.

**RN-05 — Solo precios condicionados.** Si no existe precio general: se guarda una observación con `precio_efectivo` = el menor precio condicionado, `condicion_especial` = su tipo y `condicion_especial_detalle` = su rótulo; `apta_para_referencia = no`. Si en el rótulo de ese precio se detectan dos o más tipos, `condicion_especial = otra` y el detalle tiene el formato `"{tipos separados por coma}: {rótulo}"` (truncado a 300 caracteres).

**RN-06 — Entrega a consumidores.** Toda observación con `condicion_especial` ≠ `ninguna` se entrega con `apta_para_referencia = no` y la marca `"Precio sujeto a condición especial: {tipo legible}"` (tarjeta específica, cupón, financiación, membresía u otra). Las observaciones condicionadas no se usan como precio general de mercado.

**RN-07 — Configuración.** Solo el Administrador edita la lista de palabras clave (por tipo, de 0 a 30 frases de 2 a 60 caracteres, sin duplicados ignorando mayúsculas y tildes; duplicado: `"La palabra clave {frase} ya existe en el tipo {tipo}."`; fuera de límites: `"Cada tipo admite hasta 30 palabras clave de 2 a 60 caracteres."`). Los cambios no son retroactivos y generan un evento auditable con usuario, fecha y hora, valor anterior y nuevo.

**RN-08 — Lenguaje.** Ninguna marca o mensaje usa los términos "sobreprecio", "corrupción", "fraude" ni "hallazgo fiscal".

### Interfaz

Sin pantalla propia (nota del Dominio 12 del PRD). En la carga manual el campo `condicion_especial` es una selección obligatoria con las seis opciones. La configuración de palabras clave se realiza por operación administrativa (interfaz mínima, comando o script).

### Sistemas Externos (Si aplica)

Rótulos de precio publicados por Alkosto y Falabella en los datos estructurados o elementos de precio de sus páginas de producto.

---

## Contexto y Referencias

**Épica origen:** [Referencias de Mercado Trazables](../../../epicas.md#épica-004-referencias-de-mercado-trazables)

**Exclusiones de la Épica:**
- NO incluye Mercado Libre ni Éxito como fuentes automáticas (Adenda 2); solo carga manual si el Administrador lo decide.
- NO incluye vendedores terceros de marketplace.
- NO incluye fuentes externas de precios históricos (archivos web, sitios de seguimiento).
- NO incluye evasión de CAPTCHA, bloqueos ni autenticación.
- NO incluye alertas de cambio de precio para usuarios.

**Historias relacionadas:** HU-042 (campo `apta_para_referencia`), HU-045 (precio efectivo), HU-047, HU-048, HU-049 (carga manual), HU-051, HU-052 (conectores que aplican la detección).

---

## Supuestos

> Elementos inferidos por la IA que NO estaban explícitos en el PRD o la Épica. Todos los supuestos han sido resueltos: convertidos en reglas de negocio explícitas o eliminados mediante reformulación. Si aparece algún supuesto no resuelto, esta HU NO está lista para desarrollo.

1. **Observación condicionada se guarda, pero no es apta:** marcar en lugar de descartar, para conservar evidencia. Resuelta (RN-05, RN-06).
2. **Palabras clave iniciales** definidas como configuración editable, evaluadas solo sobre el rótulo del precio para evitar falsos positivos por mensajes de financiación generales. Resuelta (RN-03).
3. **Varias condiciones** en un mismo precio se marcan como `otra` con detalle. Resuelta (RN-05).

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
