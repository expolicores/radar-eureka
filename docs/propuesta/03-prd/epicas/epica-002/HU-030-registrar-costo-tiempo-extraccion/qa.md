# Casos de Prueba — HU-030: Registrar el costo estimado y el tiempo de procesamiento de la extracción por documento

**Historia:** [historia.md](./historia.md) | **Autor:** Juan Camilo | **Fecha:** 2026-10-02

## Alcance de las Pruebas

Se prueban el registro por solicitud, el cálculo del costo, la estimación sin tokens informados, las tarifas y su vigencia, el reparto por documento, los tiempos de preparación, las consultas por documento, proceso y mes, los nulos y los permisos. El servicio de IA se sustituye por uno simulado que informa tokens y duraciones controladas.

## Precondiciones y Datos Base

- Usuarios `admin.po@piloto.test` (Administrador) y `analista1@piloto.test` (Analista).
- Tarifas: "modelo-A" USD 2 / 10 por millón (entrada / salida), vigente desde 2026-09-01; desde 2026-11-01, USD 1 / 5. "modelo-B" sin tarifa.
- Factores: 3,5 caracteres por token; 1.500 tokens por imagen; 2.000 tokens de salida estimados. Objetivo de tiempo: 300 s.
- Proceso `CO1.BDOS.1234567` con documentos A (21.000 caracteres → 6.000), B (10.500 caracteres → 3.000) y C (2 imágenes → 3.000).

## Matriz de Cobertura

| Criterio / Regla | Casos |
| ---------------- | ----- |
| Escenario 1 / RN-01, RN-02 | QA-01 |
| Escenario 2 / RN-05 | QA-02, QA-03 |
| Escenario 3 / RN-06 | QA-04 |
| Escenario 4 / RN-02, RN-03 | QA-05 |
| Escenario 5 / RN-03 | QA-06 |
| Escenario 6 / RN-04 | QA-07 |
| Escenario 7 / RN-04 | QA-08 |
| Escenario 8 / RN-07 | QA-09 |
| Escenario 9 / RN-07 | QA-10 |
| Escenario 10 / RN-04 | QA-11 |
| RN-08 | QA-12 |
| Permisos | QA-13 |

---

## Casos de Prueba

### QA-01: Registro y costo de una solicitud exitosa

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 1 / RN-01, RN-02
- **Datos de prueba:**

  | Campo | Valor |
  | ----- | ----- |
  | Fecha | 2026-10-02 |
  | Modelo | modelo-A |
  | Tokens entrada / salida | 14.800 / 2.000 |
  | Duración | 38,0 s |

- **Pasos:**
  1. Ejecutar la extracción del proceso base.
- **Resultado esperado:** solicitud registrada con modelo, tokens, 2 imágenes, páginas de texto, inicio, fin, 38,0 s, 1 intento, "éxito" y costo 0,049600 USD (mostrado 0,0496).

### QA-02: Reparto proporcional por documento

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 2 / RN-05
- **Pasos:**
  1. Consultar los registros de A, B y C tras QA-01.
- **Resultado esperado:** A 0,024800 USD y 19,0 s; B 0,012400 USD y 9,5 s; C 0,012400 USD y 9,5 s; todos "repartido proporcionalmente"; la suma coincide con 0,049600 USD y 38,0 s.

### QA-03: Un documento y ajuste de redondeo

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** RN-05
- **Datos de prueba:**

  | Caso | Documentos (tamaño) | Costo solicitud | Esperado |
  | ---- | ------------------- | --------------- | -------- |
  | A | Un documento | 0,031000 | 100 % al documento |
  | B | X (1), Y (1), Z (1), en ese orden de prioridad | 0,000010 | X = 0,000004; Y = 0,000003; Z = 0,000003 (ajuste de redondeo en X por empate) |

- **Pasos:**
  1. Registrar cada solicitud.
- **Resultado esperado:** el de la tabla; la suma siempre coincide con el total.

### QA-04: Tiempo de preparación y total por documento

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 3 / RN-06
- **Pasos:**
  1. Consultar el documento A con lectura de formato 4,2 s y detección 1,8 s.
- **Resultado esperado:** preparación 6,0 s, IA 19,0 s, total 25,0 s.

### QA-05: Reintento con intento fallido sin tokens

