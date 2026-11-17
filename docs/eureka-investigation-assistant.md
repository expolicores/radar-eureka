# Asistente de investigación (read-only)

Identidad local: `investigation-assistant`, mostrable como **Asistente de investigación**. Es independiente del asistente comercial Eureka. Solo explica y prioriza resultados persistidos; no inicia corridas, no consulta proveedores ni Internet, no descarga documentos, no hace OCR, no recalcula matching/scoring/comparaciones/señales y no usa SQL.

## Infraestructura y seguridad

Reutiliza la configuración `FoundrySettings`, el proyecto, deployment y `DefaultAzureCredential` existentes. Ejecuta Responses con prompt y siete function tools propios, `parallel_tool_calls=false`, `store=false`, sin retries. No crea ni modifica una definición/version remota de `eureka-assistant`. No habilita Web Search, MCP, intérprete de código ni otras tools hospedadas.

La configuración del SDK y credenciales se carga al preguntar, no al iniciar el backend. Las consultas de estado provisional, resultado ausente o corrida inexistente pueden responderse localmente sin abrir Foundry. El prompt completo está en `backend/src/public_procurement/agents/investigation_assistant/policy.py`.

Arquitectura:

```text
InvestigationAssistant → siete tools → investigation.services
→ InvestigationAssistantQueries → InvestigationRunRepository
→ ResearchRun + result.json / present_market_reports
```

El repositorio lee los formatos existentes sin construir workers ni ejecutar recuperación de corridas. Nunca lee el último informe publicado como sustituto de un UUID solicitado. No crea directorios ni actualiza archivos. Los recibos de proveedores permanecen en disco; solo se proyectan campos permitidos. Warnings/errors se reducen a códigos. Se excluyen headers, payloads crudos, credenciales y paths.

## Selección

- Sin run explícito: último por `created_at` entre `runs` y `market-date-runs`.
- `run_id` del request o UUID en el mensaje: ese run exacto, sin fallback.
- «corrida de hoy»: día de creación en America/Bogota, no fecha de publicación investigada.
- «última corrida Estado vs mercado privado» / «la de mercado privado»: filtro de run_type.
- Preguntar qué productos llegaron al mercado privado NO cambia por sí solo el tipo de corrida seleccionada.
- «esta corrida» en una conversación conserva el UUID previamente resuelto. Si cambia el run, no se envía historia de otro run al modelo.
- No implementa búsqueda histórica compleja. Los antiguos spikes por producto sin contrato de corrida por fechas no se promueven a runs ni se les inventan fechas.

## Tools

1. `get_latest_investigation_run`: metadata del run resuelto para este turno.
2. `get_investigation_run(run_id)`: metadata del UUID fijado.
3. `get_run_products(run_id)`: productos, entidad, identidad, cantidad, estado público, elegibilidad, razones y provenance.
4. `get_run_benchmarks(run_id)`: observaciones, retailers, precios persistidos, suficiencia, limitaciones y captura.
5. `get_run_comparisons(run_id)`: únicamente comparaciones existentes y elegibles de ambas líneas.
6. `get_run_signals(run_id)`: únicamente señales existentes.
7. `get_run_review_candidates(run_id)`: recomendaciones documentales basadas en flags/razones existentes; no inserta en Merecen Revisión ni en casos.

Las tools se restringen al run seleccionado. No aceptan SQL, paths, providers, scripts ni acciones. Se usan snapshots por turno y cache de lecturas. Preguntas sobre hallazgos o prioridades requieren productos + benchmarks + comparaciones + señales + revisión antes de aceptar la respuesta final. Máximo 12 llamadas/turnos y timeout configurado de Foundry.

Los resultados están acotados (30 productos/revisiones, 20 benchmarks/comparaciones/señales), con total y truncated. Provenance documental también indica su límite. Las referencias de la respuesta salen de DTOs realmente leídos, nunca del texto inventado por el modelo.

Las razones de revisión son documentales/investigativas (conflictos, evidencia pública sin resolver, errores/cobertura y señal existente), no scoring comercial ni pertenencia a la bandeja comercial. Las observaciones parciales de extracción no se suman otra vez a los productos reconstruidos de la corrida privada.

## Endpoint

`POST /api/v1/investigation/assistant/chat`

```json
{"message":"¿Qué encontró la última corrida investigativa?","conversation_id":null,"run_id":null}
```

```json
{"conversation_id":"<UUID>","response":"...","run_references":["<UUID>"],"process_references":["CO1.REQ...."]}
```

