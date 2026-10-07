# Casos de Prueba — HU-005: Validaciones de calidad en la ingesta y registro de rechazos

**Historia:** [historia.md](./historia.md) | **Autor:** Juan Camilo | **Fecha:** 2026-10-02

## Alcance de las Pruebas

Se prueba el catálogo de reglas de calidad para contratos SECOP II, ítems TVEC y órdenes TVEC: rechazos, advertencias, formatos, tolerancia aritmética, deduplicación, protección de versiones anteriores, consulta del registro de rechazos y ausencia de datos sensibles en los rechazos.

Queda fuera: la mecánica de consulta a la API (HU-001 a HU-004).

## Precondiciones y Datos Base

- Administrador: `admin.po@piloto.test`; Analista: `analista1@piloto.test`.
- Fecha de ejecución: 2026-10-02; `fecha_inicio_historico = 2023-01-01`; tolerancia CAL-TVI-08: 1 % / COP 1.000.
- Contrato válido base (CB): `id_contrato = CO1.PCCNTR.7000001`, `fecha_de_firma = 2025-04-10`, `nombre_entidad = Alcaldía de Ensayo`, `objeto_del_contrato = Adquisición de televisores LED 50"`, `ultima_actualizacion = 2025-04-12T10:00:00`, `proceso_de_compra = CO1.BDOS.7100001`, `valor_del_contrato = 9800000`, `codigo_de_categoria_principal = V1.52161505`, `urlproceso` con URL válida, fechas de inicio 2025-04-15 y fin 2025-05-15.
- Ítem TVEC válido base (IB): `:id = row-q001`, `orden = 556677`, `fecha = 2025-06-01`, `item = TELEVISOR LG 50" 50UR7800PSB`, `precio = 1890000`, `cantidad = 3`, `total = 5670000`.

## Matriz de Cobertura

| Criterio / Regla | Casos |
|---|---|
| Escenario 1 | QA-01 |
| Escenario 2 / RN-02 (CAL-SEC-01 a 07), RN-07 | QA-02 |
| Escenario 2 / RN-03 (CAL-TVI-01 a 03) | QA-03 |
| Escenario 3 / CAL-TVI-04, 05 | QA-04 |
| Escenario 4 / CAL-SEC-08 a 14 | QA-05 |
| Escenario 5 / CAL-TVI-06 a 08 | QA-06, QA-07 |
| Escenario 6 / RN-06 | QA-08 |
| Escenario 7 / RN-09 | QA-09 |
| Escenario 8 / RN-09 | QA-10 |
| Escenario 9 | QA-11, QA-12 |
| Escenario 10 / RN-07 | QA-13 |
| RN-01 | QA-14 |
| RN-04 | QA-15 |
| RN-05 | QA-16 |

---

## Casos de Prueba

### QA-01: Registros válidos sin advertencias

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 1
- **Pasos:**
  1. Procesar CB e IB.
- **Resultado esperado:** ambos escritos con `advertencias_calidad` vacía; el registro de rechazos no tiene entradas.

### QA-02: Rechazos de contratos SECOP II

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 2 / RN-02, RN-07
- **Datos de prueba:** (cada fila es CB con una modificación)

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | id_contrato | "" | CAL-SEC-01 |
  | fecha_de_firma | (nula) | CAL-SEC-02 |
  | fecha_de_firma | 2025/04/10 | CAL-SEC-03 |
  | fecha_de_firma | 2022-12-31 | CAL-SEC-04 (mín − 1) |
  | nombre_entidad | "  " | CAL-SEC-05 |
  | objeto y descripción | (ambos nulos) | CAL-SEC-06 |
  | objeto nulo, descripción "Compra de TV" | | válido (solo uno basta) |
  | ultima_actualizacion | ayer | CAL-SEC-07 |

- **Pasos:**
  1. Procesar cada variante.
