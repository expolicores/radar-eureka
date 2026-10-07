# Casos de Prueba — HU-076: Ver los datos clave del contrato y el enlace a la fuente oficial en la ficha

**Historia:** [historia.md](./historia.md) | **Autor:** Juan Camilo | **Fecha:** 2026-10-02

## Alcance de las Pruebas

Se prueba la estructura de la ficha y la sección "Datos clave": campos SECOP II y TVEC, enlace a la fuente oficial, nota del valor de referencia, nulos, ausencia de datos personales excluidos, visibilidad del documento del proveedor (NIT de persona jurídica visible; documento de persona natural oculto), navegación por secciones y posicionamiento en ítem, estados no encontrado / descartado / error / carga, acceso, "Volver", lenguaje, tiempos, accesibilidad y responsive. Quedan fuera las demás secciones (HU-077 a HU-083).

## Precondiciones y Datos Base

- **Usuarios:** `analista.piloto1@prueba.co` (Analista); visitante sin sesión.
- **Registros semilla:**

  | Registro | Datos |
  | -------- | ----- |
  | C1 (SECOP II) | id_contrato CO1.PCCNTR.5512001; proceso CO1.BDOS.4400123; objeto "Adquisición de televisores para aulas"; descripción de 450 caracteres; entidad Alcaldía de Tunja (NIT 891800846); proveedor Distribuciones Andinas S.A.S. (tipo NIT, 900123456); valor $ 22.900.000; modalidad Mínima cuantía; fecha de firma 15/09/2026; estado "En ejecución"; UNSPSC V1.52161505; Boyacá / Tunja; urlproceso publicada; 2 ítems incluidos (I1, I2) |
  | C2 (TVEC) | orden 98765; Gobernación de Santander; Comercializadora Nova S.A.S.; $ 12.480.000; fecha 01/08/2026; sin modalidad; sin URL publicada |
  | C3 (SECOP II) | CO1.PCCNTR.4410022; sin proveedor; sin valor; sin estado; sin objeto |
  | C4 (SECOP II) | CO1.PCCNTR.3300045; todos los ítems candidatos excluidos |
  | Inexistente | CO1.PCCNTR.0000000 |
  | C5 (SECOP II) | CO1.PCCNTR.5512005; proveedor María Fernanda Ríos Peña; tipo Cédula de Ciudadanía; documento almacenado 1012345678; ítem incluido |
  | C6 (SECOP II) | CO1.PCCNTR.5512006; proveedor Juan Pablo Ortiz Gil; tipo (vacío); documento almacenado 79555123; ítem incluido |
  | C7 (SECOP II) | CO1.PCCNTR.5512007; proveedor Peter Smith; tipo "XYZ" (no reconocido); documento almacenado AB123456; ítem incluido |

## Matriz de Cobertura

| Criterio / Regla | Casos |
| ---------------- | ----- |
| Escenario 1 / RN-01 / RN-02 / RN-06 | QA-01 |
| Escenario 2 / RN-03 | QA-02 |
| Escenario 3 / RN-08 | QA-03 |
| Escenario 4 | QA-02 |
| Escenario 5 / RN-05 | QA-01 |
| Escenario 6 / RN-07 | QA-04 |
| RN-04 datos personales | QA-05 |
| Escenario 7 | QA-06 |
| Escenario 8 | QA-07 |
| Escenario 9 | QA-08 |
| Escenario 10 / RN-09 | QA-09 |
| Escenario 11 | QA-10 |
| Escenario 12 | QA-11 |
| Escenario 13 | QA-12 |
| RN-10 | QA-13 |
| RN-11 | QA-14 |
| RN-12 | QA-15 |
| Escenario 14 / RN-13 | QA-01 |
| Escenario 15 / RN-13 / RN-04 | QA-16 |
| Escenario 16 / RN-13 / RN-07 | QA-17 |

---

## Casos de Prueba

