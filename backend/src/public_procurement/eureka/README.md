# Eureka — Fase 3A

El read model documental de la Fase 3B-2.3 se describe en [DETAILS.md](DETAILS.md).
Permite consultar canónicos y evidencia sin modificar el scoring de discovery.

Descubrimiento y priorización comercial sobre **metadata SECOP ya persistida**. No consulta
Socrata, no descarga documentos ni abre PDF/DOCX/XLSX. No incluye IA, OCR, agentes, scheduler
ni frontend. Las compras simuladas, los benchmarks, las señales y los casos son independientes.

## Fronteras

`services.py` es la puerta de entrada. El adaptador `adapters/ingestion.py` usa únicamente
`ingestion.services` para leer procesos por UUID, identificador SECOP o departamento. La
consulta se pagina por UUID interno (200 filas por defecto) y no filtra por cuantía ni UNSPSC.
Los consumidores no acceden directamente al catálogo, dominio ni tablas de Eureka.

`ports.py` define `ProcessMetadataSource`, sustituible por dobles en pruebas. El dominio
recibe `ProcessFacts` y configuración explícita y devuelve una evaluación determinística.
Solo `repositories.py` conoce SQLAlchemy y el esquema `eureka`.

## Configuración versionada

`config.py` separa tres conceptos:

1. **Catálogo comercial:** siete categorías, incluyendo refrigerios preparados condicionales;
   17 códigos prioritarios y 23 candidatos, con términos de producto por categoría.
2. **Reglas de descubrimiento:** términos de objetos, necesidades y entidades, exclusiones,
   geografía preferida, pesos y umbrales de prioridad.
3. **Perfil de ejecución:** intervalo atractivo de COP 2–8 millones, revisión de cuantías
   desde COP 15 millones, indicios logísticos y barreras configurables.

Las configuraciones son dataclasses tipadas e inmutables, construidas con `DEFAULT_CONFIG`.
Para ajustar reglas se crea una configuración nueva y se cambia `version`; el servicio acepta
`config=` y las pruebas usan esa misma interfaz. La CLI utiliza `eureka-discovery-v1`.
Se persiste también un snapshot JSON de la configuración empleada.

## Descubrimiento y score

El interés combina con **OR** productos, UNSPSC, objetos/necesidades y contexto de entidad.
Cuantía o ubicación por sí solas no crean interés. Los textos se normalizan sin tildes y sin
distinción de mayúsculas, con límites de palabra; no hay stemming ni búsqueda semántica.
Los códigos se comparan exactamente, incluyendo códigos publicados con prefijo `V1.`.
No se supone que un código de familia coincida con todos sus descendientes.

| Grupo | Puntos máximos por evaluación |
| --- | --- |
| Producto específico | +30 |
| UNSPSC prioritario | +20 |
| UNSPSC candidato, si no hubo prioritario | +10 |
| Objeto amplio o necesidad institucional | +15 |
| Contexto de entidad | +10 |
| Cuantía atractiva | +10 |
| Indicio explícito de logística simple | +10 |

Cada grupo puntúa una sola vez aunque existan múltiples coincidencias o categorías. El score
es la suma de razones menos penalizaciones, con piso cero. Prioridad alta desde 60 puntos,
media desde 35 y baja por debajo. **No es probabilidad, confianza estadística ni elegibilidad.**

La cuantía alta resta inicialmente 10 puntos y mantiene el proceso en revisión. Barreras
como múltiples entregas, RUP, experiencia, instalación o logística compleja restan puntos;
no excluyen por sí solas. Fuera de Boyacá/Casanare se restan 5 puntos para revisar logística,
sin descarte automático ni cálculo de proximidad a Villa de Leyva.

Las exclusiones se aplican a objetos claramente de obra, consultoría especializada,
interventoría, servicios profesionales, servicios de apoyo a la gestión sin bienes o
software a medida. Un UNSPSC favorable no neutraliza una exclusión clara. Un objeto mixto
con evidencia textual de suministros queda para revisión con penalización. Refrigerios
preparados requieren confirmar preparación, inocuidad y capacidad de entrega.

## Vigencia y estados

