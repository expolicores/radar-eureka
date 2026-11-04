# Investigación SECOP: auditoría y primera muestra real

Fecha del ejercicio: 3 de noviembre de 2026, America/Bogota.

Estado actual: [cierre de fase Estado vs Estado](eureka-investigacion-cierre-fase.md),
prototipo determinístico funcional con recuperación por contrato y revisión humana explícita.

Continuación disponible: [cierre económico de los 19 pares técnicos](eureka-investigacion-cierre-pares.md),
con evidencia local exclusivamente y matriz de bloqueo por ambos lados.

El tercer ejercicio está documentado en [Muestra real de 60 días](eureka-investigacion-secop-60dias.md)
y es el que muestra actualmente la UI. El segundo permanece en [Muestra real de 30 días](eureka-investigacion-secop-30dias.md).
Este documento conserva los resultados del
primer ejercicio; su mínimo anterior de cinco comparables no se aplica al nuevo comparador
investigativo por pares, que admite dos compras documentadas de entidades diferentes.

## Estado encontrado antes del ejercicio

Las vistas anteriores no consultaban fixtures desde React: consumían endpoints reales,
pero esos endpoints leían principalmente datos **demo persistidos en PostgreSQL**.
Por tanto, una tabla conectada a DB no demostraba adquisición real.

| Vista | Lectura existente | Estado encontrado |
|---|---|---|
| Explorar compras | `/api/v1/purchases`, `exploration.services` → `ingestion.services` | `ingestion.purchase`: 1.280 compras; `purchase_item`: 1.376 ítems. Fuente de demo: `SeedPublicDataSource` / `generate_seed_purchases`. No usar ese conjunto como comparables reales sin auditar cada origen. |
| Señales | `/api/v1/signals`, `comparison.services` | 1.267 comparaciones persistidas bajo `analitica-v1`. No son 1.267 señales ni prueba de comparaciones reales; derivan del conjunto anterior. |
| Mis casos | `/api/v1/cases`, `investigation.services` | 2 casos y 2 elementos persistidos, privados por dueño; instantáneas y notas en DB. La identidad de usuario continúa siendo la de demostración vigente. |
| Administración | `PendingSection` | Pantalla pendiente, sin adquisición investigativa operativa. |
| Procesos/documentos reales | `ingestion.secop_process`, `documents.*`, `extraction.*` | Existían 218 procesos antes de esta muestra y un pipeline real independiente de las compras demo. No todos pertenecen a investigación: hay resultados de Radar/CDP. |

No se borró ni recalculó el histórico demo. Las rutas antiguas quedan disponibles como
`/demo/explorar` y `/demo/senales`, explícitamente separadas de la muestra real.

## Infraestructura reutilizada

- Procesos: dataset Socrata `p6dx-8zbt`, mapper existente y `ProcessIngestionService.persist`.
- Inventario: dataset `dmgg-8hin`, `SocrataDocumentSource` por portafolio BDOS.
- Adquisición: `DocumentService`, `SecopDownloader`, almacenamiento por SHA-256.
- Texto/OCR: `ExtractionService` con configuración vigente; Tesseract, OCR máximo 20 páginas.
- Facts: `StructuredExtractionService`; canónicos: `ConsolidationService`.
- Casos: servicio existente; no se generaron casos automáticamente.

No se utilizó `ExistingRadarPipeline`: incluye evaluación comercial, scoring y reutilización
que no constituyen el criterio de admisión investigativo. Aquí se invocaron directamente
los servicios documentales compartidos. No se ejecutaron CDP, Foundry ni Web Search.

El contrato se consultó en `jbjy-vk9h`, con una lista explícita de campos públicos mínimos.
Se comprobó que **`proceso_de_compra = id_del_portafolio` BDOS**, no el REQ. El informe
solo enlaza por esa igualdad exacta. No se infieren equivalencias NTC ↔ REQ. No se
consultaron campos de documentos personales, cuentas bancarias ni representantes.

## Muestra y fechas