### QA-01: Ficha SECOP II con datos clave completos y nota del valor

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 1 / Escenario 5 / Escenario 14 / RN-01 / RN-02 / RN-05 / RN-06 / RN-13
- **Pasos:**
  1. Abrir la ficha de C1 desde la exploración.
  2. Activar "Ver más" en la descripción.
- **Resultado esperado:** encabezado "SECOP II", "CO1.PCCNTR.5512001" y "Adquisición de televisores para aulas"; datos clave con proceso CO1.BDOS.4400123, entidad y NIT, proveedor "Distribuciones Andinas S.A.S. — NIT 900123456", "$ 22.900.000" con la nota "Valor publicado en datos abiertos. Es un dato de referencia del contrato: no se usa como precio unitario ni como valor adjudicado de los ítems.", "Mínima cuantía", "15/09/2026", "En ejecución", UNSPSC "52161505", "Boyacá / Tunja" y enlace "Ver en SECOP II"; la descripción aparece truncada a 300 caracteres y "Ver más" muestra los 450.

### QA-02: Ficha TVEC sin modalidad ni URL

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 2 / Escenario 4 / RN-03
- **Pasos:**
  1. Abrir la ficha de C2.
- **Resultado esperado:** encabezado "TVEC" y "Orden de compra 98765"; modalidad "Tienda Virtual del Estado (TVEC)"; en lugar del enlace: "Enlace a la fuente oficial no disponible. Identificador en la fuente: 98765."

### QA-03: El enlace oficial abre en pestaña nueva

- **Tipo:** Integración
- **Prioridad:** Media
- **Cubre:** Escenario 3 / RN-08
- **Pasos:**
  1. En la ficha de C1 activar "Ver en SECOP II".
- **Resultado esperado:** se abre la `urlproceso` en una pestaña nueva; la ficha sigue abierta; el lector de pantalla anuncia "se abre en una pestaña nueva".

### QA-04: Campos sin dato y encabezado sin objeto

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** Escenario 6 / RN-07
- **Pasos:**
  1. Abrir la ficha de C3.
- **Resultado esperado:** proveedor, valor, estado y objeto muestran "Sin dato en la fuente"; el encabezado muestra solo "SECOP II" y "CO1.PCCNTR.4410022".

### QA-05: No se muestran datos personales excluidos

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** RN-04
- **Pasos:**
  1. Revisar el texto completo de la ficha de C1, incluido el código fuente de la respuesta mostrada.
- **Resultado esperado:** no aparecen banco, tipo ni número de cuenta, ni documentos de identidad de representantes legales, supervisores u ordenadores del gasto.

### QA-06: Navegación por el índice de secciones

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 7
- **Pasos:**
  1. En la ficha de C1 activar "Documentos" en el índice usando teclado.
- **Resultado esperado:** la vista se desplaza a "Documentos" y el foco queda en su título.

### QA-07: Posicionamiento en un ítem existente y en uno inexistente

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** Escenario 8
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Ítem solicitado | I2 de C1 | existe |
  | Ítem solicitado | I9 de C1 | no existe |

- **Pasos:**
  1. Abrir la ficha desde el ítem I2 en la exploración.
  2. Abrir la URL de la ficha de C1 con el ítem I9.
- **Resultado esperado:** paso 1 posiciona y resalta I2 en "Ítems de televisor"; paso 2 muestra la ficha desde el inicio con "El ítem solicitado ya no está disponible en esta ficha."

### QA-08: Contrato inexistente

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** Escenario 9
- **Pasos:**
  1. Abrir la URL de la ficha de CO1.PCCNTR.0000000 y activar "Ir a Exploración".
- **Resultado esperado:** "No encontramos este contrato. Revisa el enlace o búscalo en Exploración."; el botón lleva a "Exploración".

### QA-09: Registro descartado del universo

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** Escenario 10 / RN-09
- **Pasos:**
  1. Abrir la URL de la ficha de C4.
