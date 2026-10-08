# Casos de Prueba — Historia #8: Casos de investigación mínimos y notas

**Historia:** [historia.md](./historia.md) | **Autor:** Juan Camilo | **Fecha:** 2026-10-07

## Alcance de las Pruebas

**Se prueba:** crear y listar casos, guardar señales y compras como instantáneas, notas, validaciones, duplicados, privacidad por dueño, pantalla «Mis casos» y botón «Guardar en caso».
**Queda fuera:** edición o borrado de notas, autenticación.

## Precondiciones y Datos Base

| Dato | Valor | Nota |
| ---- | ----- | ---- |
| Usuario | Analista demo (dueño) y un segundo dueño de prueba | Integración |
| Señal | `SG-2026-0142` | Seed recalculado |
| Caso | «Televisores en sedes educativas — Valle» | Título del mockup |

## Matriz de Cobertura

| Criterio / Regla | Casos |
| ---------------- | ----- |
| Escenario 1: guardar y listar | QA-01, QA-02, QA-08 |
| Escenario 2: validaciones y duplicados | QA-03, QA-04 |
| Escenario 3: 404 | QA-05 |
| Escenario 4: instantáneas y notas | QA-06, QA-07 |
| Escenario 5: Mis casos | QA-08, QA-09 |

---

## Casos de Prueba

### QA-01: Guardar una señal crea su instantánea

- **Tipo:** Integración · **Prioridad:** Alta
- **Resultado esperado:** el caso tiene un elemento `signal` con código, ítem, precio 4.950.000, mediana, desviación, confianza, `analitica-v1` y fecha de guardado.

### QA-02: Guardar una compra crea su instantánea

- **Tipo:** Integración · **Prioridad:** Alta
- **Resultado esperado:** elemento `purchase` con referencia, entidad, proveedor y valor 39.600.000.

### QA-03: Datos inválidos responden 400

- **Tipo:** Negativo · **Prioridad:** Alta
- **Datos de prueba:** título vacío; título de 121 caracteres; nota vacía; nota de 5.001 caracteres; tipo de elemento desconocido.
- **Resultado esperado:** 400 *problem details* en español; nada guardado.

### QA-04: Guardar dos veces el mismo elemento responde 422

- **Tipo:** Borde · **Prioridad:** Alta
- **Resultado esperado:** 422 «Ese elemento ya está guardado en el caso»; el caso conserva un solo elemento.

### QA-05: Un caso ajeno, una señal o una compra inexistentes responden 404

- **Tipo:** Permisos · **Prioridad:** Alta
- **Resultado esperado:** 404 para el caso de otro dueño (lectura, nota y guardado) y para guardar una señal o compra inexistente.

### QA-06: La instantánea no cambia tras un recálculo

- **Tipo:** Integración · **Prioridad:** Alta
- **Resultado esperado:** después de recalcular, la instantánea conserva sus valores y su fecha.

### QA-07: Las notas se listan en orden con fecha

- **Tipo:** Positivo · **Prioridad:** Media
- **Resultado esperado:** dos notas en el orden en que se crearon, con fecha.

### QA-08: «Mis casos» lista, crea y muestra el caso

- **Tipo:** Positivo · **Prioridad:** Alta
- **Resultado esperado:** lista con contadores; al crear un caso aparece seleccionado; elementos con su instantánea y enlace; aviso de privacidad.

### QA-09: Agregar una nota desde la pantalla

- **Tipo:** Positivo · **Prioridad:** Media
- **Resultado esperado:** la nota se envía a la API y aparece; con el campo vacío no se envía.

### QA-10: «Guardar en caso» desde el detalle de la señal

- **Tipo:** Positivo · **Prioridad:** Alta
- **Resultado esperado:** al elegir un caso se envía `{kind: "signal", reference: "SG-2026-0142"}` y se confirma «Guardado en el caso…».

---

**Total de casos:** 10
