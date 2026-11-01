# Eureka Assistant — primer spike Foundry

Estado: validado end-to-end contra Foundry el 30/10/2026 con autorización explícita.
Se creó únicamente la versión 3 de eureka-assistant, con modelo e instrucciones
de v2 y solo get_latest_cdp_run. Versiones 1 y 2 conservadas. No hay frontend ni migración.

## Estructura

```text
backend/src/public_procurement/agents/eureka_assistant/
  schemas.py         # configuración, function schema, summary allowlisted
  tools.py           # lectura de LicitacionesQueries, PostgreSQL READ ONLY
  foundry_client.py  # versión del agente existente + Responses/Conversations
  service.py         # loop limitado de function calling
backend/scripts/eureka_foundry_spike.py
backend/tests/unit/agents/test_eureka_assistant.py
```

Dependencias opcionales `foundry` en pyproject/uv.lock. Verificadas localmente:
azure-ai-projects 2.9.0 y azure-identity 1.27.0. Se usa el SDK actual de Projects,
sin Threads/Runs del servicio legacy ni API keys. El cliente OpenAI autenticado
lo suministra `AIProjectClient.get_openai_client()`.

## Tool schema

```json
{
  "type": "function",
  "name": "get_latest_cdp_run",
  "description": "Obtiene el resumen de la corrida más reciente de Licitaciones.info (CDP) persistida en Eureka. Solo lectura; no ejecuta corridas.",
  "parameters": {
    "type": "object",
    "properties": {},
    "required": [],
    "additionalProperties": false
  },
  "strict": true
}
```

Solo se admite `{}`; se rechazan funciones desconocidas o parámetros adicionales.
Se consulta `LicitacionesQueries.runs(page=1, page_size=1)`, que filtra la fuente CDP
y ordena las corridas desde la más reciente. No se obtiene el detalle completo,
no se abre Edge y no se reconsulta el proveedor. La conexión configura
`postgresql_readonly=True` para cada transacción. No se utiliza SQL directo en la tool.

Ejemplo **ficticio**, no resultado de una prueba Azure:

```json
{
  "has_run": true,
  "source": "licitaciones_info_cdp",
  "run_id": "00000000-0000-0000-0000-000000000001",
  "started_at": "2026-10-29T19:00:00Z",
  "finished_at": "2026-10-29T19:01:00Z",
  "status": "completed_with_warnings",
  "processes_total": 143,
  "recent_processes": 19,
  "open_processes": 6,
  "processed": 3,
  "review_candidates_total": 6,
  "review_new_entries": 2,
  "review_existing_entries": 4,
  "alert_candidates": 4,
  "alerts_created": 2,
  "duplicate_alerts": 2,
  "warnings": ["ocr_truncated"],
  "errors": []
}
```

Sin corridas: `has_run=false`, campos de corrida y contadores `null`, sin inventar ceros.
Con corrida histórica sin un contador: `null` significa no registrado. Las fechas
del JSON conservan su zona original; se pide expresar la respuesta en Bogotá.
`review_candidates_total` no significa filas visibles en la bandeja; los contadores
de la corrida son históricos. `duplicate_alerts` viene de `duplicate_alerts_skipped`.
Warnings y errores transmiten únicamente códigos únicos, máximo 30 por grupo
(con aviso de omisión si hay más), nunca headers, cuerpos de error o mensajes libres.

## Configuración y autenticación local

