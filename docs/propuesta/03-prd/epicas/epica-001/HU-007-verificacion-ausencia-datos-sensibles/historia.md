# Historia #007: Verificación automática de ausencia de datos personales sensibles

**Estado:** Borrador (PO)  
**Release:** Release MVP  
**Épica:** [Universo de Compras Públicas de Televisores](../../../epicas.md#épica-001-universo-de-compras-públicas-de-televisores)  
**Feature:** Controlar Calidad y Trazabilidad de la Ingesta  
**Prioridad:** Crítica  
**FRs relacionados:** FR-006

Escrita por el flujo generar-historias-usuario (Método Ceiba) — MVP propio, no comercial

---

## Historia de Usuario

**Como** Administrador del MVP,  
**Quiero** una verificación automática que demuestre que ningún campo personal sensible del dataset de contratos (banco, tipo y número de cuenta, documentos de identidad de representantes legales, supervisores y ordenadores del gasto) existe en ninguna capa del sistema,  
**Para** cumplir la minimización de datos de la Ley 1581 de 2012 y la meta de 0 campos sensibles almacenados, con evidencia verificable y no solo por diseño.

## Descripción

Las cargas de la épica conservan solo los campos de una lista blanca. Esta historia agrega el **control que lo comprueba**: una verificación con tres comprobaciones —configuración, esquema de datos y prueba con valores testigo— que se ejecuta en el conjunto de pruebas automáticas ante cada cambio y que el Administrador puede ejecutar por comando en cualquier entorno (con las comprobaciones que aplican a ese entorno).

Además, cada carga deja registrados los **nombres** (nunca los valores) de los campos recibidos de la fuente que fueron descartados por no estar en la lista blanca, para detectar campos nuevos de la fuente sin exponer su contenido.

Cumple el criterio de la épica: "Una prueba automática confirma que ningún campo personal excluido existe en la base de datos".

---

## Criterios de Aceptación

### Escenario 1: Verificación completa sin hallazgos

- **Dado** que la configuración, el esquema y las capas de almacenamiento no contienen campos ni valores sensibles
- **Cuando** se ejecuta la verificación en el entorno de pruebas
- **Entonces** las tres comprobaciones (configuración, esquema y valores testigo) terminan "Aprobada" y el resultado general es "Aprobada: 0 campos personales sensibles encontrados"

### Escenario 2: Lista blanca con un campo prohibido

- **Dado** que alguien agregó `tipo_de_cuenta` a la lista blanca de una fuente
- **Cuando** se ejecuta la verificación
- **Entonces** la comprobación de configuración termina "Fallida" con "Campo prohibido en la lista blanca de SECOP II contratos: tipo_de_cuenta (patrón: cuenta)" y el resultado general es "Fallida"

### Escenario 3: Columna sensible en el esquema de datos

- **Dado** que una tabla o colección del sistema tiene una columna llamada `numero_cuenta_proveedor`
- **Cuando** se ejecuta la verificación
- **Entonces** la comprobación de esquema termina "Fallida" listando la tabla, la columna y el patrón coincidente

### Escenario 4: Valor testigo encontrado en alguna capa

- **Dado** que en el entorno de pruebas se ingiere un contrato sintético con valores testigo únicos en los campos sensibles
- **Cuando** la verificación busca esos valores en la base de datos, el registro de rechazos, la bitácora de ejecuciones, los logs de aplicación y los archivos temporales y de almacenamiento del sistema
- **Entonces** si encuentra alguno, la comprobación termina "Fallida" indicando la capa y la ubicación, y si no encuentra ninguno termina "Aprobada"

### Escenario 5: Verificación como bloqueo en pruebas automáticas

- **Dado** que la verificación forma parte del conjunto de pruebas automáticas
- **Cuando** su resultado general es "Fallida"
- **Entonces** el conjunto de pruebas falla y el cambio no puede promoverse a ningún entorno

### Escenario 6: Ejecución en producción

- **Dado** que el Administrador ejecuta la verificación por comando en producción
- **Cuando** corre
- **Entonces** se ejecutan solo las comprobaciones de configuración y esquema (no se ingieren valores testigo), y el resultado indica "Comprobación de valores testigo: no aplica en este entorno"

### Escenario 7: Campos nuevos descartados en una carga

- **Dado** que la API empieza a enviar un campo que no está en la lista blanca (ej. `nombre_banco_pago`)
- **Cuando** una carga lo descarta
- **Entonces** la ejecución registra "Campos descartados no reconocidos: nombre_banco_pago" (solo nombres, sin valores), una vez por ejecución y campo

### Escenario 8: Patrones prohibidos vacíos

- **Dado** que la lista de patrones prohibidos está vacía o no configurada
- **Cuando** se ejecuta la verificación o una carga
- **Entonces** ambas fallan sin procesar datos con "La lista de patrones prohibidos está vacía. Configure al menos los patrones iniciales."

---

## Información Recopilada

### Usuario y Contexto

- **Tipo de usuario:** Administrador del MVP (PO); el conjunto de pruebas automáticas la ejecuta en cada cambio.
- **Permisos requeridos:** rol Administrador para ejecutarla por comando.
- **Valor de negocio:** cumplimiento normativo verificable (NFR-SEG-005: 0 campos sensibles en cualquier capa) y reducción del riesgo legal y reputacional.

### Reglas de Negocio

- **RN-01 Patrones prohibidos:** lista configurable, evaluada sobre nombres de campo y de columna normalizados (minúsculas, sin tildes, guiones y espacios convertidos en `_`). Valor inicial: contiene `banco`; contiene `cuenta`; contiene `cedula`; contiene (`identificacion` o `documento` o `n_mero_de_documento` o `numero_documento`) **y** (`representante` o `supervisor` o `ordenador`). La lista no puede quedar vacía (Escenario 8).
- **RN-02 Excepción explícita:** `documento_proveedor` / `proveedor_documento` no se considera campo sensible excluido (identifica al proveedor adjudicado, se requiere para identificación, cruce y trazabilidad, y no está en FR-006); por tanto **se almacena** y su presencia en configuración o esquema no es un hallazgo de esta verificación. Las excepciones son una lista configurable que solo admite nombres exactos; valor inicial: `documento_proveedor`, `proveedor_documento`. **Regla de visibilidad (decisión PO 2026-10-05, Ley 1581 de 2012):** aunque se almacena, el campo está sujeto a una regla de presentación según su tipo (`tipodocproveedor`): si el tipo es NIT (persona jurídica), el número es visible y buscable; si el tipo es cédula de ciudadanía, cédula de extranjería, pasaporte, cualquier otro tipo distinto de NIT, o el tipo está vacío o es desconocido (se trata como persona natural por seguridad), el número nunca se muestra en vistas, listas, tarjetas, paneles de evidencia, instantáneas de casos ni exportaciones del analista, no es buscable ni filtrable por número, y en su lugar se muestra "Persona natural — documento no visible" (el nombre del proveedor sigue visible y buscable). El acceso al valor crudo es exclusivo del Administrador por medios técnicos o administrativos, fuera de la interfaz del analista. Esta regla se hace cumplir en las historias de presentación (ej. HU-070, HU-075, HU-076) y no forma parte de las comprobaciones de esta historia.
- **RN-03 Comprobación de configuración:** recorre la lista blanca de cada fuente (SECOP II contratos, TVEC ítems, TVEC órdenes) y falla si algún campo coincide con un patrón y no está en las excepciones.
- **RN-04 Comprobación de esquema:** recorre los nombres de todas las columnas o propiedades de todas las tablas o colecciones del sistema y falla ante cualquier coincidencia no exceptuada. Reporta tabla, columna y patrón.
- **RN-05 Comprobación con valores testigo (solo entornos no productivos):** ingiere por la misma ruta de las cargas reales un contrato sintético `CO1.PCCNTR.TESTIGO-{marca de tiempo}` con valores únicos generados en cada ejecución (ej. `TESTIGO-BANCO-{aleatorio}`, `TESTIGO-CTA-{aleatorio}`, `TESTIGO-DOC-REP-{aleatorio}`, `TESTIGO-DOC-SUP-{aleatorio}`, `TESTIGO-DOC-ORD-{aleatorio}`) en campos llamados `nombre_del_banco`, `tipo_de_cuenta`, `n_mero_de_cuenta`, `identificaci_n_representante_legal`, `n_mero_de_documento_supervisor`, `n_mero_de_documento_ordenador_del_gasto`. Además, ingiere una variante del mismo contrato sin `nombre_entidad` para que pase por el registro de rechazos. Luego busca cada valor testigo en: base de datos (todas las tablas), registro de rechazos, bitácora de ejecuciones, logs de aplicación y archivos del sistema. Al terminar elimina el contrato sintético.
- **RN-06 Resultado:** cada comprobación: "Aprobada", "Fallida" o "No aplica en este entorno". Resultado general "Aprobada" solo si ninguna comprobación aplicable es "Fallida". Se registra con fecha y hora, entorno, usuario (o "pruebas automáticas") y detalle de hallazgos (sin valores reales).
- **RN-07 Bloqueo:** en el conjunto de pruebas automáticas, un resultado "Fallida" hace fallar el conjunto (Escenario 5).
- **RN-08 Campos descartados no reconocidos:** cada carga registra en su ejecución los nombres de los campos recibidos que no están en la lista blanca, una sola vez por nombre y ejecución. Nunca se registran valores.
- **RN-09 Fuentes TVEC:** las mismas comprobaciones de configuración y esquema aplican a las listas blancas de TVEC aunque FR-006 se refiera al dataset de contratos.

### Interfaz

No requiere interfaz gráfica. Comando "verificar datos sensibles" con salida en consola o log: una línea por comprobación con su resultado y, si falla, la lista de hallazgos; y la línea final con el resultado general.

### Sistemas Externos (Si aplica)

No consulta sistemas externos: la comprobación con valores testigo usa una fuente simulada con la misma estructura del dataset `jbjy-vk9h`.

---

## Contexto y Referencias

**Épica origen:** [Universo de Compras Públicas de Televisores](../../../epicas.md#épica-001-universo-de-compras-públicas-de-televisores)

**Exclusiones de la Épica:**
- NO incluye SECOP I (Adenda 1).
- NO incluye categorías distintas a televisores.
- NO incluye el dataset de Procesos (`p6dx-8zbt`) como unidad base.
- NO incluye adiciones, modificaciones ni ejecución del contrato (ciclo de vida).
- NO incluye scraping del portal SECOP.

**Historias relacionadas:** HU-001, HU-002 (lista blanca SECOP II), HU-003, HU-004 (listas blancas TVEC), HU-005 (registro de rechazos), HU-006 (bitácora).

---

## Supuestos

> Elementos inferidos por la IA que NO estaban explícitos en el PRD o la Épica. Todos los supuestos han sido resueltos: convertidos en reglas de negocio explícitas o eliminados mediante reformulación. Si aparece algún supuesto no resuelto, esta HU NO está lista para desarrollo.

- Los nombres exactos de los campos sensibles del dataset no están documentados → resuelto con patrones de nombre (RN-01) y valores testigo (RN-05).
- `documento_proveedor` no es un campo excluido por FR-006 → resuelto como excepción explícita configurable (RN-02): se almacena, pero cuando el proveedor es persona natural (tipo distinto de NIT, vacío o desconocido) su número no se muestra ni es buscable en la interfaz del analista (decisión PO 2026-10-05, Ley 1581); la regla se aplica en las historias de presentación, por lo que almacenarlo no constituye una violación de campo sensible.
- En producción no se deben ingerir datos sintéticos → resuelto: la comprobación con valores testigo solo corre fuera de producción (RN-05, Escenario 6).

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
| 2026-10-02 | 1.0 | Historia generada desde Épica ÉPICA-001 | Juan Camilo (PO) |
| 2026-10-05 | 1.1 | Regla de visibilidad del documento del proveedor persona natural (decisión PO, Ley 1581) | Juan Camilo (PO) |

---

> **Método Ceiba estimar hus** v6.1.95 | Modelo: claude-opus-5-5 | Usuario: Juan Camilo | Fecha: 2026-10-05