Usa el mismo `current_user_provider` del asistente existente. Conversaciones aisladas por dueño en memoria, TTL 30 minutos, máximo 50 y 10 turnos; una consulta simultánea por conversación. Reiniciar el backend pierde la conversación, no los resultados investigativos. Errores no revelan excepciones de SDK ni credenciales. No se implementa UI en este incremento; `SUGGESTED_QUESTIONS` prepara los textos.

## CLI (desde backend)

```powershell
.\.venv\Scripts\python.exe scripts/eureka_investigation_assistant.py "¿Qué encontró la última corrida investigativa?"
.\.venv\Scripts\python.exe scripts/eureka_investigation_assistant.py "¿Qué revisarías primero?" --run-id <UUID>
```

Diagnóstico sin Foundry ni conexiones externas:

```powershell
.\.venv\Scripts\python.exe scripts/eureka_investigation_assistant.py --snapshot
```

`--snapshot` imprime metadata, DTOs de las cinco lecturas y una síntesis determinista. Está identificado como `offline_snapshot`: no simula una respuesta real de Foundry.

## Ejemplos y evidencia

Lectura offline real: run `ee517ba9-ab50-4db2-9a65-2ee1a567accd`, Estado vs mercado privado, ventana 02–05/09/2026, completed_with_warnings. Registra 865 descubiertos, 48 seleccionados, 5 productos reconstruidos, 0 elegibles, 0 benchmarks/comparaciones/señales, 13 extracciones fallidas y 41 documentos parciales. Esto describe insuficiencia de evidencia; no ausencia de posibles problemas.

Fixture Samsung: oferta documentada de $3.767.123, dos observaciones privadas high ($1.799.900 y $3.339.900), benchmark insuficiente y ninguna comparación/señal definitiva. Son referencias preliminares para revisar; no se confirma compra aceptada, sobreprecio ni equivalencia histórica de precios. No se ha ejecutado otra búsqueda para generar este ejemplo.

Fixture Estado vs Estado: lee y resume el par elegible y la señal ya guardados, sin volver a calcular diferencia ni umbrales.

## Validación y límites pendientes

Tests con repositorios temporales, Responses simulado y fixtures: selección latest/UUID/tipo/hoy, running/completed/warnings, ausencia de resultados/productos/elegibles, Samsung insuficiente, comparaciones/señales existentes, conflictos/revisión humana, chaining obligatorio, rechazo de tools/UUID ajenos, ownership, errores seguros y ausencia de escrituras.

La implementación inicial se validó offline. La conexión generativa se validó posteriormente el 16/11/2026, como se documenta abajo. No hay migración, dependencias nuevas ni cambios a frontend, matching, señales o al agente comercial. La política y las comprobaciones reducen errores pero no sustituyen la revisión humana; el guard de texto sobre señales/conclusiones es acotado, no una garantía semántica general. No hay histórico de chat persistido ni búsqueda histórica compleja.

## Diagnóstico y validación real Foundry — 16/11/2026

La causa del fallo generativo era la serialización de mensajes: el adaptador enviaba
`{"role":"user","content":"..."}` sin discriminador explícito. El endpoint Projects
Responses rechazó la primera solicitud con HTTP **400**, `invalid_value`, parámetro
`input[1]`, mensaje `Invalid value: ''. Supported values are ... message ...`.
No era falta de resultados locales, ni credencial incorrecta, ni necesidad de crear
un agente remoto. El transporte ahora añade `"type":"message"` a mensajes de
usuario/developer/historial/recordatorios; conserva las llamadas y resultados de
funciones sin alteraciones y no muta el historial original. El comercial ya enviaba
mensajes con ese discriminador.

Comparación con el asistente comercial:

| Aspecto | Comercial | Investigativo |
| --- | --- | --- |
| Proyecto / recurso | compras-publicas-eureka / compras-publicas-eureka-resource | Los mismos |
| Endpoint | `FoundrySettings.azure_foundry_project_endpoint`, Project endpoint `/api/projects/...` | El mismo campo y cliente Projects |
| Deployment | `gpt-4.1-mini-eureka` | El mismo |
| Autenticación | `DefaultAzureCredential(exclude_interactive_browser_credential=True)` | Idéntica; funcionó con Azure CLI existente |
| Cliente | `AIProjectClient.get_openai_client()` | Idéntico SDK y configuración de timeout/retries |
| Agente remoto | Versionado de `eureka-assistant`, `agent_reference` | No requerido: modelo + policy local + siete function tools inline |
| Conversación | `conversations.create()` remota | Historial local acotado, enviado en `input`; `store=false` |
| Ejecución | Responses + function calls | Responses + function calls; sin tools hospedadas |
| Registro tools | Definición/version remota comercial | `TOOL_SCHEMAS` local por request; sin cambios a sus contratos |

