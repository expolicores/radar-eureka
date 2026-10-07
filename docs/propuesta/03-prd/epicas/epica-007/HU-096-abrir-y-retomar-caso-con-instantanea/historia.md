# Historia #096: Abrir y retomar un caso con su evidencia conservada como instantánea

**Estado:** Borrador (PO)  
**Release:** Release MVP  
**Épica:** [Espacio de Investigación del Analista](../../../epicas.md#épica-007-espacio-de-investigación-del-analista)  
**Feature:** Consultar y Retomar Casos Propios  
**Prioridad:** Crítica  
**FRs relacionados:** FR-080, FR-081

Escrita por el flujo generar-historias-usuario (Método Ceiba) — MVP propio, no comercial

---

## Historia de Usuario

**Como** Analista,  
**Quiero** abrir uno de mis casos y ver las señales, contratos y evidencias tal como los guardé, junto con mis notas,  
**Para** retomar la investigación donde la dejé, con la seguridad de que la evidencia no cambió aunque el sistema haya recalculado los benchmarks.

## Descripción

Segundo paso del Journey 2: el analista abre un caso creado días atrás. El detalle del caso muestra sus datos, los elementos guardados como **instantáneas** con su fecha de captura (FR-081) y las notas. Desde cada instantánea puede consultar su contenido completo, abrir la copia conservada del documento de evidencia y, si aún existe, ir a la versión vigente de la señal o del contrato para compararla. La instantánea nunca se reemplaza por la información vigente.

Las notas se agregan, editan y eliminan según HU-093 y HU-094; guardar más elementos, según HU-092. Solo el autor puede abrir el caso (HU-097).

---

## Criterios de Aceptación

### Escenario 1: Abrir un caso propio

- **Dado** que la analista tiene el caso "Compra TV 65 Gobernación" con 2 señales, 1 contrato, 1 evidencia y 3 notas
- **Cuando** lo abre desde "Mis casos" o desde su dirección directa
- **Entonces** el sistema muestra: título, descripción (o "Sin descripción"), fecha de creación y de última actualización; la sección "Elementos guardados" con los 4 elementos, cada uno con su tipo, un resumen y la etiqueta "Instantánea del dd/mm/aaaa hh:mm"; y la sección "Notas" con las 3 notas

### Escenario 2: Ver el contenido completo de una instantánea de señal

- **Dado** que el caso tiene una señal guardada
- **Cuando** la analista pulsa "Ver detalle" en ese elemento
- **Entonces** el sistema muestra todos los datos guardados en la instantánea (ítem, contrato, benchmarks con su estado, cada referencia u observación con origen, fecha, método de adquisición e indicador de manual, fórmula, desviación, tipo de emparejamiento, nivel de confianza, base tributaria, evidencia de origen, fecha de corte) y la advertencia "Esta señal no constituye una conclusión ni una acusación; indica un caso que merece revisión."

### Escenario 3: La instantánea se mantiene tras recalcular

- **Dado** que la señal se guardó con desviación +42 % y confianza "Medio", y después el sistema la recalculó a +35 % y "Alto"
- **Cuando** la analista abre el caso
- **Entonces** la instantánea muestra +42 % y "Medio", y el elemento ofrece el enlace "Ver versión actual" con el texto "La información vigente puede diferir de esta instantánea."

### Escenario 4: Ir a la versión vigente

- **Dado** que la señal o el contrato guardado todavía existe en el sistema
- **Cuando** la analista pulsa "Ver versión actual"
- **Entonces** el sistema abre el detalle vigente de la señal o la ficha vigente del contrato, sin modificar la instantánea del caso

### Escenario 5: La señal ya no existe

- **Dado** que la señal guardada ya no existe tras un recálculo
- **Cuando** la analista abre el caso
- **Entonces** el elemento muestra la instantánea completa, no ofrece "Ver versión actual" y muestra: "Esta señal ya no está vigente en el sistema; se conserva la instantánea guardada."

### Escenario 6: Abrir la evidencia documental conservada

- **Dado** que una instantánea referencia el documento `oferta_economica.pdf`, página 3
- **Cuando** la analista pulsa "Ver documento"
- **Entonces** el sistema abre la copia conservada del documento (identificada por su hash) en la página indicada (o en la hoja y celda, para hojas de cálculo), y muestra también el enlace "Ver en la fuente oficial" con la URL original

### Escenario 7: La copia del documento no está disponible

- **Dado** que la copia conservada del documento no puede leerse en ese momento
- **Cuando** la analista pulsa "Ver documento"
- **Entonces** el sistema registra el error en el log de aplicación y muestra: "La copia del documento no está disponible en este momento. Puedes consultar la fuente oficial." con el enlace a la URL original

### Escenario 8: Retomar el trabajo en el caso

- **Dado** que la analista está en el detalle del caso
- **Cuando** agrega una nota o guarda un nuevo contrato desde la exploración
- **Entonces** al volver al caso ve la nota y el nuevo elemento, y la fecha de última actualización refleja el cambio

### Escenario 9: Caso inexistente o ajeno

- **Dado** que el identificador no corresponde a ningún caso o el caso pertenece a otro usuario
- **Cuando** la analista intenta abrirlo
- **Entonces** el sistema no muestra ningún dato y muestra: "No encontramos este caso." con un enlace a "Mis casos"

### Escenario 10: Falla al cargar el caso

- **Dado** que ocurre un error interno al consultar el caso
- **Cuando** la analista lo abre
- **Entonces** el sistema registra el error y muestra: "No pudimos cargar el caso. Intenta de nuevo." con un botón "Reintentar"

### Escenario 11: Caso sin notas

- **Dado** que el caso no tiene notas
- **Cuando** la analista lo abre
- **Entonces** la sección de notas muestra: "Aún no hay notas en este caso."

---

## Información Recopilada

### Usuario y Contexto

- **Tipo de usuario:** Analista (también el Administrador, sobre sus propios casos)
- **Permisos requeridos:** sesión activa y ser autor del caso
- **Valor de negocio:** cumple el criterio de la épica "un analista crea un caso, agrega notas, cierra sesión y lo retoma intacto" y garantiza evidencia reproducible

### Reglas de Negocio

- **RN-01 — Encabezado:** título, descripción (o "Sin descripción"), "Creado el dd/mm/aaaa hh:mm" y "Actualizado el dd/mm/aaaa hh:mm" (hora de Colombia).
- **RN-02 — Elementos:** se listan por fecha de captura descendente, agrupables por tipo (Señales, Contratos, Evidencias) con el conteo de cada tipo. Todo caso tiene al menos un elemento (se crea con uno y en el MVP no se quitan elementos).
- **RN-03 — Resumen por tipo:**
  - **Señal:** contrato (identificador y entidad), ítem (marca, modelo, tamaño), desviación, tipo de emparejamiento y nivel de confianza.
  - **Contrato:** fuente, identificador, entidad, proveedor, número de ítems de televisor extraídos y de señales.
  - **Evidencia:** subtipo ("Documento de origen" u "Observación de referencia"); para documento, nombre y página u hoja y celda, y el dato que respalda; para observación, origen, precio, fecha, método de adquisición y la marca "Observación manual" cuando aplique.
- **RN-04 — Fuente de lo mostrado:** todo lo que se muestra de un elemento proviene de su instantánea; nunca se completa ni se sustituye con datos vigentes. Los datos que se guardaron como "No disponible" se muestran así.
- **RN-05 — Versión vigente:** "Ver versión actual" solo aparece si la señal o el contrato con ese identificador existe hoy en el sistema; el texto "La información vigente puede diferir de esta instantánea." acompaña al enlace. Para evidencias de tipo observación, el enlace no aplica.
- **RN-06 — Señal no vigente:** si la señal ya no existe, se muestra el texto del Escenario 5. Para un contrato que ya no exista en el sistema: "Este contrato ya no está disponible en el sistema; se conserva la instantánea guardada."
- **RN-07 — Documento de evidencia:** "Ver documento" abre la copia conservada por el sistema identificada por el identificador del documento y su hash, posicionada en la página (PDF o imagen) o en la hoja y celda (hoja de cálculo) registradas; si el formato no permite posicionar, se abre el documento y se muestra "Ubicación: {página, hoja o celda}". Siempre se ofrece "Ver en la fuente oficial".
- **RN-08 — Advertencia:** toda instantánea de señal muestra la advertencia del Escenario 2.
- **RN-09 — Lenguaje:** los textos generados por el sistema nunca usan "sobreprecio", "corrupción", "fraude" ni "hallazgo fiscal".
- **RN-10 — Acceso:** solo el autor; para cualquier otro usuario (incluido el Administrador) o identificador inexistente, la misma respuesta "No encontramos este caso.", sin distinguir entre ambos casos.
- **RN-11 — Rendimiento:** el detalle del caso carga en ≤ 3 segundos (p95) con el volumen del piloto y hasta el máximo de elementos por caso (objetivo inicial de ingeniería, recalibrable).

### Interfaz

- Página "Detalle del caso" con: encabezado (RN-01); sección "Elementos guardados" con pestañas o filtros por tipo y conteos; cada elemento con etiqueta de instantánea, resumen, "Ver detalle" (expande el contenido completo), "Ver versión actual" (cuando aplique) y, en evidencias documentales, "Ver documento" y "Ver en la fuente oficial"; sección "Notas" (HU-093 y HU-094).
- Estados: carga ("Cargando el caso…"), error con "Reintentar", no encontrado con enlace a "Mis casos", notas vacías.
- Desde la evidencia de origen de una instantánea de señal, el documento se abre en ≤ 2 clics desde el detalle del caso.
- Desktop-first desde 1366 × 768 px; funcional en 768 px y 360 px; WCAG 2.1 AA.

### Sistemas Externos (Si aplica)

- **Almacenamiento de evidencia documental del sistema:** entrega la copia conservada por identificador y hash. No disponible → Escenario 7.
- **Fuente oficial (SECOP II, TVEC o tienda retail):** solo se enlaza la URL original; el sistema no la consulta al abrir el caso.

---

## Contexto y Referencias

**Épica origen:** [Espacio de Investigación del Analista](../../../epicas.md#épica-007-espacio-de-investigación-del-analista)

**Exclusiones de la Épica:**
- NO incluye casos compartidos ni colaboración entre analistas.
- NO incluye login social (Google, Microsoft) ni SSO.
- NO incluye exportación del expediente (candidata, ÉPICA-009).
- NO incluye publicación de casos ni un canal de denuncia a entes de control.

**Historias relacionadas:** HU-095 (lista de casos), HU-092 (guardar elementos), HU-093 y HU-094 (notas), HU-097 (privacidad)

---

## Supuestos

> Elementos inferidos por la IA que NO estaban explícitos en el PRD o la Épica. Todos los supuestos han sido resueltos: convertidos en reglas de negocio explícitas o eliminados mediante reformulación. Si aparece algún supuesto no resuelto, esta HU NO está lista para desarrollo.

- Se ofrece "Ver versión actual" para comparar con la información vigente sin alterar la instantánea; no se calcula automáticamente la diferencia entre ambas (RN-05).
- La evidencia documental se abre desde la copia conservada por el sistema, con enlace adicional a la fuente oficial (RN-07).

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
| 2026-10-02 | 1.0 | Historia generada desde Épica ÉPICA-007 | Juan Camilo (PO) |

---

> **Método Ceiba estimar hus** v6.1.95 | Modelo: claude-opus-5-5 | Usuario: Juan Camilo | Fecha: 2026-10-05
