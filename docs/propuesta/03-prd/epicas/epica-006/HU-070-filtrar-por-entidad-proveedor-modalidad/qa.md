# Casos de Prueba — HU-070: Filtrar la exploración por entidad, proveedor y modalidad

**Historia:** [historia.md](./historia.md) | **Autor:** Juan Camilo | **Fecha:** 2026-10-02

## Alcance de las Pruebas

Se prueban los filtros Entidad, Proveedor y Modalidad de la exploración: búsqueda por nombre y por NIT, ocultamiento y no búsqueda del documento de proveedores persona natural, sugerencias, selección múltiple y límite, selección explícita, agrupación de modalidades TVEC y sin modalidad, combinación entre criterios, nulos, modo ítems, persistencia, errores, accesibilidad y tiempos. Quedan fuera la vista base (HU-069), los demás filtros (HU-071, HU-072) y las fichas de entidad o proveedor (excluidas de la épica).

## Precondiciones y Datos Base

- **Usuario:** `analista.piloto1@prueba.co` (rol Analista, sesión activa).
- **Universo semilla:**

  | Registro | Fuente | Entidad (NIT) | Proveedor (NIT, persona jurídica) | Modalidad |
  | -------- | ------ | ------------- | ---------------- | --------- |
  | R1 | SECOP II | Alcaldía de Tunja (891800846) | Distribuciones Andinas S.A.S. (900123456) | Mínima cuantía |
  | R2 | SECOP II | ALCALDIA DE TUNJA (891800846) | Comercializadora Nova S.A.S. (901555777) | Subasta inversa |
  | R3 | TVEC | Gobernación de Santander (890201235) | Comercializadora Nova S.A.S. (901555777) | (no publicada) |
  | R4 | SECOP II | Hospital San Rafael E.S.E. (820000142) | (sin proveedor publicado) | Régimen especial |
  | R5 | SECOP II | Universidad Pedagógica de Tunja (891800330) | Distribuciones Andinas S.A.S. (900123456) | (sin modalidad) |

- 12 entidades adicionales cuyo nombre contiene "Municipio de", para probar el límite de 10.
- **Universo complementario (solo QA-18 a QA-21):** se agregan estos registros; no altera los conteos de los demás casos.

  | Registro | Fuente | Entidad (NIT) | Proveedor | Tipo de documento (`tipodocproveedor`) | Documento almacenado | Modalidad |
  | -------- | ------ | ------------- | --------- | -------------------------------------- | -------------------- | --------- |
  | R6 | SECOP II | Alcaldía de Tunja (891800846) | María Fernanda Ríos Peña | Cédula de Ciudadanía | 1012345678 | Mínima cuantía |
  | R7 | SECOP II | Gobernación de Santander (890201235) | Juan Pablo Ortiz Gil | (vacío) | 79555123 | Mínima cuantía |
  | R8 | SECOP II | Hospital San Rafael E.S.E. (820000142) | Ana Lucía Gómez | Tipo no reconocido "XYZ" | 52444888 | Mínima cuantía |
  | R9 | SECOP II | Hospital San Rafael E.S.E. (820000142) | Peter Smith | Cédula de Extranjería | 901555 | Mínima cuantía |

## Matriz de Cobertura

| Criterio / Regla | Casos |
| ---------------- | ----- |
| Escenario 1 / RN-02 / RN-07 | QA-01 |
| Escenario 2 / RN-03 / RN-05 | QA-02 |
| Escenario 3 / RN-10 | QA-03 |
| Escenario 4 / RN-08 | QA-04 |
| Escenario 5 / RN-04 | QA-05 |
| Escenario 6 / RN-06 | QA-06 |
| Escenario 7 / RN-09 | QA-07 |
| Escenario 8 / RN-13 | QA-08 |
| Escenario 9 / RN-01 / RN-11 | QA-09 |
| Escenario 10 / RN-10 | QA-10 |
| Escenario 11 / RN-11 | QA-11 |
| Escenario 12 | QA-12 |
| RN-04 orden de sugerencias | QA-13 |
| RN-12 modo ítems | QA-14 |
| RN-14 persistencia | QA-15 |
| RN-15 tiempos | QA-16 |
| RN-16 accesibilidad | QA-17 |
| Escenario 13 / RN-17 / RN-05 | QA-18 |
| Escenario 14 / RN-03 / RN-17 | QA-19 |
| Escenario 15 / RN-17 | QA-20 |
| RN-17 / RN-14 no exposición en URL y etiquetas | QA-21 |

