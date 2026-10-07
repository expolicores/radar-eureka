# Casos de Prueba — HU-064: Navegar desde la señal hasta el contrato, el documento y la página de origen, y cada observación de referencia

**Historia:** [historia.md](./historia.md) | **Autor:** Juan Camilo | **Fecha:** 2026-10-02

## Alcance de las Pruebas

Se prueba la navegación desde el detalle de la señal a la evidencia del precio contratado (PDF, hoja de cálculo, comprimido, TVEC), al contrato y a la fuente oficial, y a la evidencia de cada observación (pública y retail), con la versión correcta, los errores, el número de clics y el regreso. Queda fuera la ficha del contrato en sí.

## Precondiciones y Datos Base

- Analista "analista.piloto1" con sesión iniciada.
- **SG-1** (versión 1): precio de "Oferta económica.pdf" (DOC-77), página 4, hash A1B2…, descargado el 15/09/2026, URL original de SECOP II; contrato CO1.PCCNTR.5550001 con URL pública del proceso.
- **SG-6:** precio derivado de "Anexo 3.xlsx", hoja "Económica", F12 = 18.400.000 y D12 = 8.
- **SG-7:** precio de "Cotizacion.pdf" dentro de "Anexos.zip", página 2.
- **SG-8:** ítem TVEC orden 160001, línea 2, dataset `3hdv-smhz`, corte 01/10/2026.
- **SG-2:** observación Alkosto manual (captura PNG adjunta, precio efectivo $ 1.799.900, precio anterior $ 2.199.900, 12/08/2026).

## Matriz de Cobertura

| Criterio / Regla | Casos |
|---|---|
| Escenario 1 / RN-03 / RN-06 | QA-01 |
| Escenario 2 / RN-02 | QA-02 |
| Escenario 3 / RN-02 | QA-03 |
| Escenario 4 / RN-04 | QA-04 |
| Escenario 5 | QA-05 |
| Escenario 6 / RN-05 | QA-06 |
| Escenario 7 | QA-07 |
| RN-01 versión por hash | QA-08 |
| Escenario 8 / RN-07 | QA-09 |
| RN-07 evidencia retail no disponible | QA-10 |
| Escenario 9 / RN-02 | QA-11 |
| Escenario 10 | QA-12 |
| Permisos sin sesión | QA-13 |
| RN-08 rendimiento | QA-14 |

---

## Casos de Prueba

### QA-01: Documento en la página exacta en 2 clics

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 1 / RN-03 / RN-06
- **Pasos:**
  1. Desde la lista de señales, abrir SG-1 (clic 1).
  2. Pulsar "Ver evidencia" junto al precio contratado (clic 2).
- **Resultado esperado:** Visor de la copia conservada en la página 4; panel con "Oferta económica.pdf", "Página 4", 15/09/2026, hash A1B2…, enlace a la URL original y "Estás viendo la copia conservada por el sistema el 15/09/2026"; total 2 clics.

### QA-02: Evidencia en hoja de cálculo

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 2 / RN-02
- **Pasos:**
  1. Abrir SG-6 y pulsar "Ver evidencia".
  2. Pulsar "Descargar copia conservada".
- **Resultado esperado:** Panel con "Hoja Económica, celdas F12 y D12" y fórmula "18.400.000 / 8 = 2.300.000 COP"; se descarga la copia conservada de "Anexo 3.xlsx".

### QA-03: Archivo dentro de un comprimido

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 3 / RN-02
- **Pasos:**
  1. Abrir SG-7 y pulsar "Ver evidencia".
- **Resultado esperado:** Ruta "Anexos.zip › Cotizacion.pdf" y visor en la página 2.

### QA-04: Registro TVEC

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 4 / RN-04
- **Pasos:**
  1. Abrir SG-8 y pulsar "Ver evidencia".
- **Resultado esperado:** Registro con orden 160001, línea 2, descripción, precio, cantidad, total, fecha, entidad, dataset `3hdv-smhz`, corte 01/10/2026 y enlace "Ver en datos abiertos".

