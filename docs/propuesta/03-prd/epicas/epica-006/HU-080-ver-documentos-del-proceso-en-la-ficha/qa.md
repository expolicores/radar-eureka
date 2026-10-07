# Casos de Prueba — HU-080: Ver los documentos del proceso en la ficha del contrato

**Historia:** [historia.md](./historia.md) | **Autor:** Juan Camilo | **Fecha:** 2026-10-02

## Alcance de las Pruebas

Se prueba la sección "Documentos" de la ficha: columnas, orden, estados, priorización, enlaces a la fuente oficial y a la copia conservada, versión conservada vs. publicación actual, comprimidos, procesos sin documentos o sin obtener, órdenes TVEC, errores, volumen, lenguaje, rendimiento y accesibilidad. Quedan fuera la obtención, priorización y extracción de documentos.

## Precondiciones y Datos Base

- **Usuario:** `analista.piloto1@prueba.co` (Analista).
- **Contrato C1 (SECOP II, proceso CO1.BDOS.4400123), documentos:**

  | Documento | Tipo | Tamaño | Fecha de carga | Priorizado | Estado | Evidencia |
  | --------- | ---- | ------ | -------------- | ---------- | ------ | --------- |
  | Oferta económica.pdf | PDF | 1,2 MB | 05/09/2026 | Sí | Procesado | Sí, copia del 06/09/2026 |
  | Anexo económico.xlsx | XLSX | 85,0 KB | 04/09/2026 | Sí | Procesado | Sí, copia del 06/09/2026; URL oficial ya no responde |
  | Cotizaciones.zip | ZIP | 3,4 MB | 01/09/2026 | Sí | Procesado | contiene "Cotización A.pdf" (Procesado, evidencia) y "Cotización B.pdf" (Excluido: duplicado de Cotización A.pdf) |
  | Formato propuesta económica.docx | DOCX | 40,0 KB | 01/09/2026 | Sí | Excluido: documento en blanco o sin diligenciar | No |
  | Estudios previos.pdf | PDF | 4,8 MB | 20/08/2026 | Sí | Pendiente de procesamiento | No |
  | Póliza.pdf | PDF | 300,0 KB | 10/09/2026 | No | No priorizado | No |
  | Plano.dwg | DWG | 2,0 MB | 20/08/2026 | No | No soportado | No |

- **Contrato C3:** proceso sin documentos publicados. **Contrato C5:** documentos aún no consultados. **Orden C2:** TVEC 98765. **Contrato C9:** 60 documentos.

## Matriz de Cobertura

| Criterio / Regla | Casos |
| ---------------- | ----- |
| Escenario 1 / RN-01 / RN-02 / RN-04 | QA-01 |
| Escenario 2 / RN-06 | QA-02 |
| Escenario 3 / RN-05 | QA-03 |
| Escenario 4 | QA-04 |
| Escenario 5 / RN-03 | QA-05 |
| Escenario 6 | QA-06 |
| Escenario 7 | QA-07 |
| Escenario 8 | QA-08 |
| Escenario 9 | QA-09 |
| Escenario 10 | QA-10 |
| RN-07 nulos | QA-11 |
| RN-08 | QA-12 |
| RN-09 | QA-13 |
| RN-10 | QA-14 |

---

## Casos de Prueba

### QA-01: Lista de documentos con columnas y orden

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 1 / RN-01 / RN-02 / RN-04
- **Pasos:**
  1. Abrir la ficha de C1 en "Documentos".
- **Resultado esperado:** título "Documentos del proceso (7)"; orden: Oferta económica.pdf, Anexo económico.xlsx, Cotizaciones.zip, Formato propuesta económica.docx (estos dos del 01/09/2026 en orden alfabético), Estudios previos.pdf, y luego los no priorizados Póliza.pdf y Plano.dwg; columnas Nombre, Tipo, Tamaño ("1,2 MB", "85,0 KB"), Fecha de carga, Priorizado, Estado y Acciones.

### QA-02: Abrir en SECOP II

- **Tipo:** Integración
- **Prioridad:** Alta
- **Cubre:** Escenario 2 / RN-06
- **Pasos:**
  1. Activar "Abrir en SECOP II" en Póliza.pdf.
- **Resultado esperado:** se abre la `url_descarga_documento` en una pestaña nueva; la ficha sigue abierta.

### QA-03: Copia conservada de un documento de evidencia

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 3 / RN-05
- **Pasos:**
  1. Activar "Ver copia conservada" en Oferta económica.pdf.
  2. Revisar Póliza.pdf.
