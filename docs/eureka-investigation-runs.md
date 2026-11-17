# Corridas investigativas bajo demanda por fechas

Entrada: `/explorar` → **Nueva corrida** → **Fecha inicial** / **Fecha final** →
**Iniciar corrida**. El único criterio configurable son las fechas. Panel simple,
cancelar antes de iniciar, botón bloqueado durante POST y durante una corrida activa.

Alcance confirmado: **flujo investigativo por fechas; mantener benchmarks privados
existentes**. No se ejecutan SerpApi, Scout ni benchmarks privados automáticamente.
La UI los identifica como resultados publicados independientes de la nueva corrida.
No cambia la taxonomía de televisores, matching, scoring, señales, alertas, reglas
de comparación Estado vs Estado ni scheduler.

## Contrato HTTP

`POST /api/v1/investigation/runs` → **202**. Request estricto:

```json
{"start_date":"2026-10-01","end_date":"2026-10-31"}
```

Campos desconocidos (paths, scripts, filtros, shell, etc.) devuelven 422. Fechas
calendario ISO `YYYY-MM-DD`, ambas obligatorias; inicio ≤ fin. Máximo **60 días
inclusivos**, límite ya existente de discovery. El backend publica esa política en
`GET /api/v1/investigation/runs/policy`; la UI la muestra sin implementar otra regla
de tamaño de ventana. No hay prohibición nueva de fechas futuras ni otros filtros.

Respuesta `ResearchRun`:

- `run_id` UUID, `status`, `start_date`, `end_date`, `created_at`.
- `window_start_at`, `window_before_at`, `started_at`, `finished_at` en UTC.
- `stage`, `counts`, `warnings`, `errors`, `result_url` si terminó y hay resultado.

Estados: `queued`, `running`, `completed`, `completed_with_warnings`, `failed`.
UI: Pendiente, En ejecución, Completada, Completada con advertencias, Fallida.

`GET /api/v1/investigation/runs/{run_id}` recupera el registro persistido. UUID no
encontrado: 404. Fallo de lectura: 503 sin detalles de excepción.
`GET /api/v1/investigation/runs/active` permite recuperar una creación cuyo POST
tuvo timeout; no crea otra corrida. Otro rango mientras hay una activa: 409.
POST repetido para la misma ventana activa devuelve el mismo run_id.

`GET /api/v1/investigation/research?run_id=<UUID>` lee el resultado de esa corrida.
Sin run_id sigue leyendo la proyección actual. Resultado no disponible: 404.
Enlace final: `/explorar?run=<UUID>`. Abrir/cerrar procesos y navegar a señales
conserva el run para evitar mezclar evidencias de distintas corridas.

## Tiempo y pipeline

El ejemplo incluye del 1 al 31 de octubre completos en America/Bogota. Límites
persistidos: `2026-10-01T05:00:00Z` a `2026-11-01T05:00:00Z` exclusivo.
Se adapta a los parámetros existentes del discovery: `--before 2026-11-01
--days 31`. Se conserva su convención de fechas calendario de publicación;
no se cambia la interpretación de timestamps del proveedor ni se infieren fechas
de compra. Presentación de eventos en Bogotá.

`ExistingResearchPipeline` llama **los mismos entrypoints existentes** en secuencia:

1. `eureka_investigation_discover.main(argv)` con `--prepare`.
2. `eureka_investigation_sample.main(argv)` con `--execute`.
3. `eureka_investigation_report.main(argv)` sin publicar.
4. `eureka_investigation_cycle.main(argv)` sin publicar.

Los scripts aceptan ahora argv explícito, conservando su CLI; no se muta sys.argv
global ni se ejecuta un shell. Scripts y directorios solo los decide el servidor.
Se conservan defaults del discovery: 48 procesos seleccionados, 10 documentos por
proceso, ranking, fuentes y acotamientos actuales. Los servicios existentes realizan
adquisición, extracción, facts y reconstrucción; no hay una segunda implementación.
Se corrigió el caso de selección vacía para no consultar contratos con una lista
vacía y generar los recibos vacíos necesarios. Sin cambio de selección o scoring.
El Markdown de ciclo dejó de afirmar un número fijo de 12 procesos históricos.

## Ejecución y persistencia

`ManualResearchRunner`: thread daemon local, siguiendo el enfoque de ejecución
manual en segundo plano ya usado por CDP/Operaciones. No usa BackgroundTasks
bloqueantes ni mantiene el POST esperando documentos/OCR. El run queued se escribe
antes de devolver 202. Un bloqueo de archivo del sistema operativo permite una
sola ejecución por directorio compartido, incluso con más de un proceso local.