- **Resultado esperado:** cada variante inválida no se escribe y genera una entrada con fuente "SECOP II contratos", ejecución, id de origen (nulo en CAL-SEC-01), código, campo, valor recibido y motivo del catálogo; la variante con solo descripción se escribe.

### QA-03: Rechazos de ítems TVEC por identificador, fecha y descripción

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 2 / RN-03
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | :id | (nulo) | CAL-TVI-01 |
  | fecha | 01/06/2025 | CAL-TVI-02 |
  | fecha | 2026-10-03 | CAL-TVI-02 (futuro) |
  | item | "" | CAL-TVI-03 |

- **Pasos:**
  1. Procesar IB con cada modificación.
- **Resultado esperado:** ninguno se escribe; cada uno queda en el registro con su código y motivo.

### QA-04: Precio y cantidad no válidos (valores límite)

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** Escenario 3 / CAL-TVI-04, CAL-TVI-05
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | precio | 0 | rechazo |
  | precio | 0.01 | mínimo válido → se escribe |
  | precio | -1890000 | rechazo |
  | precio | "1.890.000" | separador de miles → rechazo |
  | precio | (nulo) | rechazo |
  | cantidad | 0 | rechazo |
  | cantidad | 1 | válido |
  | cantidad | "tres" | rechazo |

- **Pasos:**
  1. Procesar IB con cada valor (ajustando `total` a precio × cantidad en los válidos).
- **Resultado esperado:** rechazos con "Precio unitario no válido" o "Cantidad no válida"; los valores válidos se escriben.

### QA-05: Advertencias de contratos SECOP II

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 4 / CAL-SEC-08 a 14
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | proceso_de_compra | (nulo) | CAL-SEC-08 |
  | valor_del_contrato | "N/A" | CAL-SEC-09 → nulo |
  | valor_del_contrato | -500 | CAL-SEC-09 → nulo |
  | valor_del_contrato | 0 | CAL-SEC-10 → se guarda 0 |
  | fecha_de_fin_del_contrato | 31-12-2025 | CAL-SEC-11 → nula |
  | fecha_fin 2025-04-01, inicio 2025-04-15 | | CAL-SEC-12 |
  | codigo_de_categoria_principal | 52161505 | CAL-SEC-13, se guarda tal cual |
  | urlproceso | (nula) | CAL-SEC-14 |

- **Pasos:**
  1. Procesar CB con cada modificación.
- **Resultado esperado:** todos se escriben; `advertencias_calidad` contiene el código correspondiente; los campos indicados quedan nulos o como se señala; la ejecución cuenta 1 registro con advertencia por variante.

### QA-06: Tolerancia aritmética de la TVEC en los límites

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** Escenario 5 / CAL-TVI-08
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | precio 2150000 × 4, total | 8800000 | diferencia 200.000 > 88.000 → advertencia |
  | precio 2150000 × 4, total | 8686000 | diferencia 86.000 ≤ 86.860 → sin advertencia |
  | precio 2150000 × 4, total | 8687000 | diferencia 87.000 > 86.870 → advertencia |
  | precio 50000 × 1, total | 51000 | diferencia 1.000 = mínimo absoluto → sin advertencia |
  | precio 50000 × 1, total | 51001 | diferencia 1.001 → advertencia |

- **Pasos:**
  1. Procesar cada combinación.
- **Resultado esperado:** con advertencia, el ítem se escribe con los valores originales y CAL-TVI-08 "Total del ítem no coincide con precio × cantidad"; sin advertencia, el ítem queda limpio.

### QA-07: Ítem sin orden o sin total

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** CAL-TVI-06, CAL-TVI-07
- **Pasos:**
  1. Procesar IB con `orden` vacía; luego IB con `total = "abc"`.
- **Resultado esperado:** ambos se escriben; el primero con CAL-TVI-06; el segundo con `valor_total_item` nulo y CAL-TVI-07 (CAL-TVI-08 no se evalúa).