- `no_match`: sin señales de interés; inactivo.
- `excluded`: exclusión comercial clara; inactivo.
- `closed`: estado/fase publicado cerrado, vencido, cancelado, adjudicado o equivalente; inactivo.
- `review`: candidato con condiciones o información pendiente; activo en el radar.
- `candidate`: reservado para candidatos sin condiciones pendientes.

**Limitación de la ingesta actual:** no conserva fecha de cierre de ofertas. No se infiere
vencimiento a partir de publicación o antigüedad. Los candidatos no terminales llevan la
nota «Vigencia por confirmar». Por eso los candidatos de esta primera versión quedan en
`review`; `active` expresa interés para revisar, no confirmación de plazo abierto.
Para reconocer vencimientos sin estado terminal hará falta ampliar esa metadata en una
fase posterior y validar la semántica del campo de la fuente.

## Persistencia e idempotencia

`eureka.opportunity` mantiene un resultado vigente por `process_id`, protegido con UNIQUE
y upsert atómico. Tiene FK declarativa a `ingestion.secop_process.id`, conforme al alcance
de esta fase; no implica consultas directas a tablas ajenas desde Eureka.

Se guardan score, prioridad, estado, active, categorías, códigos, términos, contexto,
razones con puntos, penalizaciones, notas, rule_version, snapshot de configuración y
timestamps. Repetir conserva UUID y `discovered_at`, y refresca evaluación y `evaluated_at`.
Cambios de datos o reglas se aplican al reevaluar. Se guardan también resultados inactivos
sin eliminar procesos de la base compartida. No se conserva todavía un historial completo
de evaluaciones anteriores: la fila representa el resultado vigente.

Los lotes confirman una transacción por proceso, después de leer su metadata. Un fallo puede
dejar parte del lote evaluado; reejecutarlo es seguro e idempotente. No existe snapshot global
de un lote ni recálculo automático. No se escribe durante `--dry-run`.

## CLI

Aplicar la migración aditiva `0008_eureka_discovery` antes de persistir oportunidades.
Desde `backend/`:

```bash
uv run python -m public_procurement.entrypoints.cli evaluate-eureka --process CO1.REQ.11172521 --dry-run
uv run python -m public_procurement.entrypoints.cli evaluate-eureka --process CO1.REQ.11172521
uv run python -m public_procurement.entrypoints.cli evaluate-eureka --department Boyacá --dry-run
uv run python -m public_procurement.entrypoints.cli evaluate-eureka --department Casanare
```

Se requiere exactamente `--process` (UUID o SECOP) o `--department`. Los departamentos se
comparan sin tildes ni mayúsculas. La salida muestra score, prioridad, estado, categorías,
señales, razones, penalizaciones y notas. Un departamento sin registros devuelve cero.
Un proceso inexistente devuelve error. Dry-run no requiere que exista la tabla Eureka.

## Ejemplo verificado: Covarachía

El proceso persistido `CO1.REQ.11172521`, portafolio `CO1.BDOS.10985405`, fue evaluado sin
persistir y obtuvo **65 puntos**, prioridad alta, categoría alimentos empacados y refrigerios:

- +30 producto: refrigerios.
- +15 necesidades: día del colegio, comunidad educativa, actividades culturales, celebración.
- +10 entidad: institución educativa.
- +10 cuantía en zona atractiva.

No hubo coincidencia con los UNSPSC del catálogo. Esto demuestra el descubrimiento por OR.
Quedó activo **por revisar**, con vigencia por confirmar. No se consultaron documentos ni
se reevaluó la elegibilidad jurídica/comercial del proceso.

## Validación y pendientes

Pruebas unitarias de los 40 códigos, palabras, OR, exclusiones, penalizaciones, Unicode,
categorías múltiples, cierre publicado, idempotencia, actualización, dry-run, consulta interna
y migración. Persistencia comprobada en SQLite efímero; SQL PostgreSQL/FK generado offline.
No se ejecutan pruebas destructivas contra desarrollo.

Pendientes: fecha de cierre fiable, calibración con oportunidades reales, crédito de proveedores,
logística por territorio, revisión de requisitos documentales y política de historial. Las
negaciones se reconocen solo en patrones simples; los textos ambiguos requieren revisión humana.
