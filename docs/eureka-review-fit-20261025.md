# Pertinencia operativa de Merecen Revisión — 25/10/2026

La limpieza anterior eliminó el bypass Socrata, pero aún admitía coincidencias
incidentales: «herramientas» dentro de asistencia jurídica, celebraciones sin bienes,
servicios de mantenimiento y montos superiores al alcance operativo deseado.

La política de revisión versión 3 agrega una comprobación independiente de pertinencia:

- Tope configurable de $100.000.000 COP, inclusivo. Un monto ausente sigue ausente.
- Intención explícita de compra/suministro, bienes nominales concretos o servicios
  físicos soportados como impresión/estampado; alternativamente, bienes confirmados
  por hechos documentales con identidad de evidencia.
- Un servicio jurídico/profesional principal no se admite por mencionar herramientas
  o compras incidentalmente. La compra de papelería para una oficina jurídica sí cabe.
- Un score o warning de OCR no reemplaza la pertinencia del objeto ni el presupuesto.
- La metadata actual prevalece para este gate: una observación histórica aceptada
  no puede reactivar una fila actualmente fuera del alcance.

Configuración independiente: `backend/config/eureka_review_admission.v1.json`.
El catálogo comercial, sus términos/aliases/phrases, `agua`, scoring, thresholds,
vigencia, discovery y dedupe de alertas siguen sin modificaciones. La familia de
Refrigerios y bebidas sigue conservando `agua`. El filtro opera solo sobre revisión.

## Limpieza ejecutada

| Medida | Cantidad |
| --- | ---: |
| Pertenencias físicas antes | 104 |
| Eliminadas | 38 |
| Fuera del tope de presupuesto | 15 |
| Sin intención verificable de bienes | 22 |
| Servicio jurídico irrelevante | 1 |
| Protegidas por trabajo humano | 0 |
| Pertenencias físicas restantes | 66 |
| Filas visibles antes/después | 55 / 34 |

Las pertenencias físicas incluyen aliases e históricos no visibles; por eso eliminar
38 pertenencias no equivale a quitar 38 filas de la vista predeterminada.
El script revalidó el manifiesto bajo lock y eliminó solo identidades explícitas
de `manual_process_review`, en transacción. Una intervención humana impide su borrado.
Los registros protegidos fuera de alcance se mantienen accesibles para consulta
explícita; no vuelven a la vista predeterminada por ese solo motivo.

Se verificaron 32 tablas adicionales sin cambios en cantidades, incluidas las de
corridas, resultados, alertas, documentos, extracciones y canonicals. No se ejecutó
ninguna corrida ni adquisición remota. No se requiere migración.

## Comprobación posterior

`GET /api/eureka/revision?validity=active&page=1&page_size=100` respondió HTTP 200,
`Cache-Control: no-store`, `total=34`, política 3 y tope $100 millones.
No aparece `secop:CO1.REQ.11251030` (asistencia jurídica), ni hay montos conocidos
superiores al tope. Se conservaron compras de papelería, aseo, tecnología, ferretería,
material didáctico y suministros explícitos para eventos.

Auditoría local completa:

- `backend/.local/audits/review-cleanup-20261025/selection.json`
- `backend/.local/audits/review-cleanup-20261025/selection-result.json`
- `backend/.local/audits/review-cleanup-20261025/protected-table-counts-before.json`
- `backend/.local/audits/review-cleanup-20261025/post-validation.json`
