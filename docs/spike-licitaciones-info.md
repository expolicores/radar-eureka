# Spike aislado de Licitaciones.info

## Autenticación experimental con navegador

Playwright es opcional y se instala solo en la venv local con
`python -m pip install -r scripts/requirements-licitaciones-spike.txt`. Usa Edge
ya instalado; no agrega dependencias productivas ni descarga otro navegador.

Desde `backend`, ejecutar:

```powershell
.\.venv\Scripts\python.exe scripts/login_licitaciones_info.py
```

Abre un navegador visible. El usuario realiza login/CAPTCHA manualmente y una
búsqueda normal en Contratos. Solo después de observar un POST get-info 200 JSON
se conserva el estado y se verifica el mismo endpoint con `context.request`.
No se automatizan formularios ni CAPTCHA, ni se ejecutan documentos/extracción.
La ventana permanece abierta incluso después de validar o si falla la navegación.
Se cierra al cerrarla manualmente o al alcanzar el timeout amplio de 120 minutos
(configurable con `--timeout-minutes`, hasta 480). La validación hace un solo POST.
Los logs `browser-network-*.jsonl` registran endpoint sanitizado, método, status
y Location redactado de get-info, get-conteo, get-filtro y respuestas HTTP >= 300
de Licitaciones.info. Nunca guardan query, fragment, cuerpos ni headers secretos.
Un `200 JSON` no garantiza que la SPA haya terminado de cargar correctamente.

Si ya existe un estado guardado, no se sobrescribe: nuevas capturas validadas
se guardan como `storage_state.candidate-*.json` y headers/presencia equivalentes.
Las revalidaciones escriben `auth_validation.<id>.json` sin modificar el estado
anterior ni su diagnóstico histórico. No se reemplaza automáticamente la sesión
canónica por una captura incompleta.

Artefactos bajo `backend/.local/spike_licitaciones_info/`, todos ignorados por Git:

- `storage_state.json`: cookies y almacenamiento del contexto, contiene secretos.
- `request_headers.json`: headers mínimos de la consulta, puede contener tokens CSRF.
- `browser_header_presence.json`: solo nombres/presencia, sin valores.
- `auth_validation.json`: resultado 200 JSON, Location redactado y comparación
  de presencia de headers del navegador frente a context.request y al cliente anterior.

No se almacenan datos del formulario de login, usuario ni contraseña desde el script.
No se imprimen cookies/tokens ni errores crudos de Playwright. Los dos primeros
archivos son privados y no deben compartirse. `storage_state` comparte cookies
con `context.request`; los tokens CSRF observados se reutilizan solo dentro de
este experimento. Las redirecciones de las requests API están deshabilitadas.

Revalidación independiente sin abrir interfaz ni ejecutar el funnel:

```powershell
.\.venv\Scripts\python.exe scripts/login_licitaciones_info.py --validate-only
```

El spike admite `--storage-state .local/spike_licitaciones_info/storage_state.json`
para usar la misma sesión gestionada por Playwright y `--auth-check-only` para
detenerse después del POST get-info. Mantener `--session-file` para el origen y
configuración local; con storage_state no se requiere cookie copiada manualmente.
No ejecutar el resto del spike hasta confirmar primero la autenticación.

Diagnóstico del cliente anterior: HTTP 302 hacia
`https://col.licitaciones.info/cliente/contratos`, sin seguir redirección. No incluía
X-Requested-With. Esa diferencia no demuestra por sí sola la causa; la comparación
definitiva requiere observar una solicitud 200 del navegador.

Script experimental: `backend/scripts/spike_licitaciones_info.py`. No está conectado
a Radar, CLI productiva, scheduler, API ni UI. No crea motores o sesiones DB,
alertas, migraciones ni documentos oficiales. No consulta Socrata.

## Preparación local

Se ejecuta con la venv del backend (incluye `httpx` como dependencia de desarrollo).
Reutiliza la configuración OCR de `backend/.env` y los mismos lectores aislados,
Tesseract y reglas estructuradas existentes. No instala motores ni cambia reglas.

Guardar la sesión manual en `backend/.local/spike_licitaciones_info/session.json`,
que debe estar ignorado por Git. Alternativamente usar variables de entorno con
los mismos nombres; las variables tienen precedencia. Nunca pegar la sesión en
archivos versionados, argumentos CLI ni conversaciones.

Claves del objeto JSON local:

