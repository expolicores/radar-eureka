# Fase 4.2 — OCR local como fallback

Estado: implementación técnica aprobada, aceptación aislada con Tesseract real superada
y migración autorizada `0012_eureka_radar` → `0013_ocr_diagnostics` aplicada en desarrollo.

## Flujo y cobertura

`documents` entrega la versión y el binario verificado. `ExtractionService` persiste o
reutiliza la extracción nativa con pypdf antes de evaluar calidad. DOCX/XLSX conservan
sus lectores actuales. Para PDF insuficiente, un lector local implementa el mismo puerto
`ContentExtractor` y renderiza con pypdfium2; Pillow aplica escala de grises y autocontraste.
Tesseract, mediante pytesseract, reconoce únicamente las páginas necesarias.

No se reemplazan fragmentos nativos, ni siquiera cuando se intenta OCR en su página.
Un run `pdf-hybrid-local` conserva copias con referencia al run/ordinal nativo y añade
OCR utilizable. El run nativo original permanece inmutable. La salida OCR rechazada
por calidad conserva una muestra diagnóstica de hasta 4096 caracteres, sin convertirla
en evidencia válida. No se duplican reglas de structured/canonical facts.

Por página se evalúan caracteres alfanuméricos, proporción alfanumérica y caracteres
dañados. Los valores iniciales 40 / 0.50 / 0.05 son heurísticas calibrables, no reglas
comerciales. Viven en `backend/config/extraction_ocr.v1.json`, con versión y hash.
Resultados: `native_text_ok`, `native_text_low_quality`, `native_text_empty` y fallos
nativos registrados. Un fallo renderizable puede intentar OCR; cifrado, hash incorrecto,
límites de entrada o fallos de aislamiento no habilitan bypass.

Los diagnósticos incluyen `required_pages`, `processed_pages`, `successful_pages`,
`omitted_pages`, estados/errores por página, tiempo, política y motor. `ocr_truncated`
significa que quedaron páginas omitidas por límite/tiempo. `coverage_complete=false`
se conserva aunque exista texto útil o canonical facts. No se infiere ausencia de
productos/requisitos a partir de cobertura parcial.

## Persistencia y compatibilidad

`format_counts` sigue siendo `dict[str, int]`: solamente contadores.
La migración aditiva `0013_ocr_diagnostics` crea `extraction.extraction_run_diagnostic`:
PK/FK `extraction_run_id` y `payload JSONB`. No altera tablas ni contenido histórico.
Los lectores comprueban si existe; la beta y la extracción nativa funcionan en `0012`.
Si se necesita persistir OCR sin `0013`, CLI devuelve `ocr_migration_required` y cobertura
incompleta. No ejecuta migraciones automáticamente. El diagnóstico `--dry-run` no la requiere.

`content_fragment.source_locator` conserva método `native_pdf_text`/`ocr_text`, página,
versión documental, hash, motor, idioma y política. La confianza OCR es la media de
palabras válidas de Tesseract en escala 0–100; no es confianza semántica ni modifica
confianza de reglas o canonical facts. Los fragmentos híbridos llevan cobertura explícita.
Evidencia y búsqueda eligen el último run reutilizable con fragmentos, evitando que un
run vacío o fallido oculte texto anterior.

La identidad combina versión documental (restricción existente), lector nativo,
límites, política, bibliotecas, motor/idioma efectivo y SHA del traineddata cuando su ruta
es conocida. Se reutilizan resultados de igual identidad. Disponibilidad nueva del motor
o cambios de configuración generan identidad nueva. Reintentos explícitos producen runs
auditables `-a1`, `-a2`, etc., con límite configurable, sin borrar intentos anteriores.
Los reintentos OCR completos no se repiten. Una ejecución todavía `running` no se suplanta.

## Instalación local Windows

