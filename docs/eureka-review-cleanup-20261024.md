# Limpieza autorizada de pertenencia a revisión — 24/10/2026

No se ejecutó discovery, una nueva corrida, documentos, OCR, scoring ni scheduler.
El cambio es de admisión/persistencia de la bandeja; las reglas comerciales no cambian.

## Resultado local

| Medida | Cantidad |
| --- | ---: |
| Pertenencias antes | 1295 |
| Eliminadas | 1191 |
| Protegidas por intervención humana | 0 |
| Pertenencias restantes | 104 |
| Con evidencia comercial | 102 |
| Identidad no reconstruible, conservadas por precaución | 2 |
| Filas canónicas reconstruibles | 93 |
| Filas visibles con filtros predeterminados | 55 |

Las 104 pertenencias incluyen representaciones históricas equivalentes; no son 104
filas canónicas. Se conservan esos registros y su provenance. El endpoint local
respondió HTTP 200, `Cache-Control: no-store`, con `total=55` tras la limpieza.

La selección se auditó antes del DELETE con listado completo de identidades,
motivos, corridas y huellas. Se revalidó bajo lock de escritura de la tabla y
se aplicó un DELETE solo por identidades explícitas, con RETURNING y validación del
conjunto eliminado. Una edición humana concurrente invalida el plan. Cualquier error
hace rollback. Reaplicar una selección ya limpiada no borra registros adicionales.

Auditoría local, fuera del código productivo:

- `backend/.local/audits/review-cleanup-20261024/selection.json`
- `backend/.local/audits/review-cleanup-20261024/selection-result.json`
- `backend/.local/audits/review-cleanup-20261024/protected-table-counts-before.json`
- `backend/.local/audits/review-cleanup-20261024/post-validation.json`

Las otras 32 tablas conservan sus cantidades. Siguen los 424 outcomes de la corrida
`2dcbbe72-c944-494e-b3ef-d50dcd3fef1e`. No se borraron alertas, corridas, hechos,
canonicals, documentos, logs ni métricas. No se requiere migración.

Ejemplos comprobados por identidad:

| Caso | Identidad | Resultado |
| --- | --- | --- |
| Sin coincidencia comercial | `secop:CO1.REQ.11257075` | Eliminado de la bandeja |
| Exclusión fuerte | `secop:CO1.REQ.11253666` | Eliminado de la bandeja |
| Deadline desconocido sin señal | `secop:CO1.REQ.11257025` | Eliminado de la bandeja |
| Metadata comercial y documentos faltantes | `secop:CO1.NTC.11105736` | Conservado |
| Hechos sospechosos | `secop:CO1.NTC.11100741` | Conservado |
| Evaluación/nota humana | Tests aislados con rating, nota, fecha y analista | Conservado incluso sin admisión automática |

## Distribución de las 55 filas visibles

| Estado del último resultado | Cantidad |
| --- | ---: |
| Deadline por verificar con señal comercial | 32 |
| Evaluado sin alerta | 13 |
| Documentos no disponibles | 4 |
| Alerta | 2 |
| Alerta previa/dedupe | 3 |
| No elegible comercialmente (CDP) | 1 |

La evaluación humana protege también notas con contenido mínimo y campos de analista.
No había intervenciones humanas en las 1295 filas reales al ejecutar la limpieza;
esa protección se comprobó con fixtures SQL y tests de concurrencia.

## Pendiente expresamente separado

El término `agua` sigue en Refrigerios y bebidas con sus términos, aliases, phrases,
exclusiones, pesos y matching originales. No se corrigió su ruido de infraestructura.
SHA-256 del catálogo sin cambios:
`f57b8850c0fe11a30a19b35dabba759195212c86c51640b0dc1caf782e7e7ec3`.