Ventana explícita: `fecha_de_publicacion_del >= 2026-10-17` y `< 2026-10-24`.
Es una semana alrededor de los catorce días previos al 3 de noviembre, nacional, sin
filtros de regiones, montos, frescura comercial o participabilidad de Radar.

La consulta inicial por `TELEVIS` produjo servicios de comunicación/televisión y se descartó
como muestra. La consulta por `TELEVISOR` en título u objeto devolvió **82 procesos únicos**
(`SELECT DISTINCT`, 82 < límite 1.000; no consulta truncada). No es un censo exhaustivo de
todos los televisores: otras denominaciones pueden quedar fuera. De esos procesos,
4 tenían estado publicado por Socrata `Seleccionado`; 78 conservaban `Publicado`.

Se inspeccionaron los cuatro inventarios y se eligieron las tres instituciones educativas
seleccionadas, dejando fuera de la muestra documental el proceso de cómputo de la
Universidad del Atlántico. Es una selección intencional por madurez y contexto educativo,
no una muestra estadísticamente representativa ni una búsqueda de precios extremos.

| Referencia / REQ | Entidad / municipio | Contrato comprobado | Inventario | Seleccionados | Descargados | Facts investigación | Canonicals investigación |
|---|---|---|---:|---:|---:|---:|---:|
| IEGM-012-2026 / 11261672 | I.E. Gabriela Mistral, Jamundí | CO1.PCCNTR.10118865, $4.360.000 | 15 | 12 | 9 | 14 | 6 |
| C29-2026 / 11241666 | I.E. Pío XI, La Unión (Antioquia) | CO1.PCCNTR.10096044, $12.255.073 | 26 | 18 | 14 | 1 | 1 |
| RE-00102026 / 11242744 | I. Etnoeducativa La Gloria, Manaure | CO1.PCCNTR.10116127, $29.208.500 | 32 | 13 | 11 | 15 | 8 |

Los tres contratos figuraban **En ejecución** al consultar Socrata; no se confunde ese
estado publicado con una comprobación de terminación material actual.

Adquisición documental: 03/11/2026 **12:11:30–12:18:35 Bogotá**, unos 7 min 5 s.
73 entradas de inventario conservadas; 43 seleccionadas por función documental, sin el
límite comercial de dos documentos. 34 descargas disponibles y 9 fallos `network_error`.
Se continuó tras fallos aislados; no se añadieron retries de binarios.

Las 34 versiones con texto suman 123 páginas: 32 con extracción nativa y 2 mixtas
(la misma propuesta económica publicada con dos IDs; OCR de la página 4).
Cobertura del texto de los descargados completa según el extractor; cobertura del
expediente **incompleta** por las 9 adquisiciones fallidas. Hay 25 hashes distintos:
IDs/documentos repetidos no equivalen a fuentes independientes.

## Resultado analítico, sin fabricar una señal

- Gabriela Mistral: evidencia de dos televisores 55 pulgadas QLED UHD Smart TV y soportes,
  junto a otros elementos. El valor global contratado no es un precio unitario de televisor.
- Pío XI: expediente de muebles/televisores/robótica; los documentos procesados no dejan
  un ítem de televisor con especificación y precio unitario reconstruibles con confianza.
- La Gloria: fila de propuesta económica, página 1: televisor 65 pulgadas LED UHD4K Smart TV
  con base giratoria; cantidad 1; dos celdas de $3.970.000. La aritmética concuerda,
  pero el encabezado dice `VALOR TOTAL` dos veces. Se conserva como **precio de fila
  orientativo/derivado, requiere revisión, etapa oferta**. No es precio de compra confirmado,
  no se determina IVA y no se deduce marca/modelo.

Para conservar esa fila como facts/canonicals se añadió un conjunto de reglas **opt-in**
`structured-tv-research-v1`, vía el mismo servicio compartido, y consolidación
`canonical-tv-research-v1`. Exige encabezados de tabla, televisor como sustantivo inicial,
cantidad y dos celdas monetarias con aritmética coherente; no acepta soportes como TVs.
Los localizadores conservan IDs de facts, fragmentos, documento, página, hash y texto exacto.
El rule set y consolidación por defecto de Radar no cambian.

