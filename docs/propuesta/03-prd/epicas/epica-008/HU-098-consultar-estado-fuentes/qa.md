# Casos de Prueba — HU-098: Consultar el estado de las fuentes de datos

**Historia:** [historia.md](./historia.md) | **Autor:** Juan Camilo | **Fecha:** 2026-10-02

## Alcance de las Pruebas

Se prueba la consulta de resumen y de detalle del estado de las 6 fuentes del catálogo: cálculo del estado (RN-05) con su precedencia, campos mostrados, historial, parámetros, fechas, mensajes, permisos y carácter de solo lectura. Queda fuera: la ejecución de ingestas o capturas (HU-099), el envío de alertas (HU-100) y la lógica de suspensión de fuentes retail (FR-047, otra épica). El mecanismo de entrega (comando, archivo o vista mínima) es indiferente para los casos.

## Precondiciones y Datos Base

- Fecha y hora de referencia de las pruebas: **2026-10-02 08:00 (UTC−05:00)**.
- Usuarios: `admin.po@prueba.co` (rol Administrador); `analista1@prueba.co` (rol Analista).
- Parámetros: historial = 10; tolerancia de retraso = 1 hora; frecuencia ingesta pública = 24 h; frecuencia captura retail = 7 días.
- Ejecuciones semilla:

  | Fuente | Ejecuciones | Última ejecución terminada | Otros |
  | ----- | ----- | ----- | ----- |
  | SECOP II — Contratos | 15 | 2026-10-02 02:00, exitosa, leídos 120, nuevos 3, actualizados 9, rechazados 0, errores 0 | — |
  | SECOP II — Archivos | 8 | 2026-10-02 03:00, exitosa, errores 4, rechazados 2 | — |
  | TVEC — Ítems | 6 | 2026-10-02 01:30, exitosa, errores 0, rechazados 7 | — |
  | TVEC — Órdenes | 3 | 2026-10-01 04:00, exitosa | — |
  | Alkosto | 5 | 2026-09-27 09:00, exitosa | suspendida 2026-09-28 10:15, motivo "Cambio en robots.txt que prohíbe la ruta de captura" |
  | Falabella | 0 | — | sin captura automática; última carga manual 2026-09-30 |

## Matriz de Cobertura

| Criterio / Regla | Casos |
| ----- | ----- |
| Escenario 1, RN-01, RN-03, RN-08 | QA-01 |
| Escenario 2, RN-04, RN-06 | QA-02 |
| Escenario 3 | QA-03 |
| RN-07 (parámetros y nulos) | QA-04 |
| Escenario 4, Escenario 7, RN-05 (Operativa, rechazados) | QA-05 |
| Escenario 5 | QA-06 |
| Escenario 6 | QA-07 |
| Escenario 8, RN-05 (Retrasada, límite de tolerancia) | QA-08 |
| Escenario 9, RN-05 (precedencia En ejecución) | QA-09 |
| Escenario 10, RN-05 (precedencia Suspendida) | QA-10 |
| Escenario 11, RN-03 (valores "—") | QA-11 |
| Escenario 12 | QA-12 |
| Escenario 13, RN-01 (nombre insensible), RN-10 | QA-13 |
| Escenario 14, RN-10 (permisos y sesión) | QA-14 |
| RN-09 (solo lectura) | QA-15 |

---

## Casos de Prueba

### QA-01: El resumen lista las 6 fuentes en orden con todos sus campos

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 1, RN-01, RN-03, RN-08
- **Pasos:**
  1. Autenticarse como `admin.po@prueba.co`.
  2. Solicitar el resumen de estado de fuentes.
- **Resultado esperado:** 6 filas en el orden SECOP II — Contratos, SECOP II — Archivos, TVEC — Ítems, TVEC — Órdenes, Alkosto, Falabella. Cada fila trae los campos de RN-03; SECOP II — Contratos muestra inicio "2026-10-02 02:00", leídos 120, nuevos 3, actualizados 9, fecha de corte en formato `AAAA-MM-DD` y próxima ejecución esperada "2026-10-03 02:00". El encabezado indica la fecha y hora de generación en UTC−05:00.

### QA-02: El detalle muestra las 10 ejecuciones más recientes en orden descendente

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 2, RN-04, RN-06
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ----- |
  | Fuente | SECOP II — Contratos | 15 ejecuciones; la nº 14 fue `manual`, lanzada por admin.po@prueba.co, duración 12 min 10 s |

- **Pasos:**
  1. Solicitar el detalle de "SECOP II — Contratos".
- **Resultado esperado:** 10 ejecuciones, de la más reciente a la más antigua. La ejecución manual muestra origen `manual`, usuario `admin.po@prueba.co` y duración 13 minutos (redondeo hacia arriba); las programadas muestran usuario "—".

### QA-03: Historial con menos ejecuciones que el parámetro

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** Escenario 3
- **Pasos:**
  1. Solicitar el detalle de "TVEC — Órdenes" (3 ejecuciones).
- **Resultado esperado:** se listan exactamente 3 ejecuciones, sin filas vacías ni mensaje de error.

### QA-04: Tamaño de historial en sus límites y sin definir

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** RN-07
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ----- |
  | Historial | 1 | mínimo: muestra 1 ejecución de SECOP II — Contratos |
  | Historial | 100 | máximo: muestra las 15 existentes |
  | Historial | (no definido) | usa la configuración inicial: 10 |

- **Pasos:**
  1. Para cada valor, fijar el parámetro y solicitar el detalle de "SECOP II — Contratos".
- **Resultado esperado:** se listan 1, 15 y 10 ejecuciones respectivamente.