---

## Casos de Prueba

### QA-01: Filtrar por entidad buscada por nombre sin tildes ni mayúsculas

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 1 / RN-02 / RN-07
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Entidad | tunja | minúsculas |
  | Entidad | ALCALDÍA DE  TUNJA | mayúsculas, tilde y doble espacio |

- **Pasos:**
  1. Escribir cada valor en "Entidad".
  2. Elegir "Alcaldía de Tunja — NIT 891800846".
- **Resultado esperado:** la sugerencia aparece una sola vez (R1 y R2 se agrupan por NIT con el nombre más frecuente); el listado muestra R1 y R2; etiqueta "Entidad: Alcaldía de Tunja"; conteo 2.

### QA-02: Buscar por NIT con y sin formato

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 2 / RN-03 / RN-05
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Entidad | 891800846 | sin formato |
  | Entidad | 891.800.846-1 | con puntos y dígito de verificación |
  | Entidad | 891800 | prefijo |
  | Proveedor | 901555777 | documento de proveedor |

- **Pasos:**
  1. Escribir cada valor en el campo indicado.
- **Resultado esperado:** los dos primeros sugieren "Alcaldía de Tunja — NIT 891800846"; el prefijo "891800" sugiere Alcaldía de Tunja y Universidad Pedagógica de Tunja; el NIT del proveedor persona jurídica sugiere "Comercializadora Nova S.A.S. — NIT 901555777".

### QA-03: Varias entidades se combinan con O

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 3 / RN-10
- **Pasos:**
  1. Seleccionar "Alcaldía de Tunja".
  2. Seleccionar "Gobernación de Santander".
- **Resultado esperado:** listado R1, R2 y R3; dos etiquetas de entidad; página 1.

### QA-04: Límite de 10 valores por filtro

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** Escenario 4 / RN-08
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Entidades seleccionadas | 9 | máx − 1 |
  | Entidades seleccionadas | 10 | máx |
  | Entidades seleccionadas | 11 | máx + 1 |

- **Pasos:**
  1. Seleccionar entidades "Municipio de…" hasta llegar a 9, 10 e intentar la 11.ª.
- **Resultado esperado:** 9 y 10 se aplican; la 11.ª no se agrega y aparece "Puedes seleccionar hasta 10 valores en este filtro."

### QA-05: Menos de 3 caracteres no muestra sugerencias

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** Escenario 5 / RN-04
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Entidad | tu | 2 caracteres |
  | Entidad | "t  u" | 2 caracteres con espacios |
  | Entidad | tun | 3 caracteres |
  | Entidad | texto de 101 caracteres | máx + 1 |

- **Pasos:**
  1. Escribir cada valor.
- **Resultado esperado:** con 2 caracteres (con o sin espacios) se muestra "Escribe al menos 3 caracteres del nombre o del NIT." y no hay sugerencias; con "tun" aparecen sugerencias; el campo no acepta el carácter 101.

### QA-06: Sin coincidencias en entidad y en proveedor

- **Tipo:** Estado UI
- **Prioridad:** Media
- **Cubre:** Escenario 6 / RN-06
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Entidad | Ministerio de Minas | no está en el universo |
  | Proveedor | Ecoviajes | proveedor solo de registros descartados |

- **Pasos:**
  1. Escribir cada valor en su campo.
- **Resultado esperado:** "No hay entidades con ese nombre o NIT en el universo de televisores." y "No hay proveedores con ese nombre o NIT en el universo de televisores."; el listado no cambia.

### QA-07: Enter sin elegir sugerencia no filtra

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** Escenario 7 / RN-09
- **Pasos:**
  1. Escribir "tunja" en "Entidad" y pulsar Enter sin elegir sugerencia.
  2. Escribir "nova" en "Proveedor" y salir del campo con Tab.
