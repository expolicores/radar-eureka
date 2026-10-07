# Casos de Prueba — HU-077: Ver los ítems de televisor extraídos en la ficha del contrato

**Historia:** [historia.md](./historia.md) | **Autor:** Juan Camilo | **Fecha:** 2026-10-02

## Alcance de las Pruebas

Se prueba la sección "Ítems de televisor" de la ficha: ítems mostrados y conteo, campos y producto normalizado, evidencia, precio derivado, base tributaria, ítems TVEC, correcciones, pendientes de revisión e inconsistencias, información insuficiente, ítems excluidos, estado sin ítems, evidencia no disponible, posicionamiento, formatos, lenguaje, rendimiento y accesibilidad. Quedan fuera la extracción, la corrección y la clasificación (otros procesos).

## Precondiciones y Datos Base

- **Usuario:** `analista.piloto1@prueba.co` (Analista).
- **Contrato C1 (SECOP II CO1.PCCNTR.5512001), contrato mixto:**

  | Ítem | Clasificación | Datos | Tipo precio / IVA | Origen | Validación |
  | ---- | ------------- | ----- | ----------------- | ------ | ---------- |
  | I1 | incluido | Samsung UN65CU7000, 65", 4K UHD, LED, Smart; cantidad 8; P.U. $ 3.900.000; total $ 31.200.000 | Explícito / con IVA | "Oferta económica.pdf", página 4 | Aceptado automáticamente |
  | I2 | incluido | LG 55UR8750, 55"; cantidad 5 (corregida; original 50); total $ 14.750.000; P.U. $ 2.950.000 | Derivado / indeterminada | "Anexo económico.xlsx", hoja "Propuesta", celda F12 | Corregido por revisión humana el 20/09/2026 |
  | I3 | requiere revisión | Televisor 43" (sin marca); cantidad 2; P.U. $ 1.500.000; total $ 3.500.000 | Explícito / sin IVA | "Aceptación de oferta.pdf", página 2 | Pendiente de revisión (inconsistencia aritmética) |
  | I4 | incluido | Televisor 50" smart; cantidad y precio no extraídos | — | — | Información insuficiente |
  | X1 | excluido | Monitor 24" para CCTV | — | — | motivo "Monitor, fuera del límite de categoría" |
  | X2 | excluido | Instalación de soportes | — | — | motivo "Servicio de instalación, no es compra de televisor" |

- **Orden C2 (TVEC 98765):** 1 ítem "TELEVISOR SAMSUNG 50 PULGADAS UN50CU7000", cantidad 6, P.U. $ 2.080.000, total $ 12.480.000.
- **Contrato C3 (SECOP II CO1.PCCNTR.4410022):** identificado, sin ítems extraídos.

## Matriz de Cobertura

| Criterio / Regla | Casos |
| ---------------- | ----- |
| Escenario 1 / RN-01 / RN-02 / RN-11 / RN-12 | QA-01 |
| Escenario 2 / RN-05 | QA-02 |
| Escenario 3 / RN-03 | QA-03 |
| Escenario 4 / RN-04 | QA-04 |
| Escenario 5 / RN-05 | QA-05 |
| Escenario 6 / RN-07 | QA-06 |
| Escenario 7 / RN-08 | QA-07 |
| Escenario 8 / RN-09 | QA-08 |
| Escenario 9 / RN-10 | QA-09 |
| Escenario 10 | QA-10 |
| Escenario 11 | QA-11 |
| Escenario 12 | QA-12 |
| RN-06 sin puntaje numérico | QA-13 |
| RN-13 | QA-14 |
| RN-14 | QA-15 |
| RN-15 | QA-16 |

---

## Casos de Prueba

### QA-01: Tarjetas de ítems incluidos con campos completos

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 1 / RN-01 / RN-02 / RN-11 / RN-12
- **Pasos:**
  1. Abrir la ficha de C1 en la sección "Ítems de televisor".
- **Resultado esperado:** título "Ítems de televisor (3)" (I1, I2, I4); I3 aparece con marca "Pendiente de revisión" sin sumar al conteo; I1 muestra "Samsung UN65CU7000", 65", 4K UHD, LED, Smart sí, cantidad 8, "$ 3.900.000", total "$ 31.200.000", "Explícito", "IVA: incluido", "Aceptado automáticamente" y "Ver evidencia"; tarjetas en el orden del documento.

### QA-02: Ver evidencia en página y en celda

- **Tipo:** Integración
- **Prioridad:** Alta
- **Cubre:** Escenario 2 / RN-05
- **Pasos:**
  1. Activar "Ver evidencia" en I1.
  2. Activar "Ver evidencia" en I2.
- **Resultado esperado:** I1 abre en pestaña nueva la copia de "Oferta económica.pdf" en la página 4, con la línea "Fuente: Oferta económica.pdf, página 4"; I2 abre "Anexo económico.xlsx" en la hoja "Propuesta", celda F12, con "Fuente: Anexo económico.xlsx, hoja Propuesta, celda F12".

### QA-03: Precio derivado con fórmula y nota

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 3 / RN-03
- **Pasos:**
  1. Revisar la tarjeta de I2.