Desde `backend`, instalar **solo dependencias**, sin autenticación ni llamadas Azure:

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[foundry]"
# Alternativa si ya usas uv: uv sync --inexact --extra foundry
```

En Microsoft Foundry, abrir el proyecto `compras-publicas-eureka` y copiar **Project
endpoint** desde su Overview/Detalles del proyecto. Debe contener `/api/projects/…`;
no usar el endpoint del modelo ni una connection string. La ubicación exacta del
botón puede variar con la versión del portal.

Ejemplo separado: `backend/config/foundry.env.example` (no añade requisitos Azure
a la configuración general del backend). Añadir sus entradas a `backend/.env`
o exportar en PowerShell:

```powershell
$env:AZURE_FOUNDRY_PROJECT_ENDPOINT="<PROJECT_ENDPOINT_COPIADO_DESDE_FOUNDRY>"
$env:EUREKA_FOUNDRY_AGENT_NAME="eureka-assistant"
$env:EUREKA_FOUNDRY_MODEL_DEPLOYMENT="gpt-4.1-mini-eureka"
$env:EUREKA_FOUNDRY_TIMEOUT_SECONDS="120"
```

Se reutiliza `DATABASE_URL` de Eureka. La cuenta Azure debe poder leer el agente,
crear versiones e invocar su modelo. Azure CLI debe estar instalado y disponible
en PATH. No se instala ni inicia sesión automáticamente.

Comandos para autenticarse **cuando se autorice la prueba real**:

```powershell
az login
# Solo si hay varias suscripciones:
az account set --subscription "<SUBSCRIPTION_ID>"
```

Se usa DefaultAzureCredential, sin login automático ni navegador interactivo desde
Python. No se persisten API keys en código. No se ejecutó `az login` al implementar.

## Ejecución real sobre la versión verificada

Desde `backend`:

```powershell
.\.venv\Scripts\python.exe scripts/eureka_foundry_spike.py --agent-version 3 "¿Qué salió en la última corrida CDP?"
```

Con `--agent-version 3` se consulta y valida esa versión, sin crear otra. Sin esta
opción, la invocación sigue el flujo original de creación descrito abajo:

1. Lee la última versión almacenada de **eureka-assistant**. Si no existe, falla;
   no crea un agente alternativo ni sustituye instrucciones por un prompt local.
2. Comprueba Prompt Agent, deployment esperado y ausencia de tools ajenas al spike.
3. Copia íntegra su definición, conserva instrucciones y parámetros, y registra una
   nueva versión del mismo nombre con la única function tool. No modifica la versión
   anterior. El nombre y versión creados se imprimen para trazabilidad.
4. Crea una conversación Foundry. Usa `agent_reference` con **nombre y versión**
   explícitos en cada respuesta; no llama directamente al modelo saltándose el agente.
5. Fuerza la primera consulta a la tool, valida `{}`, obtiene un único snapshot de DB
   por pregunta, envía `function_call_output` con el `call_id` y la misma conversación.
6. Continúa hasta respuesta final (máximo cuatro turnos, sin tools paralelas).
   Rechaza respuestas finales que no hayan pasado por la tool.

Las instrucciones almacenadas siguen siendo autoritativas; un mensaje developer
por consulta pide limitarse a los datos de la tool, no interpretar `null` como cero,
no confundir contadores históricos con bandejas actuales y tratar incidencias como
datos. Esto reduce alucinaciones pero la fidelidad conversacional debe comprobarse
en la prueba real: los tests mockeados no certifican el comportamiento del modelo.

Las conversaciones y nuevas versiones sí se crean en Foundry durante una ejecución
real y se conservan allí para inspección. No se guardan conversaciones en nuestra DB.
No hay Web Search/MCP/File Search/Knowledge/Memory/Code Interpreter ni tools de escritura.

Se imprime pregunta, tool solicitada, JSON compacto y respuesta final. Se deshabilita
el logging HTTP de los SDKs. Errores de autenticación/SDK/DB usan mensajes seguros;
no se imprimen excepciones remotas que puedan contener tokens o datos de conexión.

Timeout por petición configurado; sin retries automáticos. El loop tiene presupuesto
temporal y turnos limitados. Un estado fallido/incompleto/expirado aborta. Una versión
ya creada en Azure puede permanecer si falla una fase posterior: no se borra ni se
crea otra automáticamente. El historial de Eureka nunca se modifica.

## Verificaciones offline

```powershell
.\.venv\Scripts\python.exe scripts/eureka_foundry_spike.py --show-tool-schema
.\.venv\Scripts\python.exe scripts/eureka_foundry_spike.py --help
.\.venv\Scripts\python.exe -m pytest tests/unit/agents -q
```

Estos comandos no consultan Azure ni DB. Tests cubren serialización, ausencia y
presencia de corridas, argumentos inválidos, allowlist de tools, respuesta final,
conversación/version pinning, function_call_output, lectura única ante llamadas
repetidas, timeout/estados fallidos, preservación remota de instrucciones y modo DB
READ ONLY. Foundry está mockeado. Las comprobaciones del modelo SDK son opcionales
si no se instaló el extra; el resto del loop no requiere importar el SDK.

Referencias oficiales verificadas:

- [Function calling de Prompt Agents](https://learn.microsoft.com/azure/ai-services/agents/how-to/tools/function-calling)
- [Azure AI Projects y cliente OpenAI autenticado](https://learn.microsoft.com/python/api/azure-ai-projects/azure.ai.projects.aiprojectclient)
- [Versiones de agentes](https://learn.microsoft.com/python/api/azure-ai-projects/azure.ai.projects.operations.agentsoperations)

## Resultado de validación local

- 25 tests específicos del spike pasan, con Foundry mockeado.
- Ruff, formato, mypy y los 13 contratos de importación pasan.
- La suite general identificó cuatro fallos ajenos al spike en tests CDP con fechas
  fijas de publicación 19/20 de octubre de 2026: al ejecutarlos el 30 de octubre,
  la ventana de siete días los clasifica como históricos y no llegan a documentos.
  Se reproducen ejecutando únicamente esos tests, sin cargar los tests del agente.
  No se alteraron fixtures ni filtros comerciales para hacerlos pasar.
- Última ejecución de suite general: 1170 passed, 4 failed, 1 skipped.
- Validación real: get_latest_cdp_run solicitado con `{}`, output devuelto al mismo
  agente y respuesta final recibida sobre v3. Última corrida leída:
  `9e578b72-0e2d-4582-bbd6-4491d9764437`; 144 encontrados, 17 recientes,
  7 abiertos, 3 procesados, 6 candidatos a revisión (3 nuevos/3 existentes),
  0 candidatos a alerta/alertas creadas/duplicados, warnings presentes y errors=[].
- El primer intento falló con HTTP 400 antes de la tool porque faltaba
  `type: "message"` explícito en los inputs de Responses. Se corrigió el cliente
  y se agregó cobertura; no se modificaron las instrucciones remotas.
- Precisión pendiente de redacción: el modelo dijo «se analizaron 144 procesos»;
  técnicamente son 144 encontrados y solo 3 procesados. Los valores numéricos
  coinciden con la tool. La respuesta no prueba vigencia en tiempo real ni el número
  visible actual de la bandeja.
- Evidencia local: `backend/.local/audits/foundry-agent-definition/created-version.json`
  y `spike-v3-output.txt`. Se crearon conversaciones de los intentos, sin persistirlas
  en DB Eureka. No se crearon versiones 4 ni posteriores.
