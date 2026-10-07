# Historia #012: Clasificación asistida por IA de candidatos que requieren revisión

**Estado:** Borrador (PO)  
**Release:** Release MVP  
**Épica:** [Universo de Compras Públicas de Televisores](../../../epicas.md#épica-001-universo-de-compras-públicas-de-televisores)  
**Feature:** Clasificar Ítems de Televisor  
**Prioridad:** Alta  
**FRs relacionados:** FR-013, FR-015

Escrita por el flujo generar-historias-usuario (Método Ceiba) — MVP propio, no comercial

---

## Historia de Usuario

**Como** Administrador del MVP,  
**Quiero** que los candidatos que las reglas dejan en "Requiere revisión" reciban una propuesta de clasificación generada con IA, con motivo, justificación y nivel de confianza, y que solo se acepte automáticamente cuando lo habilite y supere un umbral configurado,  
**Para** reducir el tiempo de revisión manual sin perder control sobre la calidad de la clasificación.

## Descripción

Las reglas determinísticas (HU-010 y HU-011) resuelven los casos claros y dejan los ambiguos en "Requiere revisión" (ej. "monitor TV", kits, lotes, contratos que solo coinciden por UNSPSC). Esta historia envía esos candidatos a un modelo de IA con el límite de categoría aprobado y recibe una propuesta estructurada.

Por defecto la propuesta es una **sugerencia** que el Administrador ve al revisar; el candidato sigue en "Requiere revisión". La **aceptación automática** está deshabilitada hasta que el PO la active con un umbral calibrado con la revisión manual. El puntaje de confianza del modelo no se interpreta como probabilidad calibrada de acierto.

La IA es opcional: desactivarla no afecta la ingesta, la marcación ni la clasificación por reglas. Esta historia tiene prioridad **Alta** (la épica es Crítica) porque el universo puede construirse solo con reglas y revisión manual; la IA reduce trabajo, pero no es indispensable.

---

## Criterios de Aceptación

### Escenario 1: Sugerencia con aceptación automática deshabilitada

- **Dado** que la IA está habilitada, la aceptación automática deshabilitada, y un ítem "Monitor TV 43 pulgadas para CCTV" está en "Requiere revisión" por la regla R6
- **Cuando** se ejecuta la clasificación asistida
- **Entonces** se registra una sugerencia con resultado propuesto, categoría de motivo, justificación, confianza, modelo, versión de instrucciones y fecha; la clasificación vigente sigue siendo "Requiere revisión" y el ítem queda con `estado_ia = Sugerencia disponible`

### Escenario 2: Aceptación automática por encima del umbral

- **Dado** que la aceptación automática está habilitada con `umbral_aceptacion_ia = 0,85` y la IA propone "Excluido" con categoría "Producto excluido: monitor o CCTV" y confianza 0,92
- **Cuando** se procesa la respuesta
- **Entonces** se agrega una clasificación vigente "Excluido" con método "IA", criterio "IA — Producto excluido: monitor o CCTV", la justificación y la confianza, y el estado de clasificación pasa a "Clasificado"

### Escenario 3: Confianza por debajo del umbral o propuesta "Requiere revisión"

- **Dado** que la aceptación automática está habilitada con umbral 0,85
- **Cuando** la IA propone un resultado con confianza 0,84, o propone "Requiere revisión" con cualquier confianza
- **Entonces** queda solo como sugerencia y la clasificación vigente sigue "Requiere revisión"

### Escenario 4: Respuesta de IA inválida

- **Dado** que la IA responde sin alguno de los campos obligatorios, con un resultado o categoría fuera de las listas permitidas, con confianza fuera de 0 a 1, con una respuesta no interpretable o con una justificación que contiene términos prohibidos
- **Cuando** se procesa la respuesta
- **Entonces** se descarta, se registra "Respuesta de IA inválida: {motivo}", se reintenta hasta 2 veces más en la misma ejecución y, si sigue inválida, el candidato queda `estado_ia = Fallida` en "Requiere revisión"

### Escenario 5: Servicio de IA no disponible

- **Dado** que el servicio de IA responde con tiempo de espera agotado, HTTP 429 o HTTP 5xx en el intento original y en 3 reintentos con espera exponencial
- **Cuando** se agotan los reintentos
- **Entonces** el candidato queda `estado_ia = Pendiente de reintento` y se vuelve a intentar en la siguiente ejecución; tras 3 ejecuciones fallidas queda `estado_ia = Fallida` y sigue en "Requiere revisión"

### Escenario 6: IA deshabilitada

- **Dado** que `clasificacion_ia_habilitada = no`
- **Cuando** se clasifica por reglas o se ejecuta el comando de clasificación asistida
- **Entonces** no se envía ninguna solicitud al servicio de IA, el comando informa "La clasificación asistida por IA está deshabilitada." y las demás funciones (ingesta, marcación, clasificación por reglas, revisión manual) operan normalmente

### Escenario 7: Candidatos que no se envían a la IA

- **Dado** que un candidato tiene clasificación vigente manual, o vigente por regla "Incluido" o "Excluido"
- **Cuando** se ejecuta la clasificación asistida
- **Entonces** no se envía a la IA

### Escenario 8: Configuración de aceptación automática inválida

- **Dado** que el Administrador intenta habilitar la aceptación automática sin umbral o con un umbral fuera del rango 0,50 a 1,00
- **Cuando** guarda la configuración
- **Entonces** se rechaza con "Para habilitar la aceptación automática defina un umbral entre 0,50 y 1,00." y se conserva la configuración anterior

### Escenario 9: Sin candidatos en revisión

- **Dado** que no hay candidatos en "Requiere revisión" pendientes de IA
- **Cuando** se ejecuta la clasificación asistida
- **Entonces** termina sin solicitudes a la IA y registra "No hay candidatos pendientes de clasificación asistida."

---

## Información Recopilada

### Usuario y Contexto

- **Tipo de usuario:** Administrador del MVP (PO); el sistema ejecuta la clasificación asistida.
- **Permisos requeridos:** rol Administrador para ejecutar y configurar.
- **Valor de negocio:** menos tiempo de revisión manual del PO (que actúa como Revisor) sobre el 28 % de candidatos que no son televisores y los casos ambiguos.

### Reglas de Negocio

- **RN-01 Configuración (valores iniciales):** `clasificacion_ia_habilitada = sí`; `aceptacion_automatica_ia = no`; `umbral_aceptacion_ia` = sin valor. Para habilitar la aceptación automática se exige un umbral decimal entre 0,50 y 1,00 (Escenario 8). El umbral se calibra con la revisión manual de una muestra de candidatos; no hay un valor fijo de negocio. Cambiar la configuración no requiere redespliegue.
- **RN-02 Candidatos enviados:** ítems (TVEC o SECOP II) y contratos SECOP II cuya clasificación vigente es "Requiere revisión" con método "Regla" o "Derivado de ítems", y `estado_ia` en "Sin procesar" o "Pendiente de reintento". Nunca se envían candidatos con clasificación vigente manual ni con resultado por regla "Incluido" o "Excluido".
- **RN-03 Datos enviados a la IA:** solo texto del candidato: `descripcion_item`, `lote_descripcion`, `costo_servicio_discriminado`, `precio_unitario_discriminado` (ítems); `objeto`, `descripcion_proceso`, `unspsc_principal` (contratos); el criterio de la regla que lo dejó en revisión; y la descripción del límite de categoría. **No** se envían nombres de entidad, proveedor, identificadores de personas ni ningún campo personal.
- **RN-04 Límite de categoría enviado:** incluye televisores LED/QLED/OLED de consumo, Smart y convencionales, de cualquier tamaño; excluye pantallas LED modulares, videowalls, señalización digital, monitores (incluidos los de CCTV), proyectores, pantallas interactivas o inflables, soluciones audiovisuales integrales, accesorios, servicios de mantenimiento o instalación, comodatos y otros contratos que no son compras, lotes que no corresponden al televisor, kits sin precio unitario determinable, e ítems con precio inseparable de instalación, obra o servicios.
- **RN-05 Respuesta obligatoria:** `resultado` ∈ {Incluido, Excluido, Requiere revisión}; `categoria_motivo` ∈ {Televisor de consumo; Producto excluido: videowall o pantalla modular; Producto excluido: señalización digital; Producto excluido: monitor o CCTV; Producto excluido: proyector; Producto excluido: pantalla interactiva o inflable; Producto excluido: solución audiovisual integral; Accesorio; Servicio de mantenimiento o instalación; No es una compra; Lote que no corresponde al televisor; Kit sin precio unitario determinable; Precio inseparable de instalación, obra o servicio; Información insuficiente}; `justificacion` texto de 1 a 500 caracteres; `confianza` decimal de 0 a 1.
- **RN-06 Validación de la respuesta:** inválida si falta un campo, un valor está fuera de su lista o rango, no es interpretable, o la justificación contiene "sobreprecio", "corrupción", "corrupcion", "fraude" o "hallazgo fiscal" (sin distinguir mayúsculas ni tildes). Respuesta inválida → hasta 2 reintentos adicionales en la misma ejecución; luego `estado_ia = Fallida`.
- **RN-07 Disponibilidad del servicio:** tiempo de espera por solicitud (valor inicial: 60 s), HTTP 429 o 5xx → hasta 3 reintentos con espera exponencial (valores iniciales: 2, 4 y 8 s). Agotados → `estado_ia = Pendiente de reintento`; tras 3 ejecuciones con ese resultado → `Fallida`. HTTP 400, 401 y 403 → `Fallida` sin reintento y error en el log "El servicio de IA rechazó la solicitud (HTTP {código})".
- **RN-08 Registro de la sugerencia:** evento con `resultado_propuesto`, `categoria_motivo`, `justificacion`, `confianza`, `modelo`, `version_instrucciones`, `fecha_hora`, `aceptada_automaticamente` (sí/no). Los eventos no se modifican ni se eliminan.
- **RN-09 Aceptación automática:** solo si `aceptacion_automatica_ia = sí`, el resultado propuesto es "Incluido" o "Excluido" y `confianza ≥ umbral_aceptacion_ia`. En ese caso se agrega una clasificación vigente con método "IA", criterio "IA — {categoria_motivo}" y la confianza; para contratos SECOP II se aplica al nivel "Preliminar (contrato)". En cualquier otro caso queda como sugerencia.
- **RN-10 Estados de IA del candidato:** "Sin procesar", "Sugerencia disponible", "Aceptada automáticamente", "Pendiente de reintento", "Fallida". Si el candidato vuelve a "Pendiente de clasificación" (cambio en la fuente), su `estado_ia` vuelve a "Sin procesar".
- **RN-11 Disparo:** automático después de cada ejecución de clasificación por reglas sobre los nuevos candidatos en revisión; manual por comando "clasificación asistida por IA".
- **RN-12 Secretos:** las credenciales del servicio de IA se leen de un gestor de secretos o variable de entorno; nunca se escriben en logs.
- **RN-13 Resumen:** "Clasificación asistida por IA: {n} enviados. Sugerencias: {n}. Aceptadas automáticamente: {n}. Respuestas inválidas: {n}. Pendientes de reintento: {n}. Fallidas: {n}."

### Interfaz

No requiere interfaz gráfica. Comando y configuración; las sugerencias se consultan en la cola de revisión de la HU-013. Resumen en consola o log (RN-13).

### Sistemas Externos (Si aplica)

- **Servicio de IA (modelo de lenguaje):** proveedor y modelo definidos en arquitectura; entrada de texto y salida estructurada (RN-05). Autenticación por credencial en gestor de secretos.

---

## Contexto y Referencias

**Épica origen:** [Universo de Compras Públicas de Televisores](../../../epicas.md#épica-001-universo-de-compras-públicas-de-televisores)

**Exclusiones de la Épica:**
- NO incluye SECOP I (Adenda 1).
- NO incluye categorías distintas a televisores.
- NO incluye el dataset de Procesos (`p6dx-8zbt`) como unidad base.
- NO incluye adiciones, modificaciones ni ejecución del contrato (ciclo de vida).
- NO incluye scraping del portal SECOP.

**Historias relacionadas:** HU-010 (reglas de ítem), HU-011 (reglas de contrato), HU-013 (revisión y corrección manual).

---

## Supuestos

> Elementos inferidos por la IA que NO estaban explícitos en el PRD o la Épica. Todos los supuestos han sido resueltos: convertidos en reglas de negocio explícitas o eliminados mediante reformulación. Si aparece algún supuesto no resuelto, esta HU NO está lista para desarrollo.

- El PRD permite clasificar por "reglas y/o IA" pero no fija cuándo aceptar la IA → resuelto: sugerencia por defecto y aceptación automática solo con umbral configurado (RN-01, RN-09), en línea con el criterio de la decisión P-15.
- La IA solo se usa para lo que las reglas no resuelven → resuelto en RN-02.
- El proveedor y modelo de IA se definen en arquitectura → la historia fija solo entradas, salidas y validaciones (RN-03 a RN-06).
- Prioridad Alta en una épica Crítica → justificado en la descripción.

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

---

> **Método Ceiba estimar hus** v6.1.95 | Modelo: claude-opus-5-5 | Usuario: Juan Camilo | Fecha: 2026-10-05
