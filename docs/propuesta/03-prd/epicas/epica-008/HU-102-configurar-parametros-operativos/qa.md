# Casos de Prueba — HU-102: Configurar términos de búsqueda, umbral de aceptación de extracción y frecuencias

**Historia:** [historia.md](./historia.md) | **Autor:** Juan Camilo | **Fecha:** 2026-10-02

## Alcance de las Pruebas

Se prueban la consulta y el cambio de términos de búsqueda, umbral de aceptación automática con referencia de calibración y frecuencias por fuente, con sus validaciones, versionado, no retroactividad, auditoría y permisos. Queda fuera: la lógica de identificación de candidatos, de extracción y de la cola de revisión (otras HU y épicas) y los parámetros analíticos (HU-101).

## Precondiciones y Datos Base

- Hora de referencia: **2026-10-02 08:00 (UTC−05:00)**.
- Usuarios: `admin.po@prueba.co` (Administrador); `analista1@prueba.co` (Analista).
- Versión vigente: 4, con términos "televisor", "smart tv", "tv"; umbral "sin calibrar"; frecuencias públicas 24 h; retail 7 días.
- Últimas ejecuciones: TVEC — Ítems inició 2026-10-02 01:00; SECOP II — Contratos inició 2026-10-01 22:00.
- Motivo válido: "Ajuste tras revisión semanal de la cola".

## Matriz de Cobertura

| Criterio / Regla | Casos |
| ----- | ----- |
| Escenario 1, RN-01 | QA-01 |
| Escenario 2, RN-02, RN-06, RN-08 | QA-02 |
| Escenario 3, RN-02 (validaciones de términos) | QA-03 |
| RN-02 (normalización de espacios y límite de 30) | QA-04 |
| Escenario 4, RN-03, RN-08 | QA-05 |
| Escenario 5, RN-03 | QA-06 |
| Escenario 6, RN-03 (rango y formato) | QA-07 |
| Escenario 7, RN-03 | QA-08 |
| Escenario 8, RN-04 | QA-09 |
| Escenario 9, RN-04 | QA-10 |
| Escenario 10, RN-01 (límites de frecuencias) | QA-11 |
| RN-04 (fuente suspendida) | QA-12 |
| Escenario 11, RN-05 | QA-13 |
| Escenario 12, RN-05, RN-06, RN-08 | QA-14 |
| Escenario 13, RN-07 | QA-15 |
| Escenario 14 | QA-16 |

---

## Casos de Prueba

### QA-01: Consultar parámetros operativos vigentes

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 1, RN-01
- **Pasos:**
  1. Consultar los parámetros operativos.
- **Resultado esperado:** versión 4; términos de búsqueda (3); umbral "sin calibrar"; referencia vacía; 4 frecuencias de ingesta en 24 horas y 2 de captura en 7 días; cada uno con rango y configuración inicial.

### QA-02: Agregar un término crea versión con auditoría

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 2, RN-02, RN-06, RN-08
- **Pasos:**
  1. Enviar la lista "televisor", "smart tv", "tv", "pantalla led tv" con motivo válido y versión de partida 4.
- **Resultado esperado:** "Configuración guardada como versión 5."; v5 contiene los 4 términos y el resto de parámetros igual a v4; evento de auditoría con la lista anterior y la nueva.

### QA-03: Validaciones de términos

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 3, RN-02
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ----- |
  | Lista | (vacía) | "Debe existir al menos un término de búsqueda." |
  | Término | t | "El término 't' debe tener entre 2 y 50 caracteres." |
  | Término | tv (2) | aceptado (mínimo) |
  | Término | texto de 50 / 51 caracteres | aceptado / rechazado |
  | Término | tv;drop | "El término 'tv;drop' solo puede contener letras, números, espacios y guiones." |
  | Término | televisión 4k-uhd | aceptado (tilde, número y guion) |
  | Términos | TV, tv | "El término 'tv' está repetido." |
  | Términos | televisor, televisór | repetido (tilde ignorada) |

- **Pasos:**
  1. Enviar cada lista por separado.
- **Resultado esperado:** el resultado indicado; los rechazos no crean versión.

### QA-04: Normalización de espacios y máximo de términos

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** RN-02
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ----- |
  | Término | `  smart   tv  ` | se guarda "smart tv"; repetido si ya existe "smart tv" |
  | Lista | 30 términos válidos distintos | aceptada |
  | Lista | 31 términos válidos distintos | "Se permiten como máximo 30 términos de búsqueda." |

- **Pasos:**
  1. Enviar cada lista.
- **Resultado esperado:** el resultado indicado en la nota.

### QA-05: Fijar umbral con referencia de calibración

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 4, RN-03, RN-08
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ----- |
  | Umbral | 0,85 | — |
  | Referencia | D4-4: 228 filas validadas, relación confianza-corrección del 2026-10-20 | — |

- **Pasos:**
  1. Enviar el cambio con motivo válido.
- **Resultado esperado:** nueva versión con umbral 0,85 y la referencia; auditoría con anterior "sin calibrar", nuevo 0,85 y la referencia.

### QA-06: Umbral sin referencia de calibración válida

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 5, RN-03
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ----- |
  | Referencia | (vacía) | rechazada |
  | Referencia | D4-4 ok (9) | rechazada |
  | Referencia | 10 caracteres / 200 caracteres | aceptadas |
  | Referencia | 201 caracteres | rechazada |

