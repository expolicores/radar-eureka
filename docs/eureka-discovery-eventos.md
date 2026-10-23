# Descubrimiento controlado de suministros bajo gestión de eventos

El catálogo compartido está en `backend/config/eureka_radar.v1.json`.
La revisión `eureka-radar-v1.1` añade únicamente **80141607** en la familia
`event_supplies_discovery`, marcada `discovery_only: true`.
Total: **45 códigos únicos**, de los cuales **44 conservan su alcance comercial
anterior** y uno sirve exclusivamente para descubrimiento. No se activan prefijos.

La marca se valida en configuración: una familia de este alcance necesita códigos
y no puede aportar términos, marcas, frases ni aliases comerciales.

## Taxonomía y propuestas

Fuente primaria: [clasificador UNSPSC en español v14_0801 publicado por Colombia
Compra Eficiente](https://operaciones.colombiacompra.gov.co/sites/cce_public/files/cce_clasificador/unspsc_spanish_v14_0801.pdf),
páginas 1875–1876. Fecha de consulta: 22/10/2026. Es la versión de la fuente citada;
no se presume que represente revisiones posteriores de UNSPSC.

80141607 es un producto (ocho dígitos), no una clase con subramas inferiores.
Su clase es 80141600. Los siguientes son hermanos o agregaciones, no descendientes
de 80141607. La pertinencia comercial y el riesgo son una evaluación para Eureka,
no una afirmación de la taxonomía sobre el contenido de cada contratación.

| Código | Descripción oficial | Posible contenido útil | Ruido | Decisión |
| --- | --- | --- | --- | --- |
| 80141607 | Gestión de eventos | El caso Guateque reporta bienes dentro del evento | Alto: también organización sin suministros | **Incluir ahora**, solo discovery |
| 80141605 | Mercancía promocional | Distintivos, obsequios, artículos impresos | Medio: puede incluir campañas ajenas al alcance | Observar; primera alternativa a medir |
| 80141611 | Servicios de personalización de obsequios o productos | Balones, camisetas y bolsas personalizadas | Medio: puede ser solo servicio sobre bienes del cliente | Observar |
| 80141616 | Materiales en puntos de venta, excluido el material impreso | Artículos promocionales físicos | Medio/alto: exhibidores e instalación especializada | Observar |
| 80141626 | Servicio de gestión de programas promocionales | Kits y materiales asociados | Alto: gestión de campañas sin suministro | Observar |
| 80141630 | Servicio de comercialización directa de materiales impresos | Impresos y papelería | Alto: distribución comercial, no necesariamente compra de impresos | Observar |
| 80141601 | Servicios de promoción de ventas | Posibles artículos asociados a promoción | Alto: servicio puro | No incluir |
| 80141602 | Servicios de relaciones públicas | Posibles materiales accesorios | Alto: asesoría y servicios profesionales | No incluir |
| 80141603 | Telemercadeo | Sin relación directa con suministro | Alto | No incluir |
| 80141609 | Patrocinio de eventos o de celebridades | No garantiza adquisición de bienes | Alto: patrocinio/talento | No incluir |
| 80141600 | Actividades de ventas y promoción de negocios | Agrega los productos anteriores | Muy alto; amplía indiscriminadamente | No incluir |

Solo el primer código se incorpora. Los de observación requieren casos verificables
y autorización antes de ampliar el catálogo. Tampoco se agregan la familia 80,
consultoría ni servicios administrativos o profesionales genéricos.

## Semántica y trazabilidad

Socrata mantiene su adquisición actual por fechas/geografía y paginación; el
catálogo se aplica en el filtro local de candidatos. No se añade un filtro remoto.
Después de los gates existentes, la coincidencia exacta UNSPSC permite entrar al
pipeline documental normal. No garantiza descubrimiento si la fuente no entrega
el proceso o faltan los metadatos exigidos por los gates actuales.

Se reutiliza la provenance persistida `candidate_matches`:

```json
{
  "category": "event_supplies_discovery",
  "method": "unspsc",
  "matched": "80141607",
  "origin": "metadata",
  "discovery_only": true
}
```

Para medir recall por UNSPSC, seleccionar coincidencias `method == "unspsc"` y
agrupar sus valores `matched`; no se duplica esta evidencia en otro contrato.
Las coincidencias quedan en el resultado del proceso y snapshot de evaluación.

El matcher comercial ignora las familias `discovery_only`. Solo el filtro de
entrada las habilita. Sin documentos, el código contextual por sí solo no habilita
una alerta provisional: queda evidencia `discovery_only_requires_commercial_evidence`
y revisión por documentos no disponibles. Otras señales comerciales o términos
de descubrimiento anteriores conservan su semántica provisional; siguen sujetas
a las exclusiones metadata-only existentes. Los productos documentales siguen
evaluándose con las reglas habituales. No cambia scoring, umbrales ni dedupe.

CDP carga el mismo catálogo, incluido el código nuevo, pero mantiene
`pending_remote_mapping`: seis búsquedas por objeto/ubicación, sin UNSPSC remoto,
sin nuevas requests y sin atribuir coincidencias UNSPSC que no observó.

## Regresión offline Guateque

`backend/tests/fixtures/eureka/mg_mic_057_2026.json` conserva los datos reportados
de MG-MIC-057-2026: objeto, ubicación, presupuesto y lista de bienes. No incluye
documentos originales, identidad SECOP ni fechas inventadas. El harness usa una
identidad y fechas sintéticas para satisfacer los gates existentes.

Los tests aíslan el UNSPSC quitando temporalmente los términos amplios del harness:
sin el código no hay candidato; con él se invoca el pipeline compartido. La
ausencia de afinidad documental no fuerza alerta. Otro caso prueba que una señal
comercial previa sí conserva su evaluación habitual y su score sin alteraciones.

Con el catálogo completo, el objeto reportado también coincide con los términos
amplios anteriores «celebración» e «integración». Por eso esta regresión demuestra
la nueva vía UNSPSC de forma aislada; no prueba que la ausencia de ese código fuera
la causa única de la omisión original ni mide recall real sin una corrida autorizada.

Una tabla **sintética**, con los 500 balones declarados y precios desconocidos,
ejercita el extractor existente y su provenance. No equivale a validar el PDF real
ni confirma automáticamente todos los bienes reportados. La validación documental
del caso real queda pendiente de una corrida autorizada; no se descargó ni ejecutó
OCR en esta iteración. No se requiere migración.
