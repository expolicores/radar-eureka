# Casos de Prueba — HU-075: Filtrar y ordenar la lista de señales que merecen revisión

**Historia:** [historia.md](./historia.md) | **Autor:** Juan Camilo | **Fecha:** 2026-10-02

## Alcance de las Pruebas

Se prueban los filtros y el orden configurable de la vista "Señales": cada criterio evaluado sobre el contrato u orden del ítem, validaciones, combinación, ocultamiento y no búsqueda del documento de proveedores persona natural, estado sin resultados, limpieza, vuelta a la prioridad por defecto, persistencia, lenguaje, tiempos y accesibilidad. Quedan fuera el contenido base de la lista (HU-074) y el cálculo de señales.

## Precondiciones y Datos Base

- **Usuario:** `analista.piloto1@prueba.co` (Analista). **Fecha de referencia:** 02/10/2026.
- **Señales vigentes semilla:**

  | Señal | Fuente / Contrato | Entidad (NIT) | Proveedor | Modalidad | Departamento / Municipio | Fecha | Valor contrato | UNSPSC | Precio unitario | Desviación | Confianza |
  | ----- | ----------------- | ------------- | --------- | --------- | ------------------------ | ----- | -------------- | ------ | --------------- | ---------- | --------- |
  | S1 | SECOP II CO1.PCCNTR.6001 | Gobernación de Santander (890201235) | Distribuciones Andinas S.A.S. | Mínima cuantía | Santander / Bucaramanga | 15/09/2026 | $ 22.900.000 | 52161505 | $ 3.900.000 | +35,2 % | Alta |
  | S2 | TVEC 98765 | Alcaldía de Bucaramanga (890201222) | Comercializadora Nova S.A.S. | (no publicada) | Santander / Bucaramanga | 01/08/2026 | $ 12.480.000 | — | $ 2.600.000 | +52,9 % | Media |
  | S3 | SECOP II CO1.PCCNTR.6003 | Alcaldía de Tunja (891800846) | Distribuciones Andinas S.A.S. | Subasta inversa | Boyacá / Tunja | 10/03/2025 | $ 50.000.000 | 52161505 | $ 2.950.000 | +55,3 % | Media |
  | S4 | SECOP II CO1.PCCNTR.6004 | Hospital San Rafael E.S.E. (820000142) | (sin dato) | Régimen especial | Santander / (sin dato) | 02/10/2025 | (sin valor) | 43211500 | $ 1.300.000 | +31,0 % | Baja |

- Los proveedores de S1 a S3 son personas jurídicas con tipo de documento NIT.
- **Señales complementarias (solo QA-17 y QA-18):** se agregan a las anteriores; no alteran los resultados de los demás casos.

  | Señal | Fuente / Contrato | Proveedor | Tipo de documento (`tipodocproveedor`) | Documento almacenado | Departamento |
  | ----- | ----------------- | --------- | -------------------------------------- | -------------------- | ------------ |
  | S5 | SECOP II CO1.PCCNTR.6005 | María Fernanda Ríos Peña | Cédula de Ciudadanía | 1012345678 | Boyacá |
  | S6 | SECOP II CO1.PCCNTR.6006 | Juan Pablo Ortiz Gil | (vacío) | 79555123 | Boyacá |
  | S7 | SECOP II CO1.PCCNTR.6007 | Peter Smith | Pasaporte | AB123456 | Boyacá |

## Matriz de Cobertura

| Criterio / Regla | Casos |
| ---------------- | ----- |
| Escenario 1 / RN-04 / RN-07 / RN-11 | QA-01 |
| Escenario 2 / RN-02 / RN-03 | QA-02, QA-03 |
| Escenario 3 / RN-05 / RN-06 | QA-04 |
| Escenario 4 / RN-08 | QA-05 |
| Escenario 5 / RN-10 | QA-06 |
| Escenario 6 / RN-11 | QA-07 |
| Escenario 7 | QA-08 |
| Escenario 8 | QA-09 |
| Escenario 9 | QA-10 |
| Escenario 10 / RN-12 | QA-11 |
| RN-01 combinación | QA-12 |
| RN-09 nulos | QA-13 |
| RN-13 | QA-14 |
| RN-14 | QA-15 |
| RN-15 | QA-16 |
| Escenario 11 / RN-02 / RN-16 | QA-17 |
| Escenario 12 / RN-02 / RN-16 / RN-12 | QA-18 |

---

## Casos de Prueba

### QA-01: Recorrido principal: departamento, últimos 12 meses y desviación

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 1 / RN-04 / RN-07 / RN-11
- **Pasos:**
  1. Marcar "Santander", elegir "Últimos 12 meses" y ordenar por "Desviación — Mayor a menor".
