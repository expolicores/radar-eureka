# Casos de Prueba — HU-063: Ver el detalle de una señal con su comparación, su evidencia y la advertencia de no conclusión

**Historia:** [historia.md](./historia.md) | **Autor:** Juan Camilo | **Fecha:** 2026-10-02

## Alcance de las Pruebas

Se prueba la vista de detalle de la señal: bloques y orden, advertencia, origen de observaciones, etiquetas de evidencia limitada y no disponible, marcas de calidad, versiones y no vigencia, estados de carga, error e inexistencia, autenticación, formatos, rendimiento y accesibilidad. Queda fuera el comportamiento de "Ver evidencia" (HU-064), "Calificar señal" (HU-066) y "Reportar un error" (HU-067).

## Precondiciones y Datos Base

- Usuarios: Analista "analista.piloto1" y Administrador "admin.po".
- **SG-1:** vigente, Benchmark 1, ítem del contrato CO1.PCCNTR.5550001, Samsung UN55CU7000, precio $ 2.750.000, referencia $ 2.100.000 (7 observaciones: 5 TVEC, 2 SECOP II), desviación +31,0 %, confianza 100 "Alta", corte 01/10/2026; Benchmark 2 del ítem "No disponible / evidencia insuficiente – sin observaciones de mercado en la ventana (±30 días)".
- **SG-2:** vigente, Benchmark 2, 2 observaciones (1 Alkosto por sitemap-datos estructurados, 1 Falabella manual), "Referencia de mercado disponible – evidencia limitada (2 observaciones de 2 fuentes; mínimo 3 de 2 fuentes)".
- **SG-3:** "No vigente", versiones 1 (15/09/2026) y 2 (01/10/2026).
- **SG-4:** "Retenida: evidencia incompleta".

## Matriz de Cobertura

| Criterio / Regla | Casos |
|---|---|
| Escenario 1 / RN-01 / RN-03 | QA-01 |
| Escenario 2 / RN-02 | QA-02 |
| Escenario 3 / RN-03.5 | QA-03 |
| Escenario 4 / RN-05 | QA-04 |
| Escenario 5 / RN-03.6 | QA-05 |
| Escenario 6 | QA-06 |
| Escenario 7 / RN-07 | QA-07 |
| Escenario 8 / RN-06 | QA-08 |
| Escenario 9 / RN-07 | QA-09 |
| Escenario 10 | QA-10 |
| Permisos Administrador | QA-11 |
| RN-04 formatos | QA-12 |
| RN-08 rendimiento | QA-13 |
| RN-08 responsive y accesibilidad | QA-14 |

---

## Casos de Prueba

### QA-01: Detalle completo y orden de bloques

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 1 / RN-01 / RN-03
- **Pasos:**
  1. Iniciar sesión como "analista.piloto1" y abrir SG-1.
- **Resultado esperado:** Se ven los 8 bloques en orden; encabezado "Señal que merece revisión", "Benchmark 1 – Contratación pública", "+31,0 %", "Alta (100)", corte 01/10/2026; comparación con fórmula "Desviación = (2.750.000 − 2.100.000) / 2.100.000 × 100 = +31,0 %", regla de atípicos, Q1, mediana, Q3, máximo y gráfica de distribución con la posición del precio contratado.

### QA-02: Advertencia exacta y no ocultable

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 2 / RN-02
- **Pasos:**
  1. Abrir SG-1, SG-2 y la versión 1 de SG-3.
  2. Buscar una opción para cerrar la advertencia.
- **Resultado esperado:** En las tres vistas el primer bloque es el texto exacto de RN-02; no existe opción para cerrarlo.

### QA-03: Origen y datos de cada observación

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 3 / RN-03.5
- **Pasos:**
  1. Abrir SG-1 y SG-2 y revisar la tabla de observaciones.
- **Resultado esperado:** SG-1: filas "Contratación pública – TVEC" y "– SECOP II"; SG-2: "Retail – Alkosto", "Retail – Falabella" con etiqueta "Manual" en la manual; todas con fecha, producto, precio original, precio comparado, emparejamiento, método y "Ver evidencia"; orden por precio comparado ascendente.

### QA-04: Evidencia limitada sin "precio de mercado"

- **Tipo:** Estado UI
- **Prioridad:** Alta
- **Cubre:** Escenario 4 / RN-05
- **Pasos:**
  1. Abrir SG-2 y buscar en el texto de la página "precio de mercado".