### QA-05: Estado Operativa, incluso con rechazados

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 4, Escenario 7, RN-05
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ----- |
  | SECOP II — Contratos | exitosa, errores 0, rechazados 0 | Operativa |
  | TVEC — Ítems | exitosa, errores 0, rechazados 7 | Operativa; se muestra rechazados = 7 |

- **Pasos:**
  1. Solicitar el resumen.
- **Resultado esperado:** ambas fuentes aparecen como **Operativa**; TVEC — Ítems muestra rechazados = 7.

### QA-06: Estado Fallida con mensaje de error principal

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 5
- **Precondiciones:** agregar a SECOP II — Contratos una ejecución 2026-10-02 06:00 con resultado `fallida` y mensaje "Tiempo de espera agotado tras 3 reintentos".
- **Pasos:**
  1. Solicitar el resumen.
- **Resultado esperado:** SECOP II — Contratos aparece como **Fallida**, con inicio "2026-10-02 06:00" y el mensaje "Tiempo de espera agotado tras 3 reintentos".

### QA-07: Estado Con errores

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 6
- **Pasos:**
  1. Solicitar el resumen.
- **Resultado esperado:** SECOP II — Archivos aparece como **Con errores**, con errores = 4 y rechazados = 2.

### QA-08: Estado Retrasada y límite de la tolerancia

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** Escenario 8, RN-05
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ----- |
  | Inicio última ejecución SECOP II — Contratos | 2026-10-01 07:00 (hace 25 h exactas) | igual a frecuencia + tolerancia → **Operativa** |
  | Inicio última ejecución SECOP II — Contratos | 2026-10-01 06:59 (hace 25 h 1 min) | supera frecuencia + tolerancia → **Retrasada** |
  | Inicio última ejecución SECOP II — Contratos | 2026-10-01 06:00 (hace 26 h) | **Retrasada** |

- **Pasos:**
  1. Para cada fila, dejar esa ejecución como la última y solicitar el resumen a las 2026-10-02 08:00.
- **Resultado esperado:** el estado es el indicado en la nota; en los casos Retrasada, "próxima ejecución esperada" muestra la fecha ya vencida (2026-10-02 06:59 y 2026-10-02 06:00).

### QA-09: Estado En ejecución prevalece sobre Fallida

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 9, RN-05, RN-06
- **Precondiciones:** la última ejecución terminada de TVEC — Órdenes es `fallida`; existe otra `en_curso` desde 2026-10-02 07:40.
- **Pasos:**
  1. Solicitar el resumen.
- **Resultado esperado:** TVEC — Órdenes aparece como **En ejecución**, "en curso desde 2026-10-02 07:40", y se muestra el resultado `fallida` de la última ejecución terminada.

### QA-10: Estado Suspendida prevalece aunque la última ejecución sea exitosa

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 10, RN-05
- **Pasos:**
  1. Solicitar el resumen.
- **Resultado esperado:** Alkosto aparece como **Suspendida**, con "2026-09-28 10:15" y motivo "Cambio en robots.txt que prohíbe la ruta de captura"; la fecha de corte se muestra como "—".

### QA-11: Fuente retail sin captura automática

- **Tipo:** Estado UI
- **Prioridad:** Media
- **Cubre:** Escenario 11, RN-03
- **Pasos:**
  1. Solicitar el resumen.
- **Resultado esperado:** Falabella aparece como **Sin captura automática**, con "última carga manual: 2026-09-30"; los campos de ejecución y la fecha de corte se muestran como "—" (nunca vacíos ni 0).

### QA-12: Fuente automatizada sin ejecuciones

- **Tipo:** Estado UI
- **Prioridad:** Media
- **Cubre:** Escenario 12
- **Precondiciones:** eliminar del entorno de prueba las 3 ejecuciones de TVEC — Órdenes.
- **Pasos:**
  1. Solicitar el resumen.
  2. Solicitar el detalle de "TVEC — Órdenes".
- **Resultado esperado:** en el resumen aparece como **Sin ejecuciones** con campos "—"; el detalle muestra "La fuente TVEC — Órdenes no tiene ejecuciones registradas."

### QA-13: Nombre de fuente inexistente y nombre sin distinguir mayúsculas ni tildes

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** Escenario 13, RN-01, RN-10
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ----- |
  | Fuente | Mercado Libre | inexistente |
  | Fuente | tvec — items | válida (sin tilde, minúsculas) |

- **Pasos:**
  1. Solicitar el detalle de cada valor.
- **Resultado esperado:** "Mercado Libre" devuelve "La fuente 'Mercado Libre' no existe. Fuentes válidas: SECOP II — Contratos, SECOP II — Archivos, TVEC — Ítems, TVEC — Órdenes, Alkosto, Falabella."; "tvec — items" devuelve el detalle de TVEC — Ítems.

### QA-14: Acceso denegado a Analista y a usuario sin sesión

- **Tipo:** Permisos
- **Prioridad:** Alta
- **Cubre:** Escenario 14, RN-10
- **Pasos:**
  1. Como `analista1@prueba.co`, solicitar el resumen.
  2. Sin sesión ni credencial, solicitar el resumen.
- **Resultado esperado:** paso 1: "Acción no permitida: esta consulta requiere el rol Administrador."; paso 2: "Debe autenticarse como Administrador para consultar el estado de fuentes."; en ambos no se entrega ningún dato.

### QA-15: Consultar no modifica nada

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** RN-09
- **Pasos:**
  1. Contar ejecuciones, suspensiones y eventos de auditoría.
  2. Solicitar el resumen y el detalle de las 6 fuentes.
  3. Volver a contar.
- **Resultado esperado:** los conteos no cambian; no se inició ninguna ejecución ni se levantó ninguna suspensión.

---

**Total de casos:** 15
