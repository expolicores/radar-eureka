# Casos de Prueba — HU-108: Verificar trazabilidad de señales, clasificación de comparaciones y base tributaria

**Historia:** [historia.md](./historia.md) | **Autor:** Juan Camilo | **Fecha:** 2026-10-02

## Alcance de las Pruebas

Se prueban las condiciones de trazabilidad (SECOP II y TVEC), la clasificación de comparaciones y su distribución, la detección de mezcla de bases tributarias, los estados y su regla de "exactamente 0", los estados vacíos, la exportación, el historial, el lenguaje y los permisos. Queda fuera: la generación de señales y comparaciones (otra épica).

## Precondiciones y Datos Base

- Usuarios: `admin.po@prueba.co` (Administrador); `analista1@prueba.co` (Analista).
- Conjunto base: 120 señales vigentes y 1.400 comparaciones vigentes, todas conformes (310 mismo modelo, 780 producto equivalente, 310 insuficiente/no confiable).
- Documentos con copia conservada y hash correcto: DOC-30542, DOC-30610. Observaciones: OBS-7700…OBS-7790.

## Matriz de Cobertura

| Criterio / Regla | Casos |
| ----- | ----- |
| Escenario 1, RN-05 | QA-01 |
| Escenario 2, RN-02 (ubicación) | QA-02 |
| Escenario 3, RN-02 (copia y hash) | QA-03 |
| Escenario 4, RN-02 (referencias) | QA-04 |
| RN-02 (contrato inexistente, fórmula/versión, varios motivos) | QA-05 |
| Escenario 5, RN-02 (TVEC) | QA-06 |
| Escenario 6, RN-03 | QA-07 |
| Escenario 7, RN-06 | QA-08 |
| Escenario 8, Escenario 9, RN-04 (tabla de decisión) | QA-09 |
| RN-05 (exactamente 0 frente al redondeo) | QA-10 |
| RN-01 (población vigente, sin instantáneas) | QA-11 |
| Escenario 10 | QA-12 |
| Escenario 11, RN-07, RN-08 | QA-13 |
| RN-09 | QA-14 |
| Escenario 12 | QA-15 |

---

## Casos de Prueba

### QA-01: Todos los KPIs cumplen

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 1, RN-05
- **Pasos:**
  1. Con el conjunto base, calcular.
- **Resultado esperado:** trazabilidad 100,0 % (120/120) Cumple; comparabilidad 100,0 % (1.400/1.400) Cumple; base tributaria 0,0 % (0/1.400) Cumple; lista de incumplimientos vacía.

### QA-02: Falta la ubicación del precio

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 2, RN-02
- **Pasos:**
  1. Quitar la página de SEN-0042 (documento DOC-30542) y calcular.
- **Resultado esperado:** trazabilidad 99,2 % (119/120) No cumple; "SEN-0042: falta la ubicación (página, hoja o celda) del precio en el documento DOC-30542."

### QA-03: Copia ausente y hash distinto

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 3, RN-02
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ----- |
  | SEN-0050 | DOC-30611 sin copia | no trazable |
  | SEN-0051 | DOC-30700 con un byte modificado en la copia | hash distinto |

- **Pasos:**
  1. Preparar ambos casos y calcular.
- **Resultado esperado:** motivos "falta la copia conservada del documento DOC-30611." y "el hash de la copia del documento DOC-30700 no coincide con el registrado."; trazabilidad 98,3 % (118/120).

### QA-04: Observación de referencia incompleta

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 4, RN-02
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ----- |
  | OBS-7781 (retail manual) | sin evidencia adjunta | "la observación OBS-7781 no tiene evidencia adjunta." |
  | OBS-7782 (retail) | sin fecha de observación | motivo de fecha faltante |
  | OBS-7783 (TVEC) | sin identificador de origen | motivo de identificador faltante |
  | OBS-7784 | eliminada | "la observación OBS-7784 no existe." |

- **Pasos:**
  1. Asociar cada observación a una señal distinta y calcular.
- **Resultado esperado:** las 4 señales son no trazables, cada una con un motivo que nombra la observación y la condición incumplida.

### QA-05: Contrato inexistente, sin fórmula y motivos múltiples

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** RN-02
- **Pasos:**
  1. Preparar SEN-0080 con contrato inexistente y sin versión de configuración registrada; calcular.
- **Resultado esperado:** SEN-0080 aparece una vez en el conteo de no trazables y con dos motivos en la lista.

