# Casos de Prueba — Historia #4: Pantalla Explorar compras

**Historia:** [historia.md](./historia.md) | **Autor:** Juan Camilo | **Fecha:** 2026-10-07

## Alcance de las Pruebas

**Se prueba:** render del listado con formatos, filtros y búsqueda contra la API, estados cargando/vacío/error, paginación, filtros en la URL y navegación del marco.
**Queda fuera:** ficha, señales, login.

## Precondiciones y Datos Base

| Dato | Valor | Nota |
| ---- | ----- | ---- |
| API simulada (tests) | Respuesta con `CO1.PCCNTR.0000142` · $39.600.000 · 2026-08-14 · `pending_comparison`; total 1.280 | Dobles de `fetch` en Vitest |
| Opciones de filtro | fuentes `secop_ii`/`tvec`; departamento «Valle del Cauca»; modalidad «Mínima cuantía»; corte `2026-10-06T08:10:00Z` | |
| API real (manual) | Backend con la carga seed | Verificación en navegador |

## Matriz de Cobertura

| Criterio / Regla | Casos |
| ---------------- | ----- |
| Escenario 1: listado y formatos | QA-01, QA-02 |
| Escenario 2: filtros y URL | QA-03, QA-04 |
| Escenario 3: vacío, error, cargando | QA-05, QA-06 |
| Escenario 4: paginación | QA-07 |
| Escenario 5: marco y navegación | QA-08 |
| Regla: insignias del estado | QA-02 |

---

## Casos de Prueba

### QA-01: El listado muestra compras con formatos colombianos y la fecha de corte

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 1
- **Resultado esperado:** fila con «CO1.PCCNTR.0000142», «SECOP II», «$39.600.000», «14-ago-2026»; chip «1.280 compras»; texto «Datos actualizados al 06-oct-2026 03:10».

### QA-02: Cada estado del análisis se muestra con su insignia

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Regla de insignias
- **Datos de prueba:** los 5 estados de la regla.
- **Resultado esperado:** el texto de la regla para cada estado.

### QA-03: Los filtros y la búsqueda consultan la API con los parámetros correctos y vuelven a la página 1

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 2
- **Datos de prueba:** buscar «san rafael»; Fuente «TVEC»; Valor «$20 M – $100 M»; Orden «Mayor valor».
- **Resultado esperado:** la última consulta lleva `q=san rafael`, `source=tvec`, `value_range=between_20m_100m`, `sort=value_desc`, `page=1`.

### QA-04: Los filtros quedan en la URL y se restauran al recargar

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 2
- **Pasos:** abrir `/explorar?source=tvec&page=2`.
- **Resultado esperado:** el selector Fuente muestra «TVEC» y la consulta usa `source=tvec&page=2`.

### QA-05: Sin resultados muestra el estado vacío

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** Escenario 3
- **Resultado esperado:** «No hay compras que coincidan con los filtros».

### QA-06: Un error de la API muestra el mensaje y permite reintentar

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 3
- **Pasos:** la API responde 503; pulsar «Reintentar» cuando ya responde 200.
- **Resultado esperado:** «No fue posible cargar las compras. Intenta de nuevo.»; tras reintentar, la tabla.

### QA-07: La paginación avanza y se deshabilita en los extremos

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 4
- **Resultado esperado:** «Página 1 de 52 · 1.280 compras»; «Anterior» deshabilitado en la página 1; «Siguiente» consulta `page=2`.

### QA-08: El marco navega a las secciones pendientes

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 5
- **Resultado esperado:** al pulsar «Mis casos» se ve el título y «Disponible en un próximo incremento del MVP Beta»; la opción queda activa; `/` muestra «Explorar compras».

---

**Total de casos:** 8
