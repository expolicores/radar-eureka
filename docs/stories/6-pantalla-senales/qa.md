# Casos de Prueba — Historia #6: API y pantalla de Señales

**Historia:** [historia.md](./historia.md) | **Autor:** Juan Camilo | **Fecha:** 2026-10-07

## Alcance de las Pruebas

**Se prueba:** lista de señales vigentes con prioridad, filtros, orden y paginación; indicadores; estados de la pantalla; lenguaje no acusatorio.
**Queda fuera:** detalle de la señal, calificación y casos.

## Precondiciones y Datos Base

| Dato | Valor | Nota |
| ---- | ----- | ---- |
| Base | Seed cargado y recalculado (`analitica-v1`) | Integración |
| Señal de referencia | `SG-2026-0142` · Alcaldía Municipal de San Rafael del Valle · 8 × $4.950.000 | |
| API simulada (frontend) | Lista con `SG-2026-0142` (alta, +82,1 %) y resumen 1.280 / 42 | Vitest |

## Matriz de Cobertura

| Criterio / Regla | Casos |
| ---------------- | ----- |
| Escenario 1: lista e indicadores | QA-01, QA-02, QA-06 |
| Escenario 2: prioridad, filtros, orden | QA-03, QA-04, QA-07 |
| Escenario 3: estados | QA-08 |
| Escenario 4: lenguaje | QA-05, QA-09 |

---

## Casos de Prueba

### QA-01: La lista devuelve solo señales vigentes con los datos de la compra

- **Tipo:** Integración
- **Prioridad:** Alta
- **Resultado esperado:** `total` = señales vigentes; `SG-2026-0142` con entidad, proveedor, precio 4.950.000, mediana, desviación, emparejamiento y confianza.

### QA-02: Los indicadores cuadran con los resultados vigentes

- **Tipo:** Integración
- **Prioridad:** Alta
- **Resultado esperado:** compras analizadas = SECOP II + TVEC con televisor; señales = alta + media + baja; incompletas y sin información con los conteos de los resultados vigentes.

### QA-03: La prioridad ordena por confianza y luego por desviación

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Resultado esperado:** ninguna señal de confianza menor antecede a una mayor; dentro del mismo nivel, desviación descendente.

### QA-04: Los filtros y órdenes se aplican

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Datos de prueba:** `q=san rafael`, `department=Valle del Cauca`, `source=tvec`, `confidence=high`, `year=2026`, `sort=deviation|value|date`.
- **Resultado esperado:** todas las señales cumplen cada filtro; cada orden es monótono.

### QA-05: Las respuestas de la API no usan términos acusatorios

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Resultado esperado:** ni la lista ni el resumen contienen «sobreprecio», «corrupción», «fraude» ni «hallazgo fiscal».

### QA-06: La pantalla muestra indicadores, aviso y tabla con formatos

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Resultado esperado:** «1.280», «42», aviso «Una señal no es una conclusión», fila `SG-2026-0142` con «$4.950.000», «+82,1 %», «Equivalente», «Alta».

### QA-07: Los filtros de la pantalla consultan la API

- **Tipo:** Positivo
- **Prioridad:** Media
- **Resultado esperado:** Confianza «Alta» y orden «Desviación» → `confidence=high&sort=deviation&page=1`.

### QA-08: Estados vacío y error

- **Tipo:** Borde
- **Prioridad:** Media
- **Resultado esperado:** «No hay señales que coincidan con los filtros.»; error con «Reintentar».

### QA-09: La pantalla no usa términos acusatorios

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Resultado esperado:** el texto renderizado no contiene los términos prohibidos.

---

**Total de casos:** 9
