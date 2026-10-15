# Extracción estructurada — Fase 3B-2

La capa vive dentro de `extraction`. Consume exclusivamente `content_fragment` ya persistido
del último run reutilizable de cada versión documental vigente. No abre archivos, descarga
documentos, vuelve a ejecutar lectores, consulta Socrata ni altera Eureka. No añade dependencias.

## Modelo y servicio público

La migración aditiva `0010_structured_extraction` sigue a `0009_extraction_schema` y crea
`extraction.structured_fact`. Cada fila conserva UUID, proceso, versión documental, fragmento
único cuando corresponde, tipo de hecho, valores string/Decimal/boolean, unidad, valor normalizado
JSONB, confianza, texto de evidencia, localizador JSONB, regla, versión de regla, huella y fecha.

Los importes usan `NUMERIC(24,6)`, no float de aplicación. `process_id` se resuelve mediante
el servicio público de `documents`, que ya encapsula la consulta a ingestion; extraction no
consulta tablas de ingestion. Hay FK a la versión documental y al fragmento único.

`source_locator.sources` conserva **todos** los fragmentos participantes, run de origen, nombre
original, localizador previo, offsets dentro del fragmento y texto exacto. Para filas de tablas
se incluyen encabezados y celdas de datos. Si hay varias fuentes, `content_fragment_id` es NULL
y los IDs completos permanecen en JSONB. No se crea una tabla de enlaces adicional en esta fase.
Los campos `group_key` y `subject` relacionan ítems/productos/presentaciones y distinguen el
objeto del requisito, por ejemplo póliza frente a garantía de cumplimiento.

El texto de evidencia no se normaliza ni resume. Si combina fuentes, concatena sus textos
con separadores de nueva línea; cada segmento sigue disponible individualmente en `sources`.
Las reglas trabajan sobre una vista sin tildes y con espacios compactados, con un mapa de
offsets hacia el original. Los valores normalizados están separados de esa evidencia.

Interfaz pública en `extraction.services`:

- `StructuredExtractionService.extract(reference, dry_run=False)`: hechos encontrados y número
  de nuevos registros. No tener fragmentos persistidos produce un error claro.
- `list_facts(reference, include_history=False)`: hechos de las reglas vigentes y fragmentos
  vigentes. `include_history=True` conserva acceso a versiones anteriores y reglas históricas.
- `build_structured_service(sessions, settings)`: composición local reutilizable por Eureka.

La versión inicial es `structured-v1`; al cambiar el significado de una regla se debe incrementar
`RULE_VERSION`. La restricción única usa proceso + versión documental + versión de regla +
huella. Esta huella incluye tipo, fuentes/offsets/localizadores, grupo y valores, de modo que
repetir la ejecución no duplica registros. Se usa INSERT ON CONFLICT DO NOTHING; no hay UPDATE
ni borrado de hechos históricos. Dos reglas que produzcan exactamente el mismo hecho y
evidencia se deduplican. Un nuevo run textual conserva nuevos vínculos de evidencia; no reemplaza
los hechos anteriores. Un portafolio compartido puede producir hechos ligados a procesos distintos.

## Reglas iniciales

| Regla | Requisito explícito / salida |
| --- | --- |
| `item_row` | Encabezados reconocidos y fila completa: descripción, cantidad/unidad y precios disponibles |
| `product_presentation` | Nombre literal + `X` + cantidad + ml/l/g/kg/unidades; producto y presentación vinculados |
| `explicit_size` | Tamaños con unidad de masa/volumen; no interpreta conteos sueltos como tamaño de empaque |
| `explicit_brand` | Etiqueta `marca:` y texto de marca; sin catálogo ni inferencia de fabricante |
| `quantity_unit` | Cantidad junto a PACK, UNIDAD, CAJA, PAQUETE, PIEZA, PAR, BOLSA o KIT |
| `labelled_cop` | Precio unitario, valor total o presupuesto con etiqueta y número explícito |
| `labelled_budget` | Presupuesto oficial con importe precedido por `$`, incluso después del importe escrito en palabras |
| `explicit_unspsc` | Código de ocho dígitos próximo a la etiqueta UNSPSC |
| `labelled_deadline` | Plazo de ejecución o obligación explícita de pago, días hábiles/calendario y desencadenante cuando aparece |
| `explicit_payment` | Pago único, pagos parciales o contra entrega; porcentaje 100 cuando está en la frase |
| `explicit_payment_percent` | 100% del valor con contexto inmediato de pago |
| `labelled_delivery` | Sitio/lugar de entrega con texto explícito de la sección |
| `explicit_requirement` | Frases expresas de exigencia o negación de póliza/garantía, RUP y experiencia |
| `named_guarantee` | Garantía de cumplimiento mencionada afirmativamente, sin negación/condicional próximo |
| `explicit_deliveries` | Una sola/única entrega frente a entregas parciales/múltiples |
| `explicit_operation` | Certificado de garantía y reposición de productos defectuosos |
| `adjacent_label` | Encabezado aislado DOCX y párrafo inmediatamente siguiente dentro del mismo run |

