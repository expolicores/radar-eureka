# Historia #102: Configurar términos de búsqueda, umbral de aceptación de extracción y frecuencias

**Estado:** Borrador (PO)  
**Release:** Release MVP  
**Épica:** [Operación, Calidad y Medición del MVP](../../../epicas.md#épica-008-operación-calidad-y-medición-del-mvp)  
**Feature:** Configurar Parámetros del Análisis  
**Prioridad:** Alta  
**FRs relacionados:** FR-089 (relacionados: FR-003, FR-011, FR-012, FR-028, FR-094; NFR-DAT-001, NFR-DAT-003)

Escrita por el flujo generar-historias-usuario (Método Ceiba) — MVP propio, no comercial

---

## Historia de Usuario

**Como** Administrador del MVP (el PO),  
**Quiero** configurar los términos de búsqueda de candidatos, el umbral de aceptación automática de la extracción y las frecuencias de ingesta y captura de cada fuente, con versionado y auditoría,  
**Para** ajustar la identificación de televisores, la carga de revisión humana y el ritmo de actualización de los datos sin redesplegar el sistema.

## Descripción

FR-089 exige que el Administrador configure, además de los parámetros analíticos (HU-101), estos parámetros operativos:

- **Términos de búsqueda** de candidatos en el objeto o descripción (configuración inicial: "televisor", "smart tv", "tv"; FR-011, FR-012).
- **Umbral de aceptación automática** de datos extraídos (FR-028, P-15): **no se fija un valor arbitrario**; el valor sale de la calibración con la validación manual D4-4. Mientras no exista calibración, el umbral está "sin calibrar" y los datos críticos de confianza baja o incierta van a revisión humana.
- **Frecuencias** de ingesta pública (configuración inicial: diaria, P-13) y de captura retail automática (configuración inicial: semanal, P-14).

Estos parámetros forman parte de la **misma configuración versionada** de HU-101: cada cambio crea una versión completa e inmutable, con usuario, fecha, motivo y valores anteriores, y se registra en el log de auditoría. Las reglas de versionado se repiten aquí para que esta HU sea implementable por sí sola.

**Implementación sin UI permitida:** archivo o tabla de configuración con comando de aplicación, script o interfaz administrativa mínima.

---

## Criterios de Aceptación

### Escenario 1: Consultar los parámetros operativos vigentes

- **Dado** que la versión vigente es la 4
- **Cuando** el Administrador consulta los parámetros operativos
- **Entonces** obtiene la versión, su vigencia y, para cada parámetro de RN-01, nombre, valor vigente, unidad, rango o formato permitido y configuración inicial; el umbral de aceptación se muestra como "sin calibrar" si no tiene valor

### Escenario 2: Agregar un término de búsqueda

- **Dado** que los términos vigentes son "televisor", "smart tv", "tv"
- **Cuando** el Administrador fija los términos "televisor", "smart tv", "tv", "pantalla led tv" con motivo válido
- **Entonces** se crea una nueva versión con los 4 términos, se registra un evento de auditoría con la lista anterior y la nueva, y la respuesta es "Configuración guardada como versión {n}."

### Escenario 3: Términos inválidos

- **Dado** que el Administrador está autenticado
- **Cuando** envía una lista vacía, un término de 1 carácter ("t"), un término de más de 50 caracteres, un término con caracteres no permitidos ("tv;drop") o términos repetidos ("TV" y "tv")
- **Entonces** no se crea versión y recibe, respectivamente, "Debe existir al menos un término de búsqueda.", "El término 't' debe tener entre 2 y 50 caracteres.", el mismo mensaje con el término largo, "El término 'tv;drop' solo puede contener letras, números, espacios y guiones." y "El término 'tv' está repetido."

### Escenario 4: Fijar el umbral de aceptación con referencia de calibración

- **Dado** que el umbral está "sin calibrar"
- **Cuando** el Administrador lo fija en 0,85 con la referencia de calibración "D4-4: 228 filas validadas, relación confianza-corrección del 2026-10-20" y motivo válido
- **Entonces** se crea una nueva versión con umbral 0,85 y esa referencia, y el evento de auditoría registra anterior "sin calibrar", nuevo 0,85 y la referencia

### Escenario 5: Umbral sin referencia de calibración

- **Dado** que el umbral está "sin calibrar"
- **Cuando** el Administrador intenta fijarlo en 0,90 sin referencia de calibración o con una de menos de 10 caracteres
- **Entonces** no se crea versión y recibe "Para fijar el umbral de aceptación automática debe indicar la referencia de calibración (10 a 200 caracteres)."

### Escenario 6: Umbral fuera de rango

- **Dado** que el Administrador está autenticado
- **Cuando** intenta fijar el umbral en 1,5, en -0,1, en 0,855 o en "alto"
- **Entonces** no se crea versión y recibe "El umbral de aceptación automática debe ser un decimal entre 0,00 y 1,00 con máximo 2 decimales, o 'sin calibrar'."

### Escenario 7: Volver a "sin calibrar"

- **Dado** que el umbral vigente es 0,85
- **Cuando** el Administrador lo cambia a "sin calibrar" con motivo válido
- **Entonces** se crea una nueva versión con el umbral "sin calibrar" y la referencia de calibración vacía, y a partir de su vigencia los datos críticos de confianza baja o incierta vuelven a dirigirse a revisión humana

### Escenario 8: Cambiar la frecuencia de ingesta de una fuente pública

- **Dado** que la frecuencia de "TVEC — Ítems" es 24 horas y su última ejecución inició a las 2026-10-02 01:00
- **Cuando** el Administrador la cambia a 12 horas con motivo válido
- **Entonces** se crea una nueva versión y la próxima ejecución esperada de "TVEC — Ítems" pasa a ser 2026-10-02 13:00

### Escenario 9: Frecuencia que deja la fuente vencida

- **Dado** que "SECOP II — Contratos" inició su última ejecución hace 10 horas
- **Cuando** el Administrador cambia su frecuencia a 6 horas
- **Entonces** la nueva frecuencia queda vigente y la fuente se ejecuta en el siguiente ciclo del programador, sin esperar 6 horas más

### Escenario 10: Frecuencias fuera de rango

- **Dado** que el Administrador está autenticado
- **Cuando** intenta fijar la frecuencia de ingesta de "TVEC — Órdenes" en 0 o 169 horas, o la de captura de "Alkosto" en 0 o 31 días, o cualquiera en un valor no entero
- **Entonces** no se crea versión y recibe "La frecuencia de ingesta de TVEC — Órdenes debe ser un número entero entre 1 y 168 horas." o "La frecuencia de captura de Alkosto debe ser un número entero entre 1 y 30 días."

### Escenario 11: Validación todo o nada

- **Dado** que el Administrador envía en una sola solicitud un término válido nuevo y una frecuencia inválida
- **Cuando** el sistema valida
- **Entonces** no aplica ningún cambio, no crea versión y devuelve el mensaje de la frecuencia inválida

### Escenario 12: Motivo, cambios vacíos, concurrencia y auditoría

- **Dado** que el Administrador envía un cambio
- **Cuando** omite el motivo, no cambia ningún valor, parte de una versión que ya no es la vigente, o el log de auditoría no está disponible
- **Entonces** no se crea versión y recibe, respectivamente, "Debe indicar un motivo del cambio de 10 a 500 caracteres.", "No hay cambios respecto a la versión vigente.", "La configuración cambió (versión vigente {n}) desde que la consultó. Vuelva a consultarla y repita el cambio." o "No fue posible registrar la auditoría; el cambio no se aplicó. Intente de nuevo."

### Escenario 13: Los cambios no son retroactivos

- **Dado** que se agrega el término "pantalla led tv"
- **Cuando** corre la siguiente ingesta
- **Entonces** el nuevo término se aplica a los registros procesados desde la vigencia de la nueva versión; los candidatos ya identificados no se recalculan ni se borran por el cambio, y ninguna ejecución de ingesta ni extracción se dispara por el solo hecho de guardar la configuración

### Escenario 14: Usuario sin rol Administrador

- **Dado** que un usuario con rol Analista está autenticado
- **Cuando** intenta consultar o cambiar los parámetros operativos
- **Entonces** recibe "Acción no permitida: esta operación requiere el rol Administrador." y nada cambia

---

## Información Recopilada

### Usuario y Contexto

- **Tipo de usuario:** Administrador (en el MVP, el PO).
- **Permisos requeridos:** rol Administrador.
- **Valor de negocio:** permite ajustar la sensibilidad de identificación de candidatos, la carga de revisión humana (cola de baja confianza) y la frescura de los datos con evidencia, sin redespliegue.

### Reglas de Negocio

- **RN-01 — Parámetros de esta HU:**

  | Nombre | Descripción | Tipo / formato | Rango | Configuración inicial |
  |---|---|---|---|---|
  | `terminos_busqueda` | Términos que marcan candidatos en objeto o descripción (SECOP II) y en la descripción del ítem (TVEC) | lista de textos | 1–30 términos; cada uno de 2 a 50 caracteres | "televisor", "smart tv", "tv" |
  | `umbral_aceptacion_automatica` | Confianza mínima para aceptar un dato extraído sin revisión humana | decimal con máximo 2 decimales, o el valor "sin calibrar" | 0,00–1,00 | sin calibrar |
  | `referencia_calibracion` | Evidencia de calibración del umbral (ej. muestra D4-4) | texto | 10–200 caracteres; vacío solo si el umbral está "sin calibrar" | (vacío) |
  | `frecuencia_ingesta_horas.{fuente}` | Frecuencia de ingesta incremental, una por fuente: SECOP II — Contratos, SECOP II — Archivos, TVEC — Ítems, TVEC — Órdenes | entero (horas) | 1–168 | 24 (diaria) |
  | `frecuencia_captura_dias.{fuente}` | Frecuencia de captura automática, una por fuente: Alkosto, Falabella | entero (días) | 1–30 | 7 (semanal) |

- **RN-02 — Términos de búsqueda:** se quitan espacios al inicio y al final y los espacios internos repetidos se reducen a uno; solo se permiten letras (con o sin tilde), números, espacios y guiones; la comparación para detectar repetidos no distingue mayúsculas ni tildes; el orden de la lista no tiene efecto. El cambio se envía como la lista completa resultante.
- **RN-03 — Umbral de aceptación:** está en la misma escala 0,00–1,00 con la que el extractor registra la confianza de cada dato. Su valor numérico no se interpreta como probabilidad de corrección. Fijar un valor numérico exige `referencia_calibracion` de 10 a 200 caracteres. Cambiar a "sin calibrar" vacía la referencia. Mientras el umbral esté "sin calibrar", los datos críticos (marca, modelo/referencia, tamaño, cantidad, precio unitario) con confianza baja o incierta se dirigen a revisión humana. Los decimales se aceptan con punto o coma.
- **RN-04 — Frecuencias:** la próxima ejecución esperada de cada fuente es inicio de su última ejecución + frecuencia vigente. Si al cambiar la frecuencia ese momento ya pasó, la fuente se ejecuta en el siguiente ciclo del programador. Una fuente retail suspendida o sin captura automática conserva su frecuencia configurada, pero no se ejecuta mientras siga en ese estado. Las frecuencias no modifican los límites de ritmo y volumen de captura.
- **RN-05 — Solicitud y validación:** contiene uno o más cambios, la versión de partida y un motivo de 10 a 500 caracteres (sin contar espacios al inicio y al final). Validación todo o nada; se devuelven todos los mensajes de error.
- **RN-06 — Versionado (compartido con los parámetros analíticos):** cada cambio aceptado crea una versión con número entero consecutivo que guarda los valores de **todos** los parámetros de la configuración, el inicio de vigencia (instante del guardado; sin vigencias futuras ni retroactivas), el usuario, el motivo y los cambios (anterior → nuevo). Las versiones son inmutables y no se eliminan. Si la versión de partida no es la vigente se rechaza (mensaje de concurrencia); si no hay diferencias se rechaza ("No hay cambios respecto a la versión vigente.").
- **RN-07 — Aplicación sin retroactividad:** los procesos (identificación de candidatos, aceptación de extracción, programación de ingestas y capturas) usan la versión vigente al iniciar cada ejecución. Guardar la configuración no dispara ingestas, capturas, extracción ni reclasificación, y no modifica candidatos, datos extraídos ni colas ya existentes. Cada ejecución registra la versión de configuración con la que corrió.
- **RN-08 — Auditoría:** por cada parámetro cambiado se registra un evento "Cambio de configuración" con usuario, fecha y hora (UTC−05:00), parámetro, valor anterior, valor nuevo, versión y motivo (y la referencia de calibración cuando aplique). Si la auditoría falla, no se crea la versión.
- **RN-09 — Mensajes:**
  - "Configuración guardada como versión {n}."
  - "Debe existir al menos un término de búsqueda."
  - "Se permiten como máximo 30 términos de búsqueda."
  - "El término '{t}' debe tener entre 2 y 50 caracteres."
  - "El término '{t}' solo puede contener letras, números, espacios y guiones."
  - "El término '{t}' está repetido."
  - "El umbral de aceptación automática debe ser un decimal entre 0,00 y 1,00 con máximo 2 decimales, o 'sin calibrar'."
  - "Para fijar el umbral de aceptación automática debe indicar la referencia de calibración (10 a 200 caracteres)."
  - "La frecuencia de ingesta de {fuente} debe ser un número entero entre 1 y 168 horas."
  - "La frecuencia de captura de {fuente} debe ser un número entero entre 1 y 30 días."
  - "El parámetro '{nombre}' no existe."
  - "Debe indicar un motivo del cambio de 10 a 500 caracteres."
  - "No hay cambios respecto a la versión vigente."
  - "La configuración cambió (versión vigente {n}) desde que la consultó. Vuelva a consultarla y repita el cambio."
  - "No fue posible registrar la auditoría; el cambio no se aplicó. Intente de nuevo."
  - "Acción no permitida: esta operación requiere el rol Administrador."

### Interfaz

No requiere interfaz gráfica. Mínimo aceptable: el mismo archivo o tabla de configuración y comando de aplicación de HU-101, con la consulta de los parámetros de RN-01 y los mensajes de RN-09.

### Sistemas Externos (Si aplica)

No aplica (no consulta fuentes al guardar).

---

## Contexto y Referencias

**Épica origen:** [Operación, Calidad y Medición del MVP](../../../epicas.md#épica-008-operación-calidad-y-medición-del-mvp)

**Exclusiones de la Épica:**
- NO incluye analítica de uso avanzada ni embudos de producto.
- NO incluye facturación ni gestión de planes.
- NO incluye administración multi-organización.

**Historias relacionadas:** HU-101 (configuración versionada de parámetros analíticos), HU-098 (estado de fuentes y próxima ejecución), HU-103 (cola de revisión humana), HU-112 (auditoría).

---

## Supuestos

> Elementos inferidos por la IA que NO estaban explícitos en el PRD o la Épica. Todos los supuestos han sido resueltos: convertidos en reglas de negocio explícitas o eliminados mediante reformulación. Si aparece algún supuesto no resuelto, esta HU NO está lista para desarrollo.

- El umbral de aceptación arranca "sin calibrar" y solo admite un valor numérico acompañado de una referencia de calibración, para impedir un valor arbitrario (P-15) → resuelto en RN-01 y RN-03.
- Las frecuencias se configuran por fuente (horas para públicas, días para retail) → resuelto en RN-01.
- Cambiar términos no reclasifica el histórico ni dispara procesos → resuelto en RN-07.

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