1. Instalar Tesseract 5 de 64 bits siguiendo el enlace Windows de la
   [documentación oficial](https://tesseract-ocr.github.io/tessdoc/Installation.html), que
   remite al [instalador UB Mannheim](https://github.com/UB-Mannheim/tesseract/wiki).
2. Seleccionar datos de español durante instalación. Si no están disponibles, obtener
   [spa.traineddata del repositorio oficial tessdata_fast](https://github.com/tesseract-ocr/tessdata_fast/blob/main/spa.traineddata)
   usando la descarga del archivo binario y copiarlo a `tessdata`. No guardar el HTML de GitHub.
   También puede conservarse `eng.traineddata` para fallback explícito.
3. Verificar desde PowerShell (ajustar ruta si la instalación es distinta):

```powershell
& 'C:\Program Files\Tesseract-OCR\tesseract.exe' --version
& 'C:\Program Files\Tesseract-OCR\tesseract.exe' --list-langs
Test-Path -LiteralPath 'C:\Program Files\Tesseract-OCR\tessdata\spa.traineddata'
```

La lista debe contener `spa`. El proyecto prefiere español; si solo existe `eng`, registra
`language_fallback=true`. Si faltan ambos, devuelve `ocr_language_missing`; si falta el
binario/dependencias, el fallo es recuperable. No se instala ni descarga software del
sistema desde la aplicación.

Variables del proyecto, en `backend/.env` configuradas manualmente:

```dotenv
EXTRACTION_OCR_ENABLED=true
EXTRACTION_OCR_CONFIG_PATH=config/extraction_ocr.v1.json
EXTRACTION_TESSERACT_CMD="C:/Program Files/Tesseract-OCR/tesseract.exe"
EXTRACTION_TESSDATA_PATH="C:/Program Files/Tesseract-OCR/tessdata"
```

Ruta del motor también puede ser `tesseract` si está en PATH. Tessdata es opcional si el
motor lo descubre correctamente; configurar ruta absoluta permite verificar el modelo.
Instalar dependencias Python desde `backend/`:

```powershell
python -m uv sync --extra ocr
```

Versiones resueltas en esta implementación: pypdfium2 5.14.0, Pillow 12.3.0 y
pytesseract 0.3.13. No se agregó otro motor ni Poppler.

## CLI

Desde `backend/`, con una versión documental ya descargada:

```powershell
.venv/Scripts/python.exe -m public_procurement.entrypoints.cli extract-document --document <id>
.venv/Scripts/python.exe -m public_procurement.entrypoints.cli extract-document --document <id> --no-ocr
.venv/Scripts/python.exe -m public_procurement.entrypoints.cli extract-document --document <id> --force-ocr --dry-run
.venv/Scripts/python.exe -m public_procurement.entrypoints.cli extract-document --document <id> --retry-ocr
.venv/Scripts/python.exe -m public_procurement.entrypoints.cli extract-documents --process <secop-id>
.venv/Scripts/python.exe -m public_procurement.entrypoints.cli extract-documents --process <secop-id> --retry-ocr
```

`--document` mantiene el contrato existente: ID documental interno/externo y su versión
vigente. `--force-ocr` exige `--dry-run`; no cambia la evidencia persistida. Cobertura
incompleta tiene código de salida 1, con diagnóstico visible, incluso si hay fragmentos.
El lote imprime métricas de documentos, páginas requeridas/procesadas/exitosas/fallidas/
omitidas, indisponibilidad y tiempo OCR. Un resultado reutilizado muestra las métricas
del resultado almacenado, no un nuevo coste de OCR.

## Recursos y fallos

La política configura máximo de páginas OCR (20 inicial), DPI (300), píxeles por página
(12 millones), timeout por página (30 s), documento (180 s), memoria (512 MiB) y reintentos
(3). Siguen vigentes límites de entrada, texto, fragmentos y páginas PDF. El worker verifica
SHA y tamaño, no recibe rutas de usuario. Windows utiliza Job Object con límite de memoria
por proceso/job y cierre de descendientes; POSIX usa límite de memoria y grupo de procesos.
Un timeout no elimina el run nativo. Imágenes intermedias son temporales, no documentos
registrados. Un fallo por página permite continuar las restantes.

## Radar y UI

Radar usa los mismos servicios, con reintento OCR acotado. Si hay evidencia útil continúa
structured/consolidation; sin ella, el proceso queda fallido/reintentable. La cobertura
incompleta queda en el resultado y snapshot de alerta, y el estado de proceso permanece
reintentable incluso si produjo alerta. No se reutiliza una consolidación marcada con
cobertura incompleta como si fuera completa. Permanecen límites de intentos de Radar 4.1.
No cambian score, catálogo, canonical rules ni decisión comercial de alerta; las alertas
siguen deduplicadas y sus snapshots anteriores no se sobrescriben.

La evidencia muestra `página N · OCR` o `Texto nativo`; el detalle advierte cobertura
parcial. No se agregó vista. Los consumidores deben consultar cobertura además del estado
de consolidación: contar hechos consolidados no demuestra lectura de todas las páginas.

## Pruebas y aceptación real

Verificación inicial de implementación: 529 pruebas backend aprobadas y una omitida
(Tesseract real aún no instalado en ese momento); 62 pruebas frontend aprobadas.
Después de instalar el motor, `ocr_real` pasó (1 prueba) y la suite extraction pasó
con 125 pruebas, incluyendo OCR real. Ruff, mypy, ESLint, build frontend y los
10 contratos de arquitectura pasan. El lockfile verifica en modo offline. El renderizador
sí se ejecutó realmente en las pruebas controladas; el reconocimiento allí fue sustituido.

Smoke de compatibilidad con el código actual: GET alerts, radar-runs y detalle Covarachía
responden 200 usando una conexión PostgreSQL forzada a solo lectura. Covarachía mantiene
score 65. Desarrollo conserva `0012_eureka_radar` y no tiene la tabla nueva. No se ejecutó
una corrida de Radar contra desarrollo ni pruebas destructivas en esa base.

Pruebas aisladas usan SQLite en memoria y fixtures PDF sintéticos; no usan desarrollo ni
SECOP. Incluyen render real con reconocimiento controlado, native/mixed/scan, falta de
motor, fallo por página, límites, idempotencia/configuración/retry, provenance, structured,
canonical y composición Radar. Migración probada en SQLite y SQL PostgreSQL offline.

La prueba real NO sustituye Tesseract por un mock. Desde `backend/`, tras instalación:

```powershell
$env:EXTRACTION_TESSERACT_CMD = 'C:\Program Files\Tesseract-OCR\tesseract.exe'
$env:EXTRACTION_TESSDATA_PATH = 'C:\Program Files\Tesseract-OCR\tessdata'
$env:RUN_REAL_OCR = '1'
.venv/Scripts/python.exe -m pytest tests/unit/extraction/test_ocr_pipeline.py -m ocr_real -v
```

Esta prueba no necesita ni lee `.env`: usa SQLite en memoria. Verifica scan sin texto,
worker/Tesseract real, fragments con página/OCR y el pipeline structured/canonical para
Hit 200 ml, Chocorramo 65 g, 400 PACK, 5200 unitario y 2080000 total. Con RUN_REAL_OCR=1
un motor ausente debe fallar, no declarar aceptación exitosa. Por defecto la prueba queda
omitida explícitamente.

Resultado real con Tesseract 5.5.3.20260724: idioma `spa`, sin fallback; página 1
procesada y recuperada, un fragmento `ocr_text`, siete structured facts y siete canonical
facts confirmados. Texto OCR idéntico al texto visual definido en el fixture; confianza
media de palabras 94.37142857142857/100, OCR 1.000 s en la ejecución detallada.
La prueba pytest marcada duró 4.57 s. La repetición para capturar el reporte usó igualmente
SQLite en memoria y permitió comprobar reutilización del run sin repetir OCR.

El primer intento detectó una falla del adapter en Windows: comillas literales en el
argumento `--tessdata-dir`. Se corrigió únicamente el transporte de la ruta, usando
`TESSDATA_PREFIX` en el worker aislado. No se cambiaron reglas, umbrales ni fixture.
Los reportes locales están en `backend/.local/ocr42/real_acceptance.json`,
`raw_text.txt` e `initial_failure.json`. El PDF tiene solo un XObject Image, sin fuentes
ni operadores de texto; pypdf devuelve texto vacío. SHA-256 del fixture sin cambios:
`322a2f5a281cebcdfdd14365904194302a840c099408672636cac539171ac0e8`.

Se obtuvieron productos Hit 200 ml y Chocorramo 65 g, sus presentaciones, cantidad 400 PACK,
precio unitario 5200 COP y total 2080000 COP. No se inventaron otros requisitos ni una fila
PURCHASE_ITEM, que no existe en el formato del fixture. No se aplicó Alembic a desarrollo
ni se modificó `.env` o PATH. El cierre y despliegue quedan sujetos a revisión del usuario.

Riesgos pendientes: OCR puede confundir números/tablas; PSM 6 es simple y puede resultar
insuficiente para diagramaciones complejas; páginas breves pueden activar OCR innecesario;
los reintentos usan límites existentes y necesitan intervención si se agotan; un cierre
abrupto del proceso padre puede requerir revisar un claim `running`. No hay OCR manuscrito,
deskew, lectura de imágenes sueltas ni reconstrucción visual avanzada de tablas.

**Pendiente:** Evaluar Azure Document Intelligence / servicios especializados de extracción
documental durante la estrategia IA/cloud de Fase 4. No se implementaron Azure, Foundry,
LLM, embeddings, RAG, agentes, correo ni scheduler.

## Archivos de esta implementación

Creaciones:

```text
backend/alembic/versions/0013_ocr_diagnostics.py
backend/config/extraction_ocr.v1.json
backend/src/public_procurement/extraction/ocr_config.py
backend/src/public_procurement/extraction/domain/quality.py
backend/src/public_procurement/extraction/adapters/ocr.py
backend/src/public_procurement/extraction/adapters/hybrid.py
backend/src/public_procurement/extraction/OCR.md
backend/tests/unit/extraction/test_quality.py
backend/tests/unit/extraction/test_ocr.py
backend/tests/unit/extraction/test_ocr_pipeline.py
backend/tests/unit/extraction/test_ocr_migration.py
backend/tests/fixtures/extraction/build_ocr_fixtures.py
backend/tests/fixtures/extraction/native_refrigerios.pdf
backend/tests/fixtures/extraction/scanned_refrigerios.pdf
backend/tests/fixtures/extraction/mixed_refrigerios.pdf
backend/tests/fixtures/extraction/README.md
```

Modificaciones:

```text
README.md
backend/.env.example
backend/pyproject.toml
backend/uv.lock
backend/src/public_procurement/shared/config.py
backend/src/public_procurement/extraction/domain/content.py
backend/src/public_procurement/extraction/adapters/pdf.py
backend/src/public_procurement/extraction/adapters/isolated.py
backend/src/public_procurement/extraction/adapters/worker.py
backend/src/public_procurement/extraction/repositories.py
backend/src/public_procurement/extraction/services.py
backend/src/public_procurement/extraction/README.md
backend/src/public_procurement/entrypoints/cli/__main__.py
backend/src/public_procurement/eureka/domain/details.py
backend/src/public_procurement/eureka/adapters/extraction.py
backend/src/public_procurement/eureka/adapters/radar_pipeline.py
backend/src/public_procurement/eureka/services.py
backend/src/public_procurement/eureka/radar_services.py
backend/src/public_procurement/eureka/radar_repositories.py
backend/tests/unit/extraction/conftest.py
backend/tests/unit/eureka/test_radar_pipeline.py
backend/tests/unit/eureka/test_radar.py
backend/tests/unit/eureka/test_radar_repositories.py
backend/tests/unit/entrypoints/test_extraction_cli.py
backend/tests/unit/shared/test_config.py
backend/tests/unit/test_env_example.py
frontend/src/features/eureka/evidencePresentation.ts
frontend/src/features/eureka/evidencePresentation.test.ts
frontend/src/features/eureka/EurekaDetailPage.tsx
frontend/src/features/eureka/EurekaPage.test.tsx
```

Los demás cambios existentes del workspace pertenecen a fases anteriores.
No se modificó `backend/.env`.

## Aplicación autorizada de 0013 en desarrollo

Se aplicó únicamente `0013_ocr_diagnostics` desde `0012_eureka_radar`. La tabla nueva
`extraction.extraction_run_diagnostic` tiene PK UUID `extraction_run_id`, FK a
`extraction.extraction_run(id)` y `payload JSONB NOT NULL`. Su índice PK es único B-tree.
Sin reset, truncado, backfill o cambios de scoring/catálogo/reglas Radar.

Antes, después de migrar y después de los smoke tests se compararon filas y hashes de
las 27 tablas históricas: 41582 filas sin cambios. En desarrollo se crearon cero filas
documentales/OCR; la tabla de diagnósticos quedó vacía. Solo cambió la versión Alembic.
Covarachía mantiene score 65 y la evidencia previa intacta.

Smoke: extracción nativa de `CDP Firmado.pdf` en dry-run completada; OCR Tesseract real
5.5.3 y `spa` disponible con rutas temporales; health, señales, casos, compras, Eureka,
alerts, radar-runs, detalle y evidencia responden HTTP 200 sobre conexión read-only.
Trece pruebas aisladas de Radar pasan; no se lanzó una corrida real de Radar contra SECOP.

La prueba persistida usó un archivo SQLite nuevo separado de desarrollo. Creó 2
extraction_run (nativo + híbrido), 1 extraction_run_diagnostic, 1 content_fragment OCR,
7 structured_fact, 7 canonical_fact y 7 canonical_fact_evidence. Se cerró y reabrió
el archivo y se verificó reutilización del mismo run sin duplicar filas. El fixture
sin capa de texto conserva su SHA-256 y el motor usa español.

Reportes en `backend/.local/ocr42/migration013/`: `migration_report.json`, `smoke.json`,
`persisted_fixture.json` y `final_development_verification.json`; archivo SQLite guardado
en el mismo directorio. No hubo cambios inesperados en desarrollo.

Pendiente operativo de configuración: las pruebas usaron `EXTRACTION_TESSERACT_CMD` y
`EXTRACTION_TESSDATA_PATH` temporales. Sin ellas, la configuración actual busca `tesseract`
en PATH y este entorno todavía devuelve `ocr_unavailable`. Antes de corridas habituales,
configurar explícitamente las rutas documentadas (o suministrarlas desde el launcher).
La migración y la aceptación real están verificadas; `.env` y PATH se dejaron intactos.