La diferencia de conversación/agente es intencional para mantener las capacidades
separadas, y quedó probada funcional: no se creó ni modificó ninguna versión remota.
Identidad lógica: `investigation-assistant`. Las siete tools siguen siendo las listadas
arriba; no Web Search ni acceso a proveedores. Se reutiliza `FoundrySettings` del
comercial, no una configuración paralela ni credenciales nuevas.

Configuración en `backend/.env` o entorno (ejecutar desde `backend`):

- `AZURE_FOUNDRY_PROJECT_ENDPOINT`: requerido.
- `EUREKA_FOUNDRY_MODEL_DEPLOYMENT`: opcional; default `gpt-4.1-mini-eureka`.
- `EUREKA_FOUNDRY_TIMEOUT_SECONDS`: opcional; default 120.
- `EUREKA_FOUNDRY_AGENT_NAME` pertenece al comercial; no selecciona ni modifica
  un agente remoto en este flujo investigativo.
- Autenticación Azure existente por `DefaultAzureCredential`; no necesita API key.
  No se inicia login interactivo automáticamente.

Diagnóstico seguro opcional:

```powershell
.\.venv\Scripts\python.exe scripts/eureka_investigation_assistant.py "¿Qué encontró la última corrida investigativa?" --diagnose
```

La respuesta sigue siendo JSON en stdout. `--diagnose` emite etapas/configuración en
booleanos y nombres/totales de tools completadas en stderr. Ante un fallo, el CLI
muestra código y diagnóstico seguro aun sin ese flag: etapa, clase, HTTP status,
código/param del proveedor y mensaje sanitizado. No vuelca excepción cruda, headers,
tokens, secretos, URLs de conexión ni trazas de credenciales. El endpoint HTTP conserva
su error público acotado. No se añadieron retries.

Se ejecutaron las dos consultas solicitadas con `--diagnose` para conservar el trace:

```powershell
.\.venv\Scripts\python.exe scripts/eureka_investigation_assistant.py "¿Qué encontró la última corrida investigativa?" --diagnose
.\.venv\Scripts\python.exe scripts/eureka_investigation_assistant.py "¿Qué procesos revisarías primero y por qué?" --diagnose
```

Ambas terminaron correctamente, con corrida única
`aea6ad3f-d458-48c5-9f47-f56f919182ca`, Estado vs mercado privado, creada
16/11/2026, ventana investigada 30/05–30/06/2026, `completed_with_warnings`.
En cada consulta se completaron `get_latest_investigation_run` y las cinco lecturas
de resultados. Totales efectivos: 23 productos, 0 benchmarks, 0 comparaciones,
0 señales y 34 candidatos a revisión. No hubo nuevas consultas de mercado,
discovery, descargas ni OCR; se leyeron resultados persistidos.

La primera respuesta explicó insuficiencia de identidad/evidencia y limitaciones
documentales. La segunda propuso casos concretos por razones ya persistidas:
Gabriela Mistral `CO1.REQ.10552481`, Luis Felipe Pinto `CO1.REQ.10512300`, ITM
`CO1.REQ.10545773`, San Pablo `CO1.REQ.10484226` y Maní `CO1.REQ.10555064`.
Las identidades, entidades y razones se contrastaron offline contra los DTOs reales.
No se inventaron benchmarks, comparaciones ni señales.

Evidencia local: `backend/.local/investigation-assistant-foundry-validation/`,
archivos `summary-response.json`, `priorities-response.json`, los diagnósticos y
`local-validation-snapshot.json`. Las respuestas completas se conservan literalmente,
sin corregir retrospectivamente el texto generado.

Deuda observada de calidad conversacional (fuera de este fix de conexión): la tool
de revisión devuelve 30 de 34 elementos (`truncated=true`), pero las respuestas no
explicitaron ese límite. Tampoco citaron documento/página al priorizar. La primera
describió insuficiencia, aunque no reprodujo literalmente la advertencia de que cero
señales no demuestra ausencia de problemas. No se cambió policy/tools ni se hizo
una tercera prueba para ajustar estas formulaciones. La conexión y el function loop
funcionaron; la calidad semántica conserva estos límites de revisión humana.

Nota del entorno de validación: el sandbox no podía leer la caché de Azure CLI;
la prueba autorizada fuera de él obtuvo la credencial correctamente. Ese error de
permisos del entorno es distinto del HTTP400 reproducido y corregido en Foundry.

