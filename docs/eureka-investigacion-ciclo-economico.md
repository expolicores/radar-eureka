# Reconstrucción económica del ciclo documental

Ejercicio offline del 03/11/2026 sobre los **12 procesos con televisores confirmados**
en la [muestra previa de 30 días](eureka-investigacion-secop-30dias.md).
No se repitió discovery, adquisición, extracción nativa ni OCR: se reutilizaron los
fragmentos reales previamente extraídos, incluidos los obtenidos con Tesseract.
No se invocaron agentes, LECTOR, LLM, Web Search, CDP, mercado privado ni TVEC/TCVE.

## Alcance y contratos

`investigation/economic_cycle.py` reconstruye una proyección local, versionada como
`economic-cycle-v1`, sin escrituras en DB ni migraciones. Cada proceso conserva:

- Cobertura documental por etapa, selección, extracción, páginas y cobertura parcial.
- Registros por producto: descripción, clasificación, marca, modelo, especificaciones,
  cantidad/unidad y las ocho columnas económicas de presupuesto/oferta/adjudicación/contrato.
- Alternativas por campo, oferente, documento/página, fragmento/versión/hash, método,
  confianza, regla y origen explícito/calculado. Cuando la fuente es un fact previo,
  se conservan sus IDs y los canonicals asociados cuando están disponibles.
- Relaciones determinísticas y sus motivos. Un registro sin asociación segura
  permanece separado: el número de registros no representa unidades compradas ni
  necesariamente productos únicos.
- Conflictos, revisión manual y valores globales del contrato separados de los ítems.

### Auditoría de canonicals existentes

Antes del cambio se revisó `extraction/domain/canonical.py`: ya existen
`PRODUCT`, `PURCHASE_ITEM`, `QUANTITY`, `UNIT_PRICE_COP`, `TOTAL_COP`, `BUDGET_COP`,
`UNSPSC`, además de los conceptos comerciales/jurídicos. No había conceptos globales
por etapa para marca/modelo, oferente o proveedor adjudicado.

| Campo investigativo | Concepto reutilizado / alcance |
|---|---|
| ITEM | PURCHASE_ITEM |
| QUANTITY | QUANTITY |
| BUDGET_TOTAL | BUDGET_COP, con alcance de ítem |
| OFFER_TOTAL, AWARDED_TOTAL, CONTRACT_TOTAL | TOTAL_COP, calificado por etapa e ítem |
| Los cuatro precios unitarios | UNIT_PRICE_COP, calificado por etapa e ítem |
| Marca, modelo, unidad y proveedores | Atributos de la proyección investigativa |

No se alteraron `REQUIRED_TYPES`, los tipos persistidos ni las reglas de consolidación
compartidas. La nueva `canonical_projection` usa claves de ítem/campo/documento-oferta;
no mezcla un presupuesto con un precio contractual bajo un canonical global. Conserva
los facts/canonicals existentes; no los vuelve a insertar.

## Reglas determinísticas

Las etapas separan estudios previos/mercado, invitación, especificación técnica, oferta,
evaluación, adjudicación/aceptación, contrato, modificación, otro y desconocido.
La clasificación prioriza nombres específicos; el texto solo aporta encabezados
inequívocos. Una recomendación en evaluación **no equivale a adjudicación**.

El cruce requiere descripción normalizada específica, marca/modelo explícitos,
especificaciones compatibles, o posición de ítem con un atributo específico compartido.
Se normalizan espacios y formatos decimales; `3` y `3,00` no son conflicto.
Tamaño, cantidad o taxonomía genérica por sí solos no fuerzan asociación. Las asociaciones
se comprueban contra todos los miembros para evitar cadenas transitivas incompatibles.

Solo se divide un **total de ítem** por su cantidad documentada. Se conservan ambas
entradas y la fórmula. Se permite complementar páginas/documentos del mismo producto
y etapa cuando la asociación es inequívoca; una cantidad solicitada en presupuesto no
prueba la cantidad finalmente contratada. Una oferta tampoco toma la cantidad de otro oferente.

Los importes globales de Socrata nunca se distribuyen entre productos. Una línea de
SECOP de cantidad 1 como «TELEVISORES FI», sin producto suficientemente discriminado,
permanece sin precio unitario de producto. Los cuadros con columnas «estimado» y
«precio unitario» se separan explícitamente y verifican las dos multiplicaciones.

La selección de precio de compra prefiere contrato, adjudicación y oferta aceptada.
Contrato requiere referencia del proceso/contrato en **ese documento** y metadata de firma.
Aceptación de oferta requiere referencia explícita de oferta, proveedor, producto y
cantidad concordantes, con evidencia de aceptación; no basta coincidir el monto global.
Cobertura parcial, mezcla de bienes o discrepancia relevante impiden promover el valor.

Un conflicto presupuestal previo no borra un precio contractual posterior explícito:
se conservan ambos, se marca revisión manual y el comparador automático no usa ese
registro conflictivo. Diferencias contrato/adjudicación no se resuelven silenciosamente.

## Resultado de los 12 procesos

Se reconstruyeron **35 registros, incluidos parciales**. Hay información económica por
ítem en **6/12 procesos (50%)** y precios contractuales específicos recuperados en
**2/12 (16,67%)**. Solo uno de esos dos queda sin conflicto presupuestal previo.
Por registros: 9/35 tienen alguna columna económica y 2/35 (5,71%) un precio de compra
recuperado. Estos denominadores no miden cobertura nacional ni extracción perfecta.

