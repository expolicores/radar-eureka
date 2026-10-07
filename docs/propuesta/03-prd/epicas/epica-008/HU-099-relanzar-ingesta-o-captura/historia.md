# Historia #099: Relanzar una ingesta o captura y reactivar una fuente suspendida

**Estado:** Borrador (PO)  
**Release:** Release MVP  
**Épica:** [Operación, Calidad y Medición del MVP](../../../epicas.md#épica-008-operación-calidad-y-medición-del-mvp)  
**Feature:** Operar Fuentes de Datos  
**Prioridad:** Alta  
**FRs relacionados:** FR-088 (relacionados: FR-002, FR-003, FR-007, FR-047, FR-094)

Escrita por el flujo generar-historias-usuario (Método Ceiba) — MVP propio, no comercial

---

## Historia de Usuario

**Como** Administrador del MVP (el PO),  
**Quiero** relanzar a demanda la ingesta de una fuente pública o la captura automática de una fuente retail, y reactivar una fuente retail suspendida cuando la restricción haya desaparecido,  
**Para** recuperar la frescura de los datos después de una falla sin esperar a la siguiente ejecución programada y sin saltarme ninguna regla de acceso a las fuentes.

## Descripción

Las ingestas de SECOP II y TVEC y las capturas retail corren con la frecuencia configurada. Cuando una ejecución falla o queda retrasada (ver estado de fuentes), el Administrador necesita lanzar una ejecución inmediata. Esta HU agrega dos operaciones administrativas:

1. **Relanzar** una fuente del catálogo: inicia ya una ejecución con las mismas reglas de una ejecución programada, registrada con origen `manual` y el usuario que la lanzó.
2. **Reactivar** una fuente retail suspendida: deja la fuente activa, con motivo obligatorio y registro en el log de auditoría. Reactivar no evade nada: la siguiente captura vuelve a verificar `robots.txt` y las restricciones de acceso al iniciar.

Relanzar una ingesta **no** dispara el reprocesamiento con IA de documentos ya procesados (FR-003): ingesta y extracción documental son procesos separados.

**Implementación sin UI permitida:** las operaciones pueden exponerse como comandos, scripts o acciones de una interfaz administrativa mínima, con los mensajes de esta HU.

---

## Criterios de Aceptación

### Escenario 1: Relanzar la ingesta de una fuente pública

- **Dado** que "SECOP II — Contratos" no tiene ejecuciones en curso y su última ejecución exitosa dejó como marca de actualización 2026-10-01 23:10
- **Cuando** el Administrador solicita relanzar "SECOP II — Contratos"
- **Entonces** se crea una ejecución con origen `manual`, el usuario del Administrador y resultado `en_curso`; la ingesta lee solo registros con fecha de última actualización posterior o igual a 2026-10-01 23:10; y la respuesta es "Ejecución {id} iniciada para SECOP II — Contratos."

### Escenario 2: Relanzar una fuente pública que nunca tuvo una ejecución exitosa

- **Dado** que "TVEC — Órdenes" no tiene ninguna ejecución exitosa
- **Cuando** el Administrador solicita relanzarla
- **Entonces** la ejecución inicia leyendo desde el inicio de la ventana histórica configurada (configuración inicial: 2023-01-01) y la respuesta es "Ejecución {id} iniciada para TVEC — Órdenes."

### Escenario 3: Relanzar la captura automática de una fuente retail activa

- **Dado** que "Alkosto" tiene captura automática habilitada, no está suspendida y no tiene ejecuciones en curso
- **Cuando** el Administrador solicita relanzarla
- **Entonces** se crea una ejecución de captura con origen `manual`, que respeta los límites de ritmo y volumen configurados para la fuente, y la respuesta es "Ejecución {id} iniciada para Alkosto."

### Escenario 4: Fuente con una ejecución en curso

- **Dado** que "TVEC — Ítems" tiene una ejecución `en_curso` iniciada a las 2026-10-02 07:40
- **Cuando** el Administrador solicita relanzarla
- **Entonces** no se crea una nueva ejecución y la respuesta es "Ya existe una ejecución en curso para TVEC — Ítems, iniciada el 2026-10-02 07:40. Espere a que termine."

### Escenario 5: Doble solicitud de relanzamiento

- **Dado** que el Administrador envía dos solicitudes de relanzar "SECOP II — Contratos" con menos de un segundo de diferencia
- **Cuando** el sistema las procesa
- **Entonces** se crea una sola ejecución; la segunda solicitud recibe el mensaje del Escenario 4

### Escenario 6: Fuente retail suspendida

- **Dado** que "Alkosto" está suspendida con motivo "Cambio en robots.txt que prohíbe la ruta de captura"
- **Cuando** el Administrador solicita relanzarla
- **Entonces** no se crea ejecución y la respuesta es "La fuente Alkosto está suspendida desde 2026-09-28 10:15 (motivo: Cambio en robots.txt que prohíbe la ruta de captura). Reactívela antes de relanzar."

### Escenario 7: Reactivar una fuente suspendida

- **Dado** que "Alkosto" está suspendida
- **Cuando** el Administrador solicita reactivarla con el motivo "Se verificó el robots.txt del 2026-10-02 y la ruta vuelve a estar permitida"
- **Entonces** la fuente deja de estar suspendida, se registra un evento de auditoría de tipo "Reactivación de fuente" con usuario, fecha y hora, estado anterior "Suspendida", estado nuevo "Activa" y el motivo, y la respuesta es "La fuente Alkosto fue reactivada. La próxima captura verificará de nuevo robots.txt y las restricciones de acceso."

### Escenario 8: Reactivar sin motivo válido

- **Dado** que "Alkosto" está suspendida
- **Cuando** el Administrador solicita reactivarla sin motivo o con un motivo de menos de 10 caracteres
- **Entonces** la fuente sigue suspendida, no se registra auditoría y la respuesta es "Debe indicar un motivo de reactivación de 10 a 500 caracteres."

### Escenario 9: Reactivar una fuente que no está suspendida

- **Dado** que "Falabella" no está suspendida
- **Cuando** el Administrador solicita reactivarla
- **Entonces** no cambia nada y la respuesta es "La fuente Falabella no está suspendida."

### Escenario 10: Reactivar una fuente pública

- **Dado** que el Administrador está autenticado
- **Cuando** solicita reactivar "SECOP II — Contratos"
- **Entonces** no cambia nada y la respuesta es "Solo las fuentes retail pueden suspenderse y reactivarse."

### Escenario 11: Fuente retail sin captura automática

- **Dado** que "Falabella" no tiene mecanismo de captura automática habilitado
- **Cuando** el Administrador solicita relanzarla
- **Entonces** no se crea ejecución y la respuesta es "La fuente Falabella no tiene captura automática habilitada; sus observaciones ingresan por carga manual o semiautomática."

### Escenario 12: Límite semanal de volumen alcanzado

- **Dado** que "Alkosto" ya consumió las 2.000 solicitudes de la semana configuradas como límite
- **Cuando** el Administrador solicita relanzarla
- **Entonces** no se crea ejecución y la respuesta es "Se alcanzó el límite semanal de 2000 solicitudes configurado para Alkosto; la captura no se relanzó."

### Escenario 13: La ingesta relanzada no reprocesa con IA documentos ya procesados

- **Dado** que "SECOP II — Archivos" se relanza y entre los registros leídos hay 5 documentos que ya tienen extracción con IA terminada
- **Cuando** la ingesta termina
- **Entonces** esos 5 documentos no se vuelven a enviar a extracción con IA y sus datos extraídos no cambian

### Escenario 14: Relanzar sin duplicar registros

- **Dado** que la ejecución anterior de "SECOP II — Contratos" falló a mitad de camino después de guardar 40 registros
- **Cuando** el Administrador la relanza y la ingesta vuelve a leer esos 40 registros
- **Entonces** los 40 registros se actualizan y no se duplican; la ejecución los cuenta como "actualizados" o sin cambio, nunca como "nuevos"

### Escenario 15: La ejecución relanzada falla

- **Dado** que el Administrador relanzó "SECOP II — Contratos" y la API de datos.gov.co no responde después de los reintentos configurados
- **Cuando** la ejecución termina
- **Entonces** queda registrada con resultado `fallida`, origen `manual`, el usuario y el mensaje de error principal, igual que una ejecución programada fallida

### Escenario 16: Fuente inexistente

- **Dado** que el Administrador está autenticado
- **Cuando** solicita relanzar o reactivar "Éxito"
- **Entonces** no ocurre nada y la respuesta es "La fuente 'Éxito' no existe. Fuentes válidas: SECOP II — Contratos, SECOP II — Archivos, TVEC — Ítems, TVEC — Órdenes, Alkosto, Falabella."

### Escenario 17: Usuario sin rol Administrador

- **Dado** que un usuario con rol Analista está autenticado
- **Cuando** intenta relanzar o reactivar cualquier fuente
- **Entonces** no ocurre nada y la respuesta es "Acción no permitida: esta operación requiere el rol Administrador."

---

## Información Recopilada

### Usuario y Contexto

- **Tipo de usuario:** Administrador (en el MVP, el PO).
- **Permisos requeridos:** rol Administrador para relanzar y para reactivar.
- **Valor de negocio:** reduce el tiempo en que el sistema opera con datos desactualizados después de una falla (NFR-DAT-002: contrato nuevo disponible en ≤ 48 horas) y permite retomar la captura retail solo cuando es legítimo hacerlo.

### Reglas de Negocio

- **RN-01 — Catálogo:** las operaciones aplican a las 6 fuentes: SECOP II — Contratos, SECOP II — Archivos, TVEC — Ítems, TVEC — Órdenes (públicas) y Alkosto, Falabella (retail). El nombre se acepta sin distinguir mayúsculas/minúsculas ni tildes. Una solicitud aplica a una sola fuente.
- **RN-02 — Relanzar fuente pública:** ejecuta la ingesta incremental con las mismas reglas que la ejecución programada: lee los registros con fecha de última actualización mayor o igual a la marca de la última ejecución **exitosa** de esa fuente. Si no existe ninguna ejecución exitosa, lee desde el inicio de la ventana histórica configurada (configuración inicial: 2023-01-01, FR-002). No admite otros rangos de fechas.
- **RN-03 — Relanzar fuente retail:** solo si la fuente tiene captura automática habilitada, no está suspendida y no superó su límite semanal de volumen. La captura usa los límites de ritmo y volumen vigentes (configuración inicial: 1 solicitud cada 2 segundos y 2.000 solicitudes por semana) y verifica `robots.txt` al iniciar, como cualquier captura. Relanzar no amplía ni reinicia los límites.
- **RN-04 — Exclusión mutua:** no puede haber dos ejecuciones `en_curso` de la misma fuente. La verificación y la creación de la ejecución son atómicas: ante solicitudes simultáneas solo una crea ejecución.
- **RN-05 — Registro de la ejecución:** toda ejecución relanzada se registra igual que una programada (fuente, inicio, fin, leídos, nuevos, actualizados, rechazados, errores, resultado, mensaje de error principal), más origen `manual` y el usuario que la lanzó. La operación responde de inmediato con el identificador de la ejecución; la ejecución corre de forma asíncrona.
- **RN-06 — Sin reprocesamiento con IA:** relanzar una ingesta no envía a extracción con IA documentos que ya tengan una extracción terminada ni modifica datos extraídos existentes. Los documentos nuevos siguen el proceso de extracción separado y habitual.
- **RN-07 — Sin duplicados:** releer un registro ya existente (mismo identificador de origen) lo actualiza o lo deja igual; nunca crea un segundo registro. Se cuenta como "actualizado" si cambió algún campo y no se cuenta como "nuevo".
- **RN-08 — Reintentos:** ante caídas o tiempos de espera de la API de datos.gov.co se aplican los reintentos con espera exponencial configurados (configuración inicial: 3). Si se agotan, la ejecución termina `fallida`.
- **RN-09 — Reactivar:** solo aplica a fuentes retail con estado suspendida. Requiere motivo de texto de 10 a 500 caracteres (se ignoran espacios al inicio y al final para contar). Cambia la fuente a activa y registra un evento de auditoría "Reactivación de fuente" con usuario, fecha y hora (UTC−05:00), fuente, estado anterior "Suspendida", estado nuevo "Activa", motivo de la suspensión anterior y motivo de la reactivación. Si el evento de auditoría no puede registrarse, la reactivación no se aplica y la respuesta es "No fue posible registrar la auditoría; la reactivación no se aplicó. Intente de nuevo."
- **RN-10 — Reactivar no lanza ejecución:** la fuente reactivada vuelve a su programación normal; el Administrador puede relanzarla después de reactivarla. Si la siguiente captura vuelve a detectar CAPTCHA, bloqueo, autenticación o prohibición en `robots.txt`, la fuente se suspende de nuevo según la regla de suspensión vigente (FR-047).
- **RN-11 — Mensajes:**
  - Inicio: "Ejecución {id} iniciada para {fuente}."
  - En curso: "Ya existe una ejecución en curso para {fuente}, iniciada el {AAAA-MM-DD HH:MM}. Espere a que termine."
  - Suspendida: "La fuente {fuente} está suspendida desde {AAAA-MM-DD HH:MM} (motivo: {motivo}). Reactívela antes de relanzar."
  - Sin captura automática: "La fuente {fuente} no tiene captura automática habilitada; sus observaciones ingresan por carga manual o semiautomática."
  - Límite de volumen: "Se alcanzó el límite semanal de {n} solicitudes configurado para {fuente}; la captura no se relanzó."
  - Reactivación exitosa: "La fuente {fuente} fue reactivada. La próxima captura verificará de nuevo robots.txt y las restricciones de acceso."
  - Motivo inválido: "Debe indicar un motivo de reactivación de 10 a 500 caracteres."
  - No suspendida: "La fuente {fuente} no está suspendida."
  - Fuente pública en reactivación: "Solo las fuentes retail pueden suspenderse y reactivarse."
  - Fuente inexistente: "La fuente '{nombre}' no existe. Fuentes válidas: SECOP II — Contratos, SECOP II — Archivos, TVEC — Ítems, TVEC — Órdenes, Alkosto, Falabella."
  - Sin permiso: "Acción no permitida: esta operación requiere el rol Administrador."
- **RN-12 — Prohibiciones:** ninguna operación de esta HU puede desactivar la verificación de `robots.txt`, los límites de ritmo y volumen ni la detección de CAPTCHA, bloqueo o autenticación (NFR-CUM-002, NFR-CUM-003, NFR-CUM-005).

### Interfaz

No requiere interfaz gráfica. Mínimo aceptable: dos comandos o acciones administrativas, "relanzar {fuente}" y "reactivar {fuente} con motivo {texto}", que devuelven los mensajes de RN-11. El resultado de la ejecución se consulta en el estado de fuentes (HU-098).

### Sistemas Externos (Si aplica)

- **API de datos abiertos de datos.gov.co** (SECOP II y TVEC): respuesta correcta → la ejecución termina `exitosa`; no disponible o tiempo de espera → reintentos (RN-08) y luego `fallida`; respuesta con formato inesperado → registros rechazados o ejecución `fallida` con el mensaje de error principal.
- **Sitios de Alkosto y Falabella:** solo mediante el mecanismo de captura automática permitido y habilitado, respetando `robots.txt` y los límites configurados.

---

## Contexto y Referencias

**Épica origen:** [Operación, Calidad y Medición del MVP](../../../epicas.md#épica-008-operación-calidad-y-medición-del-mvp)

**Exclusiones de la Épica:**
- NO incluye analítica de uso avanzada ni embudos de producto.
- NO incluye facturación ni gestión de planes.
- NO incluye administración multi-organización.

**Historias relacionadas:** HU-098 (estado de fuentes), HU-100 (alertas de fallas), HU-112 (log de auditoría).

---

## Supuestos

> Elementos inferidos por la IA que NO estaban explícitos en el PRD o la Épica. Todos los supuestos han sido resueltos: convertidos en reglas de negocio explícitas o eliminados mediante reformulación. Si aparece algún supuesto no resuelto, esta HU NO está lista para desarrollo.

- Relanzar significa ejecutar la ingesta incremental estándar desde la última marca exitosa, sin rangos de fechas a elección → resuelto en RN-02.
- Se requiere una operación explícita de reactivación con motivo para retomar una fuente retail suspendida; relanzar no levanta la suspensión → resuelto en RN-09 y RN-10.
- Relanzar una captura retail no reinicia ni amplía los límites de ritmo y volumen → resuelto en RN-03.

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