- `LICITACIONES_BASE_URL`: origen HTTPS exacto que usa la sesión de navegador,
  sin ruta; dominio `licitaciones.info` o subdominio suyo. No se asume un subdominio.
- `LICITACIONES_COOKIE`: header Cookie de la sesión propia autorizada.
- `LICITACIONES_X_CSRF_TOKEN`: valor de X-CSRF-TOKEN, si la sesión lo requiere.
- `LICITACIONES_X_XSRF_TOKEN`: valor de X-XSRF-TOKEN, si se requiere.
- `LICITACIONES_BOYACA_LOCATION_IDS`: opcional, lista validada de IDs municipales
  separados por comas. En su ausencia se carga por defecto
  `backend/scripts/.local/licitaciones_boyaca_ids.txt` con los 123 IDs proporcionados.
  `--location-ids-file` permite indicar otra ruta local. No se inventan IDs ni se
  sustituyen por códigos DANE. `backend/scripts/.local/` está ignorado por Git.
- `LICITACIONES_PROFILE_ID`: opcional; por defecto `1086005`, proporcionado para el spike.

No se imprime ni se copia la sesión a los resultados. Los errores de librerías se
reportan por tipo, sin cuerpos HTTP ni headers. No hay login automatizado, CAPTCHA
ni seguimiento de redirecciones autenticadas. Ante 401/403/419, redirección o 429,
el cliente detiene nuevas solicitudes autenticadas.

## Ejecución (solo tras autorización de la prueba real)

Desde `backend`:

```powershell
.\.venv\Scripts\python.exe scripts/spike_licitaciones_info.py --region Boyaca --object refrigerio --max-processes 30 --max-document-processes 3 --max-documents 2 --session-file .local/spike_licitaciones_info/session.json
```

Solo consulta la primera página de descubrimiento, orden descendente por
FechaPublicacion, hasta 30 filas. Filtra localmente SECOP II (`id_fuente_contract=3`
o `key_config=secop2`), Boyacá y duplicados por idContrato. No aplica filtros
productivos de vigencia o comerciales. Conserva los campos de metadata recibidos.

Consulta documentos de hasta tres procesos y descarga hasta dos documentos por
proceso, priorizando invitación, estudios previos, especificaciones, anexo técnico
y ficha técnica. No descarga otros formatos ni documentos sin nombre prioritario.
Pagina inventario hasta vacío; páginas repetidas o diez páginas sin fin generan
diagnóstico de inventario incompleto, nunca éxito silencioso.

Máximo 60 requests presupuestados por ejecución; al menos 2,1 segundos entre
operaciones HTTP. Cada descarga reserva conservadoramente seis requests por los
posibles saltos del downloader existente. Timeout API 20 segundos, un reintento
para red/5xx, ninguno para 429. Descarga hasta 20 MiB y 60 segundos, con validación
HTTPS de cada salto SECOP, streaming, validación de formato/hash y movimiento
atómico compartidos. Las cookies de Licitaciones.info no se envían a SECOP.

## Resultados y límites de validación

Cada ejecución crea `backend/.local/spike_licitaciones_info/run-*/results.json`
y `binaries/sha256/…`, fuera del storage oficial. Los `.part` usan el mecanismo
existente; no se presentan como documentos válidos. Estos resultados son locales,
ignorados, y permanecen para revisión; se pueden borrar manualmente después.

El JSON incluye inventario, documentos, errores por etapa, fragments con provenance,
modo native/ocr/mixed, diagnósticos de cobertura OCR y señales estructuradas con
evidencia. Un OCR fallido/truncado conserva diagnósticos y texto nativo; no se afirma
cobertura completa. `extraction_mode` identifica el texto producido; `status` y
`diagnostics` indican si la recuperación fue suficiente. Los grupos de señales usan
solo los tipos de hechos que el extractor actual reconoce. Una lista vacía no
demuestra ausencia de requisitos en el documento. No se promete detección exhaustiva
ni consolidación canónica.

Las pruebas de parsing usan contratos sintéticos basados en los campos descritos.
Los nombres exactos de las claves documentales/wrappers todavía necesitan una muestra
anonimizada o la primera prueba real autorizada. Un contrato desconocido falla
explícitamente; no se interpreta como inventario vacío. No se ha ejecutado una
consulta real a Licitaciones.info durante la implementación.

Pruebas locales, sin red ni DB:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/unit/test_spike_licitaciones_info.py -q
```
