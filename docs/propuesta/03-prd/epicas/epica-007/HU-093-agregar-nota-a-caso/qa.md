# Casos de Prueba — HU-093: Agregar notas a un caso

**Historia:** [historia.md](./historia.md) | **Autor:** Juan Camilo | **Fecha:** 2026-10-02

## Alcance de las Pruebas

Se prueba agregar notas, el estado vacío, la validación de texto vacío y longitud, el formato de texto plano seguro, el orden, el máximo configurable, la confirmación al salir con texto sin guardar, la falla al guardar, el doble envío y la protección de casos ajenos. Quedan fuera editar y eliminar notas (HU-094).

## Precondiciones y Datos Base

| Dato | Valor |
| ---- | ----- |
| Analista | `ana.rojas@ejemplo.org`, sesión activa |
| Caso A | "Compra TV 65 Gobernación", de Ana, con 2 notas (creadas 01/10/2026 09:00 y 01/10/2026 15:00) |
| Caso V | "Caso vacío", de Ana, sin notas |
| Caso L | "Caso de Luis", de `luis.mora@ejemplo.org` |
| Parámetro | `max_notas_por_caso = 200` |

## Matriz de Cobertura

| Criterio / Regla | Casos |
| ---------------- | ----- |
| Escenario 1 / RN-01 / RN-04 / RN-06 | QA-01 |
| Escenario 2 | QA-02 |
| Escenario 3 / RN-02 | QA-03 |
| Escenario 4 / RN-02 | QA-04 |
| Escenario 5 / RN-03 | QA-05 |
| Escenario 6 / RN-05 | QA-06, QA-07 |
| Escenario 7 | QA-08 |
| Escenario 8 / RN-07 | QA-09, QA-10 |
| Escenario 9 / RN-08 | QA-11 |

---

## Casos de Prueba

### QA-01: Agregar una nota

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 1, RN-01, RN-04, RN-06
- **Datos de prueba:**

  | Campo | Valor |
  | ----- | ----- |
  | texto | `Pedir a la entidad el estudio de mercado del proceso.` |

- **Pasos:**
  1. En A, escribir el texto y pulsar "Guardar nota" a las 10:00 del 02/10/2026.
- **Resultado esperado:** "Nota guardada."; la nota aparece primera con "Creada el 02/10/2026 10:00", seguida de las de 01/10 15:00 y 09:00; el campo queda vacío; la fecha de última actualización de A es 02/10/2026 10:00.

### QA-02: Caso sin notas

- **Tipo:** Estado UI
- **Prioridad:** Media
- **Cubre:** Escenario 2
- **Pasos:**
  1. Abrir V.
- **Resultado esperado:** "Aún no hay notas en este caso." y el campo "Nueva nota".

### QA-03: Nota vacía

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 3, RN-02
- **Datos de prueba:**

  | Texto |
  | ----- |
  | (vacío) |
  | `     ` |
  | tres saltos de línea |

- **Pasos:**
  1. Guardar con cada valor.
- **Resultado esperado:** "Escribe el texto de la nota."; no se guarda.

### QA-04: Longitud límite

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** Escenario 4, RN-02
- **Datos de prueba:**

  | Texto | Esperado |
  | ----- | -------- |
  | 1 carácter `x` | guardada |
  | 5.000 caracteres | guardada |
  | 5.001 caracteres | "La nota admite máximo 5.000 caracteres." |
  | 4.998 caracteres con 2 espacios iniciales y 2 finales | guardada (recortada a 4.998) |

- **Pasos:**
  1. Guardar con cada texto.
- **Resultado esperado:** según la tabla; el contador muestra el exceso cuando supera 5.000.

### QA-05: Texto plano con saltos de línea

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 5, RN-03
- **Datos de prueba:**

  | Campo | Valor |
  | ----- | ----- |
  | texto | `Hipótesis:` (salto) `precio 42 % por encima — ¿incluye instalación?` (salto) `<b>urgente</b> <script>alert(1)</script>` |

- **Pasos:**
  1. Guardar la nota y recargar el caso.
- **Resultado esperado:** se muestran 3 líneas literales, con tildes y signos; `<b>urgente</b>` y el script aparecen como texto, sin negrita ni ejecución.

### QA-06: Máximo de notas

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** Escenario 6, RN-05
- **Datos de prueba:**

  | Notas actuales | Esperado |
  | -------------- | -------- |
  | 199 | se guarda (queda en 200) |
  | 200 | "El caso alcanzó el máximo de 200 notas." |

- **Pasos:**
  1. Agregar una nota en cada situación.
- **Resultado esperado:** según la tabla.

### QA-07: Reducción del máximo de notas

- **Tipo:** Borde
- **Prioridad:** Baja
- **Cubre:** RN-05
- **Pasos:**
  1. Con A en 15 notas, configurar `max_notas_por_caso = 10` y agregar una nota.
  2. Intentar configurar 9 y 1.001.
- **Resultado esperado:** A conserva 15 notas y rechaza la nueva con "El caso alcanzó el máximo de 10 notas."; 9 y 1.001 se rechazan por fuera del rango.

### QA-08: Salir con nota sin guardar

- **Tipo:** Estado UI
- **Prioridad:** Media
- **Cubre:** Escenario 7
- **Pasos:**
  1. Escribir texto sin guardar e ir a "Mis casos"; cancelar la confirmación.
  2. Repetir y confirmar.
- **Resultado esperado:** aparece "Tienes una nota sin guardar. ¿Deseas salir sin guardarla?"; al cancelar el texto sigue en el campo; al confirmar se sale sin nota guardada.

### QA-09: Falla al guardar

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** Escenario 8, RN-07
- **Precondiciones:** error simulado en el almacenamiento.
- **Pasos:**
  1. Guardar `Revisar anexo técnico.`
- **Resultado esperado:** "No pudimos guardar la nota. Intenta de nuevo."; el texto sigue en el campo; no hay nota nueva; error en log.

### QA-10: Doble envío

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** Escenario 8, RN-07
- **Pasos:**
  1. Enviar dos solicitudes idénticas de nota seguidas.
- **Resultado esperado:** una sola nota nueva.

### QA-11: Nota en caso ajeno

- **Tipo:** Permisos
- **Prioridad:** Alta
- **Cubre:** Escenario 9, RN-08
- **Pasos:**
  1. Con la sesión de Ana, enviar una solicitud para agregar una nota a L.
  2. Con la sesión del Administrador, repetir.
- **Resultado esperado:** ambas responden "No encontramos este caso."; L no cambia.

---

**Total de casos:** 11
