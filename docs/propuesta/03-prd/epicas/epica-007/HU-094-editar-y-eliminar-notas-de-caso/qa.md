# Casos de Prueba — HU-094: Editar y eliminar notas de un caso

**Historia:** [historia.md](./historia.md) | **Autor:** Juan Camilo | **Fecha:** 2026-10-02

## Alcance de las Pruebas

Se prueba editar notas (fechas, orden, validaciones, sin cambios, cancelar), eliminar con confirmación (incluida la última nota), el control de concurrencia entre sesiones, las fallas y la protección de casos ajenos. Queda fuera agregar notas (HU-093).

## Precondiciones y Datos Base

| Dato | Valor |
| ---- | ----- |
| Analista | `ana.rojas@ejemplo.org`, sesión activa en navegadores A y B |
| Caso C | "Compra TV 65 Gobernación", de Ana, notas N1 "Pedir el estudio de mercado." (01/10/2026 09:00) y N2 "Revisar anexo técnico." (01/10/2026 15:00) |
| Caso U | "Caso unitario", de Ana, con una sola nota N3 |
| Caso L | "Caso de Luis", de `luis.mora@ejemplo.org`, con nota NL |
| Fecha de prueba | 02/10/2026 11:00 |

## Matriz de Cobertura

| Criterio / Regla | Casos |
| ---------------- | ----- |
| Escenario 1 / RN-02 / RN-07 | QA-01 |
| Escenario 2 | QA-02 |
| Escenario 3 / RN-01 | QA-03 |
| Escenario 4 / RN-03 | QA-04 |
| Escenario 5 / RN-05 / RN-07 | QA-05 |
| Escenario 6 | QA-06 |
| Escenario 7 | QA-07 |
| Escenario 8 / RN-06 | QA-08, QA-09 |
| Escenario 9 / RN-08 | QA-10 |
| Escenario 10 | QA-11 |
| RN-04 | QA-01 |
| RN-09 | QA-12 |

---

## Casos de Prueba

### QA-01: Editar una nota

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 1, RN-02, RN-04, RN-07
- **Pasos:**
  1. Editar N1 a `Estudio de mercado solicitado el 02/10.` y guardar.
- **Resultado esperado:** "Nota actualizada."; N1 muestra el texto nuevo y "Creada el 01/10/2026 09:00 · Editada el 02/10/2026 11:00"; sigue después de N2 en la lista; el texto anterior no se conserva; la fecha de última actualización de C es 02/10/2026 11:00.

### QA-02: Cancelar edición

- **Tipo:** Estado UI
- **Prioridad:** Baja
- **Cubre:** Escenario 2
- **Pasos:**
  1. Editar N2, cambiar el texto y pulsar "Cancelar".
- **Resultado esperado:** N2 conserva texto y fechas; no aparece "Editada".

### QA-03: Edición inválida

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** Escenario 3, RN-01
- **Datos de prueba:**

  | Texto | Esperado |
  | ----- | -------- |
  | (vacío) | "Escribe el texto de la nota." |
  | solo espacios y saltos de línea | "Escribe el texto de la nota." |
  | 5.000 caracteres | guardada |
  | 5.001 caracteres | "La nota admite máximo 5.000 caracteres." |

- **Pasos:**
  1. Editar N2 con cada valor y guardar.
- **Resultado esperado:** según la tabla; en los errores N2 no cambia.

### QA-04: Guardar sin cambios

- **Tipo:** Borde
- **Prioridad:** Baja
- **Cubre:** Escenario 4, RN-03
- **Datos de prueba:**

  | Texto | Nota |
  | ----- | ---- |
  | `Revisar anexo técnico.` | idéntico |
  | `  Revisar anexo técnico.  ` | idéntico tras recorte |

- **Pasos:**
  1. Editar N2 con cada valor y guardar.
- **Resultado esperado:** la edición se cierra; no aparece "Editada"; la fecha de última actualización de C no cambia.

### QA-05: Eliminar con confirmación

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 5, RN-05, RN-07
- **Pasos:**
  1. Pulsar "Eliminar" en N2 y confirmar.
  2. Recargar el caso.
- **Resultado esperado:** diálogo "¿Eliminar esta nota? Esta acción no se puede deshacer." con foco en "Cancelar"; tras confirmar, "Nota eliminada."; N2 no aparece tras recargar; la fecha de última actualización de C cambia.

### QA-06: Cancelar eliminación

- **Tipo:** Estado UI
- **Prioridad:** Media
- **Cubre:** Escenario 6
- **Pasos:**
  1. Pulsar "Eliminar" en N1 y luego "Cancelar".
- **Resultado esperado:** N1 sigue en el caso.

### QA-07: Eliminar la última nota

- **Tipo:** Estado UI
- **Prioridad:** Media
- **Cubre:** Escenario 7
- **Pasos:**
  1. En U, eliminar N3 y confirmar.
- **Resultado esperado:** "Aún no hay notas en este caso."

### QA-08: Edición concurrente

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** Escenario 8, RN-06
- **Pasos:**
  1. En A y B, abrir la edición de N1.
  2. En B, guardar `Versión B`.
  3. En A, guardar `Versión A`.
- **Resultado esperado:** A recibe "Esta nota cambió o fue eliminada desde que la abriste. Recarga el caso para ver la versión actual."; N1 queda con `Versión B`; `Versión A` permanece en el campo de A.

### QA-09: Eliminar una nota ya editada o eliminada en otra sesión

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** Escenario 8, RN-06
- **Pasos:**
  1. En A, abrir el caso; en B, eliminar N1.
  2. En A, eliminar N1 y confirmar; luego editar N1 y guardar.
- **Resultado esperado:** ambas acciones en A muestran el mensaje del Escenario 8 sin efectos.

### QA-10: Nota de caso ajeno

- **Tipo:** Permisos
- **Prioridad:** Alta
- **Cubre:** Escenario 9, RN-08
- **Datos de prueba:**

  | Usuario | Acción sobre NL |
  | ------- | --------------- |
  | Ana (Analista) | editar |
  | Ana (Analista) | eliminar |
  | Administrador | eliminar |

- **Pasos:**
  1. Enviar cada solicitud directa.
- **Resultado esperado:** todas responden "No encontramos este caso."; NL no cambia.

### QA-11: Falla al editar o eliminar

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** Escenario 10
- **Precondiciones:** error simulado en el almacenamiento.
- **Pasos:**
  1. Editar N1 y guardar.
  2. Eliminar N2 y confirmar.
- **Resultado esperado:** "No pudimos guardar los cambios. Intenta de nuevo." y "No pudimos eliminar la nota. Intenta de nuevo."; ambas notas quedan como estaban; errores en log.

### QA-12: Las instantáneas no son editables

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** RN-09
- **Pasos:**
  1. Revisar las acciones disponibles sobre un elemento de señal del caso C.
  2. Enviar una solicitud directa para editar esa instantánea.
- **Resultado esperado:** no hay acciones "Editar" ni "Eliminar" en instantáneas; la solicitud no cambia nada.

---

**Total de casos:** 12
