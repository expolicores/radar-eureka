# Extracción documental compartida — Fase 3B

La capa sobre fragmentos persistidos de la Fase 3B-2 está documentada en
[STRUCTURED.md](STRUCTURED.md), con reglas, tabla `structured_fact`, CLI y evidencia de Covarachía.

La agrupación canónica de esos hechos, con conflictos e históricos, está documentada en
[CONSOLIDATION.md](CONSOLIDATION.md) para la Fase 3B-2.2.

`extraction` transforma versiones descargadas por `documents` en evidencia textual. No consulta
Socrata, no descarga archivos y no modifica el score de Eureka. Su interfaz pública es
`extraction.services`: `extract_process`, `extract_document`, `list_extractions` y `search`.
`list_extractions` consulta los intentos de las versiones vigentes sin ejecutar lectores.
El adaptador documental
usa exclusivamente `documents.services`; la relación proceso/portafolio/documento sigue siendo
responsabilidad de `documents`. No se aceptan rutas del usuario.

## Persistencia y versionado

La migración aditiva `0009_extraction_schema`, posterior a `0008_eureka_discovery`, crea:

- `extraction.extraction_run`: UUID, FK a `documents.document_version`, nombre original,
  identidad del extractor, estado, inicio/fin, errores, SHA-256 de entrada, longitud y número
  de fragmentos, páginas sin texto, conteos por formato y timestamp de creación.
- `extraction.content_fragment`: UUID, FK al run, ordinal, texto original, texto normalizado,
  página/párrafo/tabla/fila/columna/hoja/celda y `source_locator` JSONB.

Un índice único parcial impide más de un run en ejecución o reutilizable para una combinación
versión documental + extractor + versión del extractor. Los fallos quedan fuera de ese índice:
un reintento crea otro run, sin borrar el anterior. Cambiar el archivo implica otra versión
documental; cambiar biblioteca, versión del código del lector, normalización o límites implica
otra identidad de extractor. Los resultados finalizados no se sobrescriben. Al reutilizarlos
se verifica de nuevo la existencia, tamaño y hash del binario. Un fallo de esa verificación
se registra como otro intento fallido y conserva la evidencia histórica.

La versión vigente de un documento es la del último intento de adquisición exitoso, incluyendo
el caso A → B → A cuando `documents` reutiliza una versión anterior por hash. Sin una versión
descargada se informa `not_downloaded`, sin inventar una FK ni crear un run.

## Lectores y evidencia