- **Resultado esperado:** rango 03/10/2025 – 02/10/2026; lista S2 (+52,9 %), S1 (+35,2 %); S4 (02/10/2025) queda fuera por fecha y S3 por departamento; etiquetas "Departamento: Santander" y "Fechas: Últimos 12 meses (03/10/2025 – 02/10/2026)"; página 1.

### QA-02: Filtrar por entidad (nombre y NIT) y proveedor

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 2 / RN-02
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Entidad | bucaramanga | nombre parcial |
  | Entidad | 891.800.846-1 | NIT con formato |
  | Proveedor | andinas | |

- **Pasos:**
  1. Aplicar cada valor eligiendo la sugerencia (ejecuciones separadas).
- **Resultado esperado:** "bucaramanga" sugiere "Alcaldía de Bucaramanga — NIT 890201222" y lista S2; el NIT lista S3; "andinas" lista S1 y S3.

### QA-03: Modalidad con agrupación TVEC

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 2 / RN-03
- **Pasos:**
  1. Abrir "Modalidad" y marcar "Tienda Virtual del Estado (TVEC)" y "Subasta inversa".
- **Resultado esperado:** opciones con conteos de señales: Mínima cuantía (1), Subasta inversa (1), Régimen especial (1), Tienda Virtual del Estado (TVEC) (1); lista S2 y S3.

### QA-04: Rango de valor y UNSPSC

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 3 / RN-05 / RN-06
- **Pasos:**
  1. Aplicar valor mínimo 12.480.000 y máximo 22.900.000.
  2. Limpiar y agregar UNSPSC "V1.52161505".
- **Resultado esperado:** paso 1 lista S1 y S2 (límites incluidos); paso 2 lista S1 y S3 con la nota "Los registros de la TVEC no publican código UNSPSC y no aparecen cuando este filtro está activo."

### QA-05: Filtro de fuente y restricción de la última fuente

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** Escenario 4 / RN-08
- **Pasos:**
  1. Desmarcar "SECOP II".
  2. Intentar desmarcar "TVEC".
- **Resultado esperado:** paso 1 lista solo S2 con etiqueta "Fuente: TVEC"; paso 2 no cambia la casilla y muestra "Debe quedar al menos una fuente seleccionada."

### QA-06: Validaciones de entrada

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 5 / RN-10
- **Datos de prueba:**

  | Campo | Valor | Mensaje esperado |
  | ----- | ----- | ---------------- |
  | Desde / Hasta | 01/06/2026 / 01/01/2026 | La fecha inicial no puede ser posterior a la fecha final. |
  | Desde | 30/02/2026 | Ingresa una fecha válida con formato DD/MM/AAAA. |
  | Hasta | 03/10/2026 | La fecha no puede ser posterior a hoy. |
  | Valor mín. / máx. | 30.000.000 / 10.000.000 | El valor mínimo no puede ser mayor que el valor máximo. |
  | Valor máx. | 1000000000000 | Ingresa un valor en pesos, solo con números enteros (máximo 12 dígitos). |
  | UNSPSC | 5216150 | Ingresa un código UNSPSC de 8 dígitos (ej. 52161505). |
  | UNSPSC | 6.º código | Puedes agregar hasta 5 códigos UNSPSC. |
  | Entidad | "tu" | Escribe al menos 3 caracteres del nombre o del NIT. |
  | Entidad | "tunja" + Enter sin sugerencia | Selecciona una opción de la lista de sugerencias. |
  | Proveedor | 11.º valor | Puedes seleccionar hasta 10 valores en este filtro. |

- **Pasos:**
  1. Intentar aplicar cada dato.
- **Resultado esperado:** en cada caso se muestra el mensaje indicado, el filtro no se aplica y la lista no cambia.

### QA-07: Orden por valor, fecha y confianza con desempate

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 6 / RN-11
- **Pasos:**
  1. Ordenar por "Valor — Mayor a menor".
  2. Ordenar por "Fecha — Más antigua primero".
  3. Ordenar por "Nivel de confianza — Mayor a menor".
- **Resultado esperado:** paso 1: S1 ($ 3.900.000), S3, S2, S4; paso 2: S3, S4, S2, S1; paso 3: S1 (Alta), S2 (Media, 01/08/2026), S3 (Media, 10/03/2025), S4 (Baja).

### QA-08: Volver a la prioridad por defecto

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 7
- **Pasos:**
  1. Con orden "Valor", elegir "Prioridad (por defecto)".
- **Resultado esperado:** S1 (Alta), S3 (Media, +55,3 %), S2 (Media, +52,9 %), S4 (Baja).

### QA-09: Sin señales para los filtros