COP admite agrupaciones como `5.200`, `2.080.000` y `2’080.000,oo`, `$` opcional y centavos
con coma. No asigna significado comercial a importes aislados. `XXXXX` no es un precio; una
agrupación mal formada no se convierte en un precio parcial.

Las filas DOCX/XLSX se agrupan por versión, run, tabla/hoja, fila y columna. Se reconocen las
columnas por sus encabezados, no por posiciones fijas. Celdas divididas en fragmentos se
recomponen por ordinal. Para XLSX se usan también las coordenadas A1 existentes. PDF requiere
un encabezado textual de ítem/descripcion/cantidad/unidad/precios, y un patrón completo de fila
con límites de longitud. No reconstruye geométricamente tablas arbitrarias ni cruza páginas.

La proximidad DOCX está limitada a un encabezado reconocido, un párrafo inmediatamente siguiente
y 2.000 caracteres, sin mezclar documentos/runs/tablas. Para ejecución se admite número y
palabra entre uno y diez, por ejemplo cinco (05); si contradicen el número, no se emite el plazo.
El plazo de pago distingue pagar la factura de presentarla o revisarla. El evento de inicio
(firma/aprobación) conserva su texto, sin convertirlo en una fecha de vencimiento.

Confianza: `1.0` para celdas estructuradas y cantidades/unidades directas; `0.8` para patrones
textuales claros; `0.6` para proximidad (incluido UNSPSC contextual). Son categorías de certeza
de la regla, **no probabilidades calibradas** ni validación jurídica.

Los requisitos ausentes permanecen ausentes (unknown para el consumidor). No se deduce
`not_required` porque RUP/experiencia/póliza no aparezcan. Tampoco un pago único demuestra
una única entrega. La no exigencia de póliza no cancela obligaciones de garantía del producto.

## CLI

Desde `backend/`, después de persistir contenido mediante `extract-documents`:

```bash
uv run python -m public_procurement.entrypoints.cli extract-structured --process CO1.REQ.11172521 --dry-run
uv run python -m public_procurement.entrypoints.cli extract-structured --process CO1.REQ.11172521
uv run python -m public_procurement.entrypoints.cli show-structured --process CO1.REQ.11172521
uv run python -m public_procurement.entrypoints.cli show-structured --process CO1.REQ.11172521 --history
```

Se aceptan UUID interno o identificador SECOP. El dry-run necesita `0009` y sus fragmentos,
pero no necesita `0010`; persistencia y show necesitan `0010` en el entorno elegido. No se
aplicó esta migración a PostgreSQL de desarrollo durante la implementación. La salida incluye
tipo, valor, confianza, regla y todas las fuentes/evidencias. No ejecuta scoring ni señales.

## Validación funcional: Covarachía

Se consultó el proceso `CO1.REQ.11172521` y sus fragmentos persistidos con PostgreSQL
`transaction_read_only=on`. Los hechos se guardaron **solo en SQLite en memoria**. La primera
ejecución guardó 39 hechos con evidencia; la segunda guardó 0. Se comprobó su recuperación
por el servicio público. Esos 39 registros incluyen evidencias repetidas en distintos documentos
y campos del mismo ítem: no representan 39 productos ni 39 ítems distintos.

