# Asistente Eureka — chat V1

Vista: `/eureka/asistente`, accesible desde la navegación existente. API:
`POST /api/eureka/assistant/chat` (el prefijo `/api` sigue la convención del proyecto).

Flujo: React → FastAPI → AssistantChat → EurekaAssistant existente → Foundry →
seis tools de lectura → facades/repositorios existentes. Web Search hospedada puede
complementarlas bajo demanda (versión 12; ver eureka-assistant-web-search.md).
No hay SQL en la API ni llamadas de React a Azure. No se agregaron funciones internas,
File Search, acciones de negocio, memoria en DB ni streaming. No hay migración.

## Contrato HTTP

Primera pregunta:

```json
{
  "message": "Revisa la última corrida CDP y dime qué viste interesante",
  "conversation_id": null
}
```

Respuesta (ejemplo de estructura):

```json
{
  "conversation_id": "88cc44ee-43d2-49eb-b695-323d089aab50",
  "message": "Respuesta del agente con párrafos, listas y **negrilla**.",
  "external_references": [],
  "web_searches": [],
  "process_references": [
    {
      "identity": "secop:CO1.NTC.11147197",
      "process_code": "MC-CMC-003-2026",
      "entity": "Concejo Municipal Corrales",
      "municipality": "Corrales",
      "department": "Boyacá",
      "source_url": null
    }
  ]
}
```

Para continuar, enviar el mismo `conversation_id` del backend. No es un ID de
Azure. La respuesta no incluye agent reference, tool schemas, outputs completos,
credenciales ni project endpoint. El contrato OpenAPI y los tipos de React están
actualizados (`frontend/src/api/openapi.json` y `schema.ts`).

message: 1–4000 caracteres, sin admitir mensajes vacíos/solo espacios. Se rechazan
campos adicionales e identificadores que no sean UUID del backend.

## Contexto temporal

- El backend mantiene en memoria el vínculo UUID propio → conversación remota y
  versión del agente; no guarda el chat en PostgreSQL ni usa almacenamiento del navegador.
- TTL de inactividad: 30 minutos; máximo 20 turnos y 50 conversaciones por worker.
  Una conversación solo admite un turno simultáneo.
- La versión existente se valida en modo lectura y queda fijada para la conversación.
  La API nunca llama create_version. Herramientas/instrucciones remotas no se modifican.
- El historial visual dura mientras está montada la vista. Recargar/salir de la
  página, reiniciar backend o expirar el contexto inicia una conversación nueva.
- V1 está pensada para un worker local. Varios workers requieren afinidad de sesión
  o una decisión posterior sobre almacenamiento compartido; no se añadió ahora.
- Se reutiliza current_user_provider, igual que las demás vistas. La app conserva
  su acceso local/demo actual; esto no agrega un sistema de autenticación.
- Azure conserva los conversation/response items según su servicio/configuración;
  el TTL local no promete borrar esos registros del proveedor. No se implementa
  memoria propia de largo plazo ni se reutiliza contexto tras su expiración local.

## Referencias y presentación

Las referencias se proyectan únicamente desde resultados estructurados reales de
tools (detalle, evidencia y listas consultadas). No se extraen del texto del LLM,
no se inventan a partir de códigos y no se hacen consultas extra para completar
tarjetas. Se deduplican por identidad exacta, con máximo 20 referencias.

external_references representa por separado citas nativas de Web Search, sin
crear procesos de Eureka. web_searches contiene consultas/acciones y fuentes
públicas reportadas por el proveedor, sin IDs Azure ni schemas de tools. Las URLs
externas no se extraen de texto libre del modelo en React.

La sección se llama «Procesos consultados»: consultar una lista puede incluir
casos que el agente no termina recomendando. Las tarjetas no son una decisión
comercial nueva. Usan el detalle interno existente
`/eureka/revision/:identity`, que admite procesos persistidos. Ver un proceso no
lo inserta en la bandeja ni guarda una valoración humana.

AssistantText permite párrafos, saltos de línea, listas y negrilla con elementos
React; nunca usa dangerouslySetInnerHTML ni interpreta HTML/links arbitrarios.
Las entidades y códigos de las tarjetas también se escapan como texto.

El formulario admite Enter, Shift+Enter, botón Enviar y tres preguntas sugeridas.
Desactiva envíos duplicados durante «Consultando Eureka…», desplaza al último
mensaje y conserva la pregunta para reintentar si hay error.

## Errores y registros

Errores públicos contienen solo `code`, `message` seguro y `reset_conversation`.

| Caso | Código | HTTP |
| --- | --- | --- |
| Configuración ausente/inválida | azure_configuration_missing | 503 |
| SDK/Foundry no disponible | foundry_unavailable | 502/503 |
| Timeout | timeout | 504 |
| Fallo de tool | tool_failure | 502 |
| Respuesta vacía/no sustentada | empty_response | 502 |
| Contexto expirado/desconocido/de otro usuario | conversation_expired | 404 |
| Turno simultáneo | conversation_busy | 409 |
| Límite de turnos | conversation_limit | 409 |
| Capacidad temporal agotada | assistant_busy | 429 |

