# Consolidación canónica — Fase 3B-2.2

La capa permanece dentro de `extraction`. Recibe hechos **persistidos y vigentes** a través de
`StructuredExtractionService.list_facts`; no ejecuta reglas de extracción, abre documentos ni
consulta servicios externos. `structured_fact` y sus textos/localizadores originales permanecen
intactos. Eureka conserva su scoring actual. No se añaden dependencias ni infraestructura.

## Modelo, evidencia e históricos

La migración aditiva `0011_fact_consolidation` sigue a `0010_structured_extraction` y crea:

- `extraction.canonical_fact`: UUID, proceso, tipo, clave de agrupación, valor JSONB, confianza,
  estado, versión de regla, huella de las entradas y fechas de creación/actualización.
- `extraction.canonical_fact_evidence`: PK compuesta y FK hacia el resultado canónico y el
  hecho estructurado. No elimina ni copia la evidencia textual: la referencia conserva toda
  la cadena hecho → fragmentos → versión documental → archivo original.

Se guardan snapshots inmutables del conjunto de entradas. La huella SHA-256 incluye los hechos
originales, sus IDs, valores y localizadores, ordenados de manera estable. El UUID canónico
se deriva del proceso, versión de regla, huella, tipo y clave. Una restricción única sobre esos
campos y `INSERT ON CONFLICT DO NOTHING` impiden duplicados bajo reintento/concurrencia.
Hechos y enlaces se guardan juntos en una transacción. Una repetición no cambia los timestamps.

Cambiar entradas o reglas crea otro snapshot completo, preservando el anterior y sus vínculos.
`created_at` y `updated_at` coinciden en esta primera versión porque no hay actualizaciones
en sitio. Al cambiar la semántica de normalización o agrupación debe incrementarse
`CONSOLIDATION_VERSION` (inicial `canonical-v1`). No se decide vigencia por el timestamp más
reciente: se consulta **la huella exacta de las entradas vigentes y la regla vigente**. Si no
existe ese snapshot, se solicita consolidar de nuevo y no se presenta uno viejo como actual.

El `canonical_value` guarda valor seleccionado, candidatos con sus IDs de hechos y fuente
preferida, `corroborated` y `review_required`. Los ítems agregan `field_candidates`,
`field_sources` y `field_confidence` para mostrar la procedencia y confianza de cada campo.
`evidence_count` en consola cuenta hechos estructurados vinculados, no documentos independientes.

## Agrupación y selección

- Productos: case/acentos/espacios, singular `jugos → jugo`, patrón limitado `jugo tetra MARCA`
  / `jugo MARCA tetra`, y prefijo redundante `ponque NOMBRE tradicional`. La presentación
  sigue formando parte de la identidad. No se ordenan libremente las palabras ni hay fuzzy
  matching o catálogo de marcas. `Hit 200 ml`, `Hit 500 ml` y `Hito 200 ml` permanecen separados.
- Presentaciones: producto explícito cuando existe, valor y unidad. `ml/mL → ml`, `gr/g → g`,
  unidad/unidades → unidad. PACK y PAQUETE permanecen distintos; tampoco se convierte 1 l
  a 1000 ml ni se deduce equivalencia entre empaques.
- Ítems: igualdad de descripción normalizada, incluyendo especificaciones y tamaños.
  Se compactan espacios, se normaliza `gr/g` y el espacio entre número/unidad. No se usa
  similitud difusa. Grupos de fila se identifican dentro de su versión documental, evitando
  colisiones de ordinales entre archivos.
- Cantidades/precios/totales: se conserva el contexto del ítem. Un patrón suelto solo hereda
  esa identidad si su tramo original está contenido en el de la fila. Un valor sin asociación
  verificable queda en un grupo `unscoped`; no se asigna al ítem más cercano por intuición.
- Dinero: `Decimal` exacto, enteros JSON para COP sin fracción, sin separadores ni escala
  artificial. No se redondean importes fraccionarios: se conserva su decimal como string.
  Presupuesto oficial y total del ítem son tipos distintos, aunque coincidan numéricamente.
- UNSPSC: código exacto como string, conservando ceros iniciales.
- Plazos: `{value, unit: days, kind: calendar/business/unknown, trigger}`. El evento de inicio
  conserva su texto normalizado; no se calcula una fecha ni se equiparan días hábiles/calendario.
