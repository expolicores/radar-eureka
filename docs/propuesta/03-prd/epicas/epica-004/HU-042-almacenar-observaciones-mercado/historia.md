# Historia #042: Almacenar observaciones de precio de mercado con registro mínimo trazable

**Estado:** Borrador (PO)  
**Release:** Release MVP  
**Épica:** [Referencias de Mercado Trazables](../../../epicas.md#épica-004-referencias-de-mercado-trazables)  
**Feature:** Gestionar Base de Observaciones de Mercado  
**Prioridad:** Crítica  
**FRs relacionados:** FR-041, FR-042, FR-049

Escrita por el flujo generar-historias-usuario (Método Ceiba) — MVP propio, no comercial

---

## Historia de Usuario

**Como** Administrador de la plataforma,  
**Quiero** que toda observación de precio retail, sin importar cómo se obtuvo, se guarde en una base propia con su registro mínimo completo y su método de adquisición,  
**Para** que el Benchmark 2 – Mercado use referencias trazables y auditables que no dependan de que exista una API comercial ni del proceso de comparación.

## Descripción

Esta HU construye la **base propia de observaciones de precio de mercado** (Adenda 2, A2.3): el repositorio único, independiente del motor de comparación, donde llegan las observaciones de todos los canales de adquisición (carga manual individual, búsqueda manual, carga por archivo y captura automática). Define:

1. El **catálogo de fuentes de mercado** y sus parámetros por fuente.
2. La **estructura del registro mínimo** de cada observación y sus validaciones comunes (las aplica cualquier canal antes de guardar).
3. Los **campos derivados** que consumen las demás épicas: `es_manual`, `etiqueta_origen` y `apta_para_referencia`.
4. La **independencia** de la base frente a la comparación: guardar una observación no requiere que exista un contrato con el que compararla, y recalcular benchmarks nunca modifica observaciones.

Los canales concretos de carga (HU-047, HU-048, HU-049) y de captura (HU-050 a HU-053) usan esta base; las reglas de vendedor (HU-044), precio efectivo (HU-045) y condiciones especiales (HU-046) llenan campos definidos aquí. La normalización del producto a esquema común pertenece a la épica de normalización y emparejamiento; esta HU guarda los atributos **tal como los publica la fuente**.

---

## Criterios de Aceptación

### Escenario 1: Guardar una observación con registro mínimo completo

- **Dado** que la fuente "Alkosto" existe en el catálogo con carga manual habilitada
- **Cuando** un canal de adquisición envía una observación con todos los campos obligatorios válidos (producto, marca, modelo, vendedor "Alkosto", precio efectivo 1899900 COP, referencia URL, fecha de observación de hoy, condición de IVA, evidencia y método `manual`)
- **Entonces** el sistema guarda la observación con un `id_observacion` único, `fecha_registro` del sistema, `estado = vigente`, `es_manual = sí`, `etiqueta_origen = "Observación manual"` y `apta_para_referencia = sí`, y devuelve el `id_observacion`

### Escenario 2: Rechazar una observación sin un campo obligatorio

- **Dado** que un canal envía una observación sin `modelo_referencia` (vacío o nulo)
- **Cuando** el sistema valida el registro mínimo
- **Entonces** la observación NO se guarda y se devuelve el error `"Campo obligatorio ausente: modelo_referencia."`; si faltan varios campos se devuelve un error por cada campo faltante, en el orden de la tabla de la regla RN-03

### Escenario 3: Rechazar valores con formato inválido

- **Dado** que un canal envía una observación con `precio_efectivo = 0`, `moneda = "USD"` o `fecha_observacion` en el futuro
- **Cuando** el sistema valida el registro mínimo
- **Entonces** la observación NO se guarda y se devuelve el mensaje definido en RN-03 para el campo inválido (ej. `"precio_efectivo debe ser un entero entre 1 y 999.999.999 COP."`, `"Solo se aceptan precios en COP."`, `"La fecha de observación no puede ser futura."`)

### Escenario 4: Rechazar un método de adquisición no permitido para la fuente

- **Dado** que la fuente "Éxito" está en el catálogo con `captura_automatica_permitida = no`
- **Cuando** llega una observación de "Éxito" con `metodo_adquisicion = extraccion_web`
- **Entonces** la observación NO se guarda y se devuelve `"El método extraccion_web no está permitido para la fuente Éxito."`

### Escenario 5: Rechazar una fuente inexistente, inactiva o de contratación pública

- **Dado** que llega una observación con `fuente = "TVEC"`, con una fuente que no existe en el catálogo o con una fuente que tiene la carga manual deshabilitada
- **Cuando** el sistema valida la fuente
- **Entonces** la observación NO se guarda y se devuelve, según el caso: `"TVEC y SECOP II son fuentes de contratación pública; no se registran como observaciones de mercado."`, `"La fuente {nombre} no existe en el catálogo de fuentes de mercado."` o `"La fuente {nombre} no está habilitada para el método {método}."`

### Escenario 6: Identificación explícita de observaciones manuales

- **Dado** que existen una observación con `metodo_adquisicion = manual` y otra con `metodo_adquisicion = sitemap_datos_estructurados`
- **Cuando** cualquier consumidor (comparación, evidencia de señal, consulta administrativa) lee las observaciones
- **Entonces** la manual se entrega con `es_manual = sí`, `etiqueta_origen = "Observación manual"` y el usuario que la registró, y la automática con `es_manual = no` y `etiqueta_origen = "Captura automática (sitemap_datos_estructurados)"`; ningún consumidor puede recibir una observación sin estos dos campos

### Escenario 7: Observación con condición especial queda guardada pero no apta

- **Dado** que una observación válida llega con `condicion_especial = tarjeta_especifica`
- **Cuando** el sistema la guarda
- **Entonces** queda con `estado = vigente` y `apta_para_referencia = no`, y se entrega a los consumidores con esa marca

### Escenario 8: La base es independiente de la comparación

- **Dado** que se guarda una observación de un modelo de televisor que no aparece en ningún contrato o ítem del sistema
- **Cuando** se consulta la base de observaciones
- **Entonces** la observación existe y es consultable; y **cuando** se recalcula cualquier benchmark, ningún campo de ninguna observación cambia

### Escenario 9: Registrar una nueva fuente de mercado solo para carga manual

- **Dado** que el Administrador registra en el catálogo la fuente "Ktronix" con al menos un nombre de vendedor aceptado ("Ktronix")
- **Cuando** guarda la configuración
- **Entonces** la fuente queda con `carga_manual_habilitada = sí` y `captura_automatica_permitida = no`, y queda registrado quién y cuándo la creó; si intenta guardarla sin ningún nombre de vendedor aceptado, se rechaza con `"Una fuente de mercado requiere al menos un nombre de vendedor aceptado."`

### Escenario 10: Usuario sin rol Administrador

- **Dado** que un usuario con rol Analista intenta registrar una observación o modificar el catálogo de fuentes
- **Cuando** ejecuta la operación
- **Entonces** el sistema la rechaza con `"Operación permitida solo para el rol Administrador."` y no guarda nada

### Escenario 11: Base vacía

- **Dado** que la base no tiene observaciones
- **Cuando** un consumidor solicita observaciones de cualquier producto
- **Entonces** recibe una lista vacía sin error (la ausencia de observaciones no es un error; la épica de señales la trata como "no disponible / evidencia insuficiente")

---

## Información Recopilada

### Usuario y Contexto

- **Tipo de usuario:** Administrador (en el MVP es el PO). Los canales automáticos escriben con la identidad técnica `conector:{fuente}`.
- **Permisos requeridos:** rol Administrador para registrar observaciones y modificar el catálogo de fuentes. Ningún otro rol escribe en la base.
- **Valor de negocio:** habilita el Benchmark 2 aunque la automatización sea parcial o nula y acumula desde el primer día el histórico propio de precios de mercado.

### Reglas de Negocio

**RN-01 — Base propia e independiente.** Las observaciones se guardan en una base propia, separada de los resultados de comparación. Ninguna operación de comparación, benchmark o señal puede crear, modificar ni eliminar observaciones; solo las leen. Una observación se guarda aunque no exista ningún contrato comparable.

**RN-02 — Catálogo de fuentes de mercado.** Cada fuente tiene: `nombre` (único, 2–60 caracteres, sin distinguir mayúsculas ni tildes), `rol` (`principal` | `secundaria` | `complementaria`), `carga_manual_habilitada` (sí/no), `captura_automatica_permitida` (sí/no; solo puede ser "sí" si existe un conector de captura para la fuente), `captura_automatica_habilitada` (sí/no; la gestiona HU-050), `vendedores_aceptados` (lista de 1 a 10 nombres, cada uno de 2–100 caracteres; obligatoria), `iva_por_defecto_captura` (`incluido` | `no_incluido` | `indeterminado`), `creada_por`, `fecha_creacion`, `modificada_por`, `fecha_modificacion`. Configuración inicial (configurable por el Administrador):

| Fuente | Rol | Carga manual | Captura automática permitida | Vendedores aceptados | IVA por defecto en captura |
|---|---|---|---|---|---|
| Alkosto | principal | sí | sí (conector HU-051) | Alkosto | indeterminado |
| Falabella | secundaria | sí | sí (conector HU-052) | Falabella | indeterminado |
| Éxito | complementaria | no | no | Éxito | indeterminado |
| Mercado Libre | complementaria | no | no | (vacía: debe configurarse antes de habilitar la carga manual) | indeterminado |

- Una fuente sin `vendedores_aceptados` no puede guardarse con carga manual habilitada: `"Una fuente de mercado requiere al menos un nombre de vendedor aceptado."`
- Éxito y Mercado Libre nunca pueden tener `captura_automatica_permitida = sí` en el MVP (exclusión de la épica); solo el Administrador puede habilitarles la carga manual. Intento: `"{fuente} no admite captura automática en el MVP; solo carga manual."`
- Una fuente sin conector de captura no puede tener `captura_automatica_permitida = sí`: `"La fuente {fuente} no tiene conector de captura automática."`
- Los nombres "SECOP II", "SECOP", "TVEC", "Tienda Virtual del Estado Colombiano" y "Colombia Compra Eficiente" están reservados: no se pueden registrar como fuente de mercado: `"TVEC y SECOP II son fuentes de contratación pública; no se registran como fuentes de mercado."`
- Nombre duplicado: `"Ya existe una fuente con el nombre {nombre}."`
- No se eliminan fuentes con observaciones; solo se deshabilitan. Deshabilitar una fuente no altera sus observaciones. Intento de eliminar: `"No se puede eliminar una fuente con observaciones; deshabilítela."`

**RN-03 — Registro mínimo y validaciones comunes.** Toda observación se valida campo a campo antes de guardarse. Si algún campo obligatorio falla, la observación completa se rechaza y se devuelven todos los errores encontrados:

| Campo | Obligatorio | Formato y límites | Mensaje de error |
|---|---|---|---|
| `fuente` | Sí | Nombre existente en el catálogo, habilitada para el método (RN-04) | Ver Escenario 5 |
| `producto_descripcion` | Sí | Texto de 3 a 300 caracteres, tal como lo publica la fuente | `"producto_descripcion debe tener entre 3 y 300 caracteres."` |
| `marca` | Sí | Texto de 1 a 60 caracteres | `"marca debe tener entre 1 y 60 caracteres."` |
| `modelo_referencia` | Sí | Texto de 2 a 60 caracteres, tal como lo publica la fuente (sin normalizar) | `"modelo_referencia debe tener entre 2 y 60 caracteres."` |
| `sku` | No | Texto de 1 a 64 caracteres | `"sku debe tener entre 1 y 64 caracteres."` |
| `ean_gtin` | No | Solo dígitos, longitud 8, 12, 13 o 14, con dígito de control GTIN válido | `"ean_gtin no es un GTIN válido."` |
| `tamano_pulgadas` | No | Número entre 10 y 120, máximo 1 decimal | `"tamano_pulgadas debe estar entre 10 y 120."` |
| `resolucion` | No | `HD` \| `Full HD` \| `4K UHD` \| `8K` \| `desconocida` | `"resolucion no es un valor permitido."` |
| `tecnologia_pantalla` | No | `LED` \| `QLED` \| `OLED` \| `Mini LED` \| `otra` \| `desconocida` | `"tecnologia_pantalla no es un valor permitido."` |
| `smart` | No | `sí` \| `no` \| `desconocido` | `"smart no es un valor permitido."` |
| `vendedor` | Sí | Texto de 1 a 100 caracteres (la regla de vendedor = la tienda la aplica HU-044) | `"vendedor debe tener entre 1 y 100 caracteres."` |
| `precio_efectivo` | Sí | Entero en COP, de 1 a 999.999.999, sin decimales | `"precio_efectivo debe ser un entero entre 1 y 999.999.999 COP."` |
| `moneda` | Sí | Solo `COP` | `"Solo se aceptan precios en COP."` |
| `precio_anterior` | No | Entero en COP mayor que `precio_efectivo` (detalle en HU-045); solo evidencia | Ver HU-045 |
| `condicion_especial` | Sí | `ninguna` \| `tarjeta_especifica` \| `cupon` \| `financiacion` \| `membresia` \| `otra` | `"condicion_especial no es un valor permitido."` |
| `condicion_especial_detalle` | Si `condicion_especial` ≠ `ninguna` | Texto de 3 a 300 caracteres | `"Describa la condición especial (3 a 300 caracteres)."` |
| `tipo_referencia` | Sí | `url` \| `texto` | `"tipo_referencia debe ser url o texto."` |
| `referencia_origen` | Sí | Si `url`: URL absoluta http o https de máximo 2.048 caracteres. Si `texto`: 5 a 300 caracteres (solo permitido con `metodo_adquisicion = manual`) | `"referencia_origen no es una URL http/https válida."` / `"La referencia de texto solo se admite en observaciones manuales."` |
| `fecha_observacion` | Sí | Fecha y hora ISO 8601 en hora de Colombia (UTC−5); no posterior al momento del registro | `"La fecha de observación no puede ser futura."` |
| `iva_condicion` | Sí | `incluido` \| `no_incluido` \| `indeterminado`. Nunca se infiere: si la fuente no lo indica, el valor es `indeterminado` | `"iva_condicion no es un valor permitido."` |
| `evidencia` | Sí | Al menos 1 archivo; se guarda copia, nombre, tipo, tamaño y hash SHA-256 | `"La observación requiere al menos una evidencia."` |
| `metodo_adquisicion` | Sí | `api` \| `dataset` \| `feed` \| `sitemap_datos_estructurados` \| `extraccion_web` \| `manual` | `"metodo_adquisicion no es un valor permitido."` |
| `canal_carga` | Sí | `individual` \| `busqueda` \| `archivo` (si método `manual`); `conector` (si método automático) | `"canal_carga no corresponde al método de adquisición."` |
| `registrado_por` | Sí | Identificador del usuario Administrador (manual) o `conector:{fuente}` (automático) | `"registrado_por es obligatorio."` |
| `id_contexto` | Sí | Identificador de la ejecución de captura, de la búsqueda manual o del lote de archivo; nulo solo si `canal_carga = individual` | `"id_contexto es obligatorio para el canal {canal}."` |
| `protocolo_busqueda` | Sí | `registrado` (canal `busqueda` o archivo agrupado), `no_registrado` (individual o archivo sin agrupar), `no_aplica` (automático) | `"protocolo_busqueda no corresponde al canal de carga."` |

Campos que asigna el sistema (no se reciben): `id_observacion` (identificador único e inmutable), `fecha_registro` (fecha y hora del servidor), `estado` (inicia en `vigente`; ver HU-043), `es_manual`, `etiqueta_origen`, `apta_para_referencia`.

**RN-04 — Fuente y método.** El método `manual` exige `carga_manual_habilitada = sí`. Cualquier método automático exige `captura_automatica_permitida = sí` y `captura_automatica_habilitada = sí`. `registrado_por` debe ser coherente: método `manual` → usuario con rol Administrador; método automático → `conector:{fuente}` de la misma fuente. Incoherencia: `"registrado_por no corresponde al método de adquisición ni a la fuente."`

**RN-05 — Identificación de observaciones manuales (FR-049).** `es_manual = sí` si y solo si `metodo_adquisicion = manual`. `etiqueta_origen` = `"Observación manual"` cuando es manual, o `"Captura automática ({metodo_adquisicion})"` en otro caso. Estos campos, junto con `registrado_por` y `fecha_registro`, forman parte obligatoria de toda entrega de una observación a cualquier consumidor (comparación, evidencia mostrada al Analista, consultas). Un dato manual nunca se presenta como automático.

**RN-06 — Aptitud para referencia.** `apta_para_referencia = sí` solo si `estado = vigente` **y** `condicion_especial = ninguna`. En cualquier otro caso es `no`. Los consumidores de la épica de señales solo usan como precio general de mercado las observaciones con `apta_para_referencia = sí`. El precio anterior nunca se usa como referencia.

**RN-07 — Evidencia.** Cada archivo de evidencia se guarda como copia propia (no solo como enlace) con su hash SHA-256; la observación conserva la evidencia aunque la página original cambie o desaparezca. La base de observaciones y sus evidencias forman parte del respaldo diario de la plataforma (NFR-DIS-003), porque no se pueden reconstruir desde las fuentes.

**RN-08 — Lenguaje.** Ningún mensaje o etiqueta de esta HU usa los términos "sobreprecio", "corrupción", "fraude" ni "hallazgo fiscal".

**RN-09 — Evento auditable.** Cada alta de observación y cada cambio del catálogo de fuentes genera un evento con tipo (`alta_observacion` | `cambio_catalogo_fuente`), usuario o conector, fecha y hora e identificador afectado, disponible para el log de auditoría de la plataforma.

### Interfaz

No requiere pantalla propia (nota de implementación del Dominio 12 del PRD). La escritura en la base y la configuración del catálogo se exponen como una operación administrativa (interfaz mínima, comando o script, a definir en arquitectura) que devuelve el `id_observacion` creado o la lista de errores con los mensajes de RN-03. Los canales de carga y captura de las HUs T403 a T412 invocan esta misma operación.

### Sistemas Externos (Si aplica)

No aplica directamente. Las fuentes externas (Alkosto, Falabella) se consultan en las HUs de captura automática.

---

## Contexto y Referencias

**Épica origen:** [Referencias de Mercado Trazables](../../../epicas.md#épica-004-referencias-de-mercado-trazables)

**Exclusiones de la Épica:**
- NO incluye Mercado Libre ni Éxito como fuentes automáticas (Adenda 2); solo carga manual si el Administrador lo decide.
- NO incluye vendedores terceros de marketplace.
- NO incluye fuentes externas de precios históricos (archivos web, sitios de seguimiento).
- NO incluye evasión de CAPTCHA, bloqueos ni autenticación.
- NO incluye alertas de cambio de precio para usuarios.

**Historias relacionadas:** HU-043 (histórico inmutable y anulación), HU-044 (vendedor = la tienda), HU-045 (precio efectivo), HU-046 (condiciones especiales), HU-047, HU-048, HU-049 (canales manuales), HU-050 a HU-053 (captura automática).

---

## Supuestos

> Elementos inferidos por la IA que NO estaban explícitos en el PRD o la Épica. Todos los supuestos han sido resueltos: convertidos en reglas de negocio explícitas o eliminados mediante reformulación. Si aparece algún supuesto no resuelto, esta HU NO está lista para desarrollo.

1. **Modelo obligatorio:** el registro mínimo "marca/modelo" se interpreta como ambos obligatorios; una observación sin modelo identificable no se guarda (RN-03). Resuelta.
2. **IVA nunca inferido:** la condición de IVA se registra solo si la fuente la indica; si no, `indeterminado`. El valor por defecto de captura por fuente es configurable con valor inicial `indeterminado`, hasta que el PO documente la verificación (D6: no verificado jurídicamente). Resuelta (RN-02, RN-03).
3. **Catálogo de fuentes:** Éxito y Mercado Libre se registran deshabilitados para carga manual y sin captura automática; el Administrador decide habilitar su carga manual. Resuelta (RN-02).
4. **Límites de formato** (longitudes, rango de precio 1–999.999.999 COP, tamaño 10–120 pulgadas, enumeraciones de resolución y tecnología): valores de diseño definidos en RN-03. Resuelta.
5. **Aptitud para referencia:** se modela como campo derivado que excluye observaciones anuladas o con condición especial. Resuelta (RN-06).

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
