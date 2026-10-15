# Eureka con hechos canónicos — Fase 3B-2.3

Read model derivado sin tablas, migración, dependencias ni cache nuevos. Extraction conserva
la propiedad de sus hechos y evidencia; Eureka no los modifica ni duplica en su esquema.

## Arquitectura y servicio

`EurekaDetailsService` depende de `ProcessMetadataSource`, `OpportunityQueries` y
`CanonicalFactsSource`. El adaptador `ExtractionCanonicalSource` usa exclusivamente
`extraction.services`, sin acceso a SQL/repositorios de otro módulo. La lectura de la oportunidad
persistida usa el repositorio propio de Eureka. Extraction no depende de Eureka; los contratos
de importación verifican esa separación.

`build_eureka_details_service(sessions, settings)` compone el servicio de lectura.
`get(reference)` acepta UUID interno o identificador SECOP y devuelve `EurekaOpportunityDetails`:

- Identidad, categoría, score, prioridad y versión de scoring persistidos.
- `commercial`: productos, presentaciones, marcas explícitas, ítems, cantidades, precios,
  totales, presupuesto y UNSPSC.
- `execution`: plazo, tipo de días/evento, sitio y número de entregas.
- `payment`: método, porcentaje y plazo con evento de inicio.
- `requirements`: garantía/póliza y sujeto, RUP, experiencia y observaciones operativas.
- `quality`: candidatos en conflicto, campos ausentes, conteos y notas previas de discovery.
- `commercial_profile`: coincidencia literal de producto, presupuesto, días de ejecución/pago
  y estados de requisitos. No calcula conveniencia de participar.
- `evidence`: IDs de canónicos/hechos por campo, confianza, corroboración y procedencia/confianza
  por campo del ítem. No incluye texto documental por defecto.

Cada valor mantiene ID canónico, estado y confianza. Los candidatos conflictivos se exponen
sin seleccionar ganador y activan revisión. Un ítem puede conservar campos concordantes y
campos disputados NULL. `evidence(reference, canonical_id)` recupera el texto, versión documental,
fragmentos, localizadores y reglas originales, limitado al proceso solicitado.

Los requisitos ausentes son `None` en las secciones y `unknown` en el perfil. No equivalen a
`not_required` o false. La póliza no requerida no cancela garantía de cumplimiento, reposición
ni certificado del producto. Los UUID canónicos repetidos se muestran una sola vez; Eureka
no vuelve a consolidar valores por similitud.

`product_match` compara nombres confirmados con términos del catálogo configurado, tolerando
case/acentos y el alias limitado jugos → jugo. True significa coincidencia literal; false significa
productos disponibles sin coincidencia literal; `None` indica información insuficiente. False
no demuestra irrelevancia, y true no demuestra viabilidad. `product_match_basis` y
`catalog_version` describen el criterio. Los días del perfil deben interpretarse junto al tipo
calendar/business y evento del detalle: no se calculan fechas ni costos financieros.

## Estado y scoring

`ConsolidationService.read_state` devuelve una lectura progresiva:

| Estado | Condición |
| --- | --- |
| not_extracted | Sin run textual reutilizable para versiones documentales vigentes |
| extracted | Extracción disponible, sin hechos estructurados vigentes |
| structured | Hechos estructurados vigentes, sin snapshot canónico para sus entradas/regla vigentes |
| consolidated | Snapshot vigente sin conflictos |
| conflict | Snapshot vigente con conflictos |

La lectura detecta esquema/tablas ausentes en entornos de fases anteriores, sin crearlos. Un
proceso sin portafolio permite leer identidad/inventario vacío; sync/download mantienen el
rechazo de adquisiciones sin portafolio. No se presenta un snapshot obsoleto como actual.
Consolidated no significa campos completos; extracted puede incluir PDF sin texto/requires_ocr.
Los fallos reales de infraestructura no se ocultan como ausencia documental.

El detalle no llama `evaluate`, extracción ni consolidación. Si no hay oportunidad persistida,
devuelve identidad disponible y `opportunity_id/score/priority=None`, sin evaluar implícitamente.
Las notas previas de discovery permanecen visibles y mantienen su revisión pendiente.

