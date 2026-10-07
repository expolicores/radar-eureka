# Casos de Prueba — HU-101: Configurar y versionar los parámetros de comparación y señal

**Historia:** [historia.md](./historia.md) | **Autor:** Juan Camilo | **Fecha:** 2026-10-02

## Alcance de las Pruebas

Se prueban la consulta, el cambio, la validación (rango, formato, consistencia, motivo), el versionado, la concurrencia, la restauración, las consultas históricas, la no retroactividad, la auditoría y los permisos de los 10 parámetros analíticos. Queda fuera: la lógica de cálculo de benchmarks y señales (otra épica) y los parámetros operativos (HU-102).

## Precondiciones y Datos Base

- Usuarios: `admin.po@prueba.co` (Administrador); `analista1@prueba.co` (Analista).
- Versiones semilla: v1 (sistema, vigente desde 2026-09-01 00:00, configuración inicial); v2 (2026-09-10 09:00); v3 (2026-09-20 16:30, igual a la inicial). Vigente: v3.
- Valores de v3: ventana_b1_meses 6, ventana_b1_ampliada_meses 12, ventana_b2_dias 30, minimo_obs_b1 5, minimo_obs_b2 3, minimo_fuentes_b2 2, minimo_obs_atipicos 5, multiplicador_iqr 1,50, umbral_mismo_modelo_pct 30,0, umbral_equivalente_pct 50,0.
- Motivo válido de referencia: "Recalibración con 40 señales validadas en septiembre".

## Matriz de Cobertura

| Criterio / Regla | Casos |
| ----- | ----- |
| Escenario 1, RN-01 | QA-01 |
| Escenario 2, RN-05, RN-11, RN-12 | QA-02 |
| Escenario 3, RN-04 | QA-03 |
| Escenario 4, RN-01 (rangos y formatos, enteros) | QA-04 |
| RN-01 (decimales, separador y precisión) | QA-05 |
| Escenario 5, RN-04 | QA-06 |
| Escenario 6, RN-02 | QA-07 |
| Escenario 7, RN-03 | QA-08 |
| Escenario 8, RN-04 | QA-09 |
| Escenario 9, RN-07 | QA-10 |
| Escenario 10 | QA-11 |
| Escenario 11, RN-06 | QA-12 |
| Escenario 12, RN-10 | QA-13 |
| Escenario 13, RN-10 | QA-14 |
| Escenario 14, RN-09 | QA-15 |
| Escenario 15, RN-08 | QA-16 |
| Escenario 16, RN-11 | QA-17 |
| Escenario 17 | QA-18 |
| RN-13 (lenguaje no acusatorio) | QA-19 |

---

## Casos de Prueba

### QA-01: Consultar la configuración vigente

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 1, RN-01
- **Pasos:**
  1. Como Administrador, consultar la configuración analítica.
- **Resultado esperado:** versión 3, vigencia "2026-09-20 16:30", usuario, y los 10 parámetros con nombre, valor, unidad, rango y configuración inicial según la tabla de RN-01.

### QA-02: Cambio válido de un parámetro crea versión y auditoría

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 2, RN-05, RN-11, RN-12
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ----- |
  | umbral_mismo_modelo_pct | 25 | antes 30,0 |
  | Versión de partida | 3 | — |

- **Pasos:**
  1. Enviar el cambio con el motivo válido.
  2. Consultar la vigente y el log de auditoría.
- **Resultado esperado:** "Configuración guardada como versión 4."; v4 tiene los 9 valores restantes iguales a v3 y umbral 25,0; un evento "Cambio de configuración" con parámetro, anterior 30,0, nuevo 25,0, versión 4, usuario y motivo.

### QA-03: Cambio múltiple crea una sola versión

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 3, RN-04
- **Pasos:**
  1. Desde v4, enviar ventana_b1_meses = 4 y minimo_obs_b1 = 7 con motivo válido.
- **Resultado esperado:** se crea solo v5 con ambos cambios; 2 eventos de auditoría con versión 5.

### QA-04: Límites y formatos de parámetros enteros

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** Escenario 4, RN-01
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ----- |
  | ventana_b2_dias | 1 / 365 | aceptados |
  | ventana_b2_dias | 0 / 366 / 400 | rechazados |
  | ventana_b2_dias | treinta / (vacío) / 30,5 | rechazados |
  | minimo_obs_atipicos | 4 / 3 | 4 aceptado; 3 rechazado |
  | minimo_fuentes_b2 | 11 | rechazado |