## Calidad investigativa de respuestas — 17/11/2026

Se ajustó únicamente `policy.py`, sin cambios al transporte, arquitectura, tools ni
contratos. Para consultas de hallazgos, prioridades o falta de comparaciones, las
instrucciones piden explicar primero el bloqueo concreto usando `eligibility_reasons`,
distinguir producto identificado, precio documentado, identidad y elegibilidad, y
priorizar precios documentados con identidad pendiente antes de casos sin precio.
Se requieren ejemplos con código, entidad, producto, cantidad, precio y comprobación
humana pendiente cuando los DTOs los aportan. Las referencias documentales no confirman
por sí mismas la procedencia de un precio ni una compra aceptada.

La presentación se limita a una tabla de 2–5 procesos, seguida del alcance de lectura
(`items`, `total`, `truncated`) y la advertencia expresa de que cero señales no demuestra
ausencia de riesgo. No se hardcodearon los ejemplos/precios del usuario. El test de
regresión verifica que el prompt actualizado llega al modelo y que un precio documentado
con identidad pendiente conserva sus estados, provenance y ausencia de comparaciones,
sin reescribir el recibo. Ese test no simula una garantía de calidad del lenguaje: la
respuesta generativa se contrasta en la prueba real solicitada.

Los resultados de validación y sus iteraciones se conservan como
`quality-20261117-*.json` en `.local/investigation-assistant-foundry-validation/`.
No se generaron nuevas corridas, benchmarks ni señales para esas conversaciones.

## Chat integrado en UI — 17/11/2026

En `/eureka/asistente` hay un selector **Asistente comercial / Asistente investigativo**.
El comercial se abre por defecto y conserva su endpoint `/api/eureka/assistant/chat`,
sus sugerencias y su comportamiento. No se añadió una entrada al menú principal.

Los chats son componentes montados independientes: cada uno conserva en memoria su
`conversation_id`, mensajes, borrador, loading y errores. Cambiar de modo no destruye
la conversación del otro; «Nueva conversación» reinicia únicamente el modo activo.
Una respuesta que llega mientras se muestra el otro modo queda en su chat original.
No hay persistencia de chat en navegador ni nueva persistencia del servidor.

El investigativo envía `message`, `conversation_id` propio y `run_id` a
`POST /api/v1/investigation/assistant/chat`. `run_id` es null por defecto. Se admite
`/eureka/asistente?run_id=<UUID>`; el comercial sigue siendo el modo inicial y no recibe
ese contexto. Si cambia el UUID de la URL, se inicia un contexto investigativo nuevo.
Todavía no se añade navegación contextual desde otras pantallas.

Las respuestas incluyen «Corrida relacionada», un recuento de procesos relacionados
y un desplegable limitado a cinco IDs, sin inferir referencias del texto libre.
Al abrir una referencia se consulta metadata existente de `runs/{UUID}` y, solo ante
404, `market-runs/{UUID}` para seleccionar la ruta `/explorar` adecuada. No se abre un
resultado de otra corrida ni se adivina el tipo por el UUID. Los errores de navegación
se muestran sin detalles técnicos. Para múltiples corridas se evita atribuir un
proceso a una de ellas sin evidencia.

El renderizador existente se reutiliza; las tablas Markdown se habilitan solo para
el investigativo, con contenido escapado y scroll horizontal local. No se activa HTML
ni enlaces arbitrarios del modelo. Cuatro sugerencias investigativas, copy específico,
selector con estado accesible y layout responsive mantienen el sistema visual actual.

Pruebas: separación de endpoints/contextos/IDs, conservación de historiales y borradores,
respuestas en curso al alternar modos, reset activo, sugerencias, UUID opcional, loading,
error/reintento, respuesta vacía, referencias resumidas, rutas de ambos tipos de corrida
y tablas seguras. Las capturas desktop/mobile y recibos de validación se conservan en
`backend/.local/investigation-assistant-ui/`; las capturas con respuesta previamente
guardada están identificadas como prueba visual simulada.

Validación real posterior: una pregunta desde la página, sin interceptar HTTP,
completó UI → endpoint investigativo → Foundry con HTTP200 y corrida
`aea6ad3f-d458-48c5-9f47-f56f919182ca`. El borrador comercial y el historial investigativo
se conservaron al alternar. Capturas `live-*` y `live-ui-response.json` preservan esta
validación; no se ejecutó una nueva corrida investigativa.