- Requisitos: required/not_required/unknown; unknown no equivale a false. Se conserva el
  objeto del requisito: póliza, garantía de cumplimiento, RUP o experiencia. La póliza no
  requerida no cancela obligaciones de garantía de producto ni se mezcla con ellas.
- Lugar, forma de pago y observaciones: igualdad textual/estructurada normalizada, sin
  geocodificación, interpretación jurídica ni paráfrasis semántica.

Además de los quince tipos solicitados se conservan PAYMENT_PERCENTAGE,
OPERATIONAL_OBSERVATION, BRAND y DELIVERY_COUNT cuando están presentes. `item_description`
se vincula al PURCHASE_ITEM correspondiente, sin mostrarse como otra compra. Si aparece un
tipo futuro desconocido, se produce un error explícito para revisar las reglas; no se descarta.

La confianza es **la máxima** de los hechos de cada grupo; no se aplica un bonus estadístico.
Para elegir fuente representativa de candidatos equivalentes se prefiere mayor confianza,
después tabla/celda y por último un desempate estable por ID. No se descarta ninguna otra fuente.
La corroboración exige al menos dos conjuntos de fragmentos sin solapamiento. Dos reglas
sobre el mismo fragmento o un subconjunto de la misma evidencia no bastan. Este indicador
significa respaldo en ubicaciones diferentes, no independencia estadística de documentos.

## Conflictos y campos ausentes

Un grupo con candidatos incompatibles queda `status=conflict`, `review_required=true`, y no
selecciona un ganador aunque una fuente tenga confianza mayor. Los candidatos siguen visibles
con sus evidencias. En ítems se resuelve campo por campo: campos concordantes permanecen
disponibles y campos disputados quedan NULL con todos sus candidatos. La confianza máxima
indica calidad de una evidencia; **no elimina ni rebaja la marca de conflicto**.

Un ítem parcial puede completarse con otro de descripción idéntica: un precio ausente no es
un precio cero ni una contradicción. Se registra exactamente qué hechos proporcionaron cada
campo. Los precios no se copian entre ítems de descripción distinta.

Los tipos ausentes y campos ausentes de ítems se exponen en `CanonicalSummary.missing_fields`.
Un campo disputado no se etiqueta como ausente: requiere revisión. Ausencia de RUP/experiencia
permanece ausencia; no se crea un requisito negativo ficticio. Un pago único tampoco demuestra
una sola entrega.

## Servicio público y CLI

La interfaz está en `extraction.services`, disponible para Eureka y futuros consumidores:

- `ConsolidationService.run(reference, dry_run=False)`: resultado, conteos, conflictos y ausencias.
- `show(reference)`: únicamente el snapshot persistido de las entradas/regla vigentes.
- `evidence(reference, canonical_id)`: hechos originales completos, limitado al proceso solicitado.
- `history(reference)`: todos los snapshots del proceso, incluyendo reglas anteriores.
- `build_consolidation_service(sessions, settings)`: composición local.

Desde `backend/`, después de persistir los hechos estructurados:

```bash
uv run python -m public_procurement.entrypoints.cli consolidate-facts --process CO1.REQ.11172521 --dry-run
uv run python -m public_procurement.entrypoints.cli consolidate-facts --process CO1.REQ.11172521
uv run python -m public_procurement.entrypoints.cli show-canonical --process CO1.REQ.11172521
uv run python -m public_procurement.entrypoints.cli show-canonical --process CO1.REQ.11172521 --with-evidence
```

Se aceptan UUID interno o identificador SECOP. Dry-run necesita structured facts de `0010`
pero no las tablas de `0011`. Persistencia y consulta requieren `0011` en el entorno elegido.
La implementación **no aplicó esa migración a PostgreSQL de desarrollo**.

## Caso real: Covarachía

Se leyeron los **39 structured facts persistidos y vigentes** del proceso CO1.REQ.11172521 con
PostgreSQL `transaction_read_only=on`. Se copiaron las entradas a SQLite en memoria para probar
enlaces y recuperación de evidencias. La consolidación produjo **18 canónicos, 0 conflictos**.
Primera persistencia: 18 nuevos; segunda: 0 nuevos, mismos IDs. Los 39 hechos originales se
recuperaron mediante 39 enlaces normalizados. No se escribió ni migró PostgreSQL.