- **Resultado esperado:** "$ 2.950.000" con marca "Derivado", "Calculado como valor total del ítem ($ 14.750.000) / cantidad (5)" y "Un precio derivado tiene menor confianza que un precio publicado en el documento."

### QA-04: Tres bases tributarias

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 4 / RN-04
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | I1 | con IVA | |
  | I3 | sin IVA | |
  | I2 | indeterminada | |

- **Pasos:**
  1. Revisar las tres tarjetas.
- **Resultado esperado:** "IVA: incluido"; "IVA: no incluido"; "IVA: base indeterminada" con "Las comparaciones de este ítem se marcan como incompletas."

### QA-05: Ítem de orden TVEC sin evidencia documental

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 5 / RN-05
- **Pasos:**
  1. Abrir la ficha de C2 en "Ítems de televisor".
- **Resultado esperado:** ítem con descripción, cantidad 6, "$ 2.080.000", total "$ 12.480.000", "Explícito", "Dato estructurado publicado por la TVEC (orden 98765)" y sin "Ver evidencia".

### QA-06: Dato corregido y valor original

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 6 / RN-07
- **Pasos:**
  1. En I2 activar "Ver valor original" de la cantidad.
- **Resultado esperado:** cantidad "5" con "Corregido por revisión humana el 20/09/2026"; el valor original muestra "50"; no aparece el nombre del revisor.

### QA-07: Ítem pendiente por inconsistencia aritmética

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** Escenario 7 / RN-08
- **Pasos:**
  1. Revisar la tarjeta de I3 (2 × $ 1.500.000 ≠ $ 3.500.000).
- **Resultado esperado:** marca "Pendiente de revisión", "Este dato aún no ha sido validado; puede cambiar después de la revisión." y "Cantidad × precio unitario no coincide con el total del ítem: se revisa como posible error de lectura, no como irregularidad."

### QA-08: Información insuficiente

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** Escenario 8 / RN-09
- **Pasos:**
  1. Revisar I4 y activar "Ver motivo".
- **Resultado esperado:** marca "Información insuficiente"; cantidad y precio "No disponible"; el enlace lleva a la sección de motivos de información insuficiente.

### QA-09: Ítems excluidos plegados con motivo

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 9 / RN-10
- **Pasos:**
  1. Desplegar "Otros ítems excluidos del análisis (2)".
  2. Abrir la ficha de C2.
- **Resultado esperado:** paso 1 muestra X1 "Monitor, fuera del límite de categoría" y X2 "Servicio de instalación, no es compra de televisor", sin precio ni comparación; paso 2 no muestra el bloque (sin excluidos).

### QA-10: Contrato sin ítems extraídos

- **Tipo:** Estado UI
- **Prioridad:** Media
- **Cubre:** Escenario 10
- **Pasos:**
  1. Abrir la ficha de C3 en "Ítems de televisor".
- **Resultado esperado:** "Todavía no hay ítems de televisor extraídos para este contrato. Revisa el estado de procesamiento para conocer en qué etapa está."

### QA-11: Evidencia no disponible

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** Escenario 11
- **Precondiciones:** falla simulada al abrir la copia de "Oferta económica.pdf".
- **Pasos:**
  1. Activar "Ver evidencia" en I1.
- **Resultado esperado:** "No fue posible abrir la evidencia en este momento. Puedes consultar el documento en la fuente oficial." con enlace a la URL original del documento en SECOP II.

### QA-12: Posicionamiento y foco en el ítem de origen

- **Tipo:** Positivo
- **Prioridad:** Baja
- **Cubre:** Escenario 12
- **Pasos:**
  1. Abrir la ficha de C1 desde la señal de I2.
- **Resultado esperado:** la tarjeta de I2 está visible, resaltada y con el foco del teclado.

### QA-13: No se muestra puntaje numérico de confianza

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** RN-06
- **Pasos:**
  1. Revisar todas las tarjetas de C1.
- **Resultado esperado:** solo se muestran estados de validación ("Aceptado automáticamente", "Corregido por revisión humana…", "Pendiente de revisión"); no aparece ningún puntaje numérico del extractor.

### QA-14: Lenguaje no acusatorio

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** RN-13
- **Pasos:**
  1. Buscar en la sección de C1 los términos prohibidos.
- **Resultado esperado:** 0 apariciones de "sobreprecio", "corrupción", "fraude" o "hallazgo fiscal".

### QA-15: Rendimiento de la sección

- **Tipo:** Positivo
- **Prioridad:** Baja
- **Cubre:** RN-14
- **Precondiciones:** 20 sesiones concurrentes abriendo fichas con ítems.
- **Pasos:**
  1. Abrir la ficha de C1 repetidamente durante 10 minutos.
- **Resultado esperado:** ficha completa con ítems en ≤ 3 s (p95); la apertura de la evidencia no bloquea la carga.

### QA-16: Accesibilidad y móvil

- **Tipo:** Estado UI
- **Prioridad:** Media
- **Cubre:** RN-15
- **Pasos:**
  1. Abrir y cerrar el bloque de excluidos con teclado.
  2. Ver la sección a 360 px.
- **Resultado esperado:** el bloque anuncia "expandido/contraído"; las marcas se leen como texto; a 360 px las tarjetas ocupan el ancho completo con todos los campos.

---

**Total de casos:** 16
