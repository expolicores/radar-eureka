# Casos de Prueba — Historia #3: API de exploración y filtros de compras

**Historia:** [historia.md](./historia.md) | **Autor:** Juan Camilo | **Fecha:** 2026-10-07

## Alcance de las Pruebas

**Se prueba:** listado con búsqueda, filtros, orden y paginación; ficha; opciones de filtro y fecha de corte; estado del análisis; errores 400 y 404.
**Queda fuera:** pantallas, señales, autenticación.

## Precondiciones y Datos Base

| Dato | Valor | Nota |
| ---- | ----- | ---- |
| Base | Migrada y con la carga seed | Integración con PostgreSQL real |
| Compra de referencia | `CO1.PCCNTR.0000142` · Alcaldía Municipal de San Rafael del Valle · Valle del Cauca · $39.600.000 · 2026-08-14 | |
| Orden TVEC | `166000` (comparable del seed) | Referencia «Orden 166000» |

## Matriz de Cobertura

| Criterio / Regla | Casos |
| ---------------- | ----- |
| Escenario 1: listado por defecto | QA-01 |
| Escenario 2: búsqueda y filtros | QA-02, QA-03, QA-04 |
| Escenario 2: parámetros inválidos | QA-05 |
| Escenario 3: sin resultados / 404 | QA-06 |
| Escenario 4: ficha | QA-07 |
| Escenario 5: estado del análisis | QA-08 |
| Escenario 6: opciones y fecha de corte | QA-09 |

---

## Casos de Prueba

### QA-01: El listado por defecto pagina y ordena por fecha descendente

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 1
- **Pasos:** `GET /api/v1/purchases`
- **Resultado esperado:** 200; 25 compras; `total` = número de compras cargadas; fechas en orden descendente; cada compra con los campos del Escenario 1.

### QA-02: La búsqueda ignora mayúsculas y tildes y busca en entidad, proveedor, NIT, objeto y referencia

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 2
- **Datos de prueba:**

  | `q` | Debe incluir |
  | --- | ------------ |
  | `alcaldia municipal de san rafael` | `CO1.PCCNTR.0000142` |
  | `TECNOLOGÍA ANDINA` | `CO1.PCCNTR.0000142` |
  | `900.000.142-1` | `CO1.PCCNTR.0000142` |
  | `CO1.PCCNTR.0000142` | solo esa compra |
  | `166000` | `Orden 166000` |

- **Resultado esperado:** cada búsqueda incluye la compra indicada y todas las devueltas contienen el texto en alguno de los campos.

### QA-03: Los filtros se combinan

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 2
- **Datos de prueba:**

  | Filtros | Esperado |
  | ------- | -------- |
  | `source=tvec` | solo TVEC |
  | `department=Valle del Cauca&modality=Mínima cuantía` | ambos criterios en todas |
  | `value_range=lt_20m` | valor < 20.000.000 |
  | `value_range=between_20m_100m` | 20.000.000 ≤ valor ≤ 100.000.000 |
  | `signed_from=2026-01-01&signed_to=2026-06-30` | fechas en el rango |

- **Resultado esperado:** todas las compras cumplen; `total` igual al conteo de las que cumplen.

### QA-04: El orden por valor descendente funciona

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 2
- **Pasos:** `GET /api/v1/purchases?sort=value_desc`
- **Resultado esperado:** valores en orden descendente (los nulos al final).

### QA-05: Parámetros inválidos responden 400 en problem details

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 2
- **Datos de prueba:** `page_size=500`; `page=0`; `source=secop_iii`; `sort=random`.
- **Resultado esperado:** 400, `application/problem+json`, `title` «Solicitud inválida» y `detail` en español que nombra el parámetro.

### QA-06: Sin resultados y compra inexistente

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** Escenario 3
- **Datos de prueba:** `q=zzzz-no-existe`; `GET /api/v1/purchases/00000000-0000-0000-0000-000000000000`.
- **Resultado esperado:** 200 con `items=[]` y `total=0`; 404 *problem details* «Compra no encontrada».

### QA-07: La ficha trae datos, ítems y fecha de corte

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 4
- **Pasos:** obtener el `id` de `CO1.PCCNTR.0000142` desde el listado y pedir su ficha.
- **Resultado esperado:** 200; valor 39.600.000; 2 ítems (televisor incluido 8 × 4.950.000 IVA incluido, 65"; soporte excluido); `data_cutoff_at` presente.

### QA-08: El estado del análisis sigue la precedencia

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 5
- **Datos de prueba:**

  | Ítems de la compra | Estado |
  | ------------------ | ------ |
  | Solo servicio | `excluded` |
  | TV con precio en revisión | `quality_review` |
  | TV sin precio publicado | `no_unit_price` |
  | TV con IVA indeterminado | `vat_undetermined` |
  | TV con precio explícito e IVA incluido | `pending_comparison` |

- **Resultado esperado:** el estado de la tabla en cada caso.

### QA-09: Opciones de filtro y fecha de corte

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 6
- **Pasos:** `GET /api/v1/purchases/filters`
- **Resultado esperado:** fuentes `secop_ii` y `tvec`; departamentos y modalidades sin repetidos y ordenados; `data_cutoff_at` = 2026-10-06T08:10:00Z.

---

**Total de casos:** 9
