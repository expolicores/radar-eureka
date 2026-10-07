# Casos de Prueba — HU-021: Conservar la copia y la evidencia de los documentos de los que se extraen datos

**Historia:** [historia.md](./historia.md) | **Autor:** Juan Camilo | **Fecha:** 2026-10-02

## Alcance de las Pruebas

Se prueba la conservación de la copia y sus metadatos al registrar un dato extraído, el vínculo dato ↔ versión ↔ ubicación, el versionado, la inmutabilidad, la verificación de integridad, la disponibilidad del original, la consulta de evidencia y el acceso. Queda fuera: la navegación desde una señal (épica de señales) y la estrategia de almacenamiento (arquitectura).

## Precondiciones y Datos Base

- Usuarios `admin.po@piloto.test` (Administrador), `analista1@piloto.test` (Analista) y una sesión anónima.
- Documento 600002 "Propuesta_economica_ganador.pdf", proceso `CO1.BDOS.1234567`, URL `https://community.secop.gov.co/Public/Archive/RetrieveFile/Index?DocumentId=600002`, dataset `dmgg-8hin`, descargado el 2026-09-28 10:15, hash H1 = `9f2c…a41b`.
- Archivo interno `600010::Anexo/precios.xlsx` (hash H4) del comprimido 600010.
- Ítem `CO1.PCCNTR.7654321-01` (Televisor Smart 55 pulgadas).

## Matriz de Cobertura

| Criterio / Regla | Casos |
| ---------------- | ----- |
| Escenario 1 / RN-01, RN-02, RN-03 | QA-01 |
| RN-01 (dato rechazado) | QA-02 |
| Escenario 2 / RN-02, RN-03 | QA-03 |
| Escenario 3 / RN-02 | QA-04 |
| Escenario 4 / RN-04 | QA-05, QA-06 |
| Escenario 5 / RN-08 | QA-07 |
| Escenario 6 / RN-09 | QA-08 |
| Escenario 7 / RN-07 | QA-09 |
| Escenario 8 / RN-05 | QA-10 |
| Escenario 9 / RN-10 | QA-11 |
| Escenario 10 / RN-11 | QA-12 |
| RN-06 | QA-13 |

---

## Casos de Prueba

### QA-01: Conservación al registrar un dato de un PDF

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 1 / RN-01, RN-02, RN-03
- **Pasos:**
  1. Registrar el precio unitario 2.150.000 del ítem `CO1.PCCNTR.7654321-01` con ubicación "página 2" del documento 600002.
  2. Consultar la evidencia del documento.
- **Resultado esperado:** versión 1 de 600002 con archivo, hash H1, URL original, fuente "SECOP II — Archivos Descarga (dmgg-8hin)", fecha 2026-09-28 10:15, id y proceso; el dato queda vinculado a la versión 1 y a "página 2".

### QA-02: Se conserva aunque el dato luego sea rechazado

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** RN-01
- **Pasos:**
  1. Tras QA-01, rechazar el dato en la revisión humana.
  2. Intentar eliminar la versión 1.
- **Resultado esperado:** la copia sigue conservada y la eliminación se rechaza (sigue vinculada a un dato, aunque esté rechazado).

### QA-03: Dato de hoja de cálculo dentro de un comprimido

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 2 / RN-02, RN-03
- **Pasos:**
  1. Registrar la cantidad 8 desde `Oferta!C5` de `600010::Anexo/precios.xlsx`.
- **Resultado esperado:** copia del archivo interno con hash H4, referencia al comprimido 600010 y a su URL; ubicación "hoja Oferta, celda C5".

### QA-04: Dato leído por lectura visual o desde DOCX

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 3 / RN-02
- **Datos de prueba:**

  | Caso | Origen del dato | Se conserva además |
  | ---- | --------------- | ------------------ |
  | A | Imagen de la página 3 de un PDF escaneado | imagen de la página 3 |
  | B | Página 2 de la representación paginada de "Aceptacion de oferta.docx" | representación paginada |

- **Pasos:**
  1. Registrar un dato en cada caso.