### QA-06: Señal TVEC no exige documento

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 5, RN-02
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ----- |
  | SEN-0070 | orden TVEC 98765, ítem 3, existentes; sin documento | trazable |
  | SEN-0071 | orden TVEC 98766 inexistente | no trazable |

- **Pasos:**
  1. Calcular.
- **Resultado esperado:** SEN-0070 trazable; SEN-0071 no trazable con motivo de orden inexistente.

### QA-07: Comparaciones sin clasificar o con valor no permitido

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 6, RN-03
- **Pasos:**
  1. Dejar CMP-9001 sin tipo y CMP-9002 con "similar"; calcular.
- **Resultado esperado:** comparabilidad 99,9 % (1.398/1.400) No cumple; "CMP-9001: sin clasificación." y "CMP-9002: clasificación no válida 'similar'."

### QA-08: Distribución de clasificación por benchmark

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 7, RN-06
- **Pasos:**
  1. Con el conjunto base (1.000 de compras públicas y 400 de mercado), calcular.
- **Resultado esperado:** total 22,1 % / 55,7 % / 22,1 %; además una distribución para compras públicas y otra para mercado cuyos conteos suman 1.000 y 400.

### QA-09: Tabla de decisión de base tributaria

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** Escenario 8, Escenario 9, RN-04
- **Datos de prueba:**

  | Comparación | Base precio contratado | Bases observaciones | Marcada incompleta | Incumplimiento |
  | ----- | ----- | ----- | ----- | ----- |
  | CMP-9100 | con IVA | indeterminada | no | sí |
  | CMP-9101 | con IVA | indeterminada | sí | no |
  | CMP-9102 | con IVA | con IVA | no | no |
  | CMP-9103 | sin IVA | con IVA y sin IVA | no | sí |
  | CMP-9104 | indeterminada | indeterminada | no | sí |
  | CMP-9105 | sin IVA | sin IVA | sí | no |

- **Pasos:**
  1. Calcular con estas comparaciones.
- **Resultado esperado:** 3 incumplimientos (CMP-9100, 9103, 9104), cada uno con su motivo; estado "No cumple".

### QA-10: "Cumple" exige cero aunque el porcentaje redondee a 0,0 %

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** RN-05
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ----- |
  | Comparaciones | 2.500 con 1 incumplimiento de base | 0,04 % → se muestra 0,0 % |

- **Pasos:**
  1. Calcular.
- **Resultado esperado:** base tributaria "0,0 % (1/2.500)" con estado "No cumple".

### QA-11: Solo señales y comparaciones vigentes

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** RN-01
- **Precondiciones:** SEN-0090 reemplazada por un recálculo (SEN-0091) y no trazable; una instantánea de caso con un vínculo roto.
- **Pasos:**
  1. Calcular.
- **Resultado esperado:** SEN-0090 y la instantánea no se cuentan; SEN-0091 sí.

### QA-12: Sin señales ni comparaciones

- **Tipo:** Estado UI
- **Prioridad:** Baja
- **Cubre:** Escenario 10
- **Pasos:**
  1. Con 0 señales y 0 comparaciones, calcular.
- **Resultado esperado:** trazabilidad "—" "Sin datos: no hay señales vigentes."; comparabilidad y base tributaria "—" "Sin datos: no hay comparaciones vigentes."; sin error.

### QA-13: Exportación e historial

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 11, RN-07, RN-08
- **Pasos:**
  1. Con los incumplimientos de QA-02 y QA-07, calcular y exportar.
  2. Corregir los datos, recalcular y consultar el historial.
- **Resultado esperado:** CSV UTF-8 con columnas `kpi`, `id`, `motivo` y 3 filas; historial con dos cortes; el primero conserva sus incumplimientos.

### QA-14: Lenguaje no acusatorio del reporte

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** RN-09
- **Pasos:**
  1. Generar el reporte y la exportación; buscar "sobreprecio", "corrupción", "fraude", "hallazgo fiscal".
- **Resultado esperado:** ninguno aparece.

### QA-15: Analista sin acceso

- **Tipo:** Permisos
- **Prioridad:** Alta
- **Cubre:** Escenario 12
- **Pasos:**
  1. Como `analista1@prueba.co`, calcular y consultar el historial.
- **Resultado esperado:** "Acción no permitida: esta operación requiere el rol Administrador."

---

**Total de casos:** 15