El frontend muestra mensajes propios amigables y nunca imprime el cuerpo técnico
del proveedor/proxy. Tras un fallo parcial, el backend invalida ese contexto para
no reejecutar function calls pendientes. El historial visual permanece y se indica
que la siguiente consulta usará un contexto nuevo. No hay reintentos automáticos.

Logs: nombre de tool permitida, operación, código de error y clase de excepción,
con correlation/request IDs existentes. No se registran prompts/respuestas,
outputs, headers, tokens, endpoint, credenciales, argumentos ni IDs de Azure.
Los logs de SDK HTTP/credenciales se silencian igual que en el spike.

## Arranque y comprobación

Usar la configuración Foundry existente en backend/.env y el extra `foundry` ya
validado. No copiar credenciales/configuración a Vite. La aplicación puede arrancar
sin Azure configurado: solo el chat devuelve error amigable al consultarlo.

```powershell
# Desde backend, con acceso Azure ya autenticado y PostgreSQL disponible:
.\.venv\Scripts\python.exe -m uvicorn public_procurement.entrypoints.api.app:create_app --factory --host 127.0.0.1 --port 8000

# Desde frontend:
npm.cmd run dev -- --host 127.0.0.1 --port 5173
```

En equipos donde Azure CLI no está en PATH, añadir su directorio al entorno del
proceso del backend, como en el spike; no se automatiza login interactivo.

## Validación

Foundry mockeado en tests: conversación nueva/continuación, selección de versión
sin escritura remota, errores tipados/seguros, configuración perezosa, ausencia de
respuesta, referencias estructuradas, expiración/owner y prohibición de writers.
Se conserva la cobertura anterior de las seis tools y transacciones READ ONLY.

Frontend: mensajes/formato seguro, sugerencias, envío, loading, doble envío,
Shift+Enter, tarjetas, continuidad, contexto expirado, retry y nueva conversación.

Pruebas de agente/backend: 87 aprobadas. Suite unitaria backend completa: 1.235
aprobadas, 1 omitida y 4 fallos conocidos de fixtures CDP con fechas fijas que ya
quedan fuera de la ventana reciente. Se encuentran en test_eureka_licitaciones_cdp.py
(bounded_flow, dos parametrizaciones) y test_licitaciones_candidate.py
(discovery_only y expired_session_during_inventory). No se cambiaron esas reglas
ni fixtures para hacerlos pasar. Ruff, formato, Mypy e import-linter: correctos.

Frontend: suite completa final de 139 aprobadas, incluyendo numeración de listas
y fin del contexto; TypeScript, ESLint y build correctos.

### Única conversación real desde la UI — 2 noviembre 2026

Una conversación con dos turnos: consulta de oportunidades de la última corrida
CDP y seguimiento «¿Cuál fue el primer proceso que mencionaste…?». Ambos POST
devolvieron 200 y conservaron el mismo UUID opaco del backend. La captura del
seguimiento muestra que recordó MC-131-2026 (Cubará), sin iniciar otro contexto.
El helper local de Windows reemplazó dos acentos por `?` en la pregunta inicial;
se conserva el texto realmente enviado en la auditoría y no se repitió la prueba.
Los tests de React comprueban además el envío normal de texto acentuado.

Se seleccionó en lectura la versión 11 existente. La consulta usó perfil, última
corrida, candidatos a revisión, detalle y evidencia de tres casos; el seguimiento
consultó de nuevo el resumen y recordó el contexto. Total: 10 llamadas de lectura,
9 en el primer turno y 1 en el seguimiento. Ninguna nueva versión ni tool.

Se mostraron cinco tarjetas estructuradas: MC-131-2026, MC-RB-DR-0034-2026,
MC-CMC-003-2026, CMI-2026090 y MC-050-2026. Son procesos consultados; la respuesta
priorizó tres, no los cinco. No hubo conexiones del navegador a hosts externos.
Las respuestas HTTP solo tienen conversation_id/message/process_references.

Se compararon conteos y huellas del contenido de las 33 tablas antes y después
de los dos turnos: sin cambios. No se ejecutó discovery, descargas, OCR, scoring,
alertas ni actualización de revisión. La comprobación es evidencia local en lectura;
el endpoint no contiene SQL y todas sus tools usan PostgreSQL READ ONLY.

Capturas inspeccionadas: conversación, respuesta/tarjetas y seguimiento. La
navegación adicional al detalle existente superó una espera networkidle de 30 s;
una verificación posterior sin ese criterio confirmó la carga correcta del detalle.
Se conserva como observación de latencia de la vista existente, sin cambiar sus
consultas ni repetir el chat. No se afirma que la calidad semántica del modelo sea
perfecta: se mantuvieron la política y las limitaciones de evidencia de la versión 11.

Evidencias locales: backend/.local/audits/assistant-ui/live-result.json,
db-before.json/db-after.json, agent-answer.md y ui-*.png. La respuesta cruda del
primer turno está guardada; la del segundo no se alcanzó a guardar antes del timeout
de navegación, pero sus aserciones, logs HTTP y captura verifican la continuidad.
Todo ese directorio está ignorado por Git.
