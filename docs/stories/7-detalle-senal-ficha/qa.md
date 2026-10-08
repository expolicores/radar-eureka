# Casos de Prueba — Historia #7: Detalle de la señal y ficha de la compra

**Historia:** [historia.md](./historia.md) | **Autor:** Juan Camilo | **Fecha:** 2026-10-07

## Alcance de las Pruebas

**Se prueba:** detalle de señal (B1, B2, confianza, evidencia pendiente), 404, ficha con resultado por ítem, gráfico con alternativa en tabla, lenguaje.
**Queda fuera:** visor de documentos, calificación, casos.

## Precondiciones y Datos Base

| Dato | Valor | Nota |
| ---- | ----- | ---- |
| Base | Seed cargado y recalculado | Integración |
| Señal | `SG-2026-0142` | Compra `CO1.PCCNTR.0000142` |

## Matriz de Cobertura

| Criterio / Regla | Casos |
| ---------------- | ----- |
| Escenario 1: detalle | QA-01, QA-05 |
| Escenario 2: tabla de comparables | QA-06 |
| Escenario 3: 404 y B2 no disponible | QA-02, QA-07 |
| Escenario 4: ficha | QA-03, QA-08 |
| Escenario 5: evidencia | QA-05 |
| Regla: lenguaje | QA-04, QA-09 |

---

## Casos de Prueba

### QA-01: El detalle reproduce la comparación vigente

- **Tipo:** Integración · **Prioridad:** Alta
- **Resultado esperado:** `SG-2026-0142` con compra, entidad, ítem ×8, Q1 ≤ mediana ≤ Q3 < umbral < 4.950.000, `comparable_count` igual al número de comparables listados (cada uno con fuente, referencia, fecha y precio), Benchmark 2 con estado y observaciones con método `simulated`, confianza con penalizaciones que suman 100 − puntaje, y `config_version_id`.

### QA-02: Código inexistente responde 404

- **Tipo:** Negativo · **Prioridad:** Alta
- **Resultado esperado:** 404 *problem details* «Señal no encontrada».

### QA-03: La ficha incluye el resultado vigente de cada ítem

- **Tipo:** Integración · **Prioridad:** Alta
- **Resultado esperado:** en `CO1.PCCNTR.0000142`, el televisor tiene resultado `signal` con código `SG-2026-0142` y el soporte (excluido) no tiene resultado.

### QA-04: Las respuestas no usan términos acusatorios

- **Tipo:** Negativo · **Prioridad:** Alta
- **Resultado esperado:** ni el detalle ni la ficha contienen los términos prohibidos.

### QA-05: La pantalla del detalle muestra benchmarks, confianza y evidencia pendiente

- **Tipo:** Positivo · **Prioridad:** Alta
- **Resultado esperado:** título con el ítem ×8, enlace a la compra, «Benchmark 1», estadísticos con formato COP, «Benchmark 2», penalizaciones, aviso de no conclusión y el texto de evidencia documental pendiente.

### QA-06: «Ver como tabla» muestra los comparables con enlace a su ficha

- **Tipo:** Positivo · **Prioridad:** Media
- **Resultado esperado:** tras pulsar, una fila por comparable y el enlace a `/compras/<id>`.

### QA-07: Señal no encontrada y Benchmark 2 no disponible en pantalla

- **Tipo:** Borde · **Prioridad:** Media
- **Resultado esperado:** «Señal no encontrada» con enlace a la lista; «no disponible / evidencia insuficiente» cuando no hay observaciones.

### QA-08: La ficha muestra datos clave, ítems y resultado

- **Tipo:** Positivo · **Prioridad:** Alta
- **Resultado esperado:** valor con la nota de dato de referencia, ítems con clasificación y «⚑ Señal SG-2026-0142» enlazada.

### QA-09: Las pantallas no usan términos acusatorios

- **Tipo:** Negativo · **Prioridad:** Alta
- **Resultado esperado:** ninguno en el texto renderizado del detalle y la ficha.

---

**Total de casos:** 9