- **Resultado esperado:** paso 1 abre la copia en pestaña nueva; la fila muestra "Usado como evidencia" y "06/09/2026"; paso 2: Póliza.pdf no tiene "Ver copia conservada".

### QA-04: Evidencia disponible aunque la fuente ya no responda

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** Escenario 4
- **Pasos:**
  1. Revisar la fila de Anexo económico.xlsx y abrir su copia.
- **Resultado esperado:** la copia se abre y la fila muestra "La copia conservada corresponde a la versión descargada el 06/09/2026; puede diferir de la publicación actual."

### QA-05: Estados de documento

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 5 / RN-03
- **Pasos:**
  1. Revisar el estado de cada documento de C1.
- **Resultado esperado:** "Procesado", "Excluido: documento en blanco o sin diligenciar", "Pendiente de procesamiento", "No priorizado", "No soportado" y, en el comprimido, "Excluido: duplicado de Cotización A.pdf"; un documento simulado con error muestra "Error al procesar" y "No se pudo leer el documento".

### QA-06: Archivos dentro de un comprimido

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 6
- **Pasos:**
  1. Revisar Cotizaciones.zip.
- **Resultado esperado:** bajo el ZIP aparecen anidados "Cotización A.pdf" y "Cotización B.pdf" con "Contenido en Cotizaciones.zip"; no tienen "Abrir en SECOP II"; "Cotización A.pdf" tiene "Ver copia conservada".

### QA-07: Proceso sin documentos publicados

- **Tipo:** Estado UI
- **Prioridad:** Media
- **Cubre:** Escenario 7
- **Pasos:**
  1. Abrir la ficha de C3 en "Documentos".
- **Resultado esperado:** "La fuente no ha publicado documentos para este proceso." y enlace "Ver en SECOP II".

### QA-08: Documentos aún no obtenidos

- **Tipo:** Estado UI
- **Prioridad:** Media
- **Cubre:** Escenario 8
- **Pasos:**
  1. Abrir la ficha de C5 en "Documentos".
- **Resultado esperado:** "Los documentos de este proceso aún no se han obtenido. Revisa el estado de procesamiento."

### QA-09: Orden TVEC

- **Tipo:** Estado UI
- **Prioridad:** Media
- **Cubre:** Escenario 9
- **Pasos:**
  1. Abrir la ficha de C2 en "Documentos".
- **Resultado esperado:** "Los datos de esta orden provienen del dataset estructurado de la Tienda Virtual del Estado; no se procesan documentos para las órdenes TVEC en el MVP."

### QA-10: Error al abrir la copia conservada

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** Escenario 10
- **Precondiciones:** falla simulada en el almacenamiento de copias.
- **Pasos:**
  1. Activar "Ver copia conservada" en Oferta económica.pdf.
- **Resultado esperado:** "No fue posible abrir la copia conservada en este momento. Intenta de nuevo en unos minutos." y la opción "Abrir en SECOP II".

### QA-11: Campos no publicados

- **Tipo:** Borde
- **Prioridad:** Baja
- **Cubre:** RN-07
- **Precondiciones:** documento de C1 sin tamaño ni descripción publicados.
- **Pasos:**
  1. Revisar su fila.
- **Resultado esperado:** Tamaño "Sin dato"; no aparece línea de descripción.

### QA-12: Más de 50 documentos

- **Tipo:** Borde
- **Prioridad:** Baja
- **Cubre:** RN-08
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Documentos | 50 | máx: sin botón |
  | Documentos | 60 | máx + 10 |

- **Pasos:**
  1. Abrir la ficha con 50 documentos y la de C9 con 60; activar "Mostrar todos (60)".
- **Resultado esperado:** con 50 no aparece el botón; con 60 se muestran 50 y el botón; al activarlo aparecen los 60.

### QA-13: Lenguaje no acusatorio

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** RN-09
- **Pasos:**
  1. Buscar los términos prohibidos en la sección y sus mensajes.
- **Resultado esperado:** 0 apariciones.

### QA-14: Rendimiento, teclado y móvil

- **Tipo:** Estado UI
- **Prioridad:** Media
- **Cubre:** RN-10
- **Precondiciones:** 20 sesiones concurrentes.
- **Pasos:**
  1. Abrir la ficha de C1 repetidamente durante 10 minutos.
  2. Recorrer la sección con teclado y verla a 360 px.
- **Resultado esperado:** ficha en ≤ 3 s (p95); enlaces anunciados "se abre en una pestaña nueva"; los archivos del ZIP se anuncian como contenidos en él; a 360 px cada documento es una tarjeta con todos sus campos y acciones.

---

**Total de casos:** 14
