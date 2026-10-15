# Módulo `ingestion`

Registra las compras públicas de televisores (contratos SECOP II y órdenes de la Tienda Virtual del Estado) con sus ítems clasificados, y lleva la bitácora de cada ejecución de ingesta. Es dueño del esquema PostgreSQL `ingestion`.

## Responsabilidades

- **Identidad de la compra:** fuente + identificador de origen sin transformar (`id_contrato` en SECOP II, `identificador_de_la_orden` en TVEC).
- **Clasificación por reglas** de cada ítem (`domain/classification.py`): televisor incluido, accesorio o servicio excluido, o dudoso. Decide por el sustantivo principal de la descripción.
- **Estados explícitos** de datos faltantes: precio unitario `explicit`, `derived`, `not_published` o `pending_review`; base de IVA `included`, `excluded` o `undetermined`.
- **Privacidad:** el documento de una persona natural no se guarda (restricción en la tabla y regla en el dominio).
- **Bitácora:** una fila en `ingestion_run` por ejecución y fuente (leídas, nuevas, actualizadas, fecha de corte).

## Capas

| Archivo | Rol |
| ------- | --- |
| `domain/` | Entidades, enums y reglas puras; sin ORM ni I/O |
| `ports.py` | `PublicDataSource`: fuente de datos abiertos |
| `adapters/seed.py`, `adapters/seed_data.py` | Fuente **ficticia** y determinística para la demo (MVP Beta) |
| `repositories.py` | Tablas SQLAlchemy y mapeo al dominio |
| `unit_of_work.py` | Una transacción por ejecución |
| `services.py` | `IngestionService.run(source)`: única puerta de entrada desde otros módulos |

## Procesos SECOP (fase inicial de Eureka)

`domain/process.py` representa procesos sin exigir contrato, proveedor adjudicado ni ítems.
`adapters/socrata_processes.py` consulta el dataset real `p6dx-8zbt` por portafolio o intervalo
de publicación. La identidad única es `(dataset_id, id_del_proceso)`; `id_del_portafolio` se
conserva por separado y puede faltar. No se deduce un proceso desde el portafolio.

`ProcessIngestionService` descarga todas las páginas antes de abrir la transacción y rechaza
duplicados contradictorios. `process_repositories.py` realiza upsert atómico por identidad:
las reejecuciones no duplican procesos y no actualizan filas cuyo contenido es igual. La
bitácora de sincronizaciones exitosas es independiente de `ingestion_run`.

La paginación usa `:id ASC` y `:id > último_cursor`, sin offsets. El cursor solo pertenece a
esa ejecución; no es una marca de actualización incremental. El filtro temporal es inicio
inclusivo y fin exclusivo sobre `fecha_de_publicacion_del` (fecha sin zona del proveedor).
Las modificaciones concurrentes del dataset no tienen aislamiento de snapshot: para refrescar
estados se debe repetir el intervalo o consultar el portafolio. Alcanzar `max-pages` genera
error y no persiste una consulta truncada. Los fallos de red o HTTP transitorios se reintentan
hasta tres intentos (esperas 2/4 segundos); los campos inválidos cancelan la carga completa.

Comando desde `backend/`:

```bash
uv run python -m public_procurement.entrypoints.cli sync-processes --portfolio CO1.BDOS.10985405 --dry-run
uv run python -m public_procurement.entrypoints.cli sync-processes --portfolio CO1.BDOS.10985405
uv run python -m public_procurement.entrypoints.cli sync-processes --published-from 2026-10-01 --published-before 2026-10-08
```

`--dry-run` consulta sin requerir configuración de base ni abrir conexiones. Los demás modos
requieren aplicar primero `0006_ingestion_processes`. No se descargan documentos ni se
recalculan señales. No se guarda el JSON completo ni información de proveedores/personas:
solo la lista explícita de campos del adaptador. Precio base COP entero; no equivale a precio unitario.

## Pendiente para compras reales

- Adaptador de Socrata (datos.gov.co) para SECOP II (`jbjy-vk9h`) y TVEC (`rgxm-mmea`, ítems `usqp-5nsn`/`3hdv-smhz`), con marcas de agua y paginado.
- Validaciones de calidad con catálogo de rechazos (HU-005) y ejecución como job del worker.
