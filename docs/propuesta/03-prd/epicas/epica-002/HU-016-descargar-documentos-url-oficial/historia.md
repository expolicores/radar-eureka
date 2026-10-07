# Historia #016: Descargar los documentos priorizados desde la URL oficial sin evadir restricciones

**Estado:** Borrador (PO)  
**Release:** Release MVP  
**Épica:** [De Documentos a Datos Comparables](../../../epicas.md#épica-002-de-documentos-a-datos-comparables)  
**Feature:** Obtener y Priorizar Documentos del Proceso  
**Prioridad:** Crítica  
**FRs relacionados:** FR-020

Escrita por el flujo generar-historias-usuario (Método Ceiba) — MVP propio, no comercial

---

## Historia de Usuario

**Como** Administrador del MVP,  
**Quiero** que el sistema descargue los documentos priorizados de cada proceso usando únicamente la URL oficial publicada en el dataset de Archivos Descarga, y que se detenga ante cualquier CAPTCHA, autenticación o bloqueo,  
**Para** obtener el contenido de los documentos que contienen precios y cantidades de forma legítima, reproducible y sin riesgo de incumplir las reglas de acceso de la fuente.

## Descripción

D1 y D4 verificaron que los documentos de SECOP II se descargan por HTTP directo desde `url_descarga_documento` (dominio `community.secop.gov.co`), sin CAPTCHA ni inicio de sesión (190 documentos en D4, 0 fallas). Esta HU descarga los documentos en estado "seleccionado" o "contenedor por expandir" (HU-015), calcula la huella (hash SHA-256) del contenido y registra el resultado de cada descarga.

El sistema nunca intenta resolver un CAPTCHA, iniciar sesión, cambiar de identidad ni usar rutas distintas a la URL publicada. Ante un bloqueo, registra el motivo, no insiste y avisa al Administrador. Los fallos temporales (tiempo de espera, errores del servidor) se reintentan con espera exponencial. Un documento que falla definitivamente libera su cupo para el siguiente documento priorizado (HU-015).

La conservación de la copia como evidencia de una señal está en HU-021. Esta HU no requiere interfaz gráfica.

---

## Criterios de Aceptación

### Escenario 1: Descarga exitosa de un documento priorizado

- **Dado** que el documento 600001 "Informe de evaluación económica.pdf" del proceso `CO1.BDOS.1234567` está "seleccionado" con URL `https://community.secop.gov.co/Public/Archive/RetrieveFile/Index?DocumentId=600001`
- **Cuando** se ejecuta la descarga documental
- **Entonces** el sistema obtiene el archivo con una solicitud HTTP GET a esa URL, guarda el contenido, y registra fecha y hora de descarga, tamaño en bytes, tipo de contenido informado por el servidor, hash SHA-256 y estado "descargado"

### Escenario 2: Fallo temporal recuperado con reintento

- **Dado** que la URL del documento 600002 responde con error 503 en el primer intento y con 200 en el segundo
- **Cuando** se ejecuta la descarga documental
- **Entonces** el documento queda "descargado" con 1 reintento registrado y sin contenido duplicado

### Escenario 3: Fallo temporal persistente

- **Dado** que la URL del documento 600004 agota el tiempo de espera en el intento inicial y en los 3 reintentos configurados
- **Cuando** se ejecuta la descarga documental
- **Entonces** el documento queda "descarga fallida definitiva" con el último error y el número de intentos, y su cupo se libera para el siguiente documento priorizado

### Escenario 4: CAPTCHA, autenticación o acceso denegado

- **Dado** que la URL del documento 600005 responde con 403, o con 401, o con una página HTML que contiene un formulario de CAPTCHA o de inicio de sesión en lugar del archivo
- **Cuando** se ejecuta la descarga documental
- **Entonces** el documento queda "descarga bloqueada" con el motivo ("acceso denegado", "requiere autenticación" o "CAPTCHA detectado"), no se reintenta, no se envía ninguna respuesta al CAPTCHA ni credencial, y el Administrador recibe un aviso con el proceso, el documento y el motivo

### Escenario 5: Bloqueos repetidos suspenden las descargas de la ejecución

- **Dado** que en una misma ejecución 5 descargas consecutivas terminan en "descarga bloqueada"
- **Cuando** se produce el quinto bloqueo
- **Entonces** el sistema suspende las descargas restantes de esa ejecución, deja los documentos pendientes en "pendiente de descarga", registra la ejecución como "suspendida por bloqueos" y avisa al Administrador

### Escenario 6: Documento no disponible en la fuente

- **Dado** que la URL del documento 600006 responde 404 o 410
- **Cuando** se ejecuta la descarga documental
- **Entonces** el documento queda "documento no disponible en la fuente", sin reintentos, y su cupo se libera

### Escenario 7: Archivo que excede el tamaño máximo

- **Dado** que el tamaño máximo configurado es 200 MB y el servidor informa (o la descarga alcanza) 250 MB para el documento 600007
- **Cuando** se ejecuta la descarga documental
- **Entonces** la descarga se interrumpe al superar el límite, no se conserva contenido parcial y el documento queda "excede tamaño máximo"

### Escenario 8: Redirección a un dominio no permitido

- **Dado** que la URL oficial redirige a `https://descargas.otro-dominio.example/archivo.pdf`
- **Cuando** se ejecuta la descarga documental
- **Entonces** el sistema no sigue la redirección y el documento queda "descarga bloqueada" con el motivo "redirección fuera de los dominios permitidos"

### Escenario 9: Documento ya descargado

- **Dado** que el documento 600001 ya está "descargado" con su hash
- **Cuando** se ejecuta nuevamente la descarga documental
- **Entonces** el sistema no vuelve a descargarlo, salvo que el Administrador solicite explícitamente la redescarga de ese documento o proceso

### Escenario 10: Proceso con todos sus documentos resueltos

- **Dado** que los 8 documentos seleccionados y el contenedor del proceso `CO1.BDOS.1234567` quedaron en un estado final (descargado o con fallo definitivo)
- **Cuando** termina la descarga del último de ellos
- **Entonces** el proceso pasa al estado "documentos obtenidos" con el número de documentos descargados y el número con fallo, por motivo

### Escenario 11: Respuesta vacía o truncada

- **Dado** que el servidor responde 200 con 0 bytes, o con menos bytes que los indicados en su cabecera de longitud
- **Cuando** se ejecuta la descarga documental
- **Entonces** la respuesta de 0 bytes se guarda y el documento queda "descargado" con tamaño 0 (la regla de archivo vacío la aplica HU-017); la respuesta truncada se trata como fallo temporal y se reintenta

---

## Información Recopilada

### Usuario y Contexto

- **Tipo de usuario:** Administrador (en el MVP es el PO): recibe avisos, consulta resultados y puede solicitar redescargas. La descarga es automática.
- **Permisos requeridos:** Rol Administrador para consultar resultados y solicitar redescargas. El Analista no accede.
- **Valor de negocio:** Obtener el contenido documental es requisito para extraer precios de SECOP II; hacerlo solo por la URL oficial y sin evasión protege la legitimidad del producto (NFR-CUM-005).

### Reglas de Negocio

- **RN-01 — Documentos a descargar:** los que tienen estado "seleccionado" o "contenedor por expandir" en la priorización vigente (HU-015) y aún no están "descargado". También los archivos que el Administrador marque para redescarga.
- **RN-02 — Solo la URL oficial:** se usa exclusivamente `url_descarga_documento` registrada para el documento, con método GET, sin construir ni adivinar otras rutas. Se siguen como máximo 5 redirecciones y solo hacia dominios de la lista de dominios oficiales permitidos (configuración inicial: `community.secop.gov.co`); una redirección a otro dominio produce "descarga bloqueada" con motivo "redirección fuera de los dominios permitidos".
- **RN-03 — Prohibición de evasión:** el sistema nunca resuelve ni envía respuestas a un CAPTCHA, nunca envía credenciales, cookies de sesión de usuario ni cabeceras que simulen un navegador de una persona, y nunca rota direcciones o identidades para eludir un bloqueo. Las solicitudes se identifican con un User-Agent propio del producto que incluye un contacto (configurable).
- **RN-04 — Detección de bloqueo:** se considera bloqueo una respuesta 401 ("requiere autenticación"), 403 ("acceso denegado"), o una respuesta HTML cuando se esperaba un archivo y su contenido incluye un CAPTCHA o un formulario de inicio de sesión ("CAPTCHA detectado" / "requiere autenticación"). Un bloqueo no se reintenta y genera aviso al Administrador con proceso, documento, URL y motivo.
- **RN-05 — Suspensión por bloqueos repetidos (configurable):** si en una ejecución se producen N bloqueos consecutivos (configuración inicial: 5), se suspenden las descargas restantes de esa ejecución, los documentos pendientes quedan "pendiente de descarga", la ejecución queda "suspendida por bloqueos" y se avisa al Administrador. La siguiente ejecución programada vuelve a intentarlo.
- **RN-06 — Fallos temporales:** tiempo de espera agotado (configuración inicial: 120 segundos por solicitud), error de conexión, respuesta 429, respuesta 5xx o contenido truncado (menos bytes que la cabecera de longitud) se reintentan con espera exponencial (configuración inicial: 3 reintentos; esperas de 2, 4 y 8 segundos). Si la respuesta 429 trae una espera indicada por el servidor de hasta 10 minutos, se respeta esa espera. Agotados los reintentos: "descarga fallida definitiva" con último error y número de intentos.
- **RN-07 — No disponible:** 404 o 410 → "documento no disponible en la fuente", sin reintentos.
- **RN-08 — Tamaño máximo (configurable):** configuración inicial 200 MB por archivo. Si la cabecera de longitud lo supera, no se descarga; si la descarga lo supera en curso, se interrumpe. En ambos casos no se conserva contenido parcial y el estado es "excede tamaño máximo".
- **RN-09 — Ritmo (configurable):** se espera un mínimo entre solicitudes consecutivas al mismo dominio (configuración inicial: 1 segundo) y como máximo se ejecutan 2 descargas en paralelo.
- **RN-10 — Resultado de una descarga exitosa:** contenido guardado, fecha y hora de descarga, tamaño en bytes, tipo de contenido informado, hash SHA-256 del contenido, número de intentos y estado "descargado". Una respuesta 200 con 0 bytes se guarda como "descargado" con tamaño 0.
- **RN-11 — Idempotencia:** un documento "descargado" no se descarga de nuevo, salvo redescarga solicitada por el Administrador. Ante una redescarga, si el hash cambia, se conserva también el contenido anterior y se registra el cambio de hash con fecha.
- **RN-12 — Liberación de cupo:** los estados "descarga fallida definitiva", "descarga bloqueada", "documento no disponible en la fuente" y "excede tamaño máximo" son definitivos para la ejecución y disparan el recalculo de la priorización del proceso (HU-015).
- **RN-13 — Estado del proceso:** cuando todos sus documentos a descargar están en estado final, el proceso pasa a "documentos obtenidos", con el número de descargados y de fallidos por motivo. Si ninguno se descargó, el estado es "documentos obtenidos" con 0 descargados y los motivos.
- **RN-14 — Registro de ejecución:** inicio, fin, estado (completa / parcial / suspendida por bloqueos), documentos intentados, descargados, fallidos por motivo y bloqueos.

### Interfaz

Sin interfaz gráfica obligatoria. Los resultados se consultan por proceso y documento mediante consultas o registros; los avisos de bloqueo llegan al Administrador por el mecanismo de alertas definido en arquitectura (correo, registro de alertas u otro).

### Sistemas Externos (Si aplica)

- **Servidor de descarga de documentos de SECOP II** (`community.secop.gov.co/Public/Archive/RetrieveFile/Index?DocumentId=…`), referenciado desde los datasets oficiales de Archivos Descarga. Público, sin autenticación según D1/D4.

---

## Contexto y Referencias

**Épica origen:** [De Documentos a Datos Comparables](../../../epicas.md#épica-002-de-documentos-a-datos-comparables)

**Exclusiones de la Épica:**
- NO incluye el agente de investigación (siguiente incremento agéntico, post-MVP).
- NO incluye la extracción y comparación de precios de múltiples oferentes (FR-026, pospuesta por D4).
- NO incluye la extracción de cláusulas contractuales, garantías ni condiciones de entrega.
- NO incluye procesar todos los documentos de cada proceso, solo los priorizados.
- NO incluye la extracción de categorías distintas a televisores.
- NO incluye la base de conocimiento RAG sobre los documentos.

**Historias relacionadas:** HU-014 (URL oficial registrada), HU-015 (selección y recalculo), HU-017 (vacíos, en blanco y duplicados), HU-018 (comprimidos), HU-021 (copia de evidencia).

---

## Supuestos

> Elementos inferidos por la IA que NO estaban explícitos en el PRD o la Épica. Todos los supuestos han sido resueltos: convertidos en reglas de negocio explícitas o eliminados mediante reformulación. Si aparece algún supuesto no resuelto, esta HU NO está lista para desarrollo.

- Reintentos con espera exponencial (3) por analogía con NFR-DAT-005; tiempo de espera inicial 120 s → RN-06.
- Tamaño máximo inicial por archivo de 200 MB → RN-08.
- Ritmo inicial de 1 segundo entre solicitudes al mismo dominio y 2 descargas en paralelo → RN-09.
- Suspensión de la ejecución tras 5 bloqueos consecutivos → RN-05.
- Se usa User-Agent propio con contacto también para SECOP II, por coherencia con NFR-CUM-004 → RN-03.

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
| 2026-10-02 | 1.0 | Historia generada desde Épica ÉPICA-002 | Juan Camilo (PO) |

---

> **Método Ceiba estimar hus** v6.1.95 | Modelo: claude-opus-5-5 | Usuario: Juan Camilo | Fecha: 2026-10-05
