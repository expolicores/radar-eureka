# Historia #105: Generar la plantilla de validación y cargar los resultados verificados

**Estado:** Borrador (PO)  
**Release:** Release MVP  
**Épica:** [Operación, Calidad y Medición del MVP](../../../epicas.md#épica-008-operación-calidad-y-medición-del-mvp)  
**Feature:** Gestionar Revisión y Muestra de Validación  
**Prioridad:** Alta  
**FRs relacionados:** FR-092, FR-091 (relacionados: FR-027, FR-094; NFR-CAL-001, NFR-CAL-002, NFR-CAL-003)

Escrita por el flujo generar-historias-usuario (Método Ceiba) — MVP propio, no comercial

---

## Historia de Usuario

**Como** Administrador del MVP que valida manualmente la extracción (el PO),  
**Quiero** descargar una plantilla con los campos extraídos de la muestra de validación y cargar después, campo por campo y contrato por contrato, el valor correcto y el resultado de mi verificación,  
**Para** que el sistema calcule la precisión y la cobertura con una verificación independiente del extractor.

## Descripción

Marcar la muestra (HU-104) no basta: los KPIs de precisión (NFR-CAL-002) y de cobertura (NFR-CAL-003) necesitan la **verdad verificada** por una persona. Siguiendo el formato usado en el spike D4 (plantilla de 228 filas campo a campo y 50 filas por contrato), esta HU permite:

1. **Generar la plantilla** de los elementos de la muestra (todos, por lote o solo los que falten por validar), con dos hojas: validación por campo y validación por contrato.
2. **Cargar la plantilla diligenciada** (XLSX o CSV): el sistema valida cada fila, aplica las válidas, informa las rechazadas y conserva el historial cuando una fila se vuelve a cargar con otro resultado.

Los resultados posibles por campo siguen la metodología P-06: `correcto`, `incorrecto`, `omitido`, `ausente_y_no_extraido`, `inventado` y `no_verificable`.

**Implementación sin UI permitida:** comando o script que genera el archivo y otro que lo carga, o interfaz administrativa mínima con descarga y carga de archivo.

---

## Criterios de Aceptación

### Escenario 1: Generar la plantilla de toda la muestra

- **Dado** que la muestra tiene 50 contratos y 3 documentos individuales con 76 ítems de televisor detectados
- **Cuando** el Administrador genera la plantilla
- **Entonces** obtiene un archivo XLSX con la hoja "Validación por campo" (una fila por cada uno de los 5 campos críticos de cada ítem, haya o no valor extraído, más una fila por cada otro campo extraído), la hoja "Validación por contrato" (una fila por cada uno de los 50 contratos) y la hoja "Instrucciones", con las columnas de RN-02 y RN-03

### Escenario 2: Generar la plantilla filtrada

- **Dado** que la muestra tiene los lotes "D4-4" y "2026-10-S1" y algunos elementos ya están validados por completo
- **Cuando** el Administrador genera la plantilla del lote "2026-10-S1" con la opción "solo pendientes"
- **Entonces** la plantilla incluye solo filas de ese lote cuyo resultado aún no está registrado

### Escenario 3: Plantilla sin elementos

- **Dado** que la muestra está vacía, o todos los elementos del filtro ya tienen resultado
- **Cuando** el Administrador genera la plantilla
- **Entonces** no se genera archivo y recibe "No hay filas por validar para el filtro indicado."

### Escenario 4: Cargar resultados válidos

- **Dado** que el Administrador diligenció 40 filas por campo y 10 filas por contrato, todas válidas
- **Cuando** carga el archivo
- **Entonces** se registran los 50 resultados con usuario y fecha y hora, y recibe el resumen "Filas aplicadas: 50. Sin cambios: 0. Sin diligenciar: {n}. Rechazadas: 0."

### Escenario 5: Campo incorrecto sin valor correcto

- **Dado** que una fila tiene `valor_extraido` = 2483599 y RESULTADO = `incorrecto` sin VALOR_CORRECTO
- **Cuando** el Administrador carga el archivo
- **Entonces** esa fila se rechaza con "Fila 14: el resultado 'incorrecto' exige VALOR_CORRECTO." y las demás filas válidas se aplican

### Escenario 6: Resultado incompatible con el valor extraído

- **Dado** que una fila tiene `valor_extraido` vacío y RESULTADO = `correcto`, y otra tiene `valor_extraido` = "LG" y RESULTADO = `ausente_y_no_extraido`
- **Cuando** el Administrador carga el archivo
- **Entonces** ambas se rechazan con "Fila {n}: el resultado '{r}' no es compatible con un valor extraído {vacío|no vacío}."

### Escenario 7: Resultado no reconocido

- **Dado** que una fila tiene RESULTADO = "bien"
- **Cuando** el Administrador carga el archivo
- **Entonces** la fila se rechaza con "Fila {n}: el resultado 'bien' no es válido. Valores permitidos: correcto, incorrecto, omitido, ausente_y_no_extraido, inventado, no_verificable."

### Escenario 8: Fila sin diligenciar

- **Dado** que una fila tiene RESULTADO vacío
- **Cuando** el Administrador carga el archivo
- **Entonces** la fila se cuenta como "sin diligenciar", no es un error y no modifica un resultado previo

### Escenario 9: Fila que no corresponde a la muestra

- **Dado** que una fila tiene un `id_fila` inexistente o de un elemento retirado de la muestra
- **Cuando** el Administrador carga el archivo
- **Entonces** la fila se rechaza con "Fila {n}: la fila '{id_fila}' no corresponde a un elemento vigente de la muestra."

### Escenario 10: Veredicto por contrato

- **Dado** que la fila por contrato de CO1.PCCNTR.4946355 tiene ES_COMPRA_TV_EN_CATEGORIA = "no" y EXISTE_INFO_MINIMA = "si"
- **Cuando** el Administrador carga el archivo
- **Entonces** la fila se rechaza con "Fila {n}: si el contrato no es compra de televisor en categoría, EXISTE_INFO_MINIMA debe ser 'no' o quedar vacío."

### Escenario 11: Volver a cargar un resultado distinto

- **Dado** que la fila VF-000123 tiene registrado `correcto`
- **Cuando** el Administrador carga un archivo donde esa fila dice `incorrecto` con VALOR_CORRECTO = 55
- **Entonces** el resultado vigente pasa a `incorrecto` con valor correcto 55, el anterior queda en el historial de la fila con su usuario y fecha, y la fila se cuenta como "aplicada"

### Escenario 12: Volver a cargar el mismo archivo

- **Dado** que el Administrador ya cargó un archivo
- **Cuando** lo vuelve a cargar sin cambios
- **Entonces** no se crea historial nuevo y el resumen es "Filas aplicadas: 0. Sin cambios: {n}. Sin diligenciar: {m}. Rechazadas: 0."

### Escenario 13: Archivo inválido

- **Dado** que el Administrador está autenticado
- **Cuando** carga un PDF, un archivo de más de 10 MB, un archivo sin las columnas obligatorias o un archivo sin filas de datos
- **Entonces** no se aplica ninguna fila y recibe, respectivamente, "Formato no soportado: use XLSX o CSV con la estructura de la plantilla.", "El archivo supera el tamaño máximo de 10 MB.", "Faltan columnas obligatorias: {lista}." o "El archivo no contiene filas de datos."

### Escenario 14: Estado de validación de cada elemento

- **Dado** que un contrato de la muestra tiene 12 filas por campo y su fila por contrato
- **Cuando** se registran resultados para 7 filas por campo y nada en la fila por contrato
- **Entonces** el estado de validación del contrato es "parcial"; pasa a "completa" cuando las 12 filas por campo tienen resultado y su fila por contrato tiene ambas respuestas

### Escenario 15: Usuario sin rol Administrador

- **Dado** que un usuario con rol Analista está autenticado
- **Cuando** intenta generar o cargar la plantilla
- **Entonces** recibe "Acción no permitida: esta operación requiere el rol Administrador." y nada cambia

---

## Información Recopilada

### Usuario y Contexto

- **Tipo de usuario:** Administrador que actúa como validador manual (en el MVP, el PO).
- **Permisos requeridos:** rol Administrador.
- **Valor de negocio:** habilita los KPIs de precisión global y por campo y de cobertura con una verdad independiente del extractor, y alimenta la calibración del umbral de aceptación automática (P-15).

### Reglas de Negocio

- **RN-01 — Campos críticos:** `marca`, `modelo_referencia`, `tamano_pulgadas`, `cantidad`, `precio_unitario`. Por cada ítem de televisor detectado en un elemento de la muestra, la plantilla incluye **siempre** estas 5 filas, aunque el extractor no haya obtenido valor (así se distingue `omitido` de `ausente_y_no_extraido`). Los demás campos extraídos (ej. resolución, tecnología, Smart, valor total del ítem, IVA) se incluyen solo si tienen valor extraído.
- **RN-02 — Hoja "Validación por campo" (columnas, en este orden):** `id_fila` (identificador estable `VF-{número de 6 dígitos}`), `id_contrato`, `id_documento`, `entidad`, `anio_firma`, `item_n`, `descripcion_extraida` (máximo 200 caracteres), `campo`, `valor_extraido` (vacío si no hay), `confianza`, `evidencia` (documento | página, hoja o celda), `VALOR_CORRECTO`, `RESULTADO`, `NOTA`. Las columnas en mayúsculas las diligencia el validador; las demás son de solo lectura y se ignoran si se modifican.
- **RN-03 — Hoja "Validación por contrato" (solo contratos marcados):** `id_fila` (`VC-{6 dígitos}`), `id_contrato`, `entidad`, `objeto` (máximo 200 caracteres), `resultado_extractor`, `ES_COMPRA_TV_EN_CATEGORIA` (`si`/`no`), `EXISTE_INFO_MINIMA` (`si`/`no`: los documentos publicados contienen cantidad y precio unitario explícito o derivable), `NOTA`. Si ES_COMPRA_TV_EN_CATEGORIA = `no`, EXISTE_INFO_MINIMA debe ser `no` o vacío. Valores aceptados sin distinguir mayúsculas ni tildes (`sí` = `si`).
- **RN-04 — Resultados por campo y compatibilidad:**

  | RESULTADO | Significado | `valor_extraido` | VALOR_CORRECTO |
  |---|---|---|---|
  | `correcto` | presente y bien extraído | no vacío | opcional (se ignora) |
  | `incorrecto` | presente y mal extraído | no vacío | obligatorio |
  | `omitido` | presente en el documento pero no extraído | vacío | obligatorio |
  | `ausente_y_no_extraido` | no está en el documento y no se extrajo | vacío | debe quedar vacío |
  | `inventado` | no está en el documento pero se "extrajo" | no vacío | debe quedar vacío |
  | `no_verificable` | el validador no pudo verificarlo | cualquiera | opcional |

  Valores aceptados sin distinguir mayúsculas. Un resultado fuera de la lista o incompatible rechaza la fila.
- **RN-05 — Formato de VALOR_CORRECTO por campo:** `tamano_pulgadas`: número de 10 a 120 (decimales con punto o coma); `cantidad`: entero de 1 a 100.000; `precio_unitario`: número de 1 a 1.000.000.000 en pesos colombianos (se ignoran "$", espacios y separadores de miles); `marca` y `modelo_referencia`: texto de 1 a 100 caracteres. Un valor con formato inválido rechaza la fila con "Fila {n}: VALOR_CORRECTO '{v}' no es válido para el campo {campo}."
- **RN-06 — Carga:** archivo XLSX (hojas con los nombres de la plantilla) o CSV (un archivo por hoja, identificado por el prefijo de `id_fila`), máximo 10 MB, UTF-8 en CSV. Las filas se identifican por `id_fila`. Cada fila se valida y aplica por separado; una fila rechazada no impide aplicar las demás. Las filas con RESULTADO vacío (y, en la hoja por contrato, con ambas respuestas vacías) se cuentan como "sin diligenciar" y no borran resultados previos. `NOTA`: máximo 500 caracteres (se trunca con aviso "Fila {n}: la nota se truncó a 500 caracteres.").
- **RN-07 — Historial:** cada resultado registra usuario y fecha y hora (UTC−05:00). Si una fila ya tenía resultado y llega uno distinto (resultado, valor correcto o nota), el anterior pasa al historial y el nuevo queda vigente. Si llega idéntico, cuenta como "sin cambios". Los resultados no se eliminan.
- **RN-08 — Resumen de carga:** "Filas aplicadas: {a}. Sin cambios: {b}. Sin diligenciar: {c}. Rechazadas: {d}." seguido del detalle de cada fila rechazada (número de fila en el archivo y motivo).
- **RN-09 — Estado de validación del elemento:** "sin validar" (ninguna fila con resultado), "parcial" o "completa" (todas sus filas por campo con resultado y, si es contrato, su fila por contrato con ambas respuestas, o con ES_COMPRA_TV_EN_CATEGORIA = `no`).
- **RN-10 — Generación:** filtros opcionales por lote y "solo pendientes" (filas sin resultado vigente). Los `id_fila` son estables: la misma fila conserva su id entre plantillas. Si el extractor vuelve a procesar un documento de la muestra y cambia un valor extraído, la fila conserva su id, muestra el nuevo valor y su resultado previo pasa a historial con estado "requiere revalidar" (vuelve a contar como pendiente).
- **RN-11 — Auditoría:** cada carga registra un evento "Carga de resultados de validación" con usuario, fecha y hora, nombre y hash del archivo y los conteos de RN-08.
- **RN-12 — Mensajes:** los de los escenarios 3, 5, 6, 7, 9, 10 y 13; además:
  - "Fila {n}: el resultado '{r}' exige VALOR_CORRECTO." (aplica a `incorrecto` y `omitido`)
  - "Fila {n}: con el resultado '{r}', VALOR_CORRECTO debe quedar vacío." (aplica a `ausente_y_no_extraido` e `inventado`)
  - "Fila {n}: '{v}' no es un valor permitido en {columna}; use 'si' o 'no'."
  - "El lote '{x}' no existe en la muestra."
  - "Acción no permitida: esta operación requiere el rol Administrador."

### Interfaz

No requiere interfaz gráfica. Mínimo aceptable: comando "generar plantilla de validación" (con filtros de RN-10) que produce el XLSX con las hojas "Validación por campo", "Validación por contrato" e "Instrucciones" (con el significado de cada RESULTADO de RN-04), y comando "cargar resultados de validación" que recibe el archivo y devuelve el resumen de RN-08.

### Sistemas Externos (Si aplica)

No aplica. Los documentos de la evidencia se consultan desde las copias que conserva el sistema (FR-024).

---

## Contexto y Referencias

**Épica origen:** [Operación, Calidad y Medición del MVP](../../../epicas.md#épica-008-operación-calidad-y-medición-del-mvp)

**Exclusiones de la Épica:**
- NO incluye analítica de uso avanzada ni embudos de producto.
- NO incluye facturación ni gestión de planes.
- NO incluye administración multi-organización.

**Historias relacionadas:** HU-104 (muestra de validación), HU-106 (precisión), HU-107 (cobertura).

---

## Supuestos

> Elementos inferidos por la IA que NO estaban explícitos en el PRD o la Épica. Todos los supuestos han sido resueltos: convertidos en reglas de negocio explícitas o eliminados mediante reformulación. Si aparece algún supuesto no resuelto, esta HU NO está lista para desarrollo.

- La verdad verificada se registra con una plantilla XLSX/CSV inspirada en la del spike D4, con dos hojas (por campo y por contrato) → resuelto en RN-02, RN-03 y RN-06.
- Se agrega el resultado `omitido` (presente y no extraído) a los valores del spike D4, porque cuenta en el denominador de "campos realmente presentes" → resuelto en RN-01 y RN-04.
- Si el extractor reprocesa un documento de la muestra, el resultado previo pasa a "requiere revalidar" → resuelto en RN-10.
- Los resultados del spike D4-4 (extraídos fuera del sistema) no se importan automáticamente; la muestra del MVP se valida sobre la extracción del propio sistema → resuelto por reformulación (RN-01, RN-02).

---

## Validación INVEST

- [x] **Independiente:** Esta HU puede implementarse sin dependencias bloqueantes de otras HU
- [x] **Negociable:** Describe QUÉ se necesita, no CÓMO implementarlo (detalles técnicos son negociables)
- [x] **Valiosa:** Aporta valor tangible al negocio o usuario final (beneficio claro)
- [x] **Estimable:** El equipo puede estimar esfuerzo (scope claro, no ambiguo)
- [x] **Pequeña:** Completable en pocos días/persona (no excede 1 sprint)
- [x] **Testeable:** Criterios de aceptación permiten verificar cuándo está terminada

## Validación Anti-Ambigüedad

- [x] **Auto-contenida:** Un desarrollador puede implementar esta HU leyendo SOLO este archivo
- [x] **Reglas completas:** Todas las reglas de negocio incluyen formatos, rangos, límites y comportamiento ante nulos
- [x] **Errores explícitos:** El comportamiento ante cada tipo de error está documentado (mensaje, acción, redirección)
- [x] **Edge cases cubiertos:** Criterios de aceptación incluyen casos borde y estados vacíos
- [x] **Supuestos resueltos:** No quedan supuestos pendientes de validación
- [x] **Datos claros:** Origen, formato y proveedor de cada dato están especificados

---

## Definición de Terminado (Inicial)

- [ ] Funcionalidad implementada según criterios de aceptación
- [ ] Validaciones funcionando correctamente
- [ ] Mensajes de usuario implementados
- [ ] Pruebas funcionales pasando

---

## Registro de Cambios

| Fecha | Versión | Descripción | Autor |
|-------|---------|-------------|-------|
| 2026-10-02 | 1.0 | Historia generada desde Épica ÉPICA-008 | Juan Camilo (PO) |

---

> **Método Ceiba estimar hus** v6.1.95 | Modelo: claude-opus-5-5 | Usuario: Juan Camilo | Fecha: 2026-10-05
