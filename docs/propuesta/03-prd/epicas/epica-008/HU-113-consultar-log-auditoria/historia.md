# Historia #113: Consultar y exportar el log de auditoría

**Estado:** Borrador (PO)  
**Release:** Release MVP  
**Épica:** [Operación, Calidad y Medición del MVP](../../../epicas.md#épica-008-operación-calidad-y-medición-del-mvp)  
**Feature:** Auditar Acciones Administrativas  
**Prioridad:** Alta  
**FRs relacionados:** FR-094 (relacionados: FR-070; NFR-SEG-007)

Escrita por el flujo generar-historias-usuario (Método Ceiba) — MVP propio, no comercial

---

## Historia de Usuario

**Como** Administrador del MVP (el PO),  
**Quiero** consultar el log de auditoría con filtros, ver la historia completa de cambios de un registro y exportar el resultado,  
**Para** responder con evidencia quién cambió un dato, una clasificación, una observación o un parámetro, cuándo, desde qué valor y por qué.

## Descripción

El log de auditoría (HU-112) registra las correcciones, clasificaciones manuales, cargas manuales, cambios de configuración y demás acciones administrativas. Esta HU permite **leerlo**: búsqueda filtrada y paginada, detalle de un evento, historia cronológica de una entidad (ej. "todos los cambios del precio unitario del ítem 1 de CO1.PCCNTR.5030063") y exportación CSV. Es la base para atender un reporte de error de un analista (FR-070) o el reclamo de un proveedor.

**Implementación sin UI permitida:** comando, consulta o exportación CSV; o interfaz administrativa mínima con los mismos filtros.

---

## Criterios de Aceptación

### Escenario 1: Consulta por defecto

- **Dado** que existen eventos en los últimos 30 días
- **Cuando** el Administrador consulta el log sin filtros
- **Entonces** obtiene los eventos de los últimos 30 días, del más reciente al más antiguo, en páginas de 50, con todos sus campos (id, fecha y hora, usuario, rol, tipo, entidad, campo o parámetro, valor anterior, valor nuevo, motivo, origen, id de operación, referencias)

### Escenario 2: Filtros combinados

- **Dado** que existen eventos de varios tipos y usuarios
- **Cuando** el Administrador filtra por tipo "Cambio de configuración", usuario `admin.po@prueba.co` y rango 2026-09-01 a 2026-09-30
- **Entonces** obtiene solo los eventos que cumplen los tres filtros

### Escenario 3: Historia de una entidad

- **Dado** que el precio unitario del ítem 1 de CO1.PCCNTR.5030063 fue corregido dos veces y validado una vez
- **Cuando** el Administrador pide la historia de esa entidad
- **Entonces** obtiene los 3 eventos en orden cronológico ascendente, con valores anterior y nuevo de cada uno

### Escenario 4: Eventos de una acción masiva

- **Dado** que una carga CSV generó 12 eventos con el mismo id de operación
- **Cuando** el Administrador filtra por ese id de operación
- **Entonces** obtiene los 12 eventos

### Escenario 5: Detalle de un evento

- **Dado** que existe el evento 1520
- **Cuando** el Administrador pide su detalle
- **Entonces** obtiene todos sus campos, incluidos los valores completos hasta 4.000 caracteres y, si fue truncado, la marca "[truncado]" y el hash del valor completo

### Escenario 6: Evento inexistente

- **Dado** que no existe el evento 999999
- **Cuando** el Administrador pide su detalle
- **Entonces** recibe "El evento 999999 no existe o fue depurado por la política de retención."

### Escenario 7: Exportar a CSV

- **Dado** que el filtro devuelve 1.250 eventos
- **Cuando** el Administrador exporta
- **Entonces** obtiene un CSV UTF-8 con encabezado y 1.250 filas, sin paginar

### Escenario 8: Exportación demasiado grande

- **Dado** que el filtro devuelve 120.000 eventos
- **Cuando** el Administrador exporta
- **Entonces** no se genera el archivo y recibe "La exportación supera 100000 eventos; acote el rango de fechas u otros filtros."

### Escenario 9: Período depurado

- **Dado** que la retención es 12 meses y el evento más antiguo conservado es del 2025-10-02
- **Cuando** el Administrador consulta el rango 2025-06-01 a 2025-12-31
- **Entonces** obtiene los eventos desde 2025-10-02 y la nota "Los eventos anteriores a 2025-10-02 fueron depurados por la política de retención (12 meses)."

### Escenario 10: Sin resultados

- **Dado** que ningún evento cumple los filtros
- **Cuando** el Administrador consulta
- **Entonces** recibe "No hay eventos de auditoría que cumplan los filtros."

### Escenario 11: Filtros inválidos

- **Dado** que el Administrador está autenticado
- **Cuando** usa un tipo inexistente, una fecha con formato inválido, un rango con inicio posterior al fin, un rango de más de 366 días o una página de 0 o 501 eventos
- **Entonces** no obtiene resultados y recibe el mensaje correspondiente de RN-07

### Escenario 12: Consultar no genera eventos

- **Dado** que el Administrador consulta y exporta el log
- **Cuando** se revisa el log
- **Entonces** no se agregaron eventos por esas consultas

### Escenario 13: Usuario sin rol Administrador

- **Dado** que un usuario con rol Analista está autenticado
- **Cuando** intenta consultar, ver el detalle o exportar el log
- **Entonces** recibe "Acción no permitida: esta operación requiere el rol Administrador."

---

## Información Recopilada

### Usuario y Contexto

- **Tipo de usuario:** Administrador (en el MVP, el PO).
- **Permisos requeridos:** rol Administrador.
- **Valor de negocio:** permite explicar cualquier cambio sobre datos y parámetros que sustentan las señales; base para gestionar reportes de error y reclamos.

### Reglas de Negocio

- **RN-01 — Filtros (combinables con Y):** rango de fechas `AAAA-MM-DD` con extremos incluidos (por defecto, los últimos 30 días incluyendo hoy; máximo 366 días); usuario (correo exacto, sin distinguir mayúsculas); tipo de evento (uno o varios de: Corrección de dato extraído, Clasificación manual, Carga manual de observación, Carga semiautomática de observación, Cambio de configuración, Reactivación de fuente, Marcado de muestra de validación, Retiro de muestra de validación, Carga de resultados de validación, Depuración de auditoría); tipo e identificador de entidad (coincidencia exacta); campo o parámetro (coincidencia exacta); id de operación.
- **RN-02 — Orden y paginación:** fecha y hora descendente y, ante empate, id descendente. Tamaño de página entero de 1 a 500; por defecto 50.
- **RN-03 — Historia de una entidad:** dado el tipo e identificador de entidad (y opcionalmente el campo), devuelve todos sus eventos conservados en orden cronológico ascendente, sin límite de rango de fechas.
- **RN-04 — Detalle:** por id de evento; muestra todos los campos almacenados. Los valores enmascarados ("****") se muestran enmascarados.
- **RN-05 — Exportación:** CSV UTF-8, separador coma, con encabezado y todos los campos; incluye todo el resultado filtrado sin paginar; máximo 100.000 eventos.
- **RN-06 — Retención:** si el rango consultado empieza antes del evento más antiguo conservado, se agrega la nota "Los eventos anteriores a {fecha} fueron depurados por la política de retención ({n} meses)."
- **RN-07 — Mensajes:**
  - "No hay eventos de auditoría que cumplan los filtros."
  - "El evento {id} no existe o fue depurado por la política de retención."
  - "El tipo de evento '{x}' no es válido."
  - "La fecha '{x}' no tiene el formato AAAA-MM-DD."
  - "La fecha inicial no puede ser posterior a la fecha final."
  - "El rango de consulta no puede superar 366 días."
  - "El tamaño de página debe estar entre 1 y 500."
  - "La exportación supera 100000 eventos; acote el rango de fechas u otros filtros."
  - "Acción no permitida: esta operación requiere el rol Administrador."
- **RN-08 — Solo lectura:** consultar, ver detalle y exportar no modifican el log ni generan eventos de auditoría.

### Interfaz

No requiere interfaz gráfica. Mínimo aceptable: comandos o consultas "buscar en auditoría" (filtros de RN-01, orden y paginación de RN-02), "historia de entidad", "detalle de evento" y "exportar auditoría".

### Sistemas Externos (Si aplica)

No aplica.

---

## Contexto y Referencias

**Épica origen:** [Operación, Calidad y Medición del MVP](../../../epicas.md#épica-008-operación-calidad-y-medición-del-mvp)

**Exclusiones de la Épica:**
- NO incluye analítica de uso avanzada ni embudos de producto.
- NO incluye facturación ni gestión de planes.
- NO incluye administración multi-organización.

**Historias relacionadas:** HU-112 (registro del log de auditoría).

---

## Supuestos

> Elementos inferidos por la IA que NO estaban explícitos en el PRD o la Épica. Todos los supuestos han sido resueltos: convertidos en reglas de negocio explícitas o eliminados mediante reformulación. Si aparece algún supuesto no resuelto, esta HU NO está lista para desarrollo.

- La consulta por defecto cubre los últimos 30 días y el rango máximo es de 366 días → resuelto en RN-01.
- La exportación se limita a 100.000 eventos por archivo → resuelto en RN-05.
- La historia de una entidad no tiene límite de fechas dentro de lo conservado → resuelto en RN-03.

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