Hay **30 facts y 15 canonicals investigativos**, una fila monetaria de televisor y
evidencia adicional de especificaciones. Solo hay una entidad con esa fila monetaria;
además, 55 QLED y 65 LED son especificaciones incompatibles. No hay pares suficientes
para una diferencia de precios defendible. **Cero señales reales publicadas.**

Se conserva un conflicto `EXECUTION_TERM` de Gabriela Mistral; la UI presenta alternativas
como evidencia conflictiva, sin convertir un candidato en condición contractual confirmada.

La nueva proyección distingue `same_model`, `highly_comparable`, `partially_comparable`
y `not_comparable`. Una observación por pares no se convierte en señal. La configuración
analítica existente mantiene mínimo 5 comparables; no se rebajó para conseguir un resultado.
El motor completo de alta de señales reales no se activó sobre evidencia insuficiente.

## UI y persistencia del prototipo

- `/explorar`: muestra real, contratos, inventario, extracción, cifras y detalle de evidencia.
- `/senales`: evidencia insuficiente explícita; jamás rellena resultados con señales demo.
- `/casos`: servicio existente, sin ampliar ni crear casos automáticamente.
- `GET /api/v1/investigation/research`: lectura sin adquisición, OCR ni escritores.

La ingesta, versiones documentales, fragmentos, facts y canonicals sí quedan en sus tablas
existentes. La proyección investigativa usa un informe local `research-proof-v1`, publicado
atómicamente en `.local/investigation/latest.json`, no una nueva tabla analítica.
Sin informe, la UI muestra ausencia de muestra; ante error, muestra error y no usa fixtures.
Es un prototipo local de primer ejercicio, no una ingesta operativa programada ni una
implementación completa de todo el observatorio. **No requirió migración.**

Artefactos originales, inventarios, consultas, contratos, auditoría de descargas y fragmentos:
`backend/.local/investigation-tv-20261103/`. No se incluyen en Git por contener evidencia.

Reproyectar offline (sin red, descargas ni OCR):

```powershell
cd backend
.\.venv\Scripts\python.exe scripts/eureka_investigation_report.py `
  --sample-directory .local/investigation-tv-20261103 `
  --publish
```

`--refresh-research-facts` reejecuta únicamente reglas investigativas y consolidación sobre
fragmentos ya persistidos, idempotentemente y con versiones propias; no ejecuta OCR.
Sin ese flag el script no escribe DB. El archivo original `sample-result.json` se conserva.

## Próximo incremento y backlog explícito

Primero recuperar, con autorización de nuevo ejercicio, los documentos fallidos y evaluar
tablas de oferta/contrato con encabezados claros en más entidades. La muestra actual no
justifica bajar umbrales, imputar precios o adjudicar características de otro ítem.

Quedan pendientes: adquisición investigativa empaquetada y selección configurables;
almacenamiento consultable de corridas investigativas en DB; cobertura de otras estructuras
de tablas; madurez documental más allá de nombres; emisión/persistencia de una señal real
cuando la evidencia y mínimo analítico lo permitan; guardado de esa nueva señal en casos.

No implementar ahora: mercado privado/Benchmark 2 (mecanismo por decidir), histórico,
TVEC/TCVE, otros tipos de señales, scheduler ni pendientes acumulados.

Durante el ejercicio no cambiaron los conteos de compras demo, comparaciones, oportunidades
Eureka, casos ni elementos de caso comprobados antes/después. Ningún servicio de scoring,
alertas, notificaciones, dedupe comercial o CDP fue invocado por el ejercicio.

Validación: pruebas unitarias afectadas de extracción/investigación correctas (171 y un
nuevo caso posterior, con un test OCR opcional omitido; hubo OCR real en la muestra),
145 tests frontend correctos; Ruff, Mypy, ESLint, TypeScript/build y 13 contratos de
importación correctos. Verificación visual en Edge de exploración, detalle y señales.
La repetición offline de reglas investigativas insertó 0 facts en los tres procesos.
