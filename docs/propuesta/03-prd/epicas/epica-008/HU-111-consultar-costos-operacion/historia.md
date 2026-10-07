# Historia #111: Consultar el costo por documento procesado con IA y el costo mensual por componente

**Estado:** Borrador (PO)  
**Release:** Release MVP  
**Épica:** [Operación, Calidad y Medición del MVP](../../../epicas.md#épica-008-operación-calidad-y-medición-del-mvp)  
**Feature:** Medir KPIs del MVP  
**Prioridad:** Alta  
**FRs relacionados:** FR-091 (relacionados: FR-034; NFR-OBS-001)

Escrita por el flujo generar-historias-usuario (Método Ceiba) — MVP propio, no comercial

---

## Historia de Usuario

**Como** Administrador del MVP (el PO),  
**Quiero** consultar el costo estimado de la extracción con IA por documento y el costo mensual acumulado por componente (IA, almacenamiento, cómputo y búsqueda),  
**Para** identificar los principales drivers de costo del MVP y decidir dónde optimizar antes de ampliar el uso.

## Descripción

Uno de los objetivos del Brief es lanzar el MVP "con sus principales drivers de costo identificados". NFR-OBS-001 exige registrar el costo estimado por documento procesado con IA y el costo mensual acumulado por componente (IA, almacenamiento, cómputo, búsqueda), consultables por el Administrador. El Journey 3 incluye el "costo por documento" entre los indicadores que el Administrador consulta.

El costo por documento ya lo registra la extracción (FR-034). Los costos de almacenamiento, cómputo y búsqueda provienen de la facturación de los proveedores de infraestructura, por lo que el Administrador los registra por mes (individualmente o con un archivo CSV). Esta HU consolida ambos en un reporte mensual.

**Implementación sin UI permitida:** comando, script, consulta o reporte; registro de costos por comando o archivo CSV.

---

## Criterios de Aceptación

### Escenario 1: Reporte mensual con todos los componentes

- **Dado** que en 2026-11 se procesaron con IA 320 documentos con costo estimado total de 41,60 USD, y el Administrador registró para 2026-11 almacenamiento 6,20 USD, cómputo 28,00 USD y búsqueda 9,50 USD
- **Cuando** consulta el reporte de costos de 2026-11
- **Entonces** obtiene: IA 41,60 USD (320 documentos; costo promedio por documento 0,13 USD; mediana y máximo por documento); almacenamiento 6,20 USD; cómputo 28,00 USD; búsqueda 9,50 USD; total 85,30 USD; y la participación de cada componente en el total (IA 48,8 %, almacenamiento 7,3 %, cómputo 32,8 %, búsqueda 11,1 %)

### Escenario 2: Componente no registrado

- **Dado** que para 2026-12 no se ha registrado el costo de búsqueda
- **Cuando** el Administrador consulta 2026-12
- **Entonces** búsqueda aparece como "no registrado" (no como 0), el total se marca "parcial: falta búsqueda" y la participación se calcula solo sobre los componentes registrados

### Escenario 3: Varias monedas

- **Dado** que en 2026-11 el costo de IA está en USD y el de almacenamiento en COP
- **Cuando** el Administrador consulta el reporte
- **Entonces** los totales se muestran separados por moneda (ej. "USD 41,60 · COP 24.500") sin conversión, y la participación por componente se muestra solo dentro de cada moneda

### Escenario 4: Registrar el costo mensual de un componente

- **Dado** que no hay costo de cómputo para 2026-11
- **Cuando** el Administrador registra cómputo, 2026-11, 28,00, USD, fuente "Factura del proveedor de nube n.º 1182"
- **Entonces** el costo queda registrado con usuario y fecha, y la respuesta es "Costo de cómputo para 2026-11 registrado."

### Escenario 5: Reemplazar un costo ya registrado

- **Dado** que cómputo de 2026-11 vale 28,00 USD
- **Cuando** el Administrador registra 31,40 USD para el mismo mes y componente
- **Entonces** el valor vigente pasa a 31,40 USD, el anterior queda en el historial con su usuario y fecha, y la respuesta es "Costo de cómputo para 2026-11 actualizado (anterior: 28,00 USD)."

### Escenario 6: Registro inválido

- **Dado** que el Administrador está autenticado
- **Cuando** registra un componente "red", un mes "2026-13", un monto negativo o no numérico, una moneda "dólares" o una fuente vacía
- **Entonces** no se registra nada y recibe el mensaje correspondiente de RN-07

### Escenario 7: Intento de registrar manualmente el costo de IA

- **Dado** que el Administrador está autenticado
- **Cuando** intenta registrar manualmente el componente "IA"
- **Entonces** recibe "El costo de IA se calcula a partir de los documentos procesados y no se registra manualmente."

### Escenario 8: Carga de costos por archivo CSV

- **Dado** un archivo CSV con columnas `mes,componente,monto,moneda,fuente` y 6 filas, una con componente inválido
- **Cuando** el Administrador lo carga
- **Entonces** se registran las 5 filas válidas, la inválida se rechaza con su número de fila y motivo, y el resumen es "Filas registradas: 5. Rechazadas: 1."

### Escenario 9: Detalle de costo por documento

- **Dado** que en 2026-11 se procesaron 320 documentos
- **Cuando** el Administrador pide el detalle de IA del mes
- **Entonces** obtiene una fila por documento con id de documento, contrato, fecha de procesamiento, costo estimado, moneda y tiempo de procesamiento, ordenada por costo descendente, exportable a CSV

### Escenario 10: Documentos sin costo registrado

- **Dado** que 4 documentos procesados en 2026-11 no tienen costo estimado registrado
- **Cuando** se calcula el reporte
- **Entonces** el promedio por documento se calcula sobre los 316 con costo y el reporte indica "4 documentos procesados sin costo registrado"

### Escenario 11: Período sin datos

- **Dado** que en 2026-01 no hay documentos procesados ni costos registrados
- **Cuando** el Administrador consulta ese mes
- **Entonces** recibe "No hay costos registrados para el período consultado."

### Escenario 12: Rango de meses

- **Dado** que el Administrador consulta el rango 2026-10 a 2026-12
- **Cuando** se genera el reporte
- **Entonces** obtiene una sección por mes y un acumulado del rango por componente y moneda; un rango mayor de 24 meses o con inicio posterior al fin se rechaza con el mensaje de RN-07

### Escenario 13: Usuario sin rol Administrador

- **Dado** que un usuario con rol Analista está autenticado
- **Cuando** intenta consultar o registrar costos
- **Entonces** recibe "Acción no permitida: esta operación requiere el rol Administrador."

---

## Información Recopilada

### Usuario y Contexto

- **Tipo de usuario:** Administrador (en el MVP, el PO).
- **Permisos requeridos:** rol Administrador.
- **Valor de negocio:** cumple el objetivo del Brief de identificar los drivers de costo y la mitigación del riesgo "costo de IA por documento".

### Reglas de Negocio

- **RN-01 — Componentes:** `IA`, `almacenamiento`, `cómputo` (se acepta `computo`), `búsqueda` (se acepta `busqueda`). Ningún otro componente se admite.
- **RN-02 — Costo de IA:** proviene exclusivamente de los registros de extracción por documento (costo estimado, moneda, fecha y tiempo de procesamiento). El mes de un documento es el de su fecha de procesamiento (UTC−05:00). Un documento procesado varias veces cuenta cada procesamiento por separado. No se registra manualmente.
- **RN-03 — Indicadores de IA por mes:** número de documentos procesados; número sin costo registrado; costo total; costo promedio, mediana y máximo por documento (sobre los que tienen costo); tiempo promedio de procesamiento por documento.
- **RN-04 — Registro manual de componentes no IA:** mes `AAAA-MM` (no posterior al mes en curso), componente, monto decimal ≥ 0 con máximo 2 decimales y hasta 1.000.000.000, moneda en código ISO 4217 de 3 letras mayúsculas (ej. `USD`, `COP`), fuente de 3 a 200 caracteres. Un registro por mes y componente: registrar de nuevo reemplaza el valor vigente y guarda el anterior en el historial con usuario y fecha.
- **RN-05 — Carga CSV:** UTF-8, separador coma, encabezado `mes,componente,monto,moneda,fuente`, máximo 500 filas; cada fila se valida con RN-04 y se aplica por separado; resumen "Filas registradas: {a}. Rechazadas: {b}." con número de fila y motivo de cada rechazo.
- **RN-06 — Reporte:** por mes: valor por componente ("no registrado" si falta; 0 solo si se registró 0), total por moneda, participación porcentual (1 decimal) de cada componente dentro de su moneda, marca "parcial: falta {componentes}" si falta alguno, e indicadores de IA. Sin conversión entre monedas. Para un rango: una sección por mes y un acumulado por componente y moneda. Rango máximo 24 meses.
- **RN-07 — Mensajes:**
  - "Costo de {componente} para {mes} registrado."
  - "Costo de {componente} para {mes} actualizado (anterior: {monto} {moneda})."
  - "El componente '{x}' no es válido. Componentes válidos: almacenamiento, cómputo, búsqueda."
  - "El costo de IA se calcula a partir de los documentos procesados y no se registra manualmente."
  - "El mes '{x}' no es válido; use el formato AAAA-MM y un mes no posterior al actual."
  - "El monto debe ser un número entre 0 y 1000000000 con máximo 2 decimales."
  - "La moneda '{x}' no es válida; use un código ISO 4217 de 3 letras (ej. USD, COP)."
  - "Debe indicar la fuente del costo (3 a 200 caracteres)."
  - "El archivo supera el máximo de 500 filas." (no se registra ninguna fila)
  - "No hay costos registrados para el período consultado."
  - "El rango no puede superar 24 meses."
  - "El mes inicial no puede ser posterior al mes final."
  - "Acción no permitida: esta operación requiere el rol Administrador."

### Interfaz

No requiere interfaz gráfica. Mínimo aceptable: comando "reporte de costos {mes o rango}", comando "detalle de costo IA {mes}" con exportación CSV, comando "registrar costo" y carga CSV.

### Sistemas Externos (Si aplica)

No integra APIs de facturación de proveedores: los costos de infraestructura se registran a partir de sus facturas o exportaciones.

---

## Contexto y Referencias

**Épica origen:** [Operación, Calidad y Medición del MVP](../../../epicas.md#épica-008-operación-calidad-y-medición-del-mvp)

**Exclusiones de la Épica:**
- NO incluye analítica de uso avanzada ni embudos de producto.
- NO incluye facturación ni gestión de planes.
- NO incluye administración multi-organización.

**Historias relacionadas:** HU-106 a HU-110 (resto de KPIs del MVP).

---

## Supuestos

> Elementos inferidos por la IA que NO estaban explícitos en el PRD o la Épica. Todos los supuestos han sido resueltos: convertidos en reglas de negocio explícitas o eliminados mediante reformulación. Si aparece algún supuesto no resuelto, esta HU NO está lista para desarrollo.

- Los costos de almacenamiento, cómputo y búsqueda se registran manualmente o por CSV a partir de las facturas, sin integrar APIs de facturación → resuelto en RN-04, RN-05 y Sistemas Externos.
- No se convierte entre monedas; los totales se presentan por moneda → resuelto en RN-06.
- Esta HU mide costos de operación del MVP; no es facturación a usuarios (excluida por la épica) → resuelto en la descripción.

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
