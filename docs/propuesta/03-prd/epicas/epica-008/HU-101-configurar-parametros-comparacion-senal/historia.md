# Historia #101: Configurar y versionar los parámetros de comparación y señal

**Estado:** Borrador (PO)  
**Release:** Release MVP  
**Épica:** [Operación, Calidad y Medición del MVP](../../../epicas.md#épica-008-operación-calidad-y-medición-del-mvp)  
**Feature:** Configurar Parámetros del Análisis  
**Prioridad:** Alta  
**FRs relacionados:** FR-089 (relacionados: FR-055, FR-056, FR-058, FR-063, FR-094)

Escrita por el flujo generar-historias-usuario (Método Ceiba) — MVP propio, no comercial

---

## Historia de Usuario

**Como** Administrador del MVP (el PO),  
**Quiero** cambiar los parámetros analíticos de los benchmarks y de la señal (ventanas temporales, mínimos de observaciones, regla de atípicos y umbrales porcentuales) dejando cada cambio versionado y auditado,  
**Para** recalibrar el análisis con evidencia real sin redesplegar el sistema y poder reproducir después con qué configuración se calculó cada señal.

## Descripción

El PRD define los valores de partida como **configuración inicial**, no como verdades fijas (P-01, P-02, P-03): ventanas de ±6 meses (ampliable a ±12) para el Benchmark 1 y ±30 días para el Benchmark 2; mínimos de ≥ 5 comparables (Benchmark 1) y ≥ 3 observaciones de al menos 2 fuentes (Benchmark 2); regla de atípicos Q3 + 1,5 × IQR con muestra suficiente; y umbrales provisionales de mismo modelo ≥ +30 % y producto equivalente ≥ +50 %. Estos umbrales **solo priorizan** casos que merecen revisión.

Esta HU permite consultar y cambiar esos parámetros. Cada cambio crea una **versión** inmutable de la configuración completa, con usuario, fecha, motivo y valores anteriores, y registra el cambio en el log de auditoría. Los cálculos posteriores usan la versión vigente; los ya calculados conservan la versión con que se hicieron (factor crítico de la épica: "los parámetros deben versionarse para reproducir señales pasadas").

La configuración versionada es **una sola** para todos los parámetros analíticos y operativos; los parámetros de identificación, extracción y frecuencias se gestionan con el mismo mecanismo en HU-102.

**Implementación sin UI permitida:** archivo o tabla de configuración con un comando de aplicación, script o interfaz administrativa mínima, siempre que se cumplan las validaciones, el versionado y la auditoría de esta HU.

---

## Criterios de Aceptación

### Escenario 1: Consultar la configuración vigente

- **Dado** que la configuración vigente es la versión 3
- **Cuando** el Administrador consulta la configuración analítica
- **Entonces** obtiene el número de versión, su fecha y hora de vigencia, el usuario que la creó y, para cada parámetro de RN-01, su nombre, valor vigente, unidad, rango permitido y valor de configuración inicial

### Escenario 2: Cambiar un parámetro válido

- **Dado** que la versión vigente es la 3 con umbral de mismo modelo = 30 %
- **Cuando** el Administrador cambia el umbral de mismo modelo a 25 % con el motivo "Recalibración con 40 señales validadas en septiembre"
- **Entonces** se crea la versión 4 con todos los parámetros de la versión 3 y el umbral en 25 %, vigente desde la fecha y hora del guardado; se registra un evento de auditoría con usuario, fecha y hora, parámetro, valor anterior 30, valor nuevo 25, versión 4 y motivo; y la respuesta es "Configuración guardada como versión 4."

### Escenario 3: Cambiar varios parámetros a la vez

- **Dado** que la versión vigente es la 4
- **Cuando** el Administrador cambia en una sola operación la ventana del Benchmark 1 a 4 meses y el mínimo de observaciones del Benchmark 1 a 7, con motivo válido
- **Entonces** se crea una sola versión (5) con ambos cambios y se registran dos eventos de auditoría, uno por parámetro, ambos con versión 5

### Escenario 4: Valor fuera de rango o con formato inválido

- **Dado** que la versión vigente es la 5
- **Cuando** el Administrador intenta fijar la ventana del Benchmark 2 en 400 días, o en "treinta", o dejarla vacía
- **Entonces** no se crea versión, nada cambia y recibe "El valor de ventana_b2_dias debe ser un número entero entre 1 y 365."

### Escenario 5: Un valor inválido en un cambio múltiple rechaza todo

- **Dado** que el Administrador envía tres cambios y uno de ellos está fuera de rango
- **Cuando** el sistema valida la solicitud
- **Entonces** no aplica ninguno de los tres, no crea versión y devuelve el mensaje de cada parámetro inválido

### Escenario 6: Inconsistencia entre parámetros

- **Dado** que la ventana del Benchmark 1 vigente es 6 meses
- **Cuando** el Administrador fija la ventana ampliada en 5 meses, o fija el mínimo de fuentes del Benchmark 2 en 4 con un mínimo de observaciones del Benchmark 2 de 3
- **Entonces** no se crea versión y recibe, respectivamente, "La ventana ampliada del Benchmark 1 (5) no puede ser menor que la ventana base (6)." o "El mínimo de fuentes del Benchmark 2 (4) no puede ser mayor que el mínimo de observaciones del Benchmark 2 (3)."

### Escenario 7: Umbral de equivalente menor que el de mismo modelo

- **Dado** que el umbral de mismo modelo vigente es 30 %
- **Cuando** el Administrador fija el umbral de producto equivalente en 20 % con motivo válido
- **Entonces** el cambio se guarda como nueva versión y la respuesta incluye la advertencia "Advertencia: el umbral de producto equivalente (20 %) es menor que el de mismo modelo (30 %)."

### Escenario 8: Motivo ausente o fuera de longitud

- **Dado** que el Administrador envía un cambio válido
- **Cuando** omite el motivo o este tiene menos de 10 o más de 500 caracteres
- **Entonces** no se crea versión y recibe "Debe indicar un motivo del cambio de 10 a 500 caracteres."

### Escenario 9: Cambio sin diferencias

- **Dado** que el umbral de equivalente vigente es 50 %
- **Cuando** el Administrador envía el valor 50 como único cambio
- **Entonces** no se crea versión y recibe "No hay cambios respecto a la versión vigente."

### Escenario 10: Parámetro inexistente

- **Dado** que el Administrador está autenticado
- **Cuando** envía un cambio para "umbral_sobreprecio"
- **Entonces** no se crea versión y recibe "El parámetro 'umbral_sobreprecio' no existe."

### Escenario 11: Cambio concurrente

- **Dado** que el Administrador consultó la versión 5 para editarla y, antes de guardar, se creó la versión 6
- **Cuando** intenta guardar su cambio indicando que parte de la versión 5
- **Entonces** no se crea versión y recibe "La configuración cambió (versión vigente 6) desde que la consultó. Vuelva a consultarla y repita el cambio."

### Escenario 12: Consultar historial y versión vigente en una fecha

- **Dado** que existen las versiones 1 a 6
- **Cuando** el Administrador consulta el historial o pide la versión vigente el 2026-09-15 14:00
- **Entonces** el historial lista las 6 versiones de la más reciente a la más antigua con número, fecha de vigencia, usuario, motivo y parámetros cambiados (anterior → nuevo); y la consulta por fecha devuelve la versión cuya vigencia empezó en o antes de esa fecha y hora y terminó después, con todos sus valores

### Escenario 13: Fecha anterior a la primera versión

- **Dado** que la versión 1 está vigente desde 2026-09-01 00:00
- **Cuando** el Administrador pide la versión vigente el 2026-08-31 23:59
- **Entonces** recibe "No existía configuración vigente en 2026-08-31 23:59; la primera versión rige desde 2026-09-01 00:00."

### Escenario 14: Restaurar una versión anterior

- **Dado** que la versión vigente es la 6
- **Cuando** el Administrador restaura la versión 3 con el motivo "Volver a la configuración inicial del piloto"
- **Entonces** se crea la versión 7 con los valores exactos de la versión 3, la versión 3 no se modifica, se registra un evento de auditoría por cada parámetro que cambia, y la respuesta es "Configuración guardada como versión 7 (restaurada desde la versión 3)."

### Escenario 15: Los cálculos ya hechos no cambian

- **Dado** que una señal se calculó con la versión 3
- **Cuando** se crea la versión 4 con otro umbral
- **Entonces** la señal existente conserva su resultado y su referencia a la versión 3; los cálculos que inicien después de la vigencia de la versión 4 usan la versión 4, y un cálculo ya en curso termina con la versión con que inició

### Escenario 16: Falla del registro de auditoría

- **Dado** que el log de auditoría no está disponible
- **Cuando** el Administrador guarda un cambio válido
- **Entonces** no se crea la versión y recibe "No fue posible registrar la auditoría; el cambio no se aplicó. Intente de nuevo."

### Escenario 17: Usuario sin rol Administrador

- **Dado** que un usuario con rol Analista está autenticado
- **Cuando** intenta consultar o cambiar la configuración
- **Entonces** no obtiene datos ni cambia nada y recibe "Acción no permitida: esta operación requiere el rol Administrador."

---

## Información Recopilada

### Usuario y Contexto

- **Tipo de usuario:** Administrador (en el MVP, el PO).
- **Permisos requeridos:** rol Administrador para consultar, cambiar y restaurar.
- **Valor de negocio:** permite recalibrar los umbrales con evidencia real (reducir señales sin sustento, KPI ≥ 70 % de señales sustentadas) sin redespliegue y manteniendo la reproducibilidad de cada señal.

### Reglas de Negocio

- **RN-01 — Parámetros de esta HU (todos obligatorios, sin nulos):**

  | Nombre | Descripción | Tipo | Rango | Configuración inicial |
  |---|---|---|---|---|
  | `ventana_b1_meses` | Ventana del Benchmark 1, ± meses desde la fecha de la compra | entero | 1–24 | 6 |
  | `ventana_b1_ampliada_meses` | Ventana ampliada del Benchmark 1 cuando no hay comparables suficientes | entero | 1–36 | 12 |
  | `ventana_b2_dias` | Ventana del Benchmark 2, ± días desde la fecha de la compra | entero | 1–365 | 30 |
  | `minimo_obs_b1` | Mínimo de observaciones comparables para referencia agregada del Benchmark 1 | entero | 1–100 | 5 |
  | `minimo_obs_b2` | Mínimo de observaciones para referencia agregada del Benchmark 2 | entero | 1–100 | 3 |
  | `minimo_fuentes_b2` | Mínimo de fuentes distintas para referencia agregada del Benchmark 2 | entero | 1–10 | 2 |
  | `minimo_obs_atipicos` | Tamaño mínimo de muestra para aplicar la regla de atípicos | entero | 4–100 | 5 |
  | `multiplicador_iqr` | Multiplicador k de la regla Q3 + k × IQR | decimal (máx. 2 decimales) | 0,50–5,00 | 1,50 |
  | `umbral_mismo_modelo_pct` | Desviación mínima por encima de la referencia para señal con emparejamiento mismo modelo | decimal (máx. 1 decimal) | 0,0–500,0 | 30,0 |
  | `umbral_equivalente_pct` | Desviación mínima por encima de la referencia para señal con producto equivalente | decimal (máx. 1 decimal) | 0,0–500,0 | 50,0 |

  Los decimales se aceptan con punto o coma como separador. Un valor vacío, nulo, no numérico, con más decimales de los permitidos o fuera de rango se rechaza con: "El valor de {nombre} debe ser un número {entero|decimal} entre {mín} y {máx}."
- **RN-02 — Consistencia entre parámetros (bloqueante):** `ventana_b1_ampliada_meses` ≥ `ventana_b1_meses`; `minimo_fuentes_b2` ≤ `minimo_obs_b2`. Se evalúa sobre los valores resultantes (vigentes + cambios).
- **RN-03 — Advertencia (no bloqueante):** si `umbral_equivalente_pct` < `umbral_mismo_modelo_pct`, se guarda y se devuelve "Advertencia: el umbral de producto equivalente ({x} %) es menor que el de mismo modelo ({y} %)."
- **RN-04 — Solicitud de cambio:** contiene uno o más pares parámetro → valor nuevo, la versión de partida y un motivo de 10 a 500 caracteres (sin contar espacios al inicio y al final). La validación es todo o nada: si un parámetro falla, no se aplica ninguno y se devuelven todos los mensajes de error.
- **RN-05 — Versión:** cada cambio aceptado crea una versión con número entero consecutivo (la versión 1 es la configuración inicial, creada por el usuario "sistema" al instalar), que guarda los valores de **todos** los parámetros de la configuración (los de esta HU y los operativos de HU-102), la fecha y hora de inicio de vigencia (el instante del guardado; no se admiten vigencias futuras ni retroactivas), el usuario, el motivo y la lista de parámetros cambiados con valor anterior y nuevo. Las versiones son inmutables y no se eliminan.
- **RN-06 — Control de concurrencia:** si la versión de partida de la solicitud no es la vigente, se rechaza con "La configuración cambió (versión vigente {n}) desde que la consultó. Vuelva a consultarla y repita el cambio."
- **RN-07 — Sin cambios:** si todos los valores enviados son iguales a los vigentes, se rechaza con "No hay cambios respecto a la versión vigente."
- **RN-08 — Aplicación:** la nueva versión aplica a todo cálculo de benchmark o señal que inicie a partir de su vigencia, sin redespliegue. Un cálculo en curso termina con la versión con la que inició. Todo cálculo de benchmark o señal debe registrar el número de versión que usó. Un cambio no recalcula ni modifica retroactivamente benchmarks o señales ya calculados.
- **RN-09 — Restaurar:** "restaurar versión N" crea una nueva versión con los valores exactos de N (motivo obligatorio, mismas validaciones de RN-04 y RN-07). Si N no existe: "La versión {N} no existe."
- **RN-10 — Consultas:** (a) vigente; (b) por número de versión; (c) vigente en una fecha y hora `AAAA-MM-DD HH:MM` (UTC−05:00): la de mayor inicio de vigencia ≤ esa fecha y hora; si es anterior a la versión 1: "No existía configuración vigente en {fecha}; la primera versión rige desde {fecha_v1}."; (d) historial completo de la más reciente a la más antigua.
- **RN-11 — Auditoría:** por cada parámetro cambiado se registra un evento "Cambio de configuración" con usuario, fecha y hora, parámetro, valor anterior, valor nuevo, número de versión y motivo. La versión y sus eventos se guardan juntos: si la auditoría falla, no se crea la versión y se responde "No fue posible registrar la auditoría; el cambio no se aplicó. Intente de nuevo."
- **RN-12 — Mensajes adicionales:** éxito "Configuración guardada como versión {n}."; restauración "Configuración guardada como versión {n} (restaurada desde la versión {N})."; parámetro desconocido "El parámetro '{nombre}' no existe."; motivo inválido "Debe indicar un motivo del cambio de 10 a 500 caracteres."; sin permiso "Acción no permitida: esta operación requiere el rol Administrador."
- **RN-13 — Naturaleza de los umbrales:** las descripciones de los parámetros de señal deben referirse a "señal que merece revisión"; ningún nombre, descripción o mensaje usa los términos "sobreprecio", "corrupción", "fraude" ni "hallazgo fiscal".

### Interfaz

No requiere interfaz gráfica. Mínimo aceptable: un archivo o tabla de configuración y un comando o acción administrativa para (a) consultar la vigente, (b) aplicar cambios con motivo y versión de partida, (c) restaurar una versión, (d) consultar historial y versión vigente en una fecha. Las respuestas usan los mensajes de RN-12.

### Sistemas Externos (Si aplica)

No aplica.

---

## Contexto y Referencias

**Épica origen:** [Operación, Calidad y Medición del MVP](../../../epicas.md#épica-008-operación-calidad-y-medición-del-mvp)

**Exclusiones de la Épica:**
- NO incluye analítica de uso avanzada ni embudos de producto.
- NO incluye facturación ni gestión de planes.
- NO incluye administración multi-organización.

**Historias relacionadas:** HU-102 (parámetros de identificación, extracción y operación), HU-112 (log de auditoría).

---

## Supuestos

> Elementos inferidos por la IA que NO estaban explícitos en el PRD o la Épica. Todos los supuestos han sido resueltos: convertidos en reglas de negocio explícitas o eliminados mediante reformulación. Si aparece algún supuesto no resuelto, esta HU NO está lista para desarrollo.

- La "muestra suficiente" para aplicar la regla de atípicos se expresa como un parámetro configurable (`minimo_obs_atipicos`, inicial 5, igual al mínimo del Benchmark 1); la homogeneidad la evalúa la lógica de señales → resuelto en RN-01.
- Los rangos permitidos de cada parámetro (ej. ventana B2 de 1 a 365 días) son límites de cordura definidos por el PO, no valores analíticos → resuelto en RN-01.
- Una sola configuración versionada agrupa parámetros analíticos y operativos; cada versión es una instantánea completa → resuelto en RN-05.
- Los cambios no son retroactivos y no hay vigencias programadas a futuro → resuelto en RN-05 y RN-08.

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