| Resultado | Valor | Confianza / respaldo |
| --- | --- | --- |
| PRODUCT | jugo hit, 200 ml | 0.8, corroborado, 4 hechos |
| PRODUCT | chocorramo tradicional, 65 g | 0.8, corroborado, 4 hechos |
| PRESENTATION | 200 ml y 65 g, una por producto | 1.0, corroboradas |
| PURCHASE_ITEM | Refrigerios, 400 PACK, unitario 5200 COP, total 2080000 COP | 1.0, 6 hechos; precios con confianza por campo 0.8 |
| QUANTITY | 400 PACK | 1.0, corroborado, 5 hechos |
| UNIT_PRICE_COP | 5200 | 0.8 |
| TOTAL_COP | 2080000 | 0.8 |
| BUDGET_COP | 2080000 | 0.8 |
| UNSPSC | 50192703 | 0.6 |
| EXECUTION_TERM | 5 días calendario, desde firma | 0.8 |
| DELIVERY_LOCATION | Cláusula de entrega a I.E. San Luis Beltrán, Covarachía y dirección | 0.8 |
| PAYMENT_METHOD | single_payment, 100% | 0.8 |
| PAYMENT_TERM | 30 días calendario, desde aprobación de factura | 0.8 |
| GUARANTEE_REQUIRED | not_required, subject=policy | 0.8 |
| PAYMENT_PERCENTAGE | 100 | 0.8 |
| OPERATIONAL_OBSERVATION | Certificado de garantía; reposición de productos defectuosos | 2 resultados separados, 0.8 |

Ausentes: RUP_REQUIRED, EXPERIENCE_REQUIRED y DELIVERY_COUNT. No hay campos ausentes en el
ítem consolidado. Las fuentes principales siguen siendo Estudios Previos páginas 2, 3, 4 y 15,
y DOCX tabla 1, fila 2. Los precios vienen de Estudios Previos p. 3; la plantilla DOCX respalda
descripción/cantidad/unidad, sin inventar sus precios en blanco.

No se elevó el producto a confianza 1.0 porque sus hechos originales tienen 0.8, aunque las
presentaciones y la cantidad explícita sí alcancen 1.0. La corroboración se informa por separado.

## Limitaciones

- Los aliases de producto y encabezados son reglas pequeñas versionadas; necesitan revisión
  con otros expedientes. No identifican SKU, marcas maestras ni equivalencias de empaque.
- Descripciones diferentes quedan separadas aunque un humano pueda reconocer el mismo ítem.
  Descripciones idénticas con cantidades/precios diferentes requieren revisión; no se suman.
- Varias direcciones, códigos UNSPSC o plazos distintos pueden ser legítimos. Si comparten
  grupo de proceso se muestran como candidatos en conflicto, sin interpretar su aplicabilidad.
- La compleción de campos está implementada para ítems. Plazos o pagos con información parcial
  distinta pueden quedar para revisión; no se enriquecen automáticamente por contexto lejano.
- Los textos canónicos están normalizados para comparar. El texto original, acentos y layout
  extraído permanecen consultables en los hechos y localizadores de evidencia.
- Snapshots completos aumentan almacenamiento; no hay retención, scheduler ni limpieza automática.
  La fase está orientada al volumen local actual, sin paginación del listado histórico.
- COP fraccionario se conserva exactamente, sin redondear a entero; requiere criterio de
  presentación posterior. No hay tipo de cambio ni conversión de unidades.
- Sin UI, OCR nuevo, IA, agentes, embeddings, servicios pagos ni cambios de scoring.

## Archivos de esta fase

Nuevos:

- `backend/alembic/versions/0011_fact_consolidation.py`
- `backend/src/public_procurement/extraction/domain/canonical.py`
- `backend/src/public_procurement/extraction/consolidation.py`
- `backend/src/public_procurement/extraction/canonical_repositories.py`
- `backend/src/public_procurement/extraction/CONSOLIDATION.md`
- `backend/tests/unit/extraction/test_consolidation.py`
- `backend/tests/unit/extraction/test_canonical_service.py`
- `backend/tests/unit/extraction/test_canonical_migration.py`
- `backend/tests/unit/entrypoints/test_canonical_cli.py`

Modificados: `backend/src/public_procurement/extraction/services.py`, `README.md`;
`backend/src/public_procurement/entrypoints/cli/__main__.py`; `backend/alembic/env.py`;
y `README.md` de la raíz. Las referencias abreviadas junto a un directorio comparten ese directorio.
