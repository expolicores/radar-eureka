# Casos de Prueba — HU-006: Bitácora de ejecuciones de ingesta

**Historia:** [historia.md](./historia.md) | **Autor:** Juan Camilo | **Fecha:** 2026-10-02

## Alcance de las Pruebas

Se prueba el registro de cada ejecución de ingesta (creación, actualización parcial, cierre), coherencia de contadores, errores recuperados y no recuperados, ejecuciones omitidas e interrumpidas, consultas y permisos.

Queda fuera: las alertas y el estado de fuentes de la operación del MVP, y el detalle de rechazos de calidad (HU-005).

## Precondiciones y Datos Base

- Administrador: `admin.po@piloto.test`; Analista: `analista1@piloto.test`.
- Límite de interrupción: 6 horas.
- Ejecuciones previas en la bitácora:

  | id_ejecucion | fuente | tipo | estado | inicio |
  |---|---|---|---|---|
  | EJ-0001 | SECOP II contratos | Inicial | Exitosa | 2026-09-28T09:00 |
  | EJ-0002 | TVEC ítems | Inicial | Exitosa | 2026-09-28T13:00 |
  | EJ-0003 | SECOP II contratos | Incremental programada | Fallida | 2026-10-01T02:00 |

- No hay ejecuciones de "TVEC órdenes".

## Matriz de Cobertura

| Criterio / Regla | Casos |
|---|---|
| Escenario 1 / RN-02, RN-03 | QA-01 |
| Escenario 2 / RN-05 | QA-02 |
| Escenario 3 / RN-03 | QA-03 |
| Escenario 4 / RN-04 | QA-04 |
| Escenario 5 / RN-04 | QA-05 |
| Escenario 6 | QA-06 |
| Escenario 7 / RN-06 | QA-07 |
| Escenario 8 / RN-09 | QA-08, QA-09 |
| Escenario 9 | QA-10 |
| Escenario 10 / RN-10 | QA-11 |
| RN-07 | QA-12 |
| RN-08 | QA-13 |

---

## Casos de Prueba

### QA-01: Ejecución exitosa registrada con todos sus campos

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 1 / RN-02, RN-03
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Registros recibidos | 25 | |
  | Nuevos / actualizados / sin cambios / rechazados | 10 / 5 / 8 / 2 | |
  | Con advertencias | 3 | |

- **Pasos:**
  1. Ejecutar la incremental programada de SECOP II con esos resultados.
- **Resultado esperado:** registro con fuente "SECOP II contratos", dataset `jbjy-vk9h`, tipo "Incremental programada", inicio, fin, duración, estado "Exitosa", marcas de agua usada y resultante, fecha de corte, `leidos = 25`, `nuevos = 10`, `actualizados = 5`, `sin_cambios = 8`, `rechazados = 2`, `con_advertencias = 3`, errores vacíos y `usuario = sistema`.

### QA-02: Registro "En curso" con contadores parciales

- **Tipo:** Estado UI
- **Prioridad:** Media
- **Cubre:** Escenario 2 / RN-05
- **Pasos:**
  1. Iniciar una carga de 3 páginas y pausar la API después de la página 1.
  2. Consultar la bitácora.
- **Resultado esperado:** estado "En curso", inicio registrado, fin vacío, contadores de la página 1 y `ultima_actividad` igual al cierre de la página 1.

### QA-03: Invariante de contadores

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 3 / RN-03
- **Pasos:**
  1. Forzar (con doble de prueba) una ejecución donde se leen 25 y la suma de resultados es 24.
- **Resultado esperado:** se agrega el error "Contadores inconsistentes: leídos 25 ≠ suma 24"; en ejecuciones normales la invariante se cumple.

### QA-04: Errores recuperados

- **Tipo:** Integración
- **Prioridad:** Alta
- **Cubre:** Escenario 4 / RN-04
- **Pasos:**
  1. Inyectar tiempo de espera en la página 1 y HTTP 503 en la página 2, ambos recuperados al primer reintento.