### QA-05: Ficha del contrato y fuente oficial

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 5
- **Pasos:**
  1. En SG-1 pulsar "Ver ficha del contrato".
  2. Volver y pulsar "Ver en la fuente oficial".
- **Resultado esperado:** (1) Se abre la ficha del contrato CO1.PCCNTR.5550001. (2) Se abre la URL pública del proceso en una pestaña nueva.

### QA-06: Evidencia de observación retail manual

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 6 / RN-05
- **Pasos:**
  1. Abrir SG-2 y pulsar "Ver evidencia" en la fila de Alkosto.
- **Resultado esperado:** Tienda Alkosto, producto, SKU, "$ 1.799.900", "Precio anterior – solo evidencia: $ 2.199.900", 12/08/2026, método "Manual", etiqueta "Observación manual", captura visible, enlace a la tienda y el aviso "La página de la tienda puede haber cambiado desde el 12/08/2026; la evidencia conservada es la de esa fecha"; no aparece el usuario que la registró.

### QA-07: Evidencia de una observación pública extraída

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 7
- **Pasos:**
  1. En SG-1 pulsar "Ver evidencia" en una observación SECOP II (CO1.PCCNTR.5550100, página 3).
- **Resultado esperado:** Visor de la copia conservada de su documento en la página 3 con el panel completo.

### QA-08: Se muestra la copia del hash de la instantánea

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** RN-01
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | DOC-77 copia nueva | hash C3D4… descargada el 30/09/2026 | Posterior a la versión 1 |

- **Pasos:**
  1. Abrir la versión 1 de SG-1 y "Ver evidencia".
- **Resultado esperado:** Se muestra la copia con hash A1B2… del 15/09/2026, no la del 30/09/2026.

### QA-09: Copia no disponible

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 8 / RN-07
- **Pasos:**
  1. Simular que la copia de DOC-77 no puede abrirse y pulsar "Ver evidencia".
  2. Consultar el log.
- **Resultado esperado:** Mensaje "La copia del documento no está disponible en este momento. Puedes consultar el original en la fuente oficial." con enlace a la URL original; el log registra SG-1, DOC-77 y la fecha-hora.

### QA-10: Evidencia retail adjunta no disponible

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** RN-07
- **Pasos:**
  1. Simular falla de la captura adjunta de la observación Alkosto y abrir su evidencia.
- **Resultado esperado:** "La evidencia adjunta no está disponible en este momento." y el resto de datos de la observación visibles.

### QA-11: Formato no visualizable

- **Tipo:** Borde
- **Prioridad:** Baja
- **Cubre:** Escenario 9 / RN-02
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Documento | "Propuesta.doc" (formato antiguo), página 4 | |

- **Pasos:**
  1. Abrir la evidencia.
- **Resultado esperado:** Panel con "Página 4" y botón "Descargar copia conservada".

### QA-12: Volver a la misma versión

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 10
- **Pasos:**
  1. Abrir la versión 1 de SG-3, "Ver evidencia" y luego "Volver a la señal".
- **Resultado esperado:** Se muestra el detalle de SG-3 en la versión 1 con su franja de versión anterior.

### QA-13: Enlace de evidencia sin sesión

- **Tipo:** Permisos
- **Prioridad:** Alta
- **Cubre:** Permisos requeridos
- **Pasos:**
  1. Sin sesión, abrir el enlace directo de la evidencia de SG-1.
  2. Iniciar sesión.
- **Resultado esperado:** Redirección al inicio de sesión y, luego, a la evidencia solicitada.

### QA-14: Tiempo de apertura del panel

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** RN-08
- **Pasos:**
  1. Medir 100 aperturas de evidencia con 20 usuarios concurrentes simulados.
- **Resultado esperado:** El panel aparece en ≤ 3 s (p95); mientras el documento termina de cargar se ve "Cargando documento…".

---

**Total de casos:** 14