- **Pasos:**
  1. Enviar umbral 0,90 con cada referencia.
- **Resultado esperado:** rechazos con "Para fijar el umbral de aceptación automática debe indicar la referencia de calibración (10 a 200 caracteres)."; aceptadas crean versión.

### QA-07: Rango y formato del umbral

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** Escenario 6, RN-03
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ----- |
  | Umbral | 0,00 / 1.00 / 0,7 | aceptados (con referencia válida) |
  | Umbral | -0,1 / 1,01 / 1,5 / 0,855 / alto | rechazados |

- **Pasos:**
  1. Enviar cada valor con referencia y motivo válidos.
- **Resultado esperado:** rechazos con "El umbral de aceptación automática debe ser un decimal entre 0,00 y 1,00 con máximo 2 decimales, o 'sin calibrar'."

### QA-08: Volver a "sin calibrar"

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 7, RN-03
- **Pasos:**
  1. Con umbral 0,85, cambiarlo a "sin calibrar" con motivo válido.
  2. Procesar un dato crítico (precio unitario) con confianza baja.
- **Resultado esperado:** nueva versión con umbral "sin calibrar" y referencia vacía; el dato del paso 2 se dirige a revisión humana.

### QA-09: Cambio de frecuencia recalcula la próxima ejecución esperada

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 8, RN-04
- **Pasos:**
  1. Cambiar `frecuencia_ingesta_horas.TVEC — Ítems` a 12.
  2. Consultar el estado de fuentes.
- **Resultado esperado:** nueva versión; próxima ejecución esperada de TVEC — Ítems = 2026-10-02 13:00.

### QA-10: Frecuencia que deja la fuente vencida

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** Escenario 9, RN-04
- **Pasos:**
  1. Cambiar `frecuencia_ingesta_horas.SECOP II — Contratos` a 6 (última ejecución hace 10 horas).
  2. Esperar el siguiente ciclo del programador.
- **Resultado esperado:** la fuente inicia una ejecución programada en ese ciclo.

### QA-11: Límites de frecuencias

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** Escenario 10, RN-01
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ----- |
  | Ingesta TVEC — Órdenes (horas) | 1 / 168 | aceptados |
  | Ingesta TVEC — Órdenes (horas) | 0 / 169 / 12,5 | "La frecuencia de ingesta de TVEC — Órdenes debe ser un número entero entre 1 y 168 horas." |
  | Captura Alkosto (días) | 1 / 30 | aceptados |
  | Captura Alkosto (días) | 0 / 31 | "La frecuencia de captura de Alkosto debe ser un número entero entre 1 y 30 días." |

- **Pasos:**
  1. Enviar cada valor por separado.
- **Resultado esperado:** el resultado indicado; los rechazos no crean versión.

### QA-12: Fuente suspendida conserva frecuencia sin ejecutarse

- **Tipo:** Borde
- **Prioridad:** Baja
- **Cubre:** RN-04
- **Precondiciones:** Alkosto suspendida.
- **Pasos:**
  1. Cambiar `frecuencia_captura_dias.Alkosto` a 3.
  2. Dejar pasar 4 días.
- **Resultado esperado:** el cambio se guarda; no se ejecuta ninguna captura de Alkosto mientras siga suspendida.

### QA-13: Validación todo o nada

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** Escenario 11, RN-05
- **Pasos:**
  1. Enviar juntos el término nuevo "televisor led" y `frecuencia_captura_dias.Falabella` = 45.
- **Resultado esperado:** no se crea versión; los términos vigentes no cambian; se devuelve el mensaje de la frecuencia de Falabella.

### QA-14: Motivo, sin cambios, concurrencia y falla de auditoría

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** Escenario 12, RN-05, RN-06, RN-08
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ----- |
  | Motivo | (vacío) | "Debe indicar un motivo del cambio de 10 a 500 caracteres." |
  | Cambio | términos iguales a los vigentes | "No hay cambios respecto a la versión vigente." |
  | Versión de partida | 3 (vigente 4) | "La configuración cambió (versión vigente 4) desde que la consultó. Vuelva a consultarla y repita el cambio." |
  | Auditoría | no disponible (simulado) | "No fue posible registrar la auditoría; el cambio no se aplicó. Intente de nuevo." |

- **Pasos:**
  1. Enviar un cambio en cada condición.
- **Resultado esperado:** el mensaje indicado; nunca se crea versión.

### QA-15: Guardar no dispara procesos ni es retroactivo

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 13, RN-07
- **Precondiciones:** 355 candidatos SECOP II ya identificados.
- **Pasos:**
  1. Agregar el término "pantalla led tv".
  2. Verificar ejecuciones iniciadas inmediatamente y los candidatos existentes.
  3. Ejecutar la siguiente ingesta programada.
- **Resultado esperado:** al guardar no se inicia ninguna ingesta, captura ni extracción; los 355 candidatos siguen iguales; la ingesta del paso 3 registra la nueva versión y aplica el nuevo término a los registros que procesa.

### QA-16: Analista no puede consultar ni cambiar

- **Tipo:** Permisos
- **Prioridad:** Alta
- **Cubre:** Escenario 14
- **Pasos:**
  1. Como `analista1@prueba.co`, consultar y luego enviar un cambio válido.
- **Resultado esperado:** "Acción no permitida: esta operación requiere el rol Administrador." en ambos casos; sin versión nueva.

---

**Total de casos:** 16