### QA-08: Duplicados en la misma ejecución

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** Escenario 6 / RN-06
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | CB versión 1 ultima_actualizacion | 2025-04-12T10:00:00 | |
  | CB versión 2 ultima_actualizacion | 2025-04-13T09:00:00 | más reciente → se conserva |
  | IB dos veces con igual :updated_at | 2025-06-02T08:00:00 | se conserva la última recibida |

- **Pasos:**
  1. Procesar ambas parejas en una sola ejecución.
- **Resultado esperado:** se escribe una sola versión por identificador; la descartada queda como rechazo CAL-DUP-01 "Duplicado en la ejecución".

### QA-09: Versión rechazada no borra la anterior

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 7 / RN-09
- **Precondiciones:** CB guardado.
- **Pasos:**
  1. Procesar en una incremental CB con `fecha_de_firma` nula y `objeto` cambiado.
- **Resultado esperado:** CB conserva su objeto original y demás datos; `ultima_version_rechazada = sí` y `fecha_ultimo_rechazo` = fecha de ejecución; el rechazo CAL-SEC-02 queda registrado.

### QA-10: Corrección posterior en la fuente

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 8 / RN-09
- **Pasos:**
  1. Tras QA-09, procesar CB válido con `objeto` cambiado y `ultima_actualizacion` más reciente.
- **Resultado esperado:** CB se actualiza; `ultima_version_rechazada = no`; el rechazo de QA-09 sigue en el registro.

### QA-11: Consulta del registro de rechazos con filtros y totales

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 9
- **Pasos:**
  1. Tras QA-02 a QA-04, consultar por fuente "TVEC ítems" y código CAL-TVI-04.
  2. Consultar por un rango de fechas sin registros.
- **Resultado esperado:** (1) lista solo con los rechazos CAL-TVI-04 con todos sus campos, y total por código. (2) "No hay registros de calidad para los filtros indicados."

### QA-12: El Analista no consulta el registro de rechazos

- **Tipo:** Permisos
- **Prioridad:** Media
- **Cubre:** Usuario y Contexto (permisos)
- **Pasos:**
  1. Con `analista1@piloto.test`, intentar la consulta.
- **Resultado esperado:** acceso denegado; no se devuelve ningún registro.

### QA-13: Rechazos sin datos sensibles

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 10 / RN-07
- **Pasos:**
  1. Procesar CB sin `nombre_entidad` y con `n_mero_de_cuenta = 000123456789`.
- **Resultado esperado:** el rechazo CAL-SEC-05 se registra; el valor `000123456789` no aparece en el registro de rechazos ni en logs.

### QA-14: Varias reglas incumplidas cuentan un solo rechazado

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** RN-01, RN-10
- **Pasos:**
  1. Procesar IB con `precio = 0` y `cantidad = 0`.
- **Resultado esperado:** dos entradas en el registro (CAL-TVI-04 y CAL-TVI-05); el contador de rechazados de la ejecución suma 1.

### QA-15: Reglas de órdenes TVEC

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** RN-04
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | identificador_de_la_orden | "" | CAL-TVO-01 rechazo |
  | fecha | 2025/06/01 | CAL-TVO-02 → nula |
  | total | -10 | CAL-TVO-03 → nulo |
  | entidad | (nula) | CAL-TVO-04 |

- **Pasos:**
  1. Procesar una orden con cada variante.
- **Resultado esperado:** la primera se rechaza; las demás se escriben con la advertencia correspondiente.

### QA-16: Formatos aceptados de fecha y número

- **Tipo:** Positivo
- **Prioridad:** Baja
- **Cubre:** RN-05
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | fecha_de_firma | 2025-04-10T00:00:00.000 | válido |
  | fecha_de_firma | 2025-04-10 | válido |
  | valor_del_contrato | "9800000.50" | válido |
  | valor_del_contrato | 9800000 | número JSON válido |

- **Pasos:**
  1. Procesar CB con cada valor.
- **Resultado esperado:** todos se escriben sin advertencias ni rechazos.

---

**Total de casos:** 16