- **Resultado esperado:** "Este registro no forma parte del universo de compras de televisores analizado: fue descartado en la clasificación." y "Ir a Exploración"; no se muestra ningún dato de C4.

### QA-10: Error al cargar y reintento

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** Escenario 11
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Falla | error del servicio | |
  | Falla | 16 s sin respuesta | supera 15 s |

- **Pasos:**
  1. Abrir la ficha de C1 con cada falla y pulsar "Reintentar" dos veces seguidas.
- **Resultado esperado:** "No fue posible cargar la ficha. Intenta de nuevo en unos minutos." con "Reintentar"; una sola consulta por clic.

### QA-11: Acceso sin sesión y sesión expirada

- **Tipo:** Permisos
- **Prioridad:** Alta
- **Cubre:** Escenario 12
- **Pasos:**
  1. Como visitante abrir la URL de la ficha de C1; iniciar sesión.
  2. Con sesión expirada recargar la ficha.
- **Resultado esperado:** en ambos casos no se muestran datos y se redirige al inicio de sesión; tras iniciar sesión se abre la ficha de C1.

### QA-12: "Volver" según el origen

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 13
- **Pasos:**
  1. Desde la página 2 de la lista de señales abrir la ficha de C1 y activar "Volver".
  2. Abrir la ficha de C1 por URL directa y activar "Volver".
- **Resultado esperado:** paso 1 regresa a la página 2 de "Señales" con su estado; paso 2 lleva a "Exploración" sin filtros.

### QA-13: Lenguaje no acusatorio

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** RN-10
- **Pasos:**
  1. Buscar en las fichas de C1 y C2 y en los mensajes de error los términos prohibidos.
- **Resultado esperado:** 0 apariciones de "sobreprecio", "corrupción", "fraude" o "hallazgo fiscal".

### QA-14: Tiempo de carga de la ficha

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** RN-11
- **Precondiciones:** volumen del MVP; 20 sesiones concurrentes abriendo fichas distintas.
- **Pasos:**
  1. Abrir fichas durante 10 minutos.
- **Resultado esperado:** p95 ≤ 3 segundos (objetivo inicial de diseño).

### QA-15: Accesibilidad y adaptación a móvil

- **Tipo:** Estado UI
- **Prioridad:** Media
- **Cubre:** RN-12
- **Pasos:**
  1. Recorrer la ficha de C1 con teclado y verificar contraste y jerarquía de títulos.
  2. Abrirla a 1366 px, 768 px y 360 px.
- **Resultado esperado:** foco visible y contraste ≥ 4,5:1; títulos de sección jerárquicos; 1366 px muestra datos clave en dos columnas; 360 px en una columna con el menú "Ir a sección".

### QA-16: Proveedor persona natural muestra la leyenda en lugar del documento

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 15 / RN-13 / RN-04
- **Pasos:**
  1. Abrir la ficha de C5.
  2. Revisar la sección "Datos clave", el título de la página, el texto anunciado por el lector de pantalla y el código fuente de la respuesta mostrada.
- **Resultado esperado:** el campo "Proveedor" muestra "María Fernanda Ríos Peña" con la leyenda "Persona natural — documento no visible"; el valor 1012345678 no aparece en ninguno de los elementos revisados.

### QA-17: Tipo de documento vacío o no reconocido se trata como persona natural

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** Escenario 16 / RN-13 / RN-07
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Ficha | C6 | tipo vacío, documento 79555123 |
  | Ficha | C7 | tipo "XYZ", documento AB123456 |

- **Pasos:**
  1. Abrir cada ficha y revisar "Datos clave" y el código fuente de la respuesta mostrada.
- **Resultado esperado:** C6 muestra "Juan Pablo Ortiz Gil" y C7 "Peter Smith", ambos con la leyenda "Persona natural — documento no visible" (no "Sin dato en la fuente"); los valores 79555123 y AB123456 no aparecen.

---

**Total de casos:** 17