- **Resultado esperado:** en ambos casos aparece "Selecciona una opción de la lista de sugerencias.", no se crea etiqueta y el listado no cambia.

### QA-08: Filtrar por dos modalidades con conteos

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 8 / RN-13
- **Pasos:**
  1. Abrir "Modalidad".
  2. Marcar "Mínima cuantía" y "Subasta inversa".
- **Resultado esperado:** casillas "Mínima cuantía (1)", "Subasta inversa (1)", "Régimen especial (1)", y al final "Tienda Virtual del Estado (TVEC) (1)" y "Sin modalidad registrada (1)"; el listado muestra R1 y R2; los conteos no cambian al aplicar otros filtros.

### QA-09: Agrupaciones TVEC y sin modalidad

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** Escenario 9 / RN-01 / RN-11
- **Pasos:**
  1. Marcar solo "Tienda Virtual del Estado (TVEC)".
  2. Marcar solo "Sin modalidad registrada".
- **Resultado esperado:** paso 1 muestra R3; paso 2 muestra R5.

### QA-10: Combinación de los tres criterios con Y

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 10 / RN-10
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Combinación A | Entidad Alcaldía de Tunja + Proveedor Comercializadora Nova + Modalidad Subasta inversa | cumple R2 |
  | Combinación B | Entidad Alcaldía de Tunja + Proveedor Comercializadora Nova + Modalidad Mínima cuantía | ninguno |

- **Pasos:**
  1. Aplicar cada combinación.
- **Resultado esperado:** A lista solo R2 en página 1; B muestra "No encontramos resultados con los filtros aplicados."

### QA-11: Registro sin proveedor no cumple filtros de proveedor

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** Escenario 11 / RN-11
- **Pasos:**
  1. Seleccionar el proveedor "Distribuciones Andinas S.A.S.".
- **Resultado esperado:** listado R1 y R5; R4 (sin proveedor) no aparece.

### QA-12: Error al consultar sugerencias conserva los filtros

- **Tipo:** Integración
- **Prioridad:** Media
- **Cubre:** Escenario 12
- **Precondiciones:** filtro "Modalidad: Mínima cuantía" aplicado; falla simulada en la consulta de sugerencias.
- **Pasos:**
  1. Escribir "nova" en "Proveedor".
- **Resultado esperado:** "No fue posible cargar las sugerencias. Intenta de nuevo." debajo del campo; el filtro de modalidad sigue aplicado; el listado no cambia.

### QA-13: Orden y cantidad máxima de sugerencias

- **Tipo:** Borde
- **Prioridad:** Baja
- **Cubre:** RN-04
- **Precondiciones:** 12 entidades "Municipio de…" con 1 a 12 registros cada una.
- **Pasos:**
  1. Escribir "municipio".
- **Resultado esperado:** se muestran 10 sugerencias, de la entidad con 12 registros a la de 3 registros; en empate, orden alfabético.

### QA-14: En modo ítems se usa el contrato padre

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** RN-12
- **Precondiciones:** R1 tiene 2 ítems incluidos; R2 tiene 1.
- **Pasos:**
  1. Cambiar a "Ítems de televisor" y seleccionar entidad "Alcaldía de Tunja".
- **Resultado esperado:** se listan los 3 ítems de R1 y R2.

### QA-15: Los filtros persisten al recargar y al volver de la ficha

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** RN-14
- **Pasos:**
  1. Seleccionar entidad "Gobernación de Santander" y modalidad "Tienda Virtual del Estado (TVEC)".
  2. Recargar la página.
  3. Abrir la ficha de R3 y volver.
- **Resultado esperado:** tras recargar y al volver, ambas etiquetas y el listado R3 se mantienen.

### QA-16: Tiempos de sugerencias y de aplicación del filtro

- **Tipo:** Positivo
- **Prioridad:** Baja
- **Cubre:** RN-15
- **Precondiciones:** universo con volumen del MVP; 20 sesiones concurrentes.
- **Pasos:**
  1. Escribir "alcaldia" y detenerse.
  2. Elegir una sugerencia.