- **Resultado esperado:** estado "Exitosa"; 2 entradas de error con fecha y hora, página (1 y 2), tipo ("Tiempo de espera", "HTTP 503"), intento 1 y resultado "Recuperado".

### QA-05: Ejecución fallida sin secretos en el mensaje

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 5 / RN-04
- **Pasos:**
  1. Configurar un app token `tok-PRUEBA-123` y responder HTTP 403 con un cuerpo que repite el token.
- **Resultado esperado:** estado "Fallida"; un error "HTTP 403", intento 1, "No recuperado"; el texto `tok-PRUEBA-123` no aparece en el mensaje; contadores con lo procesado (0).

### QA-06: Ejecución omitida

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 6
- **Pasos:**
  1. Disparar la incremental de "TVEC órdenes" con una carga de TVEC ítems en curso.
- **Resultado esperado:** registro con estado "Omitida", motivo "Ejecución en curso: {id}", fecha y hora y contadores en 0.

### QA-07: Cierre de una ejecución interrumpida

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** Escenario 7 / RN-06
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | ultima_actividad | hace 6 h 1 min | se cierra |
  | ultima_actividad | hace 6 h 0 min | no se cierra |
  | Límite configurado | 0 / 49 | rechazados (rango 1–48) |

- **Pasos:**
  1. Preparar una ejecución "En curso" con cada antigüedad e iniciar otra de la misma fuente.
- **Resultado esperado:** con 6 h 1 min, la anterior queda "Fallida" con "Ejecución interrumpida sin cierre" y fin = última actividad; con 6 h 0 min, permanece "En curso". Los límites 0 y 49 no se aceptan.

### QA-08: Consulta filtrada y ordenada

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 8 / RN-09
- **Pasos:**
  1. Consultar fuente "SECOP II contratos".
  2. Consultar estado "Fallida" con rango 2026-10-01 a 2026-10-01.
  3. Consultar fuente "TVEC órdenes" con estado "Exitosa".
- **Resultado esperado:** (1) EJ-0003 antes que EJ-0001. (2) Solo EJ-0003 (extremos inclusive). (3) "No hay ejecuciones de ingesta para los filtros indicados."

### QA-09: Rango de fechas inválido

- **Tipo:** Negativo
- **Prioridad:** Baja
- **Cubre:** RN-09
- **Pasos:**
  1. Consultar con fecha inicial 2026-10-02 y final 2026-09-01.
- **Resultado esperado:** "El rango de fechas no es válido: la fecha inicial es posterior a la final."

### QA-10: Resumen por fuente

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 9
- **Pasos:**
  1. Consultar el resumen por fuente con los datos base.
- **Resultado esperado:** SECOP II contratos: última EJ-0003 (Fallida), última exitosa EJ-0001 con su marca de agua y fecha de corte; TVEC ítems: EJ-0002 en ambas; TVEC órdenes: "Sin ejecuciones".

### QA-11: El Analista no accede a la bitácora

- **Tipo:** Permisos
- **Prioridad:** Media
- **Cubre:** Escenario 10 / RN-10
- **Pasos:**
  1. Con `analista1@piloto.test`, intentar el listado y el resumen.
- **Resultado esperado:** acceso denegado en ambos.

### QA-12: Rechazos de calidad no cuentan como errores

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** RN-07
- **Pasos:**
  1. Ejecutar una carga sin fallas técnicas con 3 registros rechazados por calidad.
- **Resultado esperado:** `rechazados = 3`, lista de errores vacía, estado "Exitosa".

### QA-13: Ejecución cerrada no se modifica

- **Tipo:** Negativo
- **Prioridad:** Baja
- **Cubre:** RN-08
- **Pasos:**
  1. Ejecutar una nueva carga de SECOP II después de EJ-0001.
  2. Revisar EJ-0001.
- **Resultado esperado:** EJ-0001 conserva exactamente sus valores; la nueva carga tiene su propio `id_ejecucion`.

---

**Total de casos:** 13