- **Pasos:**
  1. Enviar cada valor por separado con motivo válido (desde la versión vigente).
- **Resultado esperado:** los aceptados crean versión; los rechazados devuelven "El valor de {nombre} debe ser un número entero entre {mín} y {máx}." (ej. "El valor de ventana_b2_dias debe ser un número entero entre 1 y 365.") y no crean versión.

### QA-05: Decimales con punto o coma y precisión máxima

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** RN-01
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ----- |
  | multiplicador_iqr | 0,50 / 5.00 / 2,25 | aceptados |
  | multiplicador_iqr | 0,49 / 5,01 / 1,505 | rechazados |
  | umbral_equivalente_pct | 0,0 / 500 / 45,5 | aceptados |
  | umbral_equivalente_pct | 500,1 / 45,55 / -1 | rechazados |

- **Pasos:**
  1. Enviar cada valor por separado con motivo válido.
- **Resultado esperado:** los aceptados se guardan con el valor numérico correcto independientemente del separador; los rechazados devuelven "El valor de {nombre} debe ser un número decimal entre {mín} y {máx}."

### QA-06: Un error en un cambio múltiple rechaza todo

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 5, RN-04
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ----- |
  | ventana_b2_dias | 45 | válido |
  | minimo_obs_b2 | 4 | válido |
  | multiplicador_iqr | 9 | inválido |

- **Pasos:**
  1. Enviar los tres cambios juntos.
- **Resultado esperado:** no se crea versión; la vigente conserva 30, 3 y 1,50; se devuelve el mensaje de multiplicador_iqr.

### QA-07: Consistencia entre parámetros

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 6, RN-02
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ----- |
  | ventana_b1_ampliada_meses | 5 (base 6) | rechazado |
  | ventana_b1_ampliada_meses | 6 (base 6) | aceptado (igual) |
  | minimo_fuentes_b2 | 4 (obs 3) | rechazado |
  | minimo_fuentes_b2 = 4 y minimo_obs_b2 = 4 | juntos | aceptado |
  | ventana_b1_meses | 13 (ampliada 12) | rechazado |

- **Pasos:**
  1. Enviar cada combinación por separado.
- **Resultado esperado:** rechazos con "La ventana ampliada del Benchmark 1 ({x}) no puede ser menor que la ventana base ({y})." o "El mínimo de fuentes del Benchmark 2 ({x}) no puede ser mayor que el mínimo de observaciones del Benchmark 2 ({y})."; las combinaciones válidas crean versión.

### QA-08: Advertencia no bloqueante de umbrales

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 7, RN-03
- **Pasos:**
  1. Con umbral mismo modelo 30,0, fijar umbral_equivalente_pct = 20.
- **Resultado esperado:** se crea la nueva versión y la respuesta incluye "Advertencia: el umbral de producto equivalente (20 %) es menor que el de mismo modelo (30 %)."

### QA-09: Motivo obligatorio y su longitud

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** Escenario 8, RN-04
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ----- |
  | Motivo | (vacío) | rechazado |
  | Motivo | `Ajuste B1` (9) | rechazado |
  | Motivo | `  Ajuste B1x  ` (10 efectivos) | aceptado |
  | Motivo | 500 / 501 caracteres | aceptado / rechazado |

- **Pasos:**
  1. Enviar un cambio válido con cada motivo.
- **Resultado esperado:** rechazos con "Debe indicar un motivo del cambio de 10 a 500 caracteres."; los aceptados crean versión.

### QA-10: Cambio sin diferencias

- **Tipo:** Negativo
- **Prioridad:** Baja
- **Cubre:** Escenario 9, RN-07
- **Pasos:**
  1. Enviar umbral_equivalente_pct = 50 (vigente 50,0).
- **Resultado esperado:** "No hay cambios respecto a la versión vigente."; no se crea versión ni auditoría.

### QA-11: Parámetro inexistente

- **Tipo:** Negativo
- **Prioridad:** Baja
- **Cubre:** Escenario 10
- **Pasos:**
  1. Enviar `umbral_sobreprecio` = 20.
