# Historia #098: Consultar el estado de las fuentes de datos

**Estado:** Borrador (PO)  
**Release:** Release MVP  
**Épica:** [Operación, Calidad y Medición del MVP](../../../epicas.md#épica-008-operación-calidad-y-medición-del-mvp)  
**Feature:** Operar Fuentes de Datos  
**Prioridad:** Alta  
**FRs relacionados:** FR-088 (relacionados: FR-007, FR-009, FR-047)

Escrita por el flujo generar-historias-usuario (Método Ceiba) — MVP propio, no comercial

---

## Historia de Usuario

**Como** Administrador del MVP (el PO),  
**Quiero** consultar en un solo lugar el estado de cada fuente de datos (última ingesta o captura, errores, rechazos y suspensiones),  
**Para** detectar rápido qué fuente está fallando o detenida y decidir si debo relanzarla o intervenirla, sin revisar logs técnicos dispersos.

## Descripción

El MVP depende de seis fuentes: cuatro públicas (SECOP II y TVEC, por API de datos abiertos) y dos retail (Alkosto y Falabella, de adquisición progresiva). Cada ejecución de ingesta o captura ya deja un registro con fuente, fecha y hora, registros leídos, nuevos, actualizados, rechazados y errores (FR-007), y las fuentes retail pueden quedar suspendidas al detectar CAPTCHA, bloqueo, autenticación o un cambio en `robots.txt` (FR-047).

Esta HU expone una **consulta de estado de fuentes** con dos niveles: un **resumen** (una fila por fuente con su estado calculado) y un **detalle** por fuente (historial de sus últimas ejecuciones). El estado se calcula de forma determinística con las reglas de esta HU.

**Implementación sin UI permitida:** según la nota del Dominio 12 del PRD, la consulta puede entregarse como comando o script que imprime un reporte, archivo CSV/JSON, consulta a la base de datos o vista administrativa mínima. La arquitectura elige el mecanismo; lo obligatorio es el contenido, las reglas y los mensajes descritos aquí.

---

## Criterios de Aceptación

### Escenario 1: Resumen del estado de todas las fuentes

- **Dado** que el Administrador está autenticado y existen ejecuciones registradas para las fuentes automatizadas
- **Cuando** solicita el resumen de estado de fuentes
- **Entonces** obtiene exactamente 6 filas, una por fuente del catálogo (RN-01), en el orden del catálogo, cada una con los campos de RN-03, y el encabezado del reporte muestra la fecha y hora de generación (zona horaria Colombia, UTC−05:00)

### Escenario 2: Detalle de una fuente con su historial de ejecuciones

- **Dado** que la fuente "SECOP II — Contratos" tiene 15 ejecuciones registradas y el parámetro de historial vale 10
- **Cuando** el Administrador solicita el detalle de esa fuente
- **Entonces** obtiene los datos del resumen de la fuente y las 10 ejecuciones más recientes ordenadas de la más reciente a la más antigua, cada una con los campos de RN-04

### Escenario 3: Historial con menos ejecuciones que el parámetro

- **Dado** que la fuente "TVEC — Órdenes" tiene 3 ejecuciones registradas y el parámetro de historial vale 10
- **Cuando** el Administrador solicita su detalle
- **Entonces** obtiene las 3 ejecuciones existentes, sin filas vacías ni error

### Escenario 4: Fuente operativa

- **Dado** que la última ejecución terminada de "TVEC — Ítems" es `exitosa` con 0 errores y no está retrasada
- **Cuando** el Administrador consulta el resumen
- **Entonces** la fuente aparece con estado **Operativa**

### Escenario 5: Última ejecución fallida

- **Dado** que la última ejecución terminada de "SECOP II — Contratos" terminó con resultado `fallida` y mensaje "Tiempo de espera agotado tras 3 reintentos"
- **Cuando** el Administrador consulta el resumen
- **Entonces** la fuente aparece con estado **Fallida**, y la fila muestra la fecha y hora de esa ejecución y el mensaje de error principal

### Escenario 6: Ejecución exitosa con errores

- **Dado** que la última ejecución terminada de "SECOP II — Archivos" es `exitosa` pero registró 4 errores y 2 rechazados
- **Cuando** el Administrador consulta el resumen
- **Entonces** la fuente aparece con estado **Con errores** y la fila muestra errores = 4 y rechazados = 2

### Escenario 7: Ejecución exitosa solo con rechazados

- **Dado** que la última ejecución terminada de "TVEC — Ítems" es `exitosa`, con 0 errores y 7 rechazados por validaciones de calidad
- **Cuando** el Administrador consulta el resumen
- **Entonces** la fuente aparece con estado **Operativa** y la fila muestra rechazados = 7

### Escenario 8: Fuente retrasada

- **Dado** que la frecuencia configurada de "SECOP II — Contratos" es 24 horas, la tolerancia de retraso es 1 hora y la última ejecución inició hace 26 horas sin que exista otra posterior
- **Cuando** el Administrador consulta el resumen
- **Entonces** la fuente aparece con estado **Retrasada** y la columna "próxima ejecución esperada" muestra la fecha y hora que ya venció

### Escenario 9: Fuente en ejecución

- **Dado** que existe una ejecución de "TVEC — Órdenes" con resultado `en_curso`
- **Cuando** el Administrador consulta el resumen
- **Entonces** la fuente aparece con estado **En ejecución**, con la hora de inicio de esa ejecución, y además se muestra el resultado de la última ejecución terminada

### Escenario 10: Fuente retail suspendida

- **Dado** que "Alkosto" está suspendida desde 2026-09-28 10:15 con motivo "Cambio en robots.txt que prohíbe la ruta de captura"
- **Cuando** el Administrador consulta el resumen
- **Entonces** la fuente aparece con estado **Suspendida**, con la fecha y hora de suspensión y el motivo, aunque su última ejecución haya sido exitosa

### Escenario 11: Fuente retail sin captura automática

- **Dado** que "Falabella" no tiene un mecanismo de captura automática habilitado y su última observación cargada manualmente es del 2026-09-30
- **Cuando** el Administrador consulta el resumen
- **Entonces** la fuente aparece con estado **Sin captura automática**, con "última carga manual: 2026-09-30" y sin campos de ejecución

### Escenario 12: Fuente automatizada sin ejecuciones

- **Dado** que "TVEC — Órdenes" está habilitada pero nunca se ha ejecutado
- **Cuando** el Administrador consulta el resumen o su detalle
- **Entonces** la fuente aparece con estado **Sin ejecuciones**, los campos de última ejecución quedan como "—" y el detalle muestra el mensaje "La fuente TVEC — Órdenes no tiene ejecuciones registradas."

### Escenario 13: Detalle de una fuente inexistente

- **Dado** que el Administrador está autenticado
- **Cuando** solicita el detalle de la fuente "Mercado Libre"
- **Entonces** no obtiene datos y recibe el mensaje "La fuente 'Mercado Libre' no existe. Fuentes válidas: SECOP II — Contratos, SECOP II — Archivos, TVEC — Ítems, TVEC — Órdenes, Alkosto, Falabella."

### Escenario 14: Usuario sin rol Administrador

- **Dado** que un usuario con rol Analista está autenticado
- **Cuando** intenta obtener el resumen o el detalle de fuentes
- **Entonces** no obtiene datos y recibe el mensaje "Acción no permitida: esta consulta requiere el rol Administrador."

---

## Información Recopilada

### Usuario y Contexto

- **Tipo de usuario:** Administrador (en el MVP, el PO, que también actúa como Revisor).
- **Permisos requeridos:** rol Administrador. Ningún otro rol puede consultar el estado de fuentes.
- **Valor de negocio:** sin ingesta al día no hay universo de compras, benchmarks ni señales; detectar fallas temprano protege la frescura de datos (NFR-DAT-002) y la operación semanal del Journey 3.

### Reglas de Negocio

- **RN-01 — Catálogo de fuentes (orden fijo):**

  | # | Fuente | Tipo | Identificador de origen |
  |---|---|---|---|
  | 1 | SECOP II — Contratos | Pública (API datos abiertos) | dataset `jbjy-vk9h` |
  | 2 | SECOP II — Archivos | Pública (API datos abiertos) | dataset `dmgg-8hin` y datasets históricos por año |
  | 3 | TVEC — Ítems | Pública (API datos abiertos) | datasets `usqp-5nsn` / `3hdv-smhz` |
  | 4 | TVEC — Órdenes | Pública (API datos abiertos) | dataset `rgxm-mmea` |
  | 5 | Alkosto | Retail (fuente principal) | captura automática permitida o carga manual |
  | 6 | Falabella | Retail (fuente secundaria) | captura automática permitida o carga manual |

  El nombre de la fuente se acepta sin distinguir mayúsculas/minúsculas ni tildes al solicitar el detalle (ej. "secop ii — contratos" o "alkosto").
- **RN-02 — Datos de origen:** la consulta lee, sin modificarlos, el registro de ejecuciones de ingesta y captura (FR-007), la fecha de corte de cada fuente pública (FR-009), el estado de suspensión de cada fuente retail (FR-047) y la fecha de la última observación manual de cada fuente retail. Esta HU no crea ni corrige ejecuciones.
- **RN-03 — Campos del resumen (por fuente):** nombre; tipo; estado (RN-05); fecha y hora de inicio y de fin de la última ejecución terminada; resultado de la última ejecución terminada (`exitosa` / `fallida`); registros leídos, nuevos, actualizados, rechazados y errores de esa ejecución (enteros ≥ 0); mensaje de error principal (texto, máximo 500 caracteres; "—" si no hay); fecha de corte de los datos (solo fuentes públicas; "—" en retail); frecuencia configurada (horas para públicas, días para retail); próxima ejecución esperada (= inicio de la última ejecución + frecuencia); para fuentes suspendidas, fecha y hora de suspensión y motivo; para fuentes retail, fecha de la última carga manual ("—" si no hay). Todo campo sin dato se muestra como "—", nunca vacío ni como 0.
- **RN-04 — Campos de cada ejecución en el detalle:** identificador de ejecución; origen (`programada` / `manual`); usuario que la lanzó (solo si es `manual`; "—" si es programada); inicio; fin ("—" si está en curso); duración en minutos (entero redondeado hacia arriba; "—" si está en curso); resultado (`en_curso` / `exitosa` / `fallida`); leídos, nuevos, actualizados, rechazados y errores; mensaje de error principal.
- **RN-05 — Cálculo del estado (se aplica la primera condición que se cumpla, en este orden):**
  1. **Suspendida:** la fuente está marcada como suspendida (solo retail).
  2. **Sin captura automática:** fuente retail sin mecanismo de captura automática habilitado.
  3. **Sin ejecuciones:** fuente automatizada sin ninguna ejecución registrada.
  4. **En ejecución:** existe una ejecución con resultado `en_curso`.
  5. **Fallida:** la última ejecución terminada tiene resultado `fallida`.
  6. **Retrasada:** la hora actual supera el inicio de la última ejecución + frecuencia configurada + tolerancia de retraso.
  7. **Con errores:** la última ejecución terminada es `exitosa` y tiene errores > 0.
  8. **Operativa:** ninguna de las anteriores.
  Los rechazados por validaciones de calidad (FR-010) se muestran pero no cambian el estado.
- **RN-06 — "Última ejecución terminada":** la de mayor fecha de inicio con resultado `exitosa` o `fallida`. Si hay una ejecución `en_curso`, el resumen muestra además su hora de inicio en un campo "en curso desde".
- **RN-07 — Parámetros (configurables, sin redespliegue):**
  - Tamaño del historial del detalle: entero de 1 a 100; **configuración inicial: 10** ejecuciones.
  - Tolerancia de retraso: entero de 0 a 24 horas; **configuración inicial: 1 hora**.
  - Frecuencias: se leen de la configuración operativa vigente (configuración inicial: ingesta pública cada 24 horas; captura retail cada 7 días).
  Si un parámetro no está definido, se usa su configuración inicial.
- **RN-08 — Fechas:** todas las fechas y horas se muestran en zona horaria de Colombia (UTC−05:00) con formato `AAAA-MM-DD HH:MM`; la fecha de corte y la última carga manual con formato `AAAA-MM-DD`.
- **RN-09 — Solo lectura:** consultar el estado no lanza ejecuciones, no cambia suspensiones y no genera eventos de auditoría.
- **RN-10 — Mensajes:**
  - Fuente inexistente: "La fuente '{nombre}' no existe. Fuentes válidas: SECOP II — Contratos, SECOP II — Archivos, TVEC — Ítems, TVEC — Órdenes, Alkosto, Falabella."
  - Sin ejecuciones (detalle): "La fuente {nombre} no tiene ejecuciones registradas."
  - Sin permiso: "Acción no permitida: esta consulta requiere el rol Administrador."
  - Sin sesión o credencial válida: "Debe autenticarse como Administrador para consultar el estado de fuentes."

### Interfaz

No requiere interfaz gráfica. Mecanismo mínimo aceptable: un comando, script o consulta administrativa con dos operaciones, "resumen de fuentes" y "detalle de fuente {nombre}", que entregan un reporte legible (tabla de texto o archivo CSV/JSON) con los campos de RN-03 y RN-04. Si la arquitectura opta por una vista administrativa mínima, debe mostrar el mismo contenido y los mismos mensajes.

### Sistemas Externos (Si aplica)

No consulta sistemas externos en tiempo real: lee los registros internos que dejan las ingestas de datos.gov.co (SECOP II, TVEC) y las capturas o cargas de Alkosto y Falabella.

---

## Contexto y Referencias

**Épica origen:** [Operación, Calidad y Medición del MVP](../../../epicas.md#épica-008-operación-calidad-y-medición-del-mvp)

**Exclusiones de la Épica:**
- NO incluye analítica de uso avanzada ni embudos de producto.
- NO incluye facturación ni gestión de planes.
- NO incluye administración multi-organización.

**Historias relacionadas:** HU-099 (relanzar ingesta o captura), HU-100 (alertas de fallas), HU-102 (frecuencias de ingesta y captura).

---

## Supuestos

> Elementos inferidos por la IA que NO estaban explícitos en el PRD o la Épica. Todos los supuestos han sido resueltos: convertidos en reglas de negocio explícitas o eliminados mediante reformulación. Si aparece algún supuesto no resuelto, esta HU NO está lista para desarrollo.

- El catálogo de fuentes separa SECOP II y TVEC en sus datasets operativos (contratos, archivos, ítems, órdenes) para ubicar la falla con precisión → resuelto en RN-01.
- Se incorpora el estado "Retrasada" con tolerancia configurable (inicial 1 hora) para detectar ingestas que no se ejecutaron → resuelto en RN-05 y RN-07.
- Los rechazados por calidad no degradan el estado de la fuente; solo los errores lo hacen → resuelto en RN-05.

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
