# Módulo `comparison`

Núcleo analítico determinístico: Benchmark 1 (compras públicas comparables), Benchmark 2 (mercado), **señal que merece revisión**, precios bajos a revisión de calidad y nivel de confianza. Es dueño del esquema PostgreSQL `comparison`.

> Una señal **no es una conclusión**: prioriza revisión humana. Nunca se usan los términos «sobreprecio», «corrupción», «fraude» ni «hallazgo fiscal».

## Reglas (configuración `analitica-v1`, `domain/config.py`)

- **Comparables:** otro ítem de televisor, mismo tamaño, resolución y panel (equivalente; «mismo modelo» si coinciden marca y modelo y hay ≥ 5), precio explícito o derivado, IVA incluido, dentro de ±6 meses (±12 si faltan). Mínimo 5.
- **Señal:** con ≥ 10 comparables y RIC/mediana ≤ 0,5, precio > Q3 + 1,5 × RIC; si no, ≥ +30 % (mismo modelo) o ≥ +50 % (equivalente) sobre la mediana. Solo desviaciones al alza.
- **Precios bajos:** < Q1 − 1,5 × RIC (o < 50 % de la mediana) → revisión de calidad, no señal.
- **Benchmark 2:** observaciones de la tienda (no terceros), sin condiciones especiales, IVA incluido, ±30 días. Referencia con ≥ 3 de ≥ 2 tiendas; si no, evidencia limitada (contra la más alta); sin observaciones, no disponible.
- **Confianza:** 100 − penalizaciones (equivalente 20, derivado 10, B2 limitado 10 / no disponible 15, < 10 comparables 10, ventana ±12 10, regla porcentual 10). Alta ≥ 75, media ≥ 50, baja < 50.
- **Estados explícitos:** sin precio, en revisión, IVA incompleto o comparables insuficientes nunca generan señal.

## Persistencia

Solo inserción con `config_version_id`: `comparison_run`, `item_comparison` (`is_current` marca la versión vigente), `item_comparable` y `item_market_observation` (vínculo con cada dato usado, FR-058/FR-065).

## Capas

| Archivo | Rol |
| ------- | --- |
| `domain/` | Hechos de entrada, estadísticos (`Decimal`), benchmarks, evaluación, confianza, código de señal |
| `repositories.py` | Tablas y consultas de resultados vigentes |
| `services.py` | `ComparisonService.recalculate()` y `ComparisonQueryService` |
