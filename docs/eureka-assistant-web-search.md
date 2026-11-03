# Eureka Assistant — Web Search bajo demanda

## Definición remota

Se registra una nueva versión del mismo eureka-assistant conservando literalmente
el modelo, instrucciones y demás propiedades existentes. Solo se añade
`{"type":"web_search"}` al array de tools. Las seis function tools permanecen
idénticas, sin eliminar versiones previas. La API sigue sin crear versiones.

Se usa WebSearchTool directa de Prompt Agents, sin toolbox, MCP ni conexión Bing
adicional, según la [documentación de Microsoft Foundry](https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/tools/web-search).

## Selección y límites

- Una petición explícita de web/internet/nuevos procesos/fuera de Eureka o una
  consulta temporal externa habilita búsqueda bajo demanda.
- Las preguntas internas (corridas/CDP/Radar/Eureka/alertas/facts/canonicals/resumen
  o investigación de oportunidades internas) excluyen web_search mediante
  tool_choice/allowed_tools; no basta con confiar en una instrucción al modelo.
- Para información externa necesaria sin frase explícita se permite decidir al
  modelo, pero la capacidad solo se habilita después de obtener el perfil.
- El primer paso externo es get_eureka_commercial_profile. Su resultado se envía
  sin copiar regiones/categorías/topes al prompt. Web no puede ejecutarse antes.
- Si la petición pide web explícitamente, tras el perfil se exige esa tool mediante
  allowed_tools/required. Luego el modelo puede combinarla con las funciones de lectura.
- El turno de búsqueda recibe de nuevo la ventana congelada al inicio. Se detectan
  intervalos ISO invertidos en la traza y cierres sin citas que piden permiso para
  profundizar. Hay como máximo una continuación de investigación dentro del mismo
  turno/presupuesto; no es un retry HTTP ni otra conversación. Si sigue sin sustento,
  se devuelve una respuesta controlada de oportunidades no confirmadas, con fuentes
  separadas. No se aceptan listados de portales como procesos recientes confirmados.
- Se conservan 120 s por pregunta (o el timeout existente configurado), máximo
  13 vueltas y 12 tool calls; las acciones hospedadas cuentan también. Sin retry
  automático, nuevas corridas ni escrituras de negocio.
- Una versión anterior sin web devuelve web_search_unavailable para esa petición;
  la UI permite iniciar un contexto nuevo. No se cambia de versión silenciosamente
  dentro de una conversación.

Las reglas web se agregan al contexto developer del turno; no se sobrescriben las
instrucciones remotas existentes. La política de evidencia/contratos se conserva.
Los datos internos siguen siendo persistidos: web no equivale a que Radar/CDP haya
actualizado su universo o comprobado vigencia.

## Ventana temporal externa

El backend aporta fecha/hora actual en America/Bogota y extremos ISO concretos:

- esta semana: lunes local 00:00 hasta ahora; no incluye publicaciones futuras;
- últimos 7 días: ahora menos 7 días hasta ahora (ventana móvil de 168 h);
- hoy: medianoche local hasta ahora;
- ayer: medianoche anterior hasta la medianoche de hoy;
- sin ventana solicitada: extremos no especificados, sin imponer un filtro nuevo.

Se usa fecha de publicación de la fuente externa, no fecha de indexación ni
timestamps de corrida/revisión. Si la fecha no puede confirmarse, el hallazgo se
declara preliminar/no confirmado para la ventana. Estas fechas orientan al agente
y a las consultas web; no son un filtro determinista sobre un dataset completo ni
cambian los filtros del pipeline.

## Procedencia y comparación

La política separa datos internos de Eureka, hallazgos externos e inferencias.
Prioriza fuentes oficiales (SECOP/Colombia Compra Eficiente/entidades) y permite
fuentes públicas complementarias, incluida Licitaciones.info accesible públicamente.
No se añaden dominios/regiones comerciales hardcodeados al proveedor ni al scoring.

Si una fuente contiene una identidad oficial exacta, el modelo puede consultar
get_process_detail para comparar. found=false significa no confirmado por ese lector,
no ausencia global. No hay dedupe destructivo, importación, equivalencia NTC/REQ,
alerta automática ni persistencia de hallazgos externos.

La respuesta debe identificar código/nombre, entidad, objeto, ubicación, publicación,
deadline, monto, URL, encaje y nivel de confianza cuando estén sustentados. Lo ausente
permanece desconocido; metadata sola no confirma participabilidad. No se resuelven
conflictos contractuales automáticamente. Una búsqueda vacía no prueba que no existan
procesos; la respuesta explica que no es exhaustiva y puede faltar indexación.

## Contrato y citas de UI

Se agregan dos campos opcionales compatibles al ChatReply:

```json
{
  "external_references": [{
    "citation_number": 1,
    "title": "Título nativo de la fuente",
    "source": "dominio de la fuente",
    "url": "https://fuente-publica.example/registro",
    "published_at": null,
    "entity": null,
    "location": null,
    "confidence": "preliminar"
  }],
  "web_searches": [{"action": "search", "queries": ["consulta pública"], "sources": []}]
}
```

