# Casos de Prueba — HU-062: Registrar la evidencia completa y reproducible de cada señal

**Historia:** [historia.md](./historia.md) | **Autor:** Juan Camilo | **Fecha:** 2026-10-02

## Alcance de las Pruebas

Se prueba el contenido obligatorio de la instantánea de evidencia por versión de señal, la fórmula con valores sustituidos, el caso de precio derivado y de ítem TVEC, la inmutabilidad, la retención por evidencia incompleta y su resolución, y la ausencia de datos personales sensibles. Queda fuera la presentación (HU-063) y la navegación (HU-064).

## Precondiciones y Datos Base

- Señal SG-1: Benchmark 1, ítem SECOP II del contrato CO1.PCCNTR.5550001 (proceso CO1.BDOS.3330001), entidad "Alcaldía de Ejemplo" NIT 800.000.001-1, proveedor "Distribuidora Ejemplo SAS", Samsung UN55CU7000, precio `explicito` 2.750.000 COP con IVA, documento DOC-77 "Oferta económica.pdf", página 4, hash de copia SHA-256 conservado, fecha de descarga 2026-09-15.
- Referencia: S7 (7 observaciones: 5 TVEC y 2 SECOP II, todas con método de adquisición "API"), mediana 2.100.000. Fechas de corte: SECOP II 2026-10-01, TVEC 2026-10-01.

## Matriz de Cobertura

| Criterio / Regla | Casos |
|---|---|
| Escenario 1 / RN-01 / RN-02 | QA-01 |
| RN-02 Benchmark 2 (métodos, manual, fecha observación) | QA-02 |
| Escenario 2 / RN-02.14 | QA-03 |
| Escenario 3 / RN-02.2, .14 | QA-04 |
| Escenario 4 / RN-03 | QA-05 |
| RN-05 "No publicado por la fuente" | QA-06 |
| Escenario 5 / RN-04 / RN-01 | QA-07 |
| Escenario 6 / RN-05 | QA-08 |
| RN-05 sin duplicar elemento | QA-09 |
| Escenario 7 / RN-05 | QA-10 |
| Escenario 8 / RN-06 | QA-11 |
| RN-04 edición prohibida | QA-12 |

---

## Casos de Prueba

### QA-01: Instantánea completa de SG-1

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 1 / RN-01 / RN-02
- **Pasos:**
  1. Generar SG-1 versión 1.
  2. Consultar la instantánea.
- **Resultado esperado:** Contiene los 15 bloques con los datos base: contrato, proceso y URL; entidad y NIT; proveedor; benchmark con mediana 2.100.000, Q1 1.950.000, Q3 2.250.000, IQR 300.000; 7 observaciones con origen; fórmula; regla de atípicos; emparejamiento y criterios; base "Completa"; métodos "API: 7" (todas las observaciones públicas llegan por la API oficial de datos abiertos); fechas de corte 2026-10-01; confianza con desglose; DOC-77, página 4, hash y fecha de descarga; parámetros y fecha-hora. Estado "Vigente".

### QA-02: Instantánea de una señal del Benchmark 2

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** RN-02
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Observaciones | Alkosto 1.799.900 (sitemap-datos estructurados, 2026-08-12), Falabella 1.899.900 (manual, 2026-09-02), Alkosto 1.849.900 (manual, 2026-08-25) | |

- **Pasos:**
  1. Generar una señal del Benchmark 2 y consultar la instantánea.
- **Resultado esperado:** Observaciones con "Retail – Alkosto"/"Retail – Falabella", indicador "Manual" en 2; métodos "sitemap-datos estructurados: 1, manual: 2"; fecha de la observación de mercado más reciente 2026-09-02.

### QA-03: Precio derivado

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 2 / RN-02.14
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Valor total del ítem | 18.400.000 COP | Hoja "Económica", celda F12 de "Anexo 3.xlsx" |
  | Cantidad | 8 | |

- **Pasos:**
  1. Generar la señal y consultar la instantánea.
- **Resultado esperado:** Indicador "Precio unitario derivado", valor total 18.400.000, cantidad 8, fórmula "18.400.000 / 8 = 2.300.000 COP", ubicación hoja "Económica" celda F12.

### QA-04: Ítem de la TVEC

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 3
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Ítem | Orden 160001, línea 2, dataset `3hdv-smhz`, corte 2026-10-01 | |

- **Pasos:**
  1. Generar la señal y consultar la instantánea.
- **Resultado esperado:** Origen del precio = registro TVEC (orden, línea, dataset, fecha de corte); sin documento ni página; la señal se publica.

### QA-05: Fórmula con valores sustituidos

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 4 / RN-03
- **Pasos:**
  1. Consultar la fórmula de SG-1.
- **Resultado esperado:** "Desviación = (2.750.000 − 2.100.000) / 2.100.000 × 100 = +31,0 %".

### QA-06: Campo no publicado por la fuente

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** RN-05
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Modelo del ítem | ausente en el documento | |
  | Modalidad | nula | |

- **Pasos:**
  1. Generar la señal.
- **Resultado esperado:** Ambos campos con "No publicado por la fuente"; la señal se publica (no son de trazabilidad crítica).

### QA-07: Inmutabilidad y versiones

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 5 / RN-01 / RN-04
- **Pasos:**
  1. Generar SG-1 versión 1.
  2. Recalcular sin cambios.
  3. Cambiar un comparable y recalcular (versión 2).
- **Resultado esperado:** Paso 2: no hay instantánea nueva. Paso 3: la versión 2 tiene instantánea nueva; la de la versión 1 es idéntica a la original.

### QA-08: Retención por falta de copia del documento

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 6 / RN-05
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Copia de DOC-77 | inexistente | |
  | Variante | ubicación (página) nula | |
  | Variante | identificador de una observación nulo | |

- **Pasos:**
  1. Generar la señal con cada variante.
  2. Consultar la lista de señales como Analista y la cola como Administrador.
- **Resultado esperado:** Estado "Retenida: evidencia incompleta – copia del documento de origen" (o "– ubicación del precio" / "– identificador de observación"); no visible para el Analista; elemento "Evidencia incompleta de señal" en la cola.

### QA-09: Sin elementos duplicados en la cola

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** RN-05
- **Pasos:**
  1. Con la señal retenida de QA-08, ejecutar dos recálculos más sin resolver la copia.
- **Resultado esperado:** Un único elemento "Evidencia incompleta de señal" para esa señal, con fecha actualizada.

### QA-10: Retención resuelta

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 7 / RN-05
- **Pasos:**
  1. Restaurar la copia de DOC-77 y recalcular el 2026-10-02.
- **Resultado esperado:** Instantánea completa, señal "Vigente" visible al Analista y elemento cerrado con "Evidencia completada en el recálculo del 2026-10-02".

### QA-11: Sin datos personales sensibles

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 8 / RN-06
- **Pasos:**
  1. Revisar el contenido completo de las instantáneas de QA-01 a QA-04.
- **Resultado esperado:** No aparecen banco, tipo o número de cuenta ni documentos de identidad de representantes, supervisores u ordenadores del gasto.

### QA-12: Ninguna instantánea es editable

- **Tipo:** Permisos
- **Prioridad:** Media
- **Cubre:** RN-04
- **Pasos:**
  1. Intentar modificar o eliminar la instantánea de SG-1 versión 1 con un Analista y con el Administrador por los medios disponibles.
- **Resultado esperado:** La operación no está disponible o es rechazada para ambos roles; la instantánea permanece igual.

---

**Total de casos:** 12