- **Resultado esperado:** Etiqueta de evidencia limitada, texto "Evidencia limitada: no es una referencia estadística robusta", sin cuartiles ni gráfica de cuartiles; no aparece "precio de mercado".

### QA-05: Otro benchmark no disponible

- **Tipo:** Estado UI
- **Prioridad:** Alta
- **Cubre:** Escenario 5
- **Pasos:**
  1. Abrir SG-1.
- **Resultado esperado:** Bloque "Otro benchmark del ítem" con "Benchmark 2 – Mercado: No disponible / evidencia insuficiente – sin observaciones de mercado en la ventana (±30 días)"; el resto del Benchmark 1 completo.

### QA-06: Marcas de base tributaria y precio derivado

- **Tipo:** Estado UI
- **Prioridad:** Alta
- **Cubre:** Escenario 6
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Señal SG-5 | Base "Incompleta / no confiable: base tributaria indeterminada en 6 de 8 observaciones", precio derivado 18.400.000 / 8 | Confianza 45 "Baja" con tope |

- **Pasos:**
  1. Abrir SG-5.
- **Resultado esperado:** Se ven el estado tributario, "Precio unitario derivado: valor total / cantidad", nivel "Baja" y la nota "Nivel limitado a Baja: comparación incompleta por base tributaria".

### QA-07: Señal no vigente y versión anterior

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 7 / RN-07
- **Pasos:**
  1. Abrir SG-3.
  2. Seleccionar la versión 1 en el historial.
- **Resultado esperado:** Franja "Esta señal ya no está vigente: {motivo}"; al elegir la versión 1: "Estás viendo la versión 1 del 15/09/2026; no es la versión más reciente" y los datos de su instantánea.

### QA-08: Señal inexistente o retenida

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 8 / RN-06
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Identificador | "SG-999999" | No existe |
  | Identificador | SG-4 | Retenida |

- **Pasos:**
  1. Abrir cada identificador.
  2. Pulsar "Volver a la lista de señales".
- **Resultado esperado:** Mensaje "La señal no existe o no está disponible." en ambos casos; el botón lleva a la lista de señales.

### QA-09: Carga y error

- **Tipo:** Estado UI
- **Prioridad:** Media
- **Cubre:** Escenario 9 / RN-07
- **Pasos:**
  1. Abrir SG-1 con respuesta lenta simulada.
  2. Simular falla de carga y pulsar "Reintentar" tras restaurar el servicio.
- **Resultado esperado:** "Cargando señal…" durante la carga; "No pudimos cargar la señal. Intenta de nuevo." con "Reintentar"; al reintentar se muestra el detalle.

### QA-10: Acceso sin sesión

- **Tipo:** Permisos
- **Prioridad:** Alta
- **Cubre:** Escenario 10
- **Pasos:**
  1. Sin sesión, abrir el enlace de SG-1.
  2. Iniciar sesión como "analista.piloto1".
- **Resultado esperado:** Redirección al inicio de sesión y, tras ingresar, se muestra el detalle de SG-1.

### QA-11: Consulta por el Administrador

- **Tipo:** Permisos
- **Prioridad:** Baja
- **Cubre:** Permisos requeridos
- **Pasos:**
  1. Abrir SG-1 como "admin.po".
- **Resultado esperado:** Se muestra el mismo detalle.

### QA-12: Formatos de presentación

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** RN-04
- **Pasos:**
  1. Revisar montos, porcentajes, fechas y campos vacíos en SG-1 (modelo de una observación sin dato).
- **Resultado esperado:** "$ 2.750.000", "+31,0 %", "01/10/2026" y "No publicado por la fuente" en el campo vacío.

### QA-13: Tiempo de carga

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** RN-08
- **Pasos:**
  1. Con 20 usuarios concurrentes simulados abriendo señales, medir la carga del detalle sobre 100 aperturas.
- **Resultado esperado:** p95 ≤ 3 s.

### QA-14: Vista en tablet y móvil, y accesibilidad

- **Tipo:** Estado UI
- **Prioridad:** Media
- **Cubre:** RN-08
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Anchos | 1366, 768 y 360 px | |

- **Pasos:**
  1. Abrir SG-1 en cada ancho.
  2. Recorrer la vista solo con teclado y medir contraste.
- **Resultado esperado:** Los 8 bloques están presentes en todos los anchos (tabla con desplazamiento horizontal en 360 px); todos los enlaces y botones son alcanzables por teclado; contraste conforme a WCAG 2.1 AA.

---

**Total de casos:** 14
