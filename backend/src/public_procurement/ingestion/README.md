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

## Pendiente para el producto real

- Adaptador de Socrata (datos.gov.co) para SECOP II (`jbjy-vk9h`) y TVEC (`rgxm-mmea`, ítems `usqp-5nsn`/`3hdv-smhz`), con marcas de agua y paginado.
- Validaciones de calidad con catálogo de rechazos (HU-005) y ejecución como job del worker.
