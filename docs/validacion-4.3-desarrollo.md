# Fase 4.3 · Migración y validación operativa en desarrollo

14 de octubre de 2026, America/Bogota. Autorización explícita del usuario para aplicar
únicamente `0013_ocr_diagnostics → 0014_transversal_search` en `public_procurement`.

## Migración y conservación

- Antes: **0013_ocr_diagnostics**. Después: **0014_transversal_search**.
- Se aplicó exclusivamente 0014 mediante Alembic. Sin reset, truncate, recreación,
  downgrade, backfill ni cambios de datos de negocio.
- Dos funciones SQL creadas: `public.search_normalize_v1(text)` y
  `public.search_values_v1(jsonb)`, ambas retornan text y son IMMUTABLE/PARALLEL SAFE.
- Cuatro índices GIN creados, ready y valid:
  `ingestion.ix_search_process_fts`, `extraction.ix_search_canonical_fts`,
  `extraction.ix_search_structured_fts`, `extraction.ix_search_fragment_fts`.
- Inventario de tablas idéntico: **ninguna tabla nueva**.
- **28 tablas históricas, 41.582 filas**, conteos y SHA-256 idénticos antes/después de
  la migración y después de los smoke tests. La única fila administrativa modificada
  es la revisión de `public.alembic_version`.
- Scoring, catálogo, reglas Radar, OCR y canonical facts no se modificaron.

Docker Desktop estaba detenido y el contenedor `compraspublicas-postgres-1` apagado.
Se iniciaron Docker y el mismo contenedor con sus volúmenes existentes. También se
iniciaron backend y frontend porque no estaban escuchando. No se recreó ningún servicio
ni volumen. Una comprobación auxiliar del auditor tuvo un error al interpretar un literal
JSON como parámetro SQL; se corrigió usando un parámetro JSON y se repitió únicamente
la verificación de lectura, sin volver a ejecutar la migración.

## Smoke tests reales HTTP

| Consulta | HTTP | Total | Tiempo HTTP ms |
|---|---:|---:|---:|
| GET /api/search | 200 | 1 | 438,590 |
| q=jugo hit | 200 | 1 | 197,214 |
| q=chocorramo | 200 | 1 | 149,283 |
| unspsc=50192703 | 200 | 1 | 64,405 |
| department=Boyacá | 200 | 1 | 79,051 |
| budget_min=2000000, budget_max=3000000 | 200 | 1 | 78,769 |
| refrigerios + Boyacá + presupuesto 2M–3M | 200 | 1 | 127,228 |
| q=inexistente_xyz_4_3 | 200 | 0 | 50,270 |

Todas las consultas positivas devuelven Covarachía `CO1.REQ.11172521`, con **score 65**.
La consulta sin resultados devuelve `items: []`, `total: 0`, paginación válida y sin error.
Evidencia por canonical_fact_id, detalle Eureka, alerts, radar-runs, compras y señales
responden 200. No se ejecutó una corrida Radar ni adquisición SECOP para estos tests.

## Golden case y evidencia

`jugo hit`: **canonical_match · exact_normalized · ranking 5**, PRODUCT vigente
`jugo hit`, presentación 200 ml. Cuatro registros de evidencia:

- `ESTUDIOS PREVIOS Firmados.pdf`, página 2: `JUGOS TETRA HIT X 200 Ml`.
- Mismo documento, páginas 3 y 15: `JUGO HIT TETRA X 200Ml`.
- `FORMATO DE PROPUESTA INSTITUCIONAL.docx`, tabla 1, fila 2, columna 2:
  `JUGO HIT TETRA X 200Ml`.

Eureka mantiene score 65 y presupuesto 2.080.000 COP. Enlace comprobado:
`/eureka/6e94cc77-9f88-4f4c-bfb8-2e832976f4c0`.

## Navegador real

Microsoft Edge headless con perfil aislado local: `/search?q=jugo%20hit` muestra el
resultado, score 65, motivos y productos. Se abrió “Ver evidencia” y se verificaron
documentos/localizadores. Se pulsó “Ver detalle Eureka” y la navegación llegó al detalle
existente de Covarachía. Se verificó la pantalla vacía para el término inexistente.
El proxy Vite `/api/search` también responde correctamente.

Aplicación local: `http://127.0.0.1:5173/search`, API: `http://127.0.0.1:8000/api/search`.

## Rendimiento y plan SQL en desarrollo

Cinco repeticiones HTTP de `jugo hit`: 140,994; 143,443; 141,914; 140,598; 161,479 ms.
**Mediana 141,914 ms**, máximo 161,479 ms. La primera consulta medida para esa búsqueda
tardó 197,214 ms; `duration_ms` del servicio fue 177,630 ms. No se calcula un p95 estable
con esta muestra pequeña; los resultados del corpus aislado están en el reporte de 4.3.

Se capturaron consultas reales del servicio y EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON).
Desarrollo contiene solo 1 proceso, 18 canonical facts, 39 structured facts y 99 fragments:
el optimizador prefirió Seq Scan para metadata, canonical y fragments, y utilizó el índice
existente `uq_structured_fact_evidence` en la rama structured. Ejemplos de ejecución SQL:
metadata 0,373 ms; fragments/versión 15,311 ms; canonical+structured 2,883 ms.
Los GIN están creados y válidos, pero no se fuerza su uso con esta cardinalidad.
Su beneficio se demostró previamente con 5.001 procesos en la base aislada.

## Evidencia local de auditoría

En `backend/.local/search43/migration014/` (no versionado): `before.json`, `after.json`,
`after_smoke.json`, `migration_report.json`, `smoke.json`, `plans.json`, `browser.json`
y captura `search.png`. Incluyen hashes por tabla, definiciones/validez de funciones e
índices, respuestas reales, tiempos, planes SQL y resultado del navegador.

**Estado final: Fase 4.3 operativa y validada en desarrollo.** Sin IA ni búsqueda semántica.
