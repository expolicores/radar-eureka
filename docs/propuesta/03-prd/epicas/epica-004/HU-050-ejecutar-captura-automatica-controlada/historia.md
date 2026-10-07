# Historia #050: Ejecutar la captura automática controlada de una fuente retail

**Estado:** Borrador (PO)  
**Release:** Release MVP  
**Épica:** [Referencias de Mercado Trazables](../../../epicas.md#épica-004-referencias-de-mercado-trazables)  
**Feature:** Capturar Precios Automáticamente con Salvaguardas  
**Prioridad:** Alta  
**FRs relacionados:** FR-043

Escrita por el flujo generar-historias-usuario (Método Ceiba) — MVP propio, no comercial

---

## Historia de Usuario

**Como** Administrador de la plataforma,  
**Quiero** que el sistema ejecute de forma programada la captura automática de observaciones de una fuente retail habilitada, respetando `robots.txt`, límites de ritmo y volumen, y un User-Agent identificado,  
**Para** acumular observaciones de mercado con menos tiempo humano, solo cuando exista un mecanismo permitido y viable, y sin evadir ninguna restricción de la fuente.

## Descripción

**Prioridad Alta (no Crítica) dentro de una épica Crítica:** la automatización completa de las fuentes retail **no es condición de éxito del MVP** y su indisponibilidad no bloquea el Benchmark 2 (FR-043, Adenda 2), que puede operar solo con carga manual o por archivo.

Esta HU construye el **marco común de captura** que usan todos los conectores de fuente (Alkosto en HU-051, Falabella en HU-052; una nueva fuente solo requiere un nuevo conector, NFR-EVO-001):

- Habilitación por fuente y condiciones previas (incluida la revisión de términos de uso antes de producción).
- Programación (configuración inicial: semanal) y una sola ejecución a la vez por fuente.
- Verificación de `robots.txt` en **cada** ejecución, límites de ritmo y volumen, User-Agent propio con contacto y prohibición de cualquier mecanismo de evasión.
- Aplicación de las reglas comunes (televisor individual, vendedor = la tienda, precio efectivo, condiciones especiales) y almacenamiento en la base propia con evidencia.
- Registro de cada ejecución con sus contadores.

La suspensión automática ante CAPTCHA, bloqueo, autenticación o cambio de `robots.txt` se define en HU-053; esta HU invoca esa suspensión cuando detecta esas condiciones. El relanzamiento manual de una captura y el panel de estado de fuentes pertenecen a la épica de operación.

---

## Criterios de Aceptación

### Escenario 1: Ejecución programada exitosa

- **Dado** que la fuente Alkosto tiene captura automática permitida y habilitada, User-Agent configurado, frecuencia semanal los lunes a las 02:00 (hora de Colombia) y estado `activa`
- **Cuando** llega la hora programada
- **Entonces** el sistema crea una ejecución `en_curso`, descarga y evalúa `robots.txt`, solicita solo URLs permitidas respetando el intervalo mínimo entre solicitudes, guarda cada observación válida con `metodo_adquisicion = sitemap_datos_estructurados`, `canal_carga = conector`, `registrado_por = conector:Alkosto` e `id_contexto = id_ejecucion`, y cierra la ejecución como `completada` con sus contadores

### Escenario 2: Habilitar la captura sin condiciones previas

- **Dado** que el Administrador intenta habilitar la captura de una fuente sin User-Agent configurado, de una fuente sin captura automática permitida, o, en el entorno de producción, de una fuente sin revisión de términos de uso registrada
- **Cuando** guarda la configuración
- **Entonces** se rechaza con `"Configure un User-Agent con contacto antes de habilitar la captura."`, `"La fuente {fuente} no admite captura automática."` o `"Registre la revisión de términos de uso de {fuente} antes de habilitar la captura en producción."`, respectivamente

### Escenario 3: URL prohibida por robots.txt

- **Dado** que `robots.txt` permite las rutas requeridas por el conector pero prohíbe una URL candidata concreta
- **Cuando** la ejecución llega a esa URL
- **Entonces** no la solicita y la registra como `omitida_por_robots`; la ejecución continúa

### Escenario 4: robots.txt no disponible

- **Dado** que la descarga de `robots.txt` responde 404, 500 o no responde en 30 segundos
- **Cuando** inicia la ejecución
- **Entonces** no se hace ninguna otra solicitud, la ejecución termina como `fallida` con motivo `"robots.txt no disponible ({código o timeout})"` y se emite el evento `captura_fallida`; si la respuesta es 401 o 403, se aplica la suspensión de HU-053

### Escenario 5: Límite de volumen alcanzado

- **Dado** que el límite de volumen es 2.000 solicitudes por semana y la fuente lleva 1.995 solicitudes en los últimos 7 días
- **Cuando** la ejecución hace la solicitud número 2.000
- **Entonces** se detiene sin hacer más solicitudes, termina como `completada_con_limite` y registra el número de URLs pendientes, que se procesan en la siguiente ejecución

### Escenario 6: Ritmo de solicitudes

- **Dado** que el intervalo mínimo configurado es 2 segundos y `robots.txt` declara `Crawl-delay: 5`
- **Cuando** la ejecución hace solicitudes consecutivas a la fuente
- **Entonces** entre el inicio de dos solicitudes consecutivas transcurren al menos 5 segundos (se usa el mayor de los dos valores)

### Escenario 7: Errores transitorios en una página

- **Dado** que una página responde 503 o excede el tiempo de espera
- **Cuando** la ejecución la solicita
- **Entonces** reintenta hasta 3 veces con esperas de 2, 4 y 8 segundos (sin bajar del intervalo mínimo); si sigue fallando, registra la URL con error y continúa; si más del 50 % de las páginas de producto de la ejecución termina en error, la ejecución termina como `fallida` y se emite `captura_fallida`

### Escenario 8: Producto que no es un televisor individual o sin modelo

- **Dado** que una URL candidata corresponde a "Combo TV 55 + soporte de pared" o a un televisor cuyo modelo no puede identificarse
- **Cuando** la ejecución procesa la página
- **Entonces** no crea observación y registra un descarte `no_es_televisor` o `modelo_no_identificable`, respectivamente

### Escenario 9: Ejecución en curso o fuente suspendida

- **Dado** que a la hora programada la ejecución anterior de la fuente sigue `en_curso`, o la fuente está `suspendida`
- **Cuando** llega la hora programada
- **Entonces** no se inicia una nueva ejecución y se registra una ejecución `omitida` con motivo `"ejecución anterior en curso"` o `"fuente suspendida"`

### Escenario 10: Deshabilitar la captura durante una ejecución

- **Dado** que hay una ejecución `en_curso`
- **Cuando** el Administrador deshabilita la captura de la fuente
- **Entonces** la ejecución termina después de la solicitud en curso, con estado `detenida_por_administrador`; las observaciones ya guardadas se conservan

### Escenario 11: Ninguna fuente automatizada

- **Dado** que ninguna fuente tiene la captura automática habilitada
- **Cuando** pasa el tiempo programado
- **Entonces** no se ejecuta ninguna captura y la carga manual, la búsqueda manual y la carga por archivo siguen funcionando con normalidad

### Escenario 12: Usuario sin rol Administrador

- **Dado** que un Analista intenta habilitar la captura o cambiar sus parámetros
- **Cuando** ejecuta la operación
- **Entonces** se rechaza con `"Operación permitida solo para el rol Administrador."`

---

## Información Recopilada

### Usuario y Contexto

- **Tipo de usuario:** Administrador (configura); el sistema ejecuta las capturas con la identidad `conector:{fuente}`.
- **Permisos requeridos:** rol Administrador para configurar y habilitar la captura.
- **Valor de negocio:** aumenta la densidad del histórico propio de precios sin depender del tiempo humano, cuando la fuente lo permite.

### Reglas de Negocio

**RN-01 — Habilitación.** `captura_automatica_habilitada = sí` solo si: (a) la fuente tiene `captura_automatica_permitida = sí` (existe conector); (b) hay User-Agent válido (RN-05); (c) en el entorno de producción, la fuente tiene `terminos_uso_revisados = sí` con fecha de revisión y nota de 10 a 1.000 caracteres registradas por el Administrador (NFR-CUM-006). En entornos distintos de producción (MVP de validación) la condición (c) no aplica. La captura contra una fuente real solo se habilita cuando la suspensión automática ante bloqueos (HU-053) está implementada. Configuración inicial: deshabilitada en todas las fuentes.

**RN-02 — Programación.** Parámetros por fuente: frecuencia (`diaria` | `semanal` | `mensual`; inicial `semanal`, NFR-DAT-003), día de la semana (inicial lunes; o día del mes 1–28 si es mensual) y hora (inicial 02:00, hora de Colombia). Una sola ejecución `en_curso` por fuente. Si la anterior sigue en curso o la fuente está suspendida, se registra una ejecución `omitida` con su motivo.

**RN-03 — robots.txt en cada ejecución (NFR-CUM-002).** Al iniciar, se descarga `robots.txt` de la fuente (tiempo máximo 30 s) y se guardan su contenido, hash SHA-256 y fecha. Respuesta 200: se evalúan las reglas aplicables al User-Agent del producto (o, si no hay grupo específico, al grupo `*`). Respuesta 401 o 403: suspensión (HU-053). Cualquier otra respuesta o error de red: ejecución `fallida` sin más solicitudes. El conector declara sus **rutas requeridas** (ej. sitemaps y prefijo de páginas de producto); si alguna está prohibida, se aplica la suspensión por cambio de `robots.txt` (HU-053). Una URL concreta prohibida que no es ruta requerida se omite (`omitida_por_robots`). Si `robots.txt` cambió (hash distinto) y sigue permitiendo las rutas requeridas, se registra la advertencia `robots_txt_modificado` y la ejecución continúa.

**RN-04 — Ritmo y volumen (NFR-CUM-003).** Intervalo mínimo entre el inicio de dos solicitudes a la fuente: configurable, inicial 2 segundos, nunca menor de 1 segundo; si `robots.txt` declara `Crawl-delay` mayor, se usa ese valor. Volumen máximo: configurable, inicial 2.000 solicitudes por fuente en los últimos 7 días (ventana móvil), contando todas las solicitudes (robots, sitemaps, páginas y reintentos). Al alcanzarlo, la ejecución se detiene como `completada_con_limite` con el número de URLs pendientes; la siguiente ejecución empieza por las pendientes. Mensajes de configuración inválida: `"El intervalo mínimo entre solicitudes no puede ser menor de 1 segundo."`, `"El volumen semanal debe ser un entero entre 1 y 20.000."`

**RN-05 — User-Agent (NFR-CUM-004).** Texto fijo configurable de 10 a 200 caracteres que incluye el nombre del producto y un contacto (correo electrónico o URL). Ejemplo: `SeguimientoComprasPublicas/0.1 (+contacto: equipo@dominio-del-producto.co)`. Se envía igual en todas las solicitudes; nunca se rota ni se imita un navegador. Sin contacto: `"El User-Agent debe incluir un correo o URL de contacto."` Longitud fuera de rango: `"El User-Agent debe tener entre 10 y 200 caracteres."`

**RN-06 — Prohibición de evasión (NFR-CUM-005).** La captura no usa: resolución o evasión de CAPTCHA, rotación de User-Agent o de direcciones IP, proxies para ocultar el origen, inicio de sesión, cookies de sesión de usuario, simulación de interacción humana, ni reintentos ante respuestas 401, 403 o 429. Tampoco solicita rutas de búsqueda de la tienda ni endpoints prohibidos por `robots.txt`. Es requisito de revisión de código obligatoria.

**RN-07 — Reintentos.** Solo ante tiempo de espera (30 s), error de red o respuestas 500, 502, 503 o 504: hasta 3 reintentos con esperas de 2, 4 y 8 segundos (respetando RN-04). Agotados, la URL queda con error. Si más del 50 % (configurable) de las páginas de producto de la ejecución termina con error, la ejecución termina como `fallida`. Ante 401, 403, 429 o señales de CAPTCHA se aplica HU-053. Otras respuestas 4xx en una página (ej. 404, 410): sin reintento; la URL queda con error.

**RN-08 — Filtro de televisor individual.** Además del filtro de URLs del conector, se descarta (`no_es_televisor`) todo producto cuyo nombre contenga alguno de los términos de exclusión configurables (inicial: "soporte", "mueble", "base para", "control remoto", "cable", "combo", "kit", "proyector", "monitor", "antena", "bafle", "barra de sonido"), sin distinguir mayúsculas ni tildes. Si el conector no logra identificar el modelo, descarte `modelo_no_identificable`. Si la página no tiene datos estructurados de producto, descarte `datos_estructurados_ausentes`.

**RN-09 — Reglas comunes y almacenamiento.** Sobre cada oferta leída se aplican, en este orden: vendedor = la tienda (ofertas de terceros → descarte `vendedor_tercero`; sin vendedor y sin vendedor implícito → `vendedor_no_identificable`), precio efectivo (sin precio vigente → `sin_precio_vigente`), condiciones especiales y validación del registro mínimo de la base. La observación se guarda con `metodo_adquisicion = sitemap_datos_estructurados`, `canal_carga = conector`, `registrado_por = conector:{fuente}`, `id_contexto = id_ejecucion`, `protocolo_busqueda = no_aplica`, `fecha_observacion` = fecha y hora de la respuesta de la página, `iva_condicion` = la declarada por los datos de la fuente o, si no la declara, el valor `iva_por_defecto_captura` de la fuente (inicial: `indeterminado`). Evidencia: copia del bloque de datos estructurados leído, URL, fecha y hora, código de respuesta y hash SHA-256. Dentro de una ejecución, la misma URL no genera dos observaciones.

**RN-10 — Registro de la ejecución.** Cada ejecución guarda: `id_ejecucion`, fuente, inicio, fin, estado (`en_curso` | `completada` | `completada_con_limite` | `fallida` | `suspendida` | `omitida` | `detenida_por_administrador`), motivo, solicitudes realizadas, URLs candidatas, páginas leídas, observaciones creadas, descartes por motivo, URLs omitidas por robots, URLs con error, advertencias y hash de `robots.txt`. Se emite el evento `captura_fallida` para estados `fallida` (para la alerta al Administrador de la épica de operación). El Administrador puede consultar las ejecuciones por fuente y rango de fechas.

**RN-11 — Independencia de la carga manual.** El estado de la captura (deshabilitada, fallida, suspendida) nunca bloquea la carga manual, la búsqueda manual ni la carga por archivo.

**RN-12 — Configuración auditable.** Todo cambio de habilitación, programación, ritmo, volumen, User-Agent, términos de exclusión o revisión de términos de uso genera un evento con usuario, fecha y hora, valor anterior y nuevo. Solo el Administrador los modifica.

### Interfaz

No requiere pantalla propia (nota del Dominio 12 del PRD): configuración, consulta de ejecuciones y deshabilitación pueden hacerse por operación administrativa, configuración o consulta. La ejecución es un proceso programado sin interacción de usuario.

### Sistemas Externos (Si aplica)

Sitios web de Alkosto y Falabella (`robots.txt`, sitemaps de producto y páginas de producto con datos estructurados schema.org), leídos a través de los conectores de HU-051 y HU-052. Respuestas posibles: 200 (correcto), 4xx/5xx o timeout (error), 401/403/429 o CAPTCHA (suspensión, HU-053).

---

## Contexto y Referencias

**Épica origen:** [Referencias de Mercado Trazables](../../../epicas.md#épica-004-referencias-de-mercado-trazables)

**Exclusiones de la Épica:**
- NO incluye Mercado Libre ni Éxito como fuentes automáticas (Adenda 2); solo carga manual si el Administrador lo decide.
- NO incluye vendedores terceros de marketplace.
- NO incluye fuentes externas de precios históricos (archivos web, sitios de seguimiento).
- NO incluye evasión de CAPTCHA, bloqueos ni autenticación.
- NO incluye alertas de cambio de precio para usuarios.

**Historias relacionadas:** HU-042 (base), HU-044, HU-045, HU-046 (reglas de precio), HU-051 (conector Alkosto), HU-052 (conector Falabella), HU-053 (suspensión y notificación).

---

## Supuestos

> Elementos inferidos por la IA que NO estaban explícitos en el PRD o la Épica. Todos los supuestos han sido resueltos: convertidos en reglas de negocio explícitas o eliminados mediante reformulación. Si aparece algún supuesto no resuelto, esta HU NO está lista para desarrollo.

1. **Prioridad Alta** porque la automatización no es condición de éxito del MVP. Resuelta (Descripción).
2. **Términos de uso:** la habilitación en producción exige registrar la revisión; en entornos de validación no. Resuelta (RN-01).
3. **robots.txt no disponible:** criterio conservador; sin `robots.txt` legible no se hacen más solicitudes. Resuelta (RN-03).
4. **Crawl-delay** de `robots.txt` prevalece si es mayor que el intervalo configurado. Resuelta (RN-04).
5. **Programación inicial:** lunes 02:00 hora de Colombia, configurable. Resuelta (RN-02).
6. **Términos de exclusión** de productos que no son televisores individuales, configurables. Resuelta (RN-08).
7. **Umbral de ejecución fallida** por errores: más del 50 % de páginas con error, configurable. Resuelta (RN-07).

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
