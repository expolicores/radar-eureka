# Casos de Prueba — HU-067: Reportar un error en un dato o en una señal

**Historia:** [historia.md](./historia.md) | **Autor:** Juan Camilo | **Fecha:** 2026-10-02

## Alcance de las Pruebas

Se prueba la creación de reportes de error desde el detalle de la señal y la vista de evidencia: objetos, tipos, validaciones de campos, registro, duplicados, aviso de reportes abiertos, "Mis reportes", errores, doble envío, cancelación y permisos. Queda fuera la gestión por el Administrador (HU-068).

## Precondiciones y Datos Base

- Analistas "analista.piloto1" y "analista.piloto2"; Administrador "admin.po".
- SG-1 vigente versión 1, cantidad mostrada 80, 7 observaciones (una de ellas OBS-TVEC-120201); SG-2 con observación Alkosto OBS-AK-0045.
- Sin reportes previos (el primero será RE-000001).

## Matriz de Cobertura

| Criterio / Regla | Casos |
|---|---|
| Escenario 1 / RN-05 / RN-09 | QA-01 |
| Escenario 2 / RN-02 | QA-02 |
| Escenario 3 / RN-01 | QA-03 |
| Escenario 4 / RN-04 | QA-04 |
| RN-04 límites exactos | QA-05 |
| Escenario 5 / RN-06 | QA-06 |
| RN-06 objeto distinto / reporte cerrado | QA-07 |
| Escenario 6 / RN-07 | QA-08 |
| Escenario 7 / RN-08 | QA-09 |
| Escenario 8 | QA-10 |
| Escenario 9 | QA-11 |
| RN-10 sin efecto en datos | QA-12 |
| Permisos | QA-13 |

---

## Casos de Prueba

### QA-01: Reportar una cantidad mal leída

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 1 / RN-05 / RN-09
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Objeto | Dato del ítem: Cantidad | |
  | Tipo | Dato mal extraído | |
  | Descripción | "En la página 4 de la oferta la cantidad es 8, no 80" | |
  | Valor sugerido | 8 | |

- **Pasos:**
  1. Como "analista.piloto1", abrir SG-1, "Reportar un error", completar y "Enviar reporte".
  2. Consultar el registro y el log de auditoría.
- **Resultado esperado:** "Recibimos tu reporte RE-000001. El equipo lo revisará."; reporte "Recibido" con usuario, fecha-hora, ítem, SG-1 versión 1, objeto, valor mostrado 80, tipo, descripción y valor sugerido; entrada de auditoría "creación de reporte de error"; aparece en "Mis reportes en esta señal".

### QA-02: Reportar la señal completa

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 2 / RN-02
- **Pasos:**
  1. Como "analista.piloto2", reportar SG-1 con objeto "La señal completa", tipo "Producto no comparable", descripción "El comparable es de 50 pulgadas y el ítem de 55".
- **Resultado esperado:** Reporte RE-000002 vinculado a SG-1 versión 1.

### QA-03: Objeto preseleccionado desde la evidencia

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 3 / RN-01
- **Pasos:**
  1. En SG-2, abrir la evidencia de OBS-AK-0045 y pulsar "Reportar un error".
- **Resultado esperado:** El formulario abre con "Observación de referencia: OBS-AK-0045" seleccionado.

### QA-04: Validaciones de campos obligatorios y longitudes

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 4 / RN-04
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Objeto | vacío | "Selecciona sobre qué es el reporte." |
  | Tipo | vacío | "Selecciona el tipo de error." |
  | Descripción | "Mal" (3) | "Describe el error con al menos 10 caracteres." |
  | Descripción | 2.001 caracteres | "La descripción admite máximo 2.000 caracteres." |
  | Valor sugerido | 201 caracteres | "El valor sugerido admite máximo 200 caracteres." |

- **Pasos:**
  1. Intentar enviar con cada variante.
- **Resultado esperado:** Mensaje junto al campo; no se crea reporte.

### QA-05: Límites exactos de los campos

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** RN-04
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Descripción | 10 caracteres ("Cantidad 8") | Aceptada |
  | Descripción | "   Mal   " | 3 tras recorte: rechazada |
  | Descripción | 2.000 caracteres | Aceptada |
  | Valor sugerido | 200 caracteres / vacío | Aceptados |

- **Pasos:**
  1. Enviar cada variante (objetos distintos para evitar duplicados).
- **Resultado esperado:** Según la tabla.

### QA-06: Reporte duplicado abierto

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 5 / RN-06
- **Pasos:**
  1. Con RE-000001 abierto, "analista.piloto1" intenta reportar de nuevo "Dato del ítem: Cantidad" en SG-1.
- **Resultado esperado:** "Ya tienes un reporte abierto sobre este dato (RE-000001)."; no se crea reporte.

### QA-07: Permitido con otro objeto, otro usuario o reporte cerrado

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** RN-06
- **Pasos:**
  1. "analista.piloto1" reporta "Dato del ítem: Precio unitario" en SG-1.
  2. "analista.piloto2" reporta "Dato del ítem: Cantidad" en SG-1.
  3. Con RE-000001 cerrado como "Descartado", "analista.piloto1" reporta otra vez la cantidad.
- **Resultado esperado:** Los tres reportes se crean.

### QA-08: Aviso de reportes abiertos

- **Tipo:** Estado UI
- **Prioridad:** Alta
- **Cubre:** Escenario 6 / RN-07
- **Pasos:**
  1. Con RE-000001 y RE-000002 abiertos, abrir SG-1 como "analista.piloto1", como un tercer Analista y como "admin.po".
  2. Cerrar ambos reportes y volver a abrir SG-1.
- **Resultado esperado:** (1) Todos ven "Esta señal tiene 2 reporte(s) de error en revisión."; el tercer Analista no ve el contenido de los reportes. (2) El aviso desaparece.

### QA-09: Estado y resolución en "Mis reportes"

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 7 / RN-08
- **Pasos:**
  1. Cerrar RE-000001 como "Corregido" con resolución "Cantidad corregida a 8".
  2. Abrir SG-1 como "analista.piloto1"; abrir SG-2 (sin reportes propios).
- **Resultado esperado:** (1) RE-000001 con estado "Corregido", fechas y resolución. (2) En SG-2 el bloque "Mis reportes en esta señal" no aparece.

### QA-10: Error al enviar y doble envío

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** Escenario 8
- **Pasos:**
  1. Simular falla y enviar un reporte.
  2. Restaurar y pulsar "Enviar reporte" dos veces seguidas.
- **Resultado esperado:** (1) "No pudimos enviar tu reporte. Intenta de nuevo." con los datos conservados. (2) Un solo reporte creado.

### QA-11: Cancelar

- **Tipo:** Positivo
- **Prioridad:** Baja
- **Cubre:** Escenario 9
- **Pasos:**
  1. Completar el formulario y pulsar "Cancelar".
- **Resultado esperado:** Se cierra sin crear reporte.

### QA-12: Reportar no modifica datos

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** RN-10
- **Pasos:**
  1. Tras QA-01, consultar la cantidad del ítem, el Benchmark 1 y SG-1.
- **Resultado esperado:** Cantidad 80, benchmark y señal sin cambios ni nueva versión.

### QA-13: Permisos

- **Tipo:** Permisos
- **Prioridad:** Media
- **Cubre:** Permisos requeridos
- **Pasos:**
  1. Como "admin.po", crear un reporte en SG-1.
  2. Sin sesión, enviar un reporte por solicitud directa.
- **Resultado esperado:** (1) Se crea el reporte. (2) Rechazado; se redirige al inicio de sesión.

---

**Total de casos:** 13