- **Tipo:** Integración
- **Prioridad:** Alta
- **Cubre:** Escenario 4 / RN-02, RN-03
- **Datos de prueba:**

  | Intento | Resultado | Tokens | Duración |
  | ------- | --------- | ------ | -------- |
  | 1 | tiempo de espera | no informados | 300,0 s |
  | Espera | — | — | 2,0 s |
  | 2 | éxito | 14.800 / 2.000 | 38,0 s |

- **Pasos:**
  1. Ejecutar la extracción.
- **Resultado esperado:** 2 intentos; duración total 340,0 s; costo del intento 1 = 0 con "sin tokens informados por el servicio"; costo total 0,049600 USD.

### QA-06: Estimación por tamaño

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** Escenario 5 / RN-03
- **Pasos:**
  1. Ejecutar una solicitud exitosa sin tokens informados con 35.000 caracteres de texto y 2 imágenes.
- **Resultado esperado:** entrada estimada 13.000 (10.000 + 3.000), salida 2.000; costo 0,046000 USD marcado "estimado por tamaño".

### QA-07: Modelo sin tarifa

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 6 / RN-04
- **Pasos:**
  1. Ejecutar una solicitud con "modelo-B".
- **Resultado esperado:** costo "no estimado" con "sin tarifa configurada para el modelo modelo-B"; no aparece 0 como costo; los documentos de la solicitud también quedan "no estimado".

### QA-08: Vigencia de tarifas

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 7 / RN-04
- **Datos de prueba:**

  | Fecha de la solicitud | Tokens | Costo esperado |
  | --------------------- | ------ | -------------- |
  | 2026-10-31 23:59 | 14.800 / 2.000 | 0,049600 |
  | 2026-11-01 00:00 | 14.800 / 2.000 | 0,024800 |

- **Pasos:**
  1. Registrar ambas solicitudes y luego consultar la de octubre.
- **Resultado esperado:** el de la tabla; la de octubre no cambió al entrar la nueva tarifa.

### QA-09: Resumen mensual

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 8 / RN-07
- **Datos de prueba:**

  | Campo | Valor |
  | ----- | ----- |
  | Documentos con IA en octubre | 280 (de 40 procesos) |
  | Documentos "no estimado" | 5 |
  | Documentos con tiempo total > 300 s | 3 |

- **Pasos:**
  1. Cargar los registros de octubre y consultar el resumen.
- **Resultado esperado:** costo total del mes; promedio y mediana por documento (sobre los 275 con costo) y por proceso; 5 "no estimado"; mediana y p95 del tiempo total por documento; 3 documentos por encima del objetivo.

### QA-10: Mes sin extracciones

- **Tipo:** Estado UI
- **Prioridad:** Baja
- **Cubre:** Escenario 9 / RN-07
- **Pasos:**
  1. Consultar el resumen de un mes sin solicitudes.
- **Resultado esperado:** 0,00 USD, 0 documentos, "sin extracciones en el periodo".

### QA-11: Tarifa inválida

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** Escenario 10 / RN-04
- **Datos de prueba:**

  | Tarifa entrada | Tarifa salida | Vigencia | Resultado |
  | -------------- | ------------- | -------- | --------- |
  | -1 | 10 | 2026-12-01 | rechazada |
  | 2 | 10 | (vacía) | rechazada |
  | 0 | 0 | 2026-12-01 | aceptada |
  | 2,12345 | 10 | 2026-12-01 | rechazada (más de 4 decimales) |

- **Pasos:**
  1. Como Administrador, guardar cada tarifa para "modelo-C".
- **Resultado esperado:** el de la tabla; los rechazos muestran "La tarifa debe ser un número mayor o igual que 0 y tener fecha de inicio de vigencia".

### QA-12: Documentos sin extracción con IA

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** RN-08
- **Pasos:**
  1. Consultar un documento preparado (5,0 s de preparación) de un proceso pendiente por IA desactivada.
  2. Consultar el promedio de costo del mes.
- **Resultado esperado:** costo de IA nulo, tiempo de preparación 5,0 s; el documento no cuenta en el promedio de costo.

### QA-13: Permisos

- **Tipo:** Permisos
- **Prioridad:** Media
- **Cubre:** Permisos requeridos
- **Pasos:**
  1. Como `analista1@piloto.test`, consultar el resumen mensual y registrar una tarifa.
- **Resultado esperado:** acceso denegado en ambas operaciones.

---

**Total de casos:** 13