- **Resultado esperado:** "El parámetro 'umbral_sobreprecio' no existe."; no se crea versión.

### QA-12: Conflicto por cambio concurrente

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** Escenario 11, RN-06
- **Pasos:**
  1. Sesión A y sesión B consultan la vigente (v5).
  2. B guarda un cambio (crea v6).
  3. A guarda un cambio indicando versión de partida 5.
- **Resultado esperado:** A recibe "La configuración cambió (versión vigente 6) desde que la consultó. Vuelva a consultarla y repita el cambio."; no se crea v7.

### QA-13: Historial y versión vigente en una fecha

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 12, RN-10
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ----- |
  | Fecha | 2026-09-15 14:00 | devuelve v2 |
  | Fecha | 2026-09-20 16:30 | límite exacto: devuelve v3 |
  | Fecha | 2026-09-20 16:29 | devuelve v2 |

- **Pasos:**
  1. Consultar el historial.
  2. Consultar la versión vigente en cada fecha.
- **Resultado esperado:** historial de la más reciente a la más antigua con número, vigencia, usuario, motivo y cambios anterior → nuevo; cada fecha devuelve la versión indicada con todos sus valores.

### QA-14: Fecha anterior a la primera versión

- **Tipo:** Borde
- **Prioridad:** Baja
- **Cubre:** Escenario 13, RN-10
- **Pasos:**
  1. Consultar la vigente en 2026-08-31 23:59.
- **Resultado esperado:** "No existía configuración vigente en 2026-08-31 23:59; la primera versión rige desde 2026-09-01 00:00."

### QA-15: Restaurar una versión anterior y versión inexistente

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 14, RN-09
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ----- |
  | Versión a restaurar | 3 (vigente 6) | crea v7 |
  | Versión a restaurar | 99 | inexistente |

- **Pasos:**
  1. Restaurar la versión 3 con motivo "Volver a la configuración inicial del piloto".
  2. Restaurar la versión 99.
- **Resultado esperado:** paso 1: "Configuración guardada como versión 7 (restaurada desde la versión 3)."; v7 = valores de v3; v3 sin cambios; un evento de auditoría por parámetro que difiere entre v6 y v7. Paso 2: "La versión 99 no existe."

### QA-16: Un cambio no altera cálculos ya hechos ni en curso

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 15, RN-08
- **Precondiciones:** señal `SEN-0101` calculada con v3; un cálculo de benchmark iniciado con v3 y aún en curso.
- **Pasos:**
  1. Crear una nueva versión con umbral_mismo_modelo_pct = 20.
  2. Dejar terminar el cálculo en curso e iniciar uno nuevo.
- **Resultado esperado:** `SEN-0101` conserva su resultado y su versión 3; el cálculo en curso registra versión 3; el nuevo cálculo registra la versión nueva; no hubo redespliegue.

### QA-17: Falla de auditoría impide crear la versión

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** Escenario 16, RN-11
- **Precondiciones:** log de auditoría no disponible (simulado).
- **Pasos:**
  1. Enviar un cambio válido.
- **Resultado esperado:** "No fue posible registrar la auditoría; el cambio no se aplicó. Intente de nuevo."; la versión vigente no cambia.

### QA-18: Analista no puede consultar ni cambiar

- **Tipo:** Permisos
- **Prioridad:** Alta
- **Cubre:** Escenario 17
- **Pasos:**
  1. Como `analista1@prueba.co`, consultar la configuración.
  2. Como `analista1@prueba.co`, enviar un cambio válido.
- **Resultado esperado:** ambos devuelven "Acción no permitida: esta operación requiere el rol Administrador."; no hay versión nueva.

### QA-19: Sin términos acusatorios en nombres, descripciones y mensajes

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** RN-13
- **Pasos:**
  1. Obtener la consulta de configuración y todos los mensajes de RN-12.
  2. Buscar los términos "sobreprecio", "corrupción", "fraude" y "hallazgo fiscal" (sin distinguir mayúsculas ni tildes).
- **Resultado esperado:** ninguno aparece salvo como eco del nombre inválido enviado por el usuario en el mensaje de parámetro inexistente; los parámetros de señal se describen como "señal que merece revisión".

---

**Total de casos:** 19
