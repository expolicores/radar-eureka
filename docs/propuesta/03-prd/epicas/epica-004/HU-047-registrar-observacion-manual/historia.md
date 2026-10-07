# Historia #047: Registrar manualmente una observación de precio con evidencia adjunta

**Estado:** Borrador (PO)  
**Release:** Release MVP  
**Épica:** [Referencias de Mercado Trazables](../../../epicas.md#épica-004-referencias-de-mercado-trazables)  
**Feature:** Cargar Observaciones Manual y Semiautomáticamente  
**Prioridad:** Crítica  
**FRs relacionados:** FR-048, FR-049, FR-050

Escrita por el flujo generar-historias-usuario (Método Ceiba) — MVP propio, no comercial

---

## Historia de Usuario

**Como** Administrador de la plataforma,  
**Quiero** registrar manualmente una observación de precio de mercado con su trazabilidad mínima y una evidencia adjunta (captura de pantalla o archivo),  
**Para** alimentar el Benchmark 2 aunque ninguna fuente retail esté automatizada, sin que un dato manual se presente nunca como automático.

## Descripción

La Adenda 2 establece que la **carga manual es válida** durante discovery/MVP, siempre que conserve trazabilidad y se identifique explícitamente como manual. Esta HU implementa el canal de **carga manual individual**: el Administrador registra una observación a la vez, con todos los campos del registro mínimo, al menos una evidencia y su usuario. La observación se guarda en la base propia de mercado con `metodo_adquisicion = manual`, `canal_carga = individual` y `protocolo_busqueda = no_registrado` (para registrar todas las ofertas de una búsqueda con sus términos se usa la búsqueda manual de HU-048).

Con este canal, el Benchmark 2 puede funcionar únicamente con observaciones cargadas a mano (criterio de aceptación de la épica).

---

## Criterios de Aceptación

### Escenario 1: Registro exitoso de una observación manual

- **Dado** que el Administrador está autenticado y la fuente Alkosto tiene la carga manual habilitada
- **Cuando** registra una observación con producto "Televisor Samsung 55 pulgadas Crystal UHD 4K Smart", marca Samsung, modelo UN55DU7000KXZL, vendedor Alkosto, precio efectivo 1.899.900 COP, URL del producto, fecha de observación de hoy, IVA "indeterminado", condición especial "ninguna", la declaración de precio por unidad marcada y una captura PNG de 450 KB
- **Entonces** el sistema guarda la observación con `metodo_adquisicion = manual`, `canal_carga = individual`, `registrado_por` = el usuario autenticado, `fecha_registro` del servidor, `es_manual = sí`, y responde `"Observación manual registrada: {id_observacion}."`

### Escenario 2: Registro sin evidencia

- **Dado** que el Administrador completa todos los campos
- **Cuando** no adjunta ninguna evidencia
- **Entonces** la observación no se guarda y se devuelve `"La observación requiere al menos una evidencia."`

### Escenario 3: Evidencia con formato, tamaño o contenido inválido

- **Dado** que el Administrador adjunta un archivo .docx, un PNG de 10,5 MB, un archivo de 0 bytes o un archivo con extensión .png cuyo contenido no es una imagen
- **Cuando** envía la observación
- **Entonces** no se guarda y se devuelve, según el caso, `"Formato de evidencia no permitido: use PNG, JPG o PDF."`, `"La evidencia supera el tamaño máximo de 10 MB."` o `"El archivo de evidencia está vacío o dañado."`

### Escenario 4: Fecha de observación fuera de la ventana permitida

- **Dado** que la antigüedad máxima configurada de una observación manual es 7 días
- **Cuando** el Administrador registra una observación con fecha de hace 8 días, o con fecha futura
- **Entonces** no se guarda y se devuelve `"La fecha de observación no puede tener más de 7 días de antigüedad."` o `"La fecha de observación no puede ser futura."`

### Escenario 5: Vendedor tercero o fuente no habilitada

- **Dado** que el Administrador registra una observación de Falabella con vendedor "TecnoImport SAS", o de Éxito (carga manual deshabilitada)
- **Cuando** envía la observación
- **Entonces** no se guarda y se devuelve `"Solo se aceptan observaciones cuyo vendedor sea directamente la tienda Falabella. Vendedor recibido: TecnoImport SAS."` o `"La fuente Éxito no está habilitada para el método manual."`

### Escenario 6: Sin declaración de precio por unidad

- **Dado** que el Administrador no marca la declaración "El precio corresponde a una unidad del televisor, sin combos ni accesorios"
- **Cuando** envía la observación
- **Entonces** no se guarda y se devuelve `"Confirme que el precio corresponde a una unidad del televisor, sin combos ni accesorios."`

### Escenario 7: Errores de varios campos a la vez

- **Dado** que el Administrador envía la observación sin marca, con precio efectivo "1.899.900,50" y con un EAN de 12 dígitos con dígito de control erróneo
- **Cuando** el sistema valida
- **Entonces** no se guarda y se devuelven todos los errores juntos: `"Campo obligatorio ausente: marca."`, `"precio_efectivo debe ser un entero entre 1 y 999.999.999 COP."`, `"ean_gtin no es un GTIN válido."`

### Escenario 8: Doble envío

- **Dado** que el Administrador registró una observación hace 3 minutos
- **Cuando** envía de nuevo exactamente los mismos datos y la misma evidencia (mismo hash)
- **Entonces** no se crea una segunda observación y se devuelve `"Esta observación ya fue registrada hace menos de 10 minutos ({id_observacion})."`

### Escenario 9: Identificación como manual ante el Analista

- **Dado** que existe una observación manual registrada por el Administrador
- **Cuando** se entrega a cualquier consumidor o vista de evidencia
- **Entonces** se entrega con la etiqueta `"Observación manual"`, `fecha_registro` y `registrado_por`; ninguna vista puede mostrarla sin la etiqueta

### Escenario 10: Usuario sin rol Administrador

- **Dado** que un Analista intenta registrar una observación manual
- **Cuando** envía la operación
- **Entonces** se rechaza con `"Operación permitida solo para el rol Administrador."`

---

## Información Recopilada

### Usuario y Contexto

- **Tipo de usuario:** Administrador (en el MVP, el PO).
- **Permisos requeridos:** rol Administrador autenticado.
- **Valor de negocio:** el Benchmark 2 deja de depender de la automatización; cada referencia manual queda auditable.

### Reglas de Negocio

**RN-01 — Campos del formulario.** El Administrador ingresa:

| Campo | Obligatorio | Formato y límites |
|---|---|---|
| Fuente | Sí | Fuente del catálogo con carga manual habilitada (inicial: Alkosto, Falabella) |
| Descripción del producto | Sí | 3 a 300 caracteres, tal como la publica la tienda |
| Marca | Sí | 1 a 60 caracteres |
| Modelo / referencia | Sí | 2 a 60 caracteres, tal como lo publica la tienda |
| SKU | No | 1 a 64 caracteres |
| EAN/GTIN | No | 8, 12, 13 o 14 dígitos con dígito de control válido |
| Tamaño (pulgadas) | No | 10 a 120, máximo 1 decimal |
| Resolución | No | HD, Full HD, 4K UHD, 8K, desconocida |
| Tecnología de pantalla | No | LED, QLED, OLED, Mini LED, otra, desconocida |
| Smart | No | sí, no, desconocido |
| Vendedor | Sí | 1 a 100 caracteres; debe ser un vendedor aceptado de la fuente |
| Precio efectivo (COP) | Sí | Entero de 1 a 999.999.999, sin puntos, comas ni símbolo |
| Precio anterior (COP) | No | Entero mayor que el precio efectivo; solo evidencia |
| Condición especial | Sí | ninguna, tarjeta específica, cupón, financiación, membresía, otra (sin valor por defecto) |
| Detalle de la condición | Si condición ≠ ninguna | 3 a 300 caracteres |
| Referencia de origen | Sí | URL http/https de hasta 2.048 caracteres, o texto de 5 a 300 caracteres si no existe URL (ej. catálogo impreso) |
| Fecha y hora de observación | Sí | Hora de Colombia; no futura; antigüedad máxima configurable (inicial: 7 días) |
| Condición de IVA | Sí | incluido, no incluido, indeterminado (elegir "indeterminado" si la tienda no lo indica) |
| Evidencias | Sí | 1 a 5 archivos PNG, JPG/JPEG o PDF, máximo 10 MB cada uno (configurable) |
| Declaración de precio por unidad | Sí | Debe estar marcada |

Campos que asigna el sistema: `metodo_adquisicion = manual`, `canal_carga = individual`, `protocolo_busqueda = no_registrado`, `id_contexto` nulo, `registrado_por` = usuario autenticado (no editable), `fecha_registro`, `estado = vigente`, `es_manual = sí`, `etiqueta_origen = "Observación manual"`, `apta_para_referencia` (sí solo si condición = ninguna), `vendedor_es_tienda = sí`.

**RN-02 — Validaciones y mensajes.** Se validan todos los campos y se devuelven todos los errores juntos. Mensajes: campo faltante `"Campo obligatorio ausente: {campo}."`; precio `"precio_efectivo debe ser un entero entre 1 y 999.999.999 COP."`; precio anterior `"El precio anterior debe ser mayor que el precio efectivo."`; EAN `"ean_gtin no es un GTIN válido."`; tamaño `"tamano_pulgadas debe estar entre 10 y 120."`; URL `"referencia_origen no es una URL http/https válida."`; fecha futura `"La fecha de observación no puede ser futura."`; antigüedad `"La fecha de observación no puede tener más de {N} días de antigüedad."`; vendedor `"Solo se aceptan observaciones cuyo vendedor sea directamente la tienda {fuente}. Vendedor recibido: {vendedor}."`; fuente `"La fuente {fuente} no está habilitada para el método manual."`; condición sin detalle `"Describa la condición especial (3 a 300 caracteres)."`; declaración `"Confirme que el precio corresponde a una unidad del televisor, sin combos ni accesorios."`

**RN-03 — Evidencia.** Se verifica el tipo real del contenido (no solo la extensión). Formatos permitidos: PNG, JPG/JPEG y PDF. Tamaño máximo por archivo: 10 MB (configurable); máximo 5 archivos. Se guarda copia propia de cada archivo con nombre original, tipo, tamaño, fecha de carga y hash SHA-256. Mensajes: `"Formato de evidencia no permitido: use PNG, JPG o PDF."`, `"La evidencia supera el tamaño máximo de 10 MB."`, `"El archivo de evidencia está vacío o dañado."`, `"Se admiten máximo 5 evidencias por observación."`

**RN-04 — Usuario que registra (FR-050).** `registrado_por` se toma de la sesión autenticada y no puede modificarse; si la operación recibe un valor de `registrado_por`, se ignora y se usa el usuario de la sesión.

**RN-05 — Identificación como manual (FR-049).** La observación se marca `es_manual = sí` y `etiqueta_origen = "Observación manual"` de forma permanente. Toda vista o entrega de la observación incluye la etiqueta; las vistas dirigidas al Analista muestran como mínimo `"Observación manual"` y la fecha de registro; la identidad del usuario que registró está disponible para el Administrador.

**RN-06 — Doble envío.** Si el mismo usuario envía una observación con valores idénticos en todos los campos ingresados y evidencias con los mismos hashes que otra registrada por él en los 10 minutos anteriores, no se crea una nueva y se devuelve `"Esta observación ya fue registrada hace menos de 10 minutos ({id_observacion})."`

**RN-07 — Evento auditable.** Cada registro genera el evento `carga_manual_observacion` con usuario, fecha y hora e `id_observacion`, disponible para el log de auditoría de la plataforma.

**RN-08 — Lenguaje.** Ningún texto usa "sobreprecio", "corrupción", "fraude" ni "hallazgo fiscal".

### Interfaz

Puede implementarse como formulario administrativo mínimo o como comando/script que recibe los campos y las rutas de los archivos (nota del Dominio 12 del PRD). En cualquier forma: permite ingresar los campos de RN-01, adjuntar las evidencias, muestra todos los errores juntos sin perder lo ingresado (en formulario) y, al guardar, muestra `"Observación manual registrada: {id_observacion}."`

### Sistemas Externos (Si aplica)

No hay integración: el Administrador consulta la tienda por su cuenta y adjunta la evidencia.

---

## Contexto y Referencias

**Épica origen:** [Referencias de Mercado Trazables](../../../epicas.md#épica-004-referencias-de-mercado-trazables)

**Exclusiones de la Épica:**
- NO incluye Mercado Libre ni Éxito como fuentes automáticas (Adenda 2); solo carga manual si el Administrador lo decide.
- NO incluye vendedores terceros de marketplace.
- NO incluye fuentes externas de precios históricos (archivos web, sitios de seguimiento).
- NO incluye evasión de CAPTCHA, bloqueos ni autenticación.
- NO incluye alertas de cambio de precio para usuarios.

**Historias relacionadas:** HU-042 (base y registro mínimo), HU-043 (corrección por anulación), HU-044 (vendedor), HU-045 (precio efectivo), HU-046 (condiciones especiales), HU-048 (búsqueda manual con todas las ofertas).

---

## Supuestos

> Elementos inferidos por la IA que NO estaban explícitos en el PRD o la Épica. Todos los supuestos han sido resueltos: convertidos en reglas de negocio explícitas o eliminados mediante reformulación. Si aparece algún supuesto no resuelto, esta HU NO está lista para desarrollo.

1. **Antigüedad máxima de la observación manual:** 7 días configurables, para que la carga manual no se convierta en una fuente de precios históricos externos (excluida). Resuelta (RN-01, RN-02).
2. **Evidencia:** PNG, JPG o PDF, 1 a 5 archivos de máximo 10 MB cada uno (configurable). Resuelta (RN-03).
3. **Declaración de precio por unidad** obligatoria para excluir combos y paquetes. Resuelta (RN-01).
4. **Protección ante doble envío** de 10 minutos. Resuelta (RN-06).
5. **Visibilidad de la identidad del registrador:** el Analista ve la etiqueta "Observación manual" y la fecha; la identidad del usuario está disponible para el Administrador. Resuelta (RN-05).

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