| Formato | Biblioteca | Unidad y localización |
| --- | --- | --- |
| PDF | [pypdf](https://pypdf.readthedocs.io/en/stable/user/extract-text.html) | Texto embebido por página, numerada desde 1 |
| DOCX | [python-docx](https://python-docx.readthedocs.io/en/latest/api/document.html) | Párrafos del cuerpo y celdas de tablas; bloque, tabla, fila y columna desde 1 |
| XLSX | [openpyxl](https://openpyxl.readthedocs.io/en/stable/optimized.html) | Celda individual, nombre de hoja y coordenada A1 |

Se preserva exactamente el texto devuelto por el lector, incluidos acentos y saltos de línea.
Los párrafos y celdas vacíos se omiten como fragmentos, pero conservan su posición al numerar.
Los conteos de párrafos/tablas incluyen bloques vacíos del cuerpo. Unidades de más de 20.000
caracteres se dividen en cortes exactos; `char_start` inclusivo y `char_end` exclusivo localizan
el corte dentro del texto de la página/párrafo/celda. El localizador persistido incluye también
versión documental, nombre, SHA-256 e identidad del extractor.

La normalización es un campo separado: Unicode, casefold, eliminación de marcas diacríticas
y compactación de espacios/saltos de línea. `search` compara substrings literales normalizados,
escapa comodines SQL y devuelve texto original, localizador y contexto. Para tablas/hojas se
incluye la misma fila; para otros fragmentos, los ordinales vecinos. El contexto tiene un
máximo de 12 fragmentos y la búsqueda de 100 resultados. Se usa el último extractor finalizado
reutilizable por versión vigente para no repetir resultados históricos. No hay inferencia de
productos, precios, requisitos ni coincidencias semánticas.

PDF sin texto en todas sus páginas queda `requires_ocr`; con algunas páginas vacías,
`partial_text`; esas páginas se enumeran explícitamente. Una página vacía es candidata a revisión,
no prueba de que contenga una imagen escaneada. DOCX/XLSX sin contenido quedan `empty_text`.

## Robustez y límites

El almacenamiento abre solamente la ruta canónica registrada por SHA-256 dentro de su raíz;
verifica tamaño/hash por streaming. Se crea un snapshot temporal privado, se vuelve a comprobar
su hash y se ejecuta el lector en un subproceso local. Se elimina el snapshot al salir. El
subproceso tiene timeout y un límite de memoria de 512 MiB mediante Job Object en Windows o
`RLIMIT_AS` en Unix; si no puede establecerlo, falla explícitamente. No constituye un sandbox
de seguridad completo para archivos hostiles.

| Variable | Valor inicial |
| --- | --- |
| `EXTRACTION_TIMEOUT_SECONDS` | 60 |
| `EXTRACTION_MAX_BYTES` | 52428800 (50 MiB) |
| `EXTRACTION_MAX_CHARS` | 2000000 |
| `EXTRACTION_MAX_FRAGMENTS` | 10000 |
| `EXTRACTION_MAX_PAGES` | 300 |

Todos esos valores deben ser positivos. Los paquetes Office se limitan adicionalmente a
100 MiB declarados descomprimidos, 5.000 entradas y 100.000 celdas recorridas. `defusedxml`
se instala para el procesamiento XML de openpyxl. XLSX usa lectura incremental y conserva
fórmulas como texto: no las ejecuta ni recalcula.

Los errores por formato no soportado, corrupción, cifrado, tamaño/hash, timeout o límites
se informan con códigos y mensajes sin volcar el contenido al log. Un fallo documental no
detiene el resto del lote; la CLI termina con código 1 si hay documentos fallidos. No se
persisten fragmentos parciales de un lector que falla.

## CLI

Desde `backend/`, con dependencias sincronizadas y documentos registrados:

```bash
uv run python -m public_procurement.entrypoints.cli extract-documents --process CO1.REQ.11172521 --dry-run
uv run python -m public_procurement.entrypoints.cli extract-documents --process CO1.REQ.11172521
uv run python -m public_procurement.entrypoints.cli extract-document --document 869769892
uv run python -m public_procurement.entrypoints.cli search-extracted-text --process CO1.REQ.11172521 --term chocorramo
uv run python -m public_procurement.entrypoints.cli search-extracted-text --process CO1.REQ.11172521 --term garantia --limit 20
```

`--process` acepta UUID interno o identificador SECOP; `--document`, UUID o ID documental
externo registrado. `--dry-run` sí analiza los archivos, pero no crea runs ni fragmentos ni
modifica documentos; funciona antes de aplicar `0009`. Persistencia y búsqueda requieren
aplicar previamente esa migración en el entorno elegido. **No se aplicó a PostgreSQL de
desarrollo durante esta implementación.**

## Validación real: Covarachía

Proceso `CO1.REQ.11172521`, portafolio `CO1.BDOS.10985405`. Se leyeron los registros de PostgreSQL
con `transaction_read_only=on`; runs y fragmentos se persistieron únicamente en SQLite en
memoria para validar extracción, búsqueda y reutilización, sin migrar ni escribir en desarrollo.

| Documento | Estado | Fragmentos | Unidades |
| --- | --- | --- | --- |
| CDP Firmado.pdf | completed | 1 | 1 página |
| ESTUDIOS PREVIOS Firmados.pdf | completed | 16 | 16 páginas |
| FORMATO DE PROPUESTA INSTITUCIONAL.docx | completed | 82 | 145 párrafos del cuerpo y 1 tabla |

No hubo páginas PDF sin texto. `chocorramo` y `hit` dieron cada uno cuatro coincidencias:
Estudios Previos páginas 2, 3 y 15, y DOCX tabla 1, fila 2, columna 2. El texto DOCX contiene
`JUGO HIT TETRA X 200Ml + CHOCORRAMO TRADICIONAL X 65 Gr`; las columnas 3 y 4 de la misma fila
contienen `400` y `PACK`. Estudios Previos página 3 conserva cantidades, presentación y sitio
de entrega; página 4 contiene condiciones de pago. Son resultados del contenido, sin reglas
ni hallazgos hardcodeados. Las búsquedas `entrega` y `garantia` dieron 9 y 1 coincidencias.

El binario canónico del DOCX estaba ausente pese a existir su registro de descarga. Se restauró
usando el almacenamiento atómico de `documents` desde la copia local ya existente, únicamente
después de comprobar que su SHA-256 coincidía exactamente con la versión registrada. No se
actualizó ningún registro PostgreSQL.

## Límites pendientes

- Sin OCR: imágenes, firmas, sellos y texto escaneado no se extraen. Una página con texto
  embebido puede contener también imágenes con texto; este lector no detecta esa omisión.
- PDF conserva el texto que produce pypdf, sin reconstruir tablas ni garantizar orden visual.
- DOCX cubre el cuerpo y tablas de primer nivel; no cuadros de texto, encabezados/pies,
  tablas anidadas, comentarios ni revisiones. Celdas combinadas pueden repetir texto.
- XLSX no renderiza formatos visuales ni evalúa fórmulas; no procesa macros, gráficos ni imágenes.
- Búsqueda por substring, sin índice de texto completo; no une términos partidos entre fragmentos.
- Un cierre abrupto del proceso coordinador puede dejar un run `running`; requiere revisión
  operativa antes de marcarlo fallido y reintentar. No se implementó scheduler ni recuperación automática.
- Los límites son por documento; no hay cuotas globales de concurrencia ni política de retención.
- Los expedientes pueden contener datos personales. Se conserva el contenido sin censura
  automática; una futura UI requerirá políticas de exposición, acceso y auditoría.

No se implementan IA, OCR, embeddings, agentes, cloud, Foundry, UI ni cambios en scoring.

## Archivos de la Fase 3B

Nuevos, relativos a `backend/`:

- `alembic/versions/0009_extraction_schema.py`.
- `src/public_procurement/extraction/__init__.py`, `README.md`, `ports.py`,
  `repositories.py`, `services.py`.
- `src/public_procurement/extraction/domain/__init__.py`, `content.py`, `text.py`.
- `src/public_procurement/extraction/adapters/__init__.py`, `common.py`, `documents.py`,
  `pdf.py`, `docx.py`, `xlsx.py`, `isolated.py`, `worker.py`.
- `tests/unit/extraction/__init__.py`, `conftest.py`, `test_readers.py`, `test_services.py`,
  `test_search.py`, `test_isolation.py`, `test_migration.py`.
- `tests/unit/entrypoints/test_extraction_cli.py`.

Modificados: `backend/.env.example`, `backend/pyproject.toml`, `backend/uv.lock`,
`backend/alembic/env.py`, `backend/src/public_procurement/shared/config.py`,
`backend/src/public_procurement/entrypoints/cli/__main__.py`,
`backend/src/public_procurement/documents/ports.py`, `repositories.py`, `services.py`,
`backend/src/public_procurement/documents/adapters/local_storage.py`,
`backend/tests/unit/documents/test_services.py`, `backend/tests/unit/shared/test_config.py`,
`backend/tests/unit/test_env_example.py` y el `README.md` de la raíz.

El resto de cambios previos del workspace pertenece a fases anteriores u otras tareas.

## Fase 4.2

El fallback OCR local y sus diagnósticos se describen en [OCR.md](OCR.md).
`format_counts` conserva su contrato de contadores; `0013_ocr_diagnostics` crea una tabla
aditiva separada. La extracción nativa sigue disponible sin aplicar esa migración.
