# Historia #043: Conservar el histórico inmutable de observaciones de mercado

**Estado:** Borrador (PO)  
**Release:** Release MVP  
**Épica:** [Referencias de Mercado Trazables](../../../epicas.md#épica-004-referencias-de-mercado-trazables)  
**Feature:** Gestionar Base de Observaciones de Mercado  
**Prioridad:** Crítica  
**FRs relacionados:** FR-053

Escrita por el flujo generar-historias-usuario (Método Ceiba) — MVP propio, no comercial

---

## Historia de Usuario

**Como** Administrador de la plataforma,  
**Quiero** que las observaciones de precio de mercado nunca se sobrescriban ni se borren, y que los errores se traten con anulación y corrección trazables,  
**Para** construir un histórico propio de precios de mercado que permita reproducir y auditar cualquier comparación pasada.

## Descripción

Las tiendas publican solo el precio actual y retiran los modelos descontinuados (D6); por eso el histórico de precios de mercado solo existe si el sistema lo guarda desde el primer día. Esta HU garantiza que la base propia de observaciones (creada en HU-042) sea **de solo inserción**:

- Cada nueva captura o carga del mismo producto crea una **nueva observación**; nunca actualiza una anterior.
- No existen operaciones de edición ni de borrado de observaciones.
- Un error se gestiona **anulando** la observación (con motivo) y, si corresponde, registrando una **observación de corrección** vinculada a la original.
- El Administrador puede **consultar el histórico** de un producto con todas sus observaciones, incluidas las anuladas.

---

## Criterios de Aceptación

### Escenario 1: Una nueva observación del mismo producto no reemplaza la anterior

- **Dado** que existe la observación OBS-1 de Alkosto para Samsung UN55DU7000KXZL a 1.899.900 COP del 2026-09-25
- **Cuando** se registra otra observación del mismo producto, fuente y URL a 1.799.900 COP el 2026-10-02
- **Entonces** existen dos observaciones independientes con sus propios identificadores, fechas y evidencias, y OBS-1 conserva todos sus valores originales

### Escenario 2: Intento de modificar una observación

- **Dado** que existe una observación vigente
- **Cuando** cualquier usuario o proceso intenta cambiar alguno de sus campos
- **Entonces** el sistema rechaza la operación con `"Las observaciones no se modifican. Para corregir, anule la observación y registre una nueva."` y la observación queda igual

### Escenario 3: Intento de eliminar una observación

- **Dado** que existe una observación (vigente o anulada)
- **Cuando** cualquier usuario o proceso intenta eliminarla
- **Entonces** el sistema rechaza la operación con `"Las observaciones no se eliminan; solo pueden anularse."`

### Escenario 4: Anular una observación con motivo

- **Dado** que existe la observación vigente OBS-2 registrada con un precio digitado por error
- **Cuando** el Administrador la anula con el motivo "Precio digitado con un cero de más; ver captura"
- **Entonces** OBS-2 queda con `estado = anulada`, `apta_para_referencia = no`, `motivo_anulacion`, `anulada_por` y `fecha_anulacion`, conserva todos sus demás campos y su evidencia, y sigue apareciendo en el histórico

### Escenario 5: Anulación sin motivo válido

- **Dado** que el Administrador intenta anular una observación
- **Cuando** el motivo está vacío, tiene menos de 10 caracteres o más de 500
- **Entonces** se rechaza con `"El motivo de anulación debe tener entre 10 y 500 caracteres."` y la observación sigue vigente

### Escenario 6: Anular una observación ya anulada o revertir una anulación

- **Dado** que OBS-2 ya está anulada
- **Cuando** el Administrador intenta anularla de nuevo, o intenta devolverla a `vigente`
- **Entonces** se rechaza con `"La observación OBS-2 ya está anulada."` o con `"Una anulación no se revierte; registre una nueva observación."`, respectivamente, sin crear eventos adicionales

### Escenario 7: Corregir una observación

- **Dado** que existe la observación vigente OBS-3 con `modelo_referencia = "UN55DU700KXZL"` (falta un cero)
- **Cuando** el Administrador ejecuta la corrección de OBS-3 con motivo y con los datos completos de la nueva observación (`modelo_referencia = "UN55DU7000KXZL"`)
- **Entonces**, en una sola operación, OBS-3 queda anulada con el motivo indicado y se crea OBS-4 con `corrige_a = OBS-3`; OBS-3 muestra `corregida_por = OBS-4`

### Escenario 8: Corrección con datos inválidos

- **Dado** que el Administrador corrige OBS-3 pero la nueva observación incumple el registro mínimo (ej. sin evidencia)
- **Cuando** ejecuta la corrección
- **Entonces** la operación completa se rechaza con los errores del registro mínimo, OBS-3 sigue vigente y no se crea ninguna observación nueva

### Escenario 9: Corregir una observación ya anulada

- **Dado** que OBS-2 está anulada
- **Cuando** el Administrador intenta corregirla
- **Entonces** se rechaza con `"Solo se pueden corregir observaciones vigentes."`

### Escenario 10: Consultar el histórico de un producto

- **Dado** que existen 6 observaciones de Samsung UN55DU7000KXZL (4 de Alkosto, 2 de Falabella, una de ellas anulada)
- **Cuando** el Administrador consulta el histórico por marca "samsung" y modelo "un55du7000-kxzl" con "incluir anuladas = sí"
- **Entonces** recibe las 6 observaciones ordenadas por `fecha_observacion` descendente, cada una con fuente, precio efectivo, fecha, `etiqueta_origen`, estado, vínculos `corrige_a` / `corregida_por` y acceso a su evidencia; con "incluir anuladas = no" recibe 5

### Escenario 11: Consulta del histórico sin resultados

- **Dado** que no hay observaciones del modelo LG OLED77C4PSA
- **Cuando** el Administrador consulta su histórico
- **Entonces** recibe una lista vacía con el mensaje `"No hay observaciones de mercado para los filtros indicados."`

### Escenario 12: Usuario sin rol Administrador

- **Dado** que un usuario con rol Analista intenta anular, corregir o consultar directamente el histórico
- **Cuando** ejecuta la operación
- **Entonces** se rechaza con `"Operación permitida solo para el rol Administrador."`

---

## Información Recopilada

### Usuario y Contexto

- **Tipo de usuario:** Administrador (en el MVP, el PO).
- **Permisos requeridos:** rol Administrador para anular, corregir y consultar el histórico. Las épicas de comparación y señales leen observaciones, pero no pueden anularlas ni corregirlas.
- **Valor de negocio:** histórico propio de precios de mercado, reproducible y auditable, que el mercado no publica.

### Reglas de Negocio

**RN-01 — Solo inserción.** La base de observaciones solo admite altas. No existe ninguna operación de actualización de campos de una observación, salvo los campos de anulación de RN-03 y el vínculo `corregida_por` de RN-04. No existe operación de borrado físico ni lógico distinta de la anulación.

**RN-02 — Repetición de observaciones.** Cada captura o carga crea una observación nueva aunque coincidan fuente, producto, URL y precio con una anterior. Única excepción: dentro de una **misma** ejecución de captura, búsqueda manual o lote de archivo (mismo `id_contexto`), no se crean dos observaciones con la misma `referencia_origen` de tipo `url`; el segundo intento se descarta, no crea observación y devuelve `"Observación duplicada en el contexto {id_contexto}: {referencia_origen}."` (protección ante reintentos o doble envío). Las referencias de tipo `texto` no se consideran para esta regla.

**RN-03 — Anulación.** Solo el Administrador anula. Requiere `motivo_anulacion` de 10 a 500 caracteres. Al anular se registran `anulada_por` (usuario) y `fecha_anulacion` (fecha y hora del servidor), y `estado` pasa de `vigente` a `anulada`; `apta_para_referencia` pasa a `no`. Transiciones válidas: `vigente → anulada`. No existe `anulada → vigente`. Aplica a observaciones manuales y automáticas.

**RN-04 — Corrección.** La corrección es una operación atómica: (a) valida la nueva observación con el registro mínimo completo de la base (los mismos campos y mensajes de validación de la HU-042); (b) si es válida, anula la original con el motivo dado y crea la nueva con `corrige_a = {id original}`, y la original queda con `corregida_por = {id nuevo}`; (c) si algo falla, no se aplica ningún cambio. Solo se corrigen observaciones `vigente`. La nueva observación conserva su propio método de adquisición, `registrado_por` (el Administrador que corrige) y evidencia; si la evidencia es la misma, se adjunta de nuevo y se registra con el mismo hash.

**RN-05 — Efecto sobre cálculos.** Anular o corregir no modifica resultados de comparación, señales ni instantáneas ya calculadas por otras épicas; los cálculos posteriores excluyen las observaciones con `apta_para_referencia = no`.

**RN-06 — Consulta del histórico.** Filtros (todos opcionales, combinables con Y): `marca` y `modelo` (coincidencia sin distinguir mayúsculas ni tildes e ignorando espacios, guiones, puntos y barras; es una búsqueda, no un emparejamiento), `ean_gtin` (exacto), `fuente`, rango de `fecha_observacion` (desde/hasta, inclusive; desde ≤ hasta), `metodo_adquisicion`, `incluir_anuladas` (sí/no; por defecto no). Orden: `fecha_observacion` descendente y, en empate, `fecha_registro` descendente. Paginación de 50 resultados por página (configurable). Rango con desde > hasta: `"La fecha inicial no puede ser posterior a la fecha final."`. Sin resultados: lista vacía y `"No hay observaciones de mercado para los filtros indicados."`. Sin ningún filtro: devuelve todas las observaciones paginadas.

**RN-07 — Conservación.** Las observaciones no tienen fecha de expiración ni purga automática en el MVP. Están incluidas en el respaldo diario de la plataforma (NFR-DIS-003).

**RN-08 — Eventos auditables.** Cada anulación y cada corrección generan un evento (`anulacion_observacion` | `correccion_observacion`) con usuario, fecha y hora, identificadores y motivo, disponible para el log de auditoría de la plataforma. Un intento rechazado no genera evento de anulación ni de corrección.

### Interfaz

No requiere pantalla propia (nota del Dominio 12 del PRD). Anulación, corrección y consulta se exponen como operaciones administrativas (interfaz mínima, comando, script o consulta, a definir en arquitectura) que devuelven el resultado o los mensajes definidos en esta HU.

### Sistemas Externos (Si aplica)

No aplica.

---

## Contexto y Referencias

**Épica origen:** [Referencias de Mercado Trazables](../../../epicas.md#épica-004-referencias-de-mercado-trazables)

**Exclusiones de la Épica:**
- NO incluye Mercado Libre ni Éxito como fuentes automáticas (Adenda 2); solo carga manual si el Administrador lo decide.
- NO incluye vendedores terceros de marketplace.
- NO incluye fuentes externas de precios históricos (archivos web, sitios de seguimiento).
- NO incluye evasión de CAPTCHA, bloqueos ni autenticación.
- NO incluye alertas de cambio de precio para usuarios.

**Historias relacionadas:** HU-042 (estructura de la observación y registro mínimo), HU-047, HU-048, HU-049 y HU-050 (canales que crean observaciones con `id_contexto`).

---

## Supuestos

> Elementos inferidos por la IA que NO estaban explícitos en el PRD o la Épica. Todos los supuestos han sido resueltos: convertidos en reglas de negocio explícitas o eliminados mediante reformulación. Si aparece algún supuesto no resuelto, esta HU NO está lista para desarrollo.

1. **Corrección por anulación + nueva observación:** "sin sobrescribirlas" se implementa con anulación trazable y observación de corrección vinculada; no hay edición. Resuelta (RN-03, RN-04).
2. **Duplicados dentro de un mismo contexto:** se descartan para evitar efectos de reintentos; entre contextos distintos siempre se crea una nueva observación. Resuelta (RN-02).
3. **Sin purga:** las observaciones se conservan sin límite de tiempo durante el MVP. Resuelta (RN-07).
4. **Consulta del histórico solo para Administrador** en esta épica; el Analista ve observaciones a través de la evidencia de las señales. Resuelta (Permisos).

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