Persistencia local junto a `ResearchReportStore`, sin migración:

```text
<investigation>/runs/<UUID>/run.json
<investigation>/runs/<UUID>/result.json
<investigation>/runs/<UUID>/<recibos discovery, documentos, ciclo...>
```

Escrituras de estado atómicas; logs estructurados con run_id/status/stage y conteos
de warnings/errors, sin cuerpos de excepción ni credenciales. Las fechas y los
artefactos están aislados por UUID. No se publica un resultado intermedio.
Al terminar, se archiva `result.json` y se publica atómicamente con el store actual.
Errores documentales aislados/cobertura parcial producen `completed_with_warnings`
y resultado disponible. Fallo fatal: `failed`, etapa registrada, artefactos
conservados y sin sustituir el último resultado completo publicado.

Reinicio/apagado: los runs interrumpidos se marcan `failed/backend_restarted`,
no se relanzan. La recuperación obtiene antes el bloqueo; un segundo backend no
marca como fallida una corrida que otro proceso mantiene activa.
Un worker en cierre no publica luego un resultado. Los servicios documentales
pueden haber persistido trabajo parcial antes del reinicio; no se borra ni simula
rollback global. Una nueva ejecución reutiliza lo que permitan esos servicios.

## Frontend

`ResearchRuns.tsx`: panel, validación, POST de máximo 20 s, recuperación de activa,
estado y conteos. La URL guarda `research_run` para seguimiento y `run` cuando se
abren resultados. No depende solo de memoria frontend.

React Query consulta cada **5 segundos**, una query por run, sin retries automáticos
de creación. Detiene polling al completar/fallar o ante error de consulta; ofrece
reintento de lectura. Abort/cleanup al desmontar. No hay WebSockets ni cancelación
de una corrida ya iniciada. “Cancelar” solo cierra el formulario antes del POST.
Los resultados anteriores siguen visibles durante la ejecución, identificados
como tales; **Ver resultados de esta corrida** abre su resultado inmutable.

## Archivos

Backend nuevos: `investigation/run_contracts.py`, `run_background.py`,
`run_pipeline.py`, `tests/unit/investigation/test_research_runs.py`.
Modificados: `investigation/research_api.py`, `entrypoints/api/app.py` y los cuatro
scripts mencionados. Los almacenes DB/documentos/extracción no cambian de contrato.

Frontend nuevos: `ResearchRuns.tsx`, `ResearchRuns.css`, `ResearchRuns.test.tsx`,
`researchNavigation.ts`. Modificados: `ResearchPage.tsx` y su test;
`ComparisonReadiness.tsx`, `PublicPriceComparison.tsx`, `MarketBenchmark.tsx` solo
conservan el contexto del run en sus enlaces; no cambian decisiones ni cálculos.

## Validación y límites

- 17 tests nuevos backend: fechas, UTC/inclusividad, campos prohibidos, estados,
  doble POST, exclusión, errores parciales/fatales, reinicio, lectura por UUID,
  orquestación fija y discovery vacío sin requests de contratos.
- 16 tests nuevos del control frontend y un test de navegación por corrida:
  formulario, fechas, POST, doble clic, todos los estados, timeout/recuperación,
  polling/stop/unmount y enlace final. 190 tests frontend completos pasan.
- 416 tests de investigación pasan. Backend unitario completo: 1678 pasan,
  4 fallan por fixtures CDP de octubre dependientes del reloj actual; 1 omitido.
  Log: `backend/.local/investigation-run-unit-validation.txt`.
- Prueba visual Edge headless con API interceptada: formulario octubre 1–31,
  un POST solo con fechas, running → completed_with_warnings → resultado;
  cero errores JS. Evidencia en `backend/.local/research-runs-ui-validation/`.
- **No se ejecutó ninguna corrida real ni se consultaron fuentes externas** durante
  la implementación/pruebas. No cambió el benchmark privado publicado.

Es un worker local, no una cola durable/distribuida. Requiere el checkout de
`backend/scripts` y los mismos recursos que el pipeline CLI (DB local/migración
vigente, conectividad Socrata/SECOP y extracción/OCR configurados). Un paquete sin
esos scripts no puede ejecutar este adaptador. No hay reanudación automática,
cancelación, historial UI, scheduler ni paralelización nueva. No se intenta
abortar a mitad de una operación documental durante el apagado; se marca la
interrupción y se conserva la evidencia parcial existente.

Reiniciar backend si no usa auto-reload para cargar endpoints y runner. Después
puede usarse **Nueva corrida**; no se inicia ninguna al abrir `/explorar`.