| Proceso | Resultado económico por producto |
|---|---|
| C29-2026, Pío XI | Ofertas unitarias $2.002.280 y $2.071.000, cantidad 5. La primera fila mezcla LG/Samsung: ambas marcas se conservan como conflicto. Sin precio adjudicado verificable; no se elige ganador por coincidir el total del lote. |
| RE-00102026, La Gloria | Oferta TV 65″: $3.970.000, cantidad 1. Sin aceptación vinculada verificable. |
| MC-070-2026, Universidad Atlántico | Ítem contractual de TV 58″ y cantidad; contrato global incluye computadores y accesorios. Unitario contractual desconocido. |
| IEGM-012-2026, Gabriela Mistral | Línea genérica «TELEVISORES FI», cantidad 1 de alcance no desagregado. No es prueba de un único TV; no se asignan sus importes globales al producto. |
| CRE004-CENE2026, Nueva Era | Presupuesto TV 55″, cantidad 2, $2.610.000 unitario. Sin precio contractual verificado. |
| 0971-2026, ESE Carmen | TV 32″ más cableado/instalación; total global no distribuido. |
| MC-VLL-CNPB-0022-2026, SENA Valle | **Contractual: $2.670.920**, cantidad 3; total de ítem $8.012.760. Conflicto entre referencias presupuestales previas conservado; revisión manual. |
| CHQ-SAMC-013-2026, Chiquinquirá | TV 58″ en alcance técnico; sin unitario adjudicado/contractual reconstruido. |
| SPD-MC-048-2026, Putumayo | TV Samsung 75″ Mini LED + pedestal; no se imputan precios de ejemplos de experiencia previa. |
| MC-15-2026, Subachoque | Pantalla táctil/interactiva; precios OCR y cobertura insuficientes para precio de compra. No se equipara automáticamente a TV convencional. |
| PN MEMAZ MIC 045 2026, Manizales | **Contractual: $5.850.000**, cantidad 3; total de ítem $17.550.000. Estimado separado: $8.500.000, total $25.500.000. |
| INEM-SI-01-2026, Leticia | Ofertas: TV 40″ $2.520.000 (2); TV 55″ $3.500.000 (4); TV 65″ $5.050.000 (1). Aceptación no verificada, no precios de compra. |

Provenance de los dos precios recuperados:

- SENA: `CO1_PCCNTR_10114833_Firmado.pdf`, página 3.
- Manizales: `CO1_PCCNTR_10133299_Firmado.pdf`, página 3.

Los importes recuperados son **explícitos**. En esta muestra no se necesitó publicar un
precio calculado nuevo. La derivación está implementada y probada con el caso conceptual
Xiaomi: 4.804.305 / 5 = 960.861, con total/cantidad y comprobación del unitario explícito.
No se hardcodeó ese proceso ni se promovió una recomendación de evaluación a adjudicación.

El nuevo comparador conserva **46 pares parciales de registros** y ningún par igual o
altamente comparable habilitado para comparar precios. Los dos contratos recuperados
corresponden a TV 65″ y TV profesional 75″: no se comparan como equivalentes.
**0 comparaciones monetarias sustentadas y 0 señales.**

## Artefactos y UI

En `backend/.local/investigation-tv-30d-20261103/`:

- `economic-cycle.json`: resultado completo de los 12, provenance por campo y pares.
- `economic-cycle.csv`: columnas económicas y conflictos por registro.
- `economic-cycle.md`: cobertura por etapa y evidencia de todas las columnas.
- `research-cycle-report.json`: proyección que consume la UI, sin borrar el informe anterior.

Explorar compras incorpora el ciclo en el detalle existente. Señales usa las comparaciones
posteriores a la reconstrucción. No se rediseñó la aplicación ni se cambiaron Radar,
scoring, alertas o reglas comerciales.

Repetición **offline**, sin DB ni red (publicar solo sustituye el informe local de la UI):

```powershell
cd backend
.\.venv\Scripts\python.exe scripts/eureka_investigation_cycle.py `
  --sample-directory .local/investigation-tv-30d-20261103 `
  --publish
```

Las limitaciones originales de extracción/cobertura siguen vigentes. Un campo desconocido
significa que estas reglas no lo reconstruyeron con suficiente evidencia; no prueba que
el dato no exista en los documentos. Los casos irresolubles siguen para revisión manual.

## Validación

- 40 tests específicos: clasificación, ejemplo Xiaomi, cálculos con ambas evidencias,
  división prohibida de montos globales, asociación ambigua, conflictos de cantidad/modelo,
  ofertas alternativas, aceptación verificable y prioridad contractual, cobertura parcial,
  separación estimado/actual y validación de referencias por versión documental.
  Se incluyen filas OCR con nombres de ítems unidos y marcas incompatibles en la misma fila.
- Suite afectada de investigación, extracción y documentos; Ruff/format, Mypy y los
  13 contratos de importación correctos.
- 150 tests frontend correctos, TypeScript/build y ESLint correctos. Una prueba de
  revisión humana ajena al módulo excedió su espera en la primera ejecución concurrente;
  pasó aislada y la suite completa pasó con dos workers, sin alterar esa prueba ni su código.
- Smoke real en Edge de los detalles de Manizales/SENA y Señales; sin errores JavaScript.