- **Tipo:** Estado UI
- **Prioridad:** Media
- **Cubre:** Escenario 8
- **Pasos:**
  1. Marcar "Boyacá" y desmarcar "SECOP II".
- **Resultado esperado:** "No hay señales que merezcan revisión con los filtros aplicados.", conteo "0 señales" y botón "Limpiar filtros".

### QA-10: Quitar etiqueta y limpiar conservando el orden

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 9
- **Precondiciones:** filtros de QA-01 y orden "Desviación — Mayor a menor".
- **Pasos:**
  1. Quitar la etiqueta de fechas.
  2. Pulsar "Limpiar filtros".
- **Resultado esperado:** paso 1 lista S2, S1, S4; paso 2 lista S3, S2, S1, S4; ambos en página 1 con el orden por desviación conservado.

### QA-11: Persistencia en URL, al volver y en otra sesión

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 10 / RN-12
- **Pasos:**
  1. Aplicar los filtros de QA-01; recargar; abrir S1 y volver; abrir la URL en otra sesión activa de Analista.
- **Resultado esperado:** en todos los casos se ven los mismos filtros, orden y página.

### QA-12: Combinación de varios criterios con Y

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** RN-01
- **Pasos:**
  1. Aplicar proveedor "Distribuciones Andinas S.A.S." + modalidad "Mínima cuantía" + "Santander".
- **Resultado esperado:** solo S1.

### QA-13: Señales con datos faltantes y filtros activos

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** RN-09
- **Pasos:**
  1. Aplicar valor mínimo 0.
  2. Limpiar, marcar "Santander" y el municipio "Bucaramanga (Santander)".
- **Resultado esperado:** paso 1 excluye S4 (sin valor); paso 2 lista S1 y S2 y excluye S4 (sin municipio).

### QA-14: Lenguaje no acusatorio en filtros y mensajes

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** RN-13
- **Pasos:**
  1. Recorrer el panel, etiquetas y mensajes buscando los términos prohibidos.
- **Resultado esperado:** 0 apariciones de "sobreprecio", "corrupción", "fraude" o "hallazgo fiscal".

### QA-15: Tiempo de respuesta

- **Tipo:** Positivo
- **Prioridad:** Baja
- **Cubre:** RN-14
- **Precondiciones:** volumen del MVP; 20 sesiones concurrentes.
- **Pasos:**
  1. Aplicar combinaciones de filtros y orden durante 10 minutos.
- **Resultado esperado:** p95 ≤ 3 segundos (objetivo inicial de diseño).

### QA-16: Teclado y panel plegable

- **Tipo:** Estado UI
- **Prioridad:** Media
- **Cubre:** RN-15
- **Pasos:**
  1. A 768 px abrir "Filtros (0)", aplicar un filtro solo con teclado y cerrar el panel.
- **Resultado esperado:** el panel se abre y cierra con teclado, los mensajes se anuncian y el botón muestra "Filtros (1)".

### QA-17: Proveedor persona natural se filtra por nombre sin mostrar su documento

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 11 / RN-02 / RN-16
- **Precondiciones:** señales complementarias cargadas (S5).
- **Pasos:**
  1. Escribir "fernanda rios" en "Proveedor" y elegir la sugerencia.
  2. Revisar sugerencia, etiqueta, lista y URL.
- **Resultado esperado:** la sugerencia es "María Fernanda Ríos Peña — Persona natural — documento no visible"; la lista muestra solo S5 con la etiqueta "Proveedor: María Fernanda Ríos Peña"; el valor 1012345678 no aparece en sugerencia, etiqueta, lista ni URL.

### QA-18: Número de documento de persona natural o tipo vacío no encuentra ni revela al proveedor

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 12 / RN-02 / RN-16 / RN-12
- **Precondiciones:** señales complementarias cargadas (S5, S6, S7).
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Proveedor | 1.012.345.678 | cédula de S5 con formato |
  | Proveedor | 101234 | prefijo de la cédula de S5 |
  | Proveedor | 79555123 | documento de S6, tipo vacío |
  | Proveedor | AB123456 | pasaporte de S7 |
  | Proveedor | ortiz gil | nombre de S6 |

- **Pasos:**
  1. Escribir cada valor en "Proveedor".
  2. Para "ortiz gil", elegir la sugerencia y revisar etiqueta y URL.
- **Resultado esperado:** los cuatro primeros valores muestran "No hay proveedores con ese nombre o NIT entre las señales vigentes." y la lista no cambia; "ortiz gil" sugiere "Juan Pablo Ortiz Gil — Persona natural — documento no visible" (tipo vacío tratado como persona natural) y lista S6; ningún número de documento de S5, S6 o S7 aparece en pantalla ni en la URL.

---

**Total de casos:** 18
