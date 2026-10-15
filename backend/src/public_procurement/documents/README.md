# Módulo documents

Inventario y adquisición documental compartidos. Dueño del esquema `documents`. Consulta
el proceso mediante `ingestion.services`; no accede a tablas de ingestion. Los consumidores
solo importan `documents.services`. No extrae contenido, no incorpora IA ni publica archivos
en la API. El frontend, seeds, señales y casos no cambian.

## Modelo y relación

- `document`: identidad única `(dataset_id, id_documento)`, portafolio, nombre original,
  fecha de carga de Socrata sin zona, URL, estado del último intento, errores y timestamps.
- `document_process`: enlace por UUID del proceso y portafolio. Permite compartir inventario
  entre varios procesos del mismo portafolio. No tiene FK hacia el esquema ingestion.
- `document_version`: una fila inmutable por documento y SHA-256; tamaño, content-type
  observado, ruta relativa, metadata fuente y fecha de descarga. Volver al mismo contenido
  reutiliza esa versión; los intentos conservan el orden de observaciones.
- `acquisition_attempt`: inicio, final, resultado, error explícito o versión obtenida.

Sincronizar actualiza metadata y fecha de consulta sin descargar ni invalidar versiones.
Si cambia nombre, fecha de carga o URL, el documento queda pendiente de una nueva adquisición.
Cada ejecución de descarga vuelve a consultar los binarios registrados, incluso los ya
disponibles, para detectar cambios que no aparezcan en la metadata. Hashes iguales no
duplican versiones ni archivos; cada ejecución deja un intento nuevo. Una versión fallida
nunca se inserta y las copias anteriores se conservan. El estado `failed` del documento
describe el último intento, no la destrucción de esas copias.

## Adquisición segura

`SocrataDocumentSource` consulta `dmgg-8hin` por `proceso = portfolio_id`, pagina con cursor
`:id` y deduplica inventario. Rechaza registros contradictorios y consultas truncadas. No
considera que una consulta vacía signifique que nunca hubo documentos: conserva el historial
registrado. No borra documentos ausentes de una consulta posterior.

`SecopDownloader` valida HTTPS, host exacto `community.secop.gov.co`, puerto 443 y ausencia
de credenciales en cada URL. Sigue manualmente un máximo de cinco redirecciones. Streaming
de 64 KiB, timeout de socket y comprobación de plazo entre lecturas. No acepta HTML,
respuestas parciales ni codificación HTTP comprimida inesperada. Los errores permiten
reintentar ejecutando de nuevo el comando; no se aplican reintentos automáticos de binarios.

`LocalBinaryStorage`, detrás del puerto `BinaryStorage`, escribe primero en `.tmp/*.part`,
verifica límite de tamaño, Content-Length cuando exista, archivo no vacío y firma/estructura
básica. Acepta PDF, ZIP (incluye DOCX/XLSX), OLE, RAR, 7z, PNG y JPEG. Para PDF exige marcador
final; para ZIP valida directorio central y estructura Office mínima cuando corresponde.
No descomprime contenidos ni hace análisis profundo, extracción o análisis antivirus.
Otros formatos quedan como `unsupported_type` y no se publican.

Tras flush/fsync, publica mediante movimiento atómico en el mismo almacenamiento a
`sha256/<prefijo>/<hash>`. No utiliza el nombre externo como ruta. La metadata de éxito
se confirma después de publicar el archivo; no hay transacciones abiertas durante red.

Un error controlado elimina el temporal. Un cierre abrupto puede dejar temporales ocultos,
intentos pendientes o binarios completos sin referencia si ocurre antes del commit. No son
documentos disponibles en la base. Un reintento reutiliza el hash; reconciliación y limpieza
de huérfanos quedan pendientes. Cambios concurrentes del inventario invalidan el resultado
del intento, con error `inventory_changed`. El bloqueo por documento serializa la inserción
de versiones al finalizar; PostgreSQL real y múltiples ejecutores requieren validación adicional.

## CLI y configuración

Desde `backend/`, aplicar `0007_documents_schema` antes de persistir inventario o descargar:

```bash
uv run python -m public_procurement.entrypoints.cli sync-documents --process CO1.REQ.11172521 --dry-run
uv run python -m public_procurement.entrypoints.cli sync-documents --process CO1.REQ.11172521
uv run python -m public_procurement.entrypoints.cli download-documents --process CO1.REQ.11172521
```

`--process` acepta UUID interno o identificador SECOP. El proceso debe estar persistido y
tener portafolio. Dry-run lee PostgreSQL para resolverlo y consulta Socrata, pero no escribe
inventario, no descarga y no crea almacenamiento. Download usa el inventario ya registrado
y retorna código 1 si al menos un documento falla; continúa procesando los demás.

`LOCAL_STORAGE_PATH` es la raíz de almacenamiento; `DOCUMENT_TIMEOUT_SECONDS` vale 120 por
defecto y `DOCUMENT_MAX_BYTES` 52428800 (50 MiB). Ambos límites deben ser positivos. No se
modifica `.env`; la plantilla `.env.example` documenta las variables.

Las pruebas unitarias usan respuestas simuladas, archivos temporales y SQLite en memoria.
No ejecutan pruebas destructivas contra desarrollo ni requieren descargar documentos reales.