- **Resultado esperado:** sugerencias en ≤ 1 s tras 300 ms sin escribir; listado filtrado en ≤ 3 s (p95).

### QA-17: Operación completa con teclado y lector de pantalla

- **Tipo:** Estado UI
- **Prioridad:** Media
- **Cubre:** RN-16
- **Pasos:**
  1. Llegar con Tab a "Entidad", escribir "tun", bajar con flechas y elegir con Enter.
  2. Pulsar Escape con la lista abierta.
  3. Marcar una modalidad con barra espaciadora.
- **Resultado esperado:** la sugerencia se elige con Enter; Escape cierra la lista; la casilla se marca; el lector de pantalla anuncia las etiquetas de los campos y los mensajes de ayuda.

### QA-18: Proveedor persona natural se encuentra por nombre sin mostrar su documento

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 13 / RN-17 / RN-05
- **Precondiciones:** universo complementario cargado (R6).
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Proveedor | fernanda rios | sin tildes ni mayúsculas |
  | Proveedor | MARÍA FERNANDA | mayúsculas y tilde |

- **Pasos:**
  1. Escribir cada valor en "Proveedor".
  2. Elegir la sugerencia del proveedor.
- **Resultado esperado:** la sugerencia es "María Fernanda Ríos Peña — Persona natural — documento no visible"; el listado muestra R6; la etiqueta es "Proveedor: María Fernanda Ríos Peña"; el valor 1012345678 no aparece en sugerencias, etiqueta, listado ni texto anunciado por el lector de pantalla.

### QA-19: Escribir el número de cédula no encuentra ni revela al proveedor persona natural

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 14 / RN-03 / RN-17
- **Precondiciones:** universo complementario cargado (R6, R9).
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Proveedor | 1012345678 | cédula completa de R6 |
  | Proveedor | 1.012.345.678 | cédula con puntos |
  | Proveedor | 101234 | prefijo de la cédula |
  | Proveedor | 901555 | documento completo de R9 (cédula de extranjería) y prefijo del NIT de Comercializadora Nova |

- **Pasos:**
  1. Escribir cada valor en "Proveedor".
- **Resultado esperado:** con los tres primeros valores se muestra "No hay proveedores con ese nombre o NIT en el universo de televisores.", no se sugiere María Fernanda Ríos Peña y el listado no cambia; con "901555" solo se sugiere "Comercializadora Nova S.A.S. — NIT 901555777" (coincidencia por NIT de persona jurídica) y Peter Smith no aparece; en ningún caso se muestra el documento de un proveedor persona natural.

### QA-20: Tipo de documento vacío o desconocido se trata como persona natural

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** Escenario 15 / RN-17
- **Precondiciones:** universo complementario cargado (R7, R8).
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Proveedor | 79555123 | documento de R7, tipo vacío |
  | Proveedor | 52444888 | documento de R8, tipo "XYZ" |
  | Proveedor | ortiz gil | nombre de R7 |
  | Proveedor | ana lucia | nombre de R8 |

- **Pasos:**
  1. Escribir cada valor en "Proveedor".
- **Resultado esperado:** los dos números no generan sugerencias ("No hay proveedores con ese nombre o NIT en el universo de televisores."); por nombre se sugieren "Juan Pablo Ortiz Gil — Persona natural — documento no visible" y "Ana Lucía Gómez — Persona natural — documento no visible"; ningún número aparece en pantalla.

### QA-21: El documento del proveedor persona natural no se expone en URL ni al restaurar filtros

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** RN-17 / RN-14
- **Precondiciones:** universo complementario cargado (R6).
- **Pasos:**
  1. Seleccionar el proveedor "María Fernanda Ríos Peña".
  2. Revisar la URL de la exploración.
  3. Recargar la página y volver desde la ficha de R6.
- **Resultado esperado:** la URL contiene un identificador interno que no incluye 1012345678; tras recargar y volver, la etiqueta "Proveedor: María Fernanda Ríos Peña" y el listado R6 se restauran sin mostrar el número.

---

**Total de casos:** 21