- **Resultado esperado:** se conservan el archivo original y el elemento de la columna "Se conserva además", ambos vinculados a la misma versión.

### QA-05: Redescarga con hash distinto crea versión 2

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 4 / RN-04
- **Pasos:**
  1. Tras QA-01, cambiar el contenido en la fuente simulada y redescargar 600002 (hash H2).
  2. Consultar la evidencia del dato de QA-01 y el historial del documento.
- **Resultado esperado:** existe versión 2 con H2 y su fecha; el dato de QA-01 sigue vinculado a la versión 1 con H1, intacta; el historial muestra ambas versiones.

### QA-06: Redescarga con el mismo hash no crea versión

- **Tipo:** Borde
- **Prioridad:** Baja
- **Cubre:** RN-04
- **Pasos:**
  1. Redescargar 600002 sin cambios en la fuente.
- **Resultado esperado:** no se crea una nueva versión.

### QA-07: Original ya no disponible

- **Tipo:** Integración
- **Prioridad:** Alta
- **Cubre:** Escenario 5 / RN-08
- **Pasos:**
  1. Configurar la fuente simulada para responder 404 a la URL de 600002 y ejecutar la verificación el 2026-10-02.
  2. Consultar la evidencia del dato.
- **Resultado esperado:** la copia se entrega con la anotación "el documento original ya no está disponible en la fuente (verificado el 2026-10-02)".

### QA-08: Consulta de evidencia por el Analista

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 6 / RN-09
- **Pasos:**
  1. Como `analista1@piloto.test`, solicitar la evidencia del precio unitario de `CO1.PCCNTR.7654321-01`.
- **Resultado esperado:** copia de la versión 1, nombre "Propuesta_economica_ganador.pdf", ubicación "página 2", hash H1, URL original, fuente y fecha de descarga.

### QA-09: Integridad comprometida

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 7 / RN-07
- **Pasos:**
  1. Alterar directamente un byte de la copia almacenada de la versión 1 (simulación de daño del archivo).
  2. Solicitar la evidencia como Analista.
- **Resultado esperado:** no se entrega la copia como evidencia válida; mensaje "La copia de este documento no supera la verificación de integridad; se notificó al Administrador"; el Administrador recibe un aviso con documento 600002, versión 1, hash registrado H1 y hash calculado.

### QA-10: Copia vinculada no se puede eliminar ni sobrescribir

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 8 / RN-05
- **Pasos:**
  1. Como Administrador, intentar eliminar la versión 1 de 600002.
  2. Intentar reemplazar su contenido.
- **Resultado esperado:** ambas operaciones se rechazan con "La copia está vinculada a datos extraídos y no puede eliminarse ni modificarse"; la copia y su hash no cambian.

### QA-11: Documento sin datos extraídos

- **Tipo:** Estado UI
- **Prioridad:** Media
- **Cubre:** Escenario 9 / RN-10
- **Pasos:**
  1. Terminar la extracción del proceso sin datos extraídos de 600007.
  2. Consultar el registro de 600007.
- **Resultado esperado:** el registro conserva identificador, nombre, tipo, fecha de carga, URL y hash; no hay versión de evidencia vinculada.

### QA-12: Acceso sin sesión

- **Tipo:** Permisos
- **Prioridad:** Alta
- **Cubre:** Escenario 10 / RN-11
- **Pasos:**
  1. Desde una sesión anónima, solicitar la copia de evidencia de 600002.
  2. Repetir como `admin.po@piloto.test`.
- **Resultado esperado:** acceso denegado para la sesión anónima; el Administrador obtiene la copia.

### QA-13: Las copias vinculadas se incluyen en el respaldo

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** RN-06
- **Pasos:**
  1. Ejecutar un respaldo tras QA-01 y QA-03.
  2. Restaurar el respaldo en un entorno de prueba y consultar la evidencia de ambos datos.
- **Resultado esperado:** ambas copias se recuperan con sus hashes H1 y H4 y su verificación de integridad es correcta.

---

**Total de casos:** 13