El scoring acepta opcionalmente `CanonicalFactsSource` y ofrece `canonical_context(reference)`
para lectura explícita. `evaluate` no usa ese contexto automáticamente: conserva pesos, reglas
y resultados. `build_eureka_service` conserva por defecto su configuración anterior sin lector
canónico. Las propiedades documentales se exponen como atributos, sin puntos nuevos.

## CLI y serialización

Desde `backend/`:

```bash
uv run python -m public_procurement.entrypoints.cli show-eureka-details --process CO1.REQ.11172521
uv run python -m public_procurement.entrypoints.cli show-eureka-details --process CO1.REQ.11172521 --json
uv run python -m public_procurement.entrypoints.cli show-eureka-details --process CO1.REQ.11172521 --json --with-evidence
```

La salida normal resume valores/calidad; JSON incluye IDs y referencias por campo. La opción
`--with-evidence` expande textos/localizadores bajo demanda, consultando cada ID canónico una vez.
La evidencia puede contener datos personales: una UI futura necesitará políticas de exposición.

El DTO es serializable con `dataclasses.asdict` y codificadores JSON de API; UUID se serializa
como string. **No había API de Eureka**: esta fase entrega CLI y servicio interno, sin crear
endpoint HTTP ni alterar contratos del frontend/API beta.

## Validación real de Covarachía

La CLI JSON con evidencias se ejecutó con PostgreSQL `transaction_read_only=on`. El registro
completo de la oportunidad fue idéntico antes/después, incluyendo configuración y fecha de
evaluación. Score **65 → 65**; prioridad **high → high (alta)**.

- Estado consolidated; categoría persistida packaged_food.
- 18 canónicos consumidos y 39 hechos originales recuperables.
- Jugo Hit 200 ml; Chocorramo tradicional 65 g.
- Ítem: 400 PACK, unitario 5200 COP, total 2080000 COP.
- Presupuesto 2080000 COP; UNSPSC 50192703.
- Ejecución 5 días calendario desde firma; entrega en I.E. San Luis Beltrán, Covarachía,
  con dirección y texto original consultables.
- Pago único, 100%, 30 días calendario desde aprobación de factura.
- Póliza not_required; reposición/certificado conservados como observaciones.
- RUP y experiencia unknown; DELIVERY_COUNT ausente. Conflictos documentales: 0.

`review_required=true` proviene de una nota **previa de discovery**, sin conflicto documental:
“Vigencia por confirmar: no hay fecha de cierre de ofertas en la metadata persistida.”
El enriquecimiento no resuelve esa revisión ni afirma que la oferta siga abierta.

No se ejecutaron escritores ni migraciones contra desarrollo. Los tests de persistencia usan
SQLite en memoria. La consulta funcional consumió exclusivamente registros ya existentes.

## Limitaciones y archivos

Sin UI, API HTTP de Eureka, cache, IA, agentes ni servicios externos. El perfil no reconoce
sinónimos, interpreta condiciones jurídicas, calcula rentabilidad/vencimientos ni recomienda
participar. Hereda las limitaciones de extracción/consolidación. La lectura es derivada por
consulta; para volúmenes mayores faltan paginación y optimización de expansión de evidencias.

Nuevos:

- `backend/src/public_procurement/eureka/domain/details.py`
- `backend/src/public_procurement/eureka/adapters/extraction.py`
- `backend/src/public_procurement/eureka/DETAILS.md`
- `backend/tests/unit/eureka/test_details.py`
- `backend/tests/unit/eureka/test_details_adapter.py`
- `backend/tests/unit/entrypoints/test_eureka_details_cli.py`

Modificados:

- `backend/src/public_procurement/eureka/ports.py`
- `backend/src/public_procurement/eureka/repositories.py`
- `backend/src/public_procurement/eureka/services.py`
- `backend/src/public_procurement/eureka/README.md`
- `backend/src/public_procurement/extraction/domain/canonical.py`
- `backend/src/public_procurement/extraction/repositories.py`
- `backend/src/public_procurement/extraction/services.py`
- `backend/src/public_procurement/documents/services.py`
- `backend/src/public_procurement/entrypoints/cli/__main__.py`
- `backend/tests/unit/extraction/test_canonical_service.py`
- `backend/tests/unit/documents/test_services.py`
- `README.md`
