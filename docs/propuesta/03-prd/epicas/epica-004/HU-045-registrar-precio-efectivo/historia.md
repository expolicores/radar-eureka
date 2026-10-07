# Historia #045: Usar el precio efectivo de venta y conservar el precio anterior solo como evidencia

**Estado:** Borrador (PO)  
**Release:** Release MVP  
**Épica:** [Referencias de Mercado Trazables](../../../epicas.md#épica-004-referencias-de-mercado-trazables)  
**Feature:** Aplicar Reglas de Precio de Referencia  
**Prioridad:** Crítica  
**FRs relacionados:** FR-045

Escrita por el flujo generar-historias-usuario (Método Ceiba) — MVP propio, no comercial

---

## Historia de Usuario

**Como** Administrador de la plataforma,  
**Quiero** que cada observación tome como precio de referencia el precio efectivo de venta al consumidor y guarde el precio tachado o anterior solo como evidencia,  
**Para** que las referencias de mercado reflejen lo que realmente se paga y no precios "antes" inflados que distorsionen la comparación.

## Descripción

Las tiendas suelen publicar un precio vigente y un precio "antes", tachado o "normal" que suele estar inflado (D6: COP 1.739.900 frente a 4.200.000 en una muestra). La Adenda 2 (A2.5) decide que la referencia es el **precio efectivo de venta disponible al consumidor en la fecha de captura**. Esta HU define cómo se determina `precio_efectivo` y cómo se guarda `precio_anterior` en todos los canales (manual individual, búsqueda manual, archivo y captura automática). El tratamiento de precios con condiciones especiales (tarjeta, cupón, financiación, membresía) se detalla en HU-046; aquí solo se establece que un precio condicionado nunca es el precio efectivo general mientras exista un precio sin condición.

---

## Criterios de Aceptación

### Escenario 1: Página con precio vigente y precio anterior

- **Dado** que una página de la tienda publica precio vigente 1.739.900 COP y precio "antes" 4.200.000 COP, ambos de la propia tienda y sin condiciones
- **Cuando** se crea la observación
- **Entonces** queda `precio_efectivo = 1739900` y `precio_anterior = 4200000` marcado como "solo evidencia"

### Escenario 2: Página solo con precio vigente

- **Dado** que la página publica únicamente el precio vigente 1.899.900 COP
- **Cuando** se crea la observación
- **Entonces** queda `precio_efectivo = 1899900` y `precio_anterior` nulo

### Escenario 3: Página con varios precios vigentes sin condición

- **Dado** que la tienda publica, para el mismo producto y sin condición especial, un "precio internet" de 2.049.900 COP y un "precio normal" de 2.199.900 COP no rotulado como tachado
- **Cuando** se crea la observación
- **Entonces** `precio_efectivo = 2049900` (el menor precio general vigente) y `precio_anterior = 2199900`

### Escenario 4: Precio anterior inconsistente en carga manual

- **Dado** que el Administrador registra manualmente `precio_efectivo = 1899900` y `precio_anterior = 1899900` (o menor)
- **Cuando** el sistema valida la observación
- **Entonces** la observación NO se guarda y se devuelve `"El precio anterior debe ser mayor que el precio efectivo."`

### Escenario 5: Precio anterior inconsistente en captura automática

- **Dado** que la captura lee `precio_efectivo = 1899900` y un precio anterior de 1.799.900 COP
- **Cuando** se crea la observación
- **Entonces** la observación se guarda con `precio_anterior` nulo y la ejecución registra la advertencia `precio_anterior_inconsistente` con la URL y ambos valores leídos

### Escenario 6: Solo existe precio anterior o tachado

- **Dado** que la captura lee una página donde solo aparece un precio rotulado como "antes" o tachado, sin precio vigente (ej. producto agotado)
- **Cuando** se procesa la página
- **Entonces** no se crea observación y la ejecución registra un descarte con motivo `sin_precio_vigente` y la URL

### Escenario 7: El precio anterior nunca se usa como referencia

- **Dado** que existe una observación con `precio_efectivo = 1739900` y `precio_anterior = 4200000`
- **Cuando** cualquier consumidor (comparación, benchmark, evidencia) lee la observación
- **Entonces** el valor de referencia entregado es 1.739.900 COP y el precio anterior se entrega rotulado como `"Precio anterior (solo evidencia)"`

### Escenario 8: Precio condicionado junto a precio general

- **Dado** que la página publica un precio general de 2.099.900 COP y un precio de 1.899.900 COP exclusivo con una tarjeta de la tienda
- **Cuando** se crea la observación
- **Entonces** `precio_efectivo = 2099900`; el precio de 1.899.900 COP no se usa como precio efectivo ni como precio anterior (su registro como evidencia se rige por HU-046)

---

## Información Recopilada

### Usuario y Contexto

- **Tipo de usuario:** Administrador (carga manual); los conectores de captura aplican la regla automáticamente.
- **Permisos requeridos:** los mismos de cada canal de carga (rol Administrador para canales manuales).
- **Valor de negocio:** referencias de mercado realistas que no inflan ni ocultan desviaciones.

### Reglas de Negocio

**RN-01 — Definición de precio efectivo.** `precio_efectivo` es el precio vigente de venta de **una unidad** del televisor, ofrecido por la propia tienda a **cualquier consumidor**, sin condición especial, en la fecha y hora de la observación, en COP con impuestos tal como los publica la tienda. No incluye costos de envío, instalación ni accesorios publicados por separado.

**RN-02 — Clasificación de precios publicados.** Cada precio que publica la fuente para la oferta de la propia tienda se clasifica como:
- **Vigente general:** precio actual sin condición (ej. `price` de la oferta en los datos estructurados, "precio internet", "precio oferta").
- **Anterior:** rotulado como "antes", "normal", "de lista", "tachado" o equivalente, o publicado como precio de lista frente a uno de oferta.
- **Condicionado:** sujeto a tarjeta específica, cupón, financiación, membresía u otra condición (HU-046).

**RN-03 — Selección.** `precio_efectivo` = el **menor** precio vigente general de la propia tienda. Si hay más de un precio vigente general, los mayores no rotulados como anteriores se tratan como anterior y el mayor de ellos queda como `precio_anterior` (Escenario 3). Si no hay ningún precio vigente general: (a) si existe un precio condicionado, se aplica HU-046; (b) si solo hay precio anterior, no se crea observación (descarte `sin_precio_vigente` en captura; en canales manuales `precio_efectivo` es obligatorio y aplica `"Campo obligatorio ausente: precio_efectivo."`).

**RN-04 — Precio anterior.** Opcional. Entero en COP de 1 a 999.999.999 y estrictamente mayor que `precio_efectivo`. Si es menor o igual: en canales manuales se rechaza la observación con `"El precio anterior debe ser mayor que el precio efectivo."` (en archivo, asociado a la fila y la columna `precio_anterior`); en captura automática la observación se guarda con `precio_anterior` nulo y se registra la advertencia `precio_anterior_inconsistente` (URL, precio efectivo y precio anterior leídos).

**RN-05 — Uso.** El único valor de referencia de una observación es `precio_efectivo`. `precio_anterior` se entrega a cualquier consumidor con la etiqueta `"Precio anterior (solo evidencia)"` y nunca participa en medianas, desviaciones, umbrales ni señales.

**RN-06 — Formato de lectura automática.** Los precios leídos de la fuente se convierten a entero COP eliminando símbolos de moneda y separadores de miles ("$ 1.739.900" → 1739900). Si un precio leído tiene centavos distintos de cero, se redondea al peso más cercano y se registra la advertencia `precio_con_decimales`. Si un precio leído no se puede interpretar como número, se trata como ausente y se registra la advertencia `precio_no_interpretable`.

**RN-07 — Lenguaje.** Ninguna etiqueta o mensaje usa los términos "sobreprecio", "corrupción", "fraude" ni "hallazgo fiscal".

### Interfaz

Sin pantalla propia (nota del Dominio 12 del PRD). En los canales manuales, el campo `precio_efectivo` se describe como "Precio vigente que paga cualquier comprador por una unidad, sin tarjeta, cupón, financiación ni membresía", y `precio_anterior` como "Precio antes o tachado (opcional, solo evidencia)".

### Sistemas Externos (Si aplica)

Precios publicados por Alkosto y Falabella en sus datos estructurados de producto (captura automática) o vistos por el Administrador en la tienda (carga manual).

---

## Contexto y Referencias

**Épica origen:** [Referencias de Mercado Trazables](../../../epicas.md#épica-004-referencias-de-mercado-trazables)

**Exclusiones de la Épica:**
- NO incluye Mercado Libre ni Éxito como fuentes automáticas (Adenda 2); solo carga manual si el Administrador lo decide.
- NO incluye vendedores terceros de marketplace.
- NO incluye fuentes externas de precios históricos (archivos web, sitios de seguimiento).
- NO incluye evasión de CAPTCHA, bloqueos ni autenticación.
- NO incluye alertas de cambio de precio para usuarios.

**Historias relacionadas:** HU-042 (registro mínimo), HU-044 (solo ofertas de la propia tienda), HU-046 (precios condicionados), HU-047, HU-048, HU-049, HU-051, HU-052 (canales que aplican la regla).

---

## Supuestos

> Elementos inferidos por la IA que NO estaban explícitos en el PRD o la Épica. Todos los supuestos han sido resueltos: convertidos en reglas de negocio explícitas o eliminados mediante reformulación. Si aparece algún supuesto no resuelto, esta HU NO está lista para desarrollo.

1. **Varios precios generales vigentes:** se toma el menor como efectivo y el mayor como anterior. Resuelta (RN-03).
2. **Precio anterior inconsistente:** rechazo en canales manuales; se omite con advertencia en captura automática. Resuelta (RN-04).
3. **Precio por unidad sin envío ni instalación:** el precio efectivo corresponde a una unidad del televisor, sin costos adicionales publicados por separado. Resuelta (RN-01).
4. **Redondeo de centavos** al peso más cercano con advertencia. Resuelta (RN-06).

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