Las referencias son bibliografía nativa, no nuevos registros estructurados de
oportunidades. Las anotaciones url_citation aportan título/URL, no monto/deadline
ni necesariamente publicación/entidad/ubicación: esos campos quedan null. Los
campos de oportunidad, si se encontraron, se explican en la respuesta con fuentes
y sus incertidumbres. No se hace una segunda extracción LLM para rellenar tarjetas.

URLs solo de annotations.url_citation o web_search_call.action.sources (incluido
en la petición). Se rechazan protocolos inseguros, credenciales y parámetros
sensibles. No se parsean URLs del texto libre del LLM ni se consultan esas URLs
desde el backend para fabricar metadata.

Las citas nativas se convierten en marcadores numerados vinculados a referencias
estructuradas, sin eliminar el texto citado. React muestra enlaces inline visibles
y tarjetas de «Fuentes externas · Web Search», claramente separadas de «Procesos
consultados en Eureka». Esto sigue el contrato de citas de
[OpenAI Docs](https://developers.openai.com/api/docs/guides/tools-web-search).
HTML arbitrario y markdown URLs no estructuradas siguen siendo texto inerte.

Si el proveedor no da citas ni fuentes estructuradas verificables, el backend no
devuelve supuestos hallazgos sin sustento: da un aviso de búsqueda no exhaustiva
sin confirmar monto/publicación/deadline. No significa que no existan procesos.

## Seguridad y observabilidad

No se publican credenciales/endpoints/agent reference/IDs Azure ni schemas. La traza
web del HTTP solo incluye acciones, queries y URLs públicas del propio turno;
no contiene razonamiento interno ni resultados crudos del proveedor. En logs solo
se registran cantidades de queries/fuentes y nombres de funciones, nunca sus textos.
La traza puede incluir warnings como invalid_search_date_range, sin secretos.

El navegador llama únicamente al backend. El proveedor ejecuta Web Search; no hay
requests Azure/Bing desde React. Los hallazgos quedan en la conversación del
proveedor/contexto temporal existente, no en PostgreSQL de Eureka.

## Tests y aceptación

Foundry/Web Search mockeados: bloqueo interno, solicitud explícita, perfil previo,
ventanas locales y cambio de semana UTC/Bogotá, fuentes nativas/no inventadas,
campos ausentes null, vacío no exhaustivo, referencias HTTP y seis funciones intactas.
React: citas seguras, tarjetas externas separadas y rechazo de URLs sin estructura.

### Resultado de la única conversación real — 2 noviembre 2026

Versión nueva: **12**, anterior **11**. Modelo gpt-4.1-mini-eureka.
Instrucciones remotas y seis funciones idénticas, verificadas tras crear la versión;
SHA256 de instrucciones:
76d50a66e2d68ac13fc900b5665abb6b04945c417b44921926eb937d5c466cc2.
Ninguna versión eliminada. Recibo: deployment.json del directorio local de auditoría.

Una pregunta exacta desde la UI, sin retry: «busca en la web procesos de mi interés
que hayan salido esta semana». HTTP 200. Se ejecutaron get_eureka_commercial_profile
y una acción hospedada web_search. No se consultaron procesos individuales porque
no se identificaron oportunidades concretas. Once referencias externas llegaron a
la UI y se inspeccionaron las tarjetas y enlaces; cero requests Azure/Bing desde React.
Las 33 tablas conservaron conteos y huellas antes/después; no hubo escrituras de negocio.

**Aceptación parcial de investigación, no completa.** El proveedor buscó con un
intervalo invertido 2026-11-02..2026-11-01 y respondió con portales generales,
pidiendo permiso para profundizar. No confirmó ningún proceso específico, fecha de
publicación, monto ni deadline. Eso no prueba ausencia de oportunidades. Las fuentes
fueron las reportadas por action.sources, no citas de condiciones contractuales
verificadas. El informe local conserva la consulta, las 11 URLs y la respuesta real.

La ventana correcta era lunes 2 de noviembre 00:00 hasta el instante de consulta
del mismo 2 de noviembre en Bogotá. Tras observar el fallo se añadieron el refuerzo
por turno y las guardas acotadas descritas arriba. Sus tests son offline/mocks;
**no se repitió la conversación real ni se afirma que el fix quedó validado en vivo**.
Estas guardas no certifican todas las fechas ni relevancia de resultados web:
detectan el caso ISO invertido observado y un patrón de cierre prematuro.

Pruebas del asistente: 112 aprobadas, con los cuatro casos nuevos de rango invertido,
continuación acotada, fallback si persiste y cierre de portales sin permiso.
TypeScript, ESLint, build, Ruff, Mypy y los 13 contratos de arquitectura se verifican.
Frontend completo: 142 aprobadas con `npm.cmd test -- --maxWorkers=4`.
La primera ejecución con concurrencia por defecto tuvo un timeout de espera en
un test existente de HumanReviewPage (seguía en «Cargando procesos»); la suite
completa pasó al limitar workers, sin modificar ese test ni la vista de revisión.

Evidencia ignorada por Git: backend/.local/audits/foundry-web/live-result.json,
agent-answer.md, ui-external-references.png, db-before.json/db-after.json,
deployment.json y acceptance-report.md. Se conservó la respuesta observada sin
reescribirla como si las guardas posteriores ya hubieran estado activas.
