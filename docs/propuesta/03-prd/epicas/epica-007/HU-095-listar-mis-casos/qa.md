# Casos de Prueba — HU-095: Listar mis casos de investigación

**Historia:** [historia.md](./historia.md) | **Autor:** Juan Camilo | **Fecha:** 2026-10-02

## Alcance de las Pruebas

Se prueba la lista "Mis casos": contenido y conteos, exclusión de casos ajenos, estado vacío, paginación, apertura de un caso, reordenamiento por actualización, error de carga, acceso sin sesión y tiempo de respuesta. Queda fuera el detalle del caso (HU-096).

## Precondiciones y Datos Base

| Dato | Valor |
| ---- | ----- |
| Analista | `ana.rojas@ejemplo.org` |
| Casos de Ana | A "Compra TV 65 Gobernación" (2 señales, 1 contrato, 1 evidencia, 3 notas; actualizado 02/10/2026 09:00), B "Equivalentes 55" (1 señal, 0 notas; actualizado 01/10/2026 18:00), T "Tunja 2025" (1 contrato, 1 nota; actualizado 30/09/2026 10:00) |
| Otro analista | `luis.mora@ejemplo.org` con 2 casos |
| Administrador | `admin.po@ejemplo.org` con 1 caso |
| Analista sin casos | `marta.diaz@ejemplo.org` |
| Analista con muchos casos | `pedro.gil@ejemplo.org` con 45 casos |

## Matriz de Cobertura

| Criterio / Regla | Casos |
| ---------------- | ----- |
| Escenario 1 / RN-02 / RN-04 / RN-06 | QA-01 |
| Escenario 2 / RN-01 | QA-02, QA-03 |
| Escenario 3 | QA-04 |
| Escenario 4 / RN-05 | QA-05, QA-06 |
| Escenario 5 | QA-07 |
| Escenario 6 / RN-03 | QA-08 |
| Escenario 7 | QA-09 |
| Escenario 8 | QA-10 |
| RN-02 (desempate) | QA-11 |
| RN-07 | QA-12 |
| RN-08 | QA-13 |

---

## Casos de Prueba

### QA-01: Lista con contenido y conteos

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 1, RN-02, RN-04, RN-06
- **Pasos:**
  1. Con la sesión de Ana, abrir "Mis casos".
- **Resultado esperado:** orden A, B, T; A muestra Señales 2, Contratos 1, Evidencias 1, Notas 3, "Actualizado 02/10/2026 09:00"; B muestra Contratos 0, Evidencias 0, Notas 0.

### QA-02: Solo casos propios

- **Tipo:** Permisos
- **Prioridad:** Alta
- **Cubre:** Escenario 2, RN-01
- **Pasos:**
  1. Con la sesión de Ana, abrir "Mis casos".
  2. Con la sesión del Administrador, abrir "Mis casos".
- **Resultado esperado:** Ana ve solo A, B, T ("de 3 casos"); el Administrador ve solo su caso.

### QA-03: Manipular la solicitud para listar casos ajenos

- **Tipo:** Permisos
- **Prioridad:** Alta
- **Cubre:** RN-01
- **Pasos:**
  1. Con la sesión de Ana, enviar la solicitud de lista agregando un parámetro de autor `luis.mora@ejemplo.org`.
- **Resultado esperado:** la respuesta contiene solo los casos de Ana.

### QA-04: Estado vacío

- **Tipo:** Estado UI
- **Prioridad:** Media
- **Cubre:** Escenario 3
- **Pasos:**
  1. Con la sesión de Marta, abrir "Mis casos" y pulsar el enlace.
- **Resultado esperado:** "Aún no tienes casos. Crea uno desde una señal o desde la ficha de un contrato."; el enlace abre la lista de señales.

### QA-05: Paginación

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** Escenario 4, RN-05
- **Datos de prueba:**

  | Página | Esperado |
  | ------ | -------- |
  | 1 | "Mostrando 1–20 de 45 casos", "Anterior" deshabilitado |
  | 2 | "Mostrando 21–40 de 45 casos" |
  | 3 | "Mostrando 41–45 de 45 casos", "Siguiente" deshabilitado |

- **Pasos:**
  1. Con la sesión de Pedro, recorrer las páginas.
- **Resultado esperado:** según la tabla, sin casos repetidos ni faltantes.

### QA-06: Página inexistente y límite exacto

- **Tipo:** Borde
- **Prioridad:** Baja
- **Cubre:** RN-05
- **Pasos:**
  1. Con la sesión de Pedro, solicitar la página 9.
  2. Con un analista que tiene exactamente 20 casos, abrir "Mis casos".
- **Resultado esperado:** (1) se muestra la página 3; (2) "Mostrando 1–20 de 20 casos" con ambos controles deshabilitados.

### QA-07: Abrir un caso desde la lista

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 5
- **Pasos:**
  1. Pulsar el título de B.
- **Resultado esperado:** se abre el detalle de B.

### QA-08: Reordenamiento tras actualizar

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 6, RN-03
- **Pasos:**
  1. Agregar una nota a T y volver a "Mis casos".
- **Resultado esperado:** orden T, A, B; T muestra Notas 2 y la nueva fecha de actualización.

### QA-09: Error al cargar

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** Escenario 7
- **Precondiciones:** error simulado en la consulta.
- **Pasos:**
  1. Abrir "Mis casos"; quitar el error y pulsar "Reintentar".
- **Resultado esperado:** "No pudimos cargar tus casos. Intenta de nuevo." con "Reintentar"; error en log; tras reintentar se muestra la lista.

### QA-10: Acceso sin sesión

- **Tipo:** Permisos
- **Prioridad:** Media
- **Cubre:** Escenario 8
- **Pasos:**
  1. Sin sesión, abrir "Mis casos" e iniciar sesión como Ana.
- **Resultado esperado:** login con "Inicia sesión para continuar."; tras el login se muestra "Mis casos" de Ana.

### QA-11: Desempate por fecha de creación

- **Tipo:** Borde
- **Prioridad:** Baja
- **Cubre:** RN-02
- **Precondiciones:** dos casos de Ana con la misma fecha de última actualización y fechas de creación 20/09 y 25/09.
- **Pasos:**
  1. Abrir "Mis casos".
- **Resultado esperado:** el creado el 25/09 aparece antes que el del 20/09.

### QA-12: Título de 120 caracteres

- **Tipo:** Estado UI
- **Prioridad:** Baja
- **Cubre:** RN-07
- **Pasos:**
  1. Ver en 1366 px y en 360 px un caso con título de 120 caracteres.
- **Resultado esperado:** el título se muestra completo con ajuste de línea; en 360 px se muestra como tarjeta con la misma información.

### QA-13: Tiempo de respuesta

- **Tipo:** Positivo
- **Prioridad:** Baja
- **Cubre:** RN-08
- **Pasos:**
  1. Medir 100 aperturas de "Mis casos" de Pedro con 20 usuarios concurrentes.
- **Resultado esperado:** p95 ≤ 3 segundos.

---

**Total de casos:** 13
