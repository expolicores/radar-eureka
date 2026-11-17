# Estado vs mercado privado — visualización inicial

`/explorar` ofrece [dos corridas independientes por fechas](eureka-investigation-modes.md):
**Nueva corrida Estado vs Estado** y **Nueva corrida Estado vs mercado privado**.
La segunda descubre sus propios productos desde los documentos de su ventana y
consulta mercado solo para candidatos elegibles, sin selección manual previa.
Cada resultado se abre por UUID y los benchmarks históricos se conservan.

Entrada: `/explorar`, bloque **Estado vs mercado privado**, enlace **Ver comparación
de mercado**. Detalle: `/explorar?market=<report_id>&process=<identidad pública>`.
El regreso conserva el proceso y la navegación del navegador funciona sin rutas nuevas.
Un proceso seleccionado solo muestra sus propios recibos disponibles.

Se reutiliza `GET /api/v1/investigation/private-market`. Sigue siendo read-only:
`MarketReportStore.read()` → `present_market_reports()` → JSON de presentación.
La lista blanca excluye requests, tokens, payloads/evidence crudos y metadata del
proveedor. Solo publica diagnósticos compactos, campos de evidencia pública y
observaciones. URLs HTTPS sin credenciales ni parámetros sensibles. El recibo
original permanece intacto. No se invocan providers ni lógica de matching/cálculo.
Se conservan decisiones, precios, contadores, limitaciones y conflictos del backend.
No hay migración, dependencias nuevas ni cambios en Estado vs Estado.

## Componentes y archivos

Frontend nuevo:

- `frontend/src/features/research/MarketBenchmark.css`: estilos locales, paneles
  adaptables y scroll horizontal dentro de las tablas en pantalla estrecha.
- `marketTypes.ts`: tipos de presentación.
- `marketLabels.ts`: traducción de estados, calidad y motivos; sin decisiones nuevas.
- `fixtures/samsungMarket.ts`: fixture histórico de aceptación, importado únicamente
  por tests; no alimenta la vista productiva ni sustituye errores de carga.

Frontend ampliado:

- `MarketBenchmark.tsx`: listado y detalle `MarketBenchmarks`, `MarketBenchmarkCard`,
  `EvidenceQualityBadge`, tabla de observaciones y diagnóstico de fuentes.
- `MarketBenchmark.test.tsx`: aceptación Samsung, observaciones, navegación, errores,
  moneda, ausencia de señal, comparación provista por backend y dedupe de presentación.
- `ResearchPage.test.tsx`: identifica el aviso propio de investigación cuando ambos
  endpoints pueden mostrar errores independientes. `ResearchPage.tsx` conserva su
  integración previa con `MarketBenchmarks`; no requiere nuevas rutas.

Backend nuevo/modificado:

- `market_benchmark/presentation.py`: proyección sin efectos; identificador de
  lectura derivado de referencia pública, producto y fecha de captura.
- `investigation/research_api.py`: aplica esa proyección al endpoint existente.
- `tests/unit/investigation/test_market_presentation.py`: decisiones intactas,
  eliminación de campos crudos/credenciales, lectura sin escrituras y error seguro.

## Semántica visual

- Oferta documentada no equivale a adjudicación o contrato confirmado.
- Cantidad, oferente, documento/página, base tributaria y conflicto se muestran
  desde la evidencia pública; no se infieren fechas ni aceptación.
- Se soportan los nombres actuales `sufficient_diverse_market_evidence` y
  `marketplace_concentrated_evidence`, además de sus alias cortos de UX.
- Estadísticas parciales si el backend indica insuficiencia o falta de diversidad.
  No se calculan diferencias, porcentajes, precios, matching ni suficiencia en UI.
- Se renderizan `comparison` y `signal` solo si existen en el recibo, con lenguaje
  neutral. No se inventa una señal a partir de una mediana parcial.
- Ofertas aceptadas visibles; ambiguas/rechazadas expandibles con motivo estructurado.
  Duplicados separados y nunca etiquetados como nuevas aceptaciones.
- Calidad diferenciada: API / página / proveedor shopping / snippet. Proveedor
  shopping no se presenta como tienda o checkout verificados. COP inferido explícito;
  moneda ausente no se sustituye por COP en observaciones que indican `null`.
- Horas en America/Bogota. Captura es fecha del recibo, no actualización del retailer.
- Sin recibo: estado explícito. Error: mensaje seguro y reintento de lectura.
  No existe concepto backend de ejecución asíncrona en este endpoint: cargar el recibo
  no se presenta como una búsqueda en ejecución.

## Aceptación y validación

Fixture Samsung: $3.767.123 antes de IVA, oferta no confirmada, cantidad 1, TEAM IT,
página 339/340, conflicto MC-028/MC-070. Éxito $1.799.900 y Puntos Colombia $3.339.900
aceptados; Addi ambiguo excluido. Dos observaciones, estadísticas parciales con mediana
$2.569.900, comparación monetaria no generada y sin señal definitiva. Limitaciones
tributarias, temporales y documentales visibles. No hay diferencias ni porcentajes.

Validación: 18 tests del componente/navegación, 173 tests frontend completos con
`npm.cmd test -- --maxWorkers=2`; 399 tests de investigación backend. Prettier,
ESLint, typecheck/build, Ruff y Mypy afectados. La primera ejecución frontend sin
límite de workers tuvo un timeout de un test de revisión ajeno a esta vista; la
suite completa con dos workers pasó.

Prueba visual con Edge headless, API interceptada usando proyección del recibo real
histórico Samsung: escritorio 1440 px, móvil 390 px, sin errores JS, sin overflow
horizontal del documento; expandir rechazados y alcanzar limitaciones mediante
scroll verificado. Evidencia: `backend/.local/market-ui-validation/`. No se hicieron
consultas externas ni publicaciones durante esta implementación.

## Datos visibles y límites pendientes

El endpoint muestra el último informe **publicado** en el almacén local configurado.
No escanea `.local` buscando corridas ni publica automáticamente un recibo nuevo.
La corrida end-to-end previa queda preservada en su carpeta original: crear esta UI
no cambia `private-market-latest.json`. Reiniciar backend si no tiene auto-reload
para cargar la nueva proyección. La SPA mantiene el enlace existente desde `/explorar`.

Pendientes: archivo histórico/listado de múltiples corridas, paginación para grandes
volúmenes, diagnóstico de fuentes más descriptivo y trazabilidad de frescura de caché.
Un enlace cuyo recibo dejó de estar publicado muestra **Recibo no disponible**;
no cambia silenciosamente a una captura nueva. No se agregan ejecución desde UI,
edición, aprobación, exportación, gráficos o nuevos workflows.