| Campo | Valor observado | Evidencia principal |
| --- | --- | --- |
| Ítem/descripción | REFRIGERIOS PACK, con su descripción completa original | Estudios Previos, p. 3 |
| Cantidad/unidad | 400 PACK | Estudios Previos, p. 3; DOCX tabla 1, fila 2 |
| Precio unitario | 5200 COP | Estudios Previos, p. 3 |
| Total del ítem | 2080000 COP | Estudios Previos, p. 3 |
| Producto/presentación | JUGO HIT TETRA, 200 ml | Estudios Previos, p. 3; DOCX tabla 1, fila 2, columna 2 |
| Producto/presentación | CHOCORRAMO TRADICIONAL, 65 g | Misma ubicación |
| UNSPSC | 50192703 | Estudios Previos, p. 2 |
| Presupuesto oficial | 2080000 COP | Estudios Previos, p. 3 |
| Ejecución | 5 días calendario desde firma del contrato | Estudios Previos, p. 3 |
| Entrega | Texto que identifica I.E. San Luis Beltrán, Covarachía, sede y dirección | Estudios Previos, p. 3 |
| Pago | Único pago, 100% | Estudios Previos, p. 4 |
| Plazo de pago | 30 días calendario siguientes a aprobación de la factura | Estudios Previos, p. 4 |
| Póliza | not_required, subject=policy | Estudios Previos, p. 4 |
| Observaciones | Certificado de garantía y reemplazo de productos defectuosos | Estudios Previos, p. 4 |

No se extrajeron RUP, experiencia exigida ni número de entregas: no hubo un patrón explícito
concluyente. El CDP no produjo hechos con estas reglas. Los precios en blanco del DOCX y de
la plantilla en Estudios Previos p. 15 siguen ausentes; no se copian desde p. 3. Tampoco se
unifican automáticamente las distintas menciones de un producto ni se elige un documento ganador.

En la revisión manual de los campos anteriores no se identificaron falsos positivos. Se
añadieron regresiones para porcentajes de garantía confundidos con pago, números sin etiqueta,
precios mal agrupados, negaciones, plazos de envío/revisión de factura y precios de plantilla.
Eso no demuestra ausencia de falsos positivos en otros expedientes: requiere revisión humana.

## Limitaciones

- Reglas iniciales de gramática española y encabezados conocidos; variantes no reconocidas
  dejan campos ausentes. No resuelven excepciones jurídicas, condiciones complejas o contradicciones.
- El nombre del producto se conserva literal; no se infiere marca a partir de un catálogo
  ni se normaliza semánticamente JUGOS TETRA HIT y JUGO HIT TETRA.
- Lugar y observaciones conservan la cláusula, sin geocodificar, limpiar direcciones ni resumir.
- No interpreta números únicamente escritos en palabras ni unidades monetarias ambiguas.
- No reconstruye filas entre páginas, tablas sin encabezado, PDFs con orden visual alterado
  ni relaciones entre referencias lejanas. No recupera contenido que requeriría OCR.
- Evidencias equivalentes en documentos distintos permanecen separadas; faltan resolución
  de conflictos y consolidación para una futura ficha comercial.
- Búsqueda/listado y reglas son locales, sin scheduler, cuotas globales ni procesamiento asíncrono.
- No hay IA, servicios pagos, Foundry, agentes, embeddings, OCR nuevo, UI ni cambios al score.
- Se conserva evidencia que puede contener datos personales; una UI futura requiere políticas
  de exposición y acceso. La CLI muestra el contenido a quien la ejecuta.

## Archivos de esta fase

Nuevos: `alembic/versions/0010_structured_extraction.py`, `extraction/domain/structured.py`,
`extraction/structured_rules.py`, `extraction/structured_tables.py`,
`extraction/structured_repositories.py`, este documento,
`tests/unit/extraction/test_structured_rules.py`, `test_structured_service.py`,
`test_structured_migration.py` y `tests/unit/entrypoints/test_structured_cli.py`.

Modificados: `extraction/domain/content.py`, `ports.py`, `adapters/documents.py`,
`repositories.py`, `services.py`, `README.md`; `documents/services.py`;
`entrypoints/cli/__main__.py`; `alembic/env.py`; `tests/unit/extraction/test_services.py`;
y `README.md` de la raíz. Las rutas de módulos son relativas a `backend/src/public_procurement/`.
