# Historia #095: Listar mis casos de investigación

**Estado:** Borrador (PO)  
**Release:** Release MVP  
**Épica:** [Espacio de Investigación del Analista](../../../epicas.md#épica-007-espacio-de-investigación-del-analista)  
**Feature:** Consultar y Retomar Casos Propios  
**Prioridad:** Crítica  
**FRs relacionados:** FR-080, FR-082

Escrita por el flujo generar-historias-usuario (Método Ceiba) — MVP propio, no comercial

---

## Historia de Usuario

**Como** Analista,  
**Quiero** ver la lista de mis casos de investigación, con los más recientes primero,  
**Para** encontrar rápidamente el caso que quiero retomar.

## Descripción

Primer paso del Journey 2: tras iniciar sesión, el analista abre **Mis casos** desde el menú principal y ve únicamente los casos que él creó (FR-080, FR-082), ordenados por la fecha de su última actualización, con un resumen de su contenido. Desde la lista abre un caso (detalle en HU-096).

---

## Criterios de Aceptación

### Escenario 1: Ver la lista de mis casos

- **Dado** que la analista tiene 3 casos
- **Cuando** abre "Mis casos" desde el menú principal
- **Entonces** el sistema muestra sus 3 casos ordenados por fecha de última actualización descendente; por cada caso: título, fecha de creación, fecha de última actualización y cantidad de señales, contratos, evidencias y notas

### Escenario 2: Solo aparecen los casos propios

- **Dado** que otros usuarios (incluido el Administrador) tienen casos
- **Cuando** la analista abre "Mis casos"
- **Entonces** la lista contiene solo los casos de los que ella es autora, y el total mostrado cuenta solo esos casos

### Escenario 3: Sin casos

- **Dado** que la analista no tiene casos
- **Cuando** abre "Mis casos"
- **Entonces** el sistema muestra: "Aún no tienes casos. Crea uno desde una señal o desde la ficha de un contrato." con un enlace a la lista de señales

### Escenario 4: Paginación

- **Dado** que la analista tiene 45 casos
- **Cuando** abre "Mis casos"
- **Entonces** el sistema muestra los 20 más recientes, el texto "Mostrando 1–20 de 45 casos" y controles para ir a la página siguiente y anterior; la página 3 muestra los casos 41–45

### Escenario 5: Abrir un caso desde la lista

- **Dado** que la analista está en "Mis casos"
- **Cuando** pulsa el título de un caso
- **Entonces** el sistema abre el detalle de ese caso

### Escenario 6: Reordenamiento al actualizar un caso

- **Dado** que el caso "Tunja 2025" era el tercero de la lista
- **Cuando** la analista le agrega una nota y vuelve a "Mis casos"
- **Entonces** "Tunja 2025" aparece primero, con la nueva fecha de última actualización y el conteo de notas incrementado

### Escenario 7: Falla al cargar la lista

- **Dado** que ocurre un error interno al consultar los casos
- **Cuando** la analista abre "Mis casos"
- **Entonces** el sistema registra el error en el log de aplicación y muestra: "No pudimos cargar tus casos. Intenta de nuevo." con un botón "Reintentar"

### Escenario 8: Acceso sin sesión

- **Dado** que no hay sesión iniciada
- **Cuando** se intenta abrir "Mis casos"
- **Entonces** el sistema dirige al inicio de sesión con "Inicia sesión para continuar." y, tras iniciar sesión, muestra "Mis casos"

---

## Información Recopilada

### Usuario y Contexto

- **Tipo de usuario:** Analista (también el Administrador, que ve solo sus propios casos)
- **Permisos requeridos:** sesión activa
- **Valor de negocio:** permite retomar investigaciones en días distintos (Journey 2), uno de los criterios de aceptación de la épica

### Reglas de Negocio

- **RN-01 — Alcance de la lista:** solo casos cuyo autor es el usuario de la sesión. El filtro se aplica en el servidor; no existe parámetro que permita listar casos de otro usuario.
- **RN-02 — Orden:** fecha de última actualización descendente; a igual fecha, fecha de creación descendente.
- **RN-03 — Fecha de última actualización:** cambia al crear el caso, al agregar un elemento y al agregar, editar (con cambios) o eliminar una nota.
- **RN-04 — Conteos:** número de elementos de tipo señal, de tipo contrato y de tipo evidencia, y número de notas vigentes; un conteo en cero se muestra como "0".
- **RN-05 — Paginación:** 20 casos por página; texto "Mostrando {desde}–{hasta} de {total} casos"; los controles de página anterior o siguiente se deshabilitan en la primera y la última página. Si la página solicitada no existe, se muestra la última página disponible.
- **RN-06 — Fechas:** formato `dd/mm/aaaa hh:mm`, hora de Colombia (UTC−5).
- **RN-07 — Títulos largos:** el título se muestra completo hasta 120 caracteres, con ajuste de línea; nunca se recorta sin indicación.
- **RN-08 — Rendimiento:** la lista responde en ≤ 3 segundos (p95) con el volumen del piloto (objetivo inicial de ingeniería, recalibrable).

### Interfaz

- Opción "Mis casos" en el menú principal de las páginas protegidas.
- Página "Mis casos": tabla o lista con columnas Título (enlace al caso), Creado, Actualizado, Señales, Contratos, Evidencias, Notas; texto de paginación y controles "Anterior" / "Siguiente".
- Estado vacío (Escenario 3), estado de carga ("Cargando tus casos…") y estado de error con "Reintentar" (Escenario 7).
- Desktop-first desde 1366 × 768 px; en 768 px y 360 px se muestra como lista de tarjetas con la misma información; WCAG 2.1 AA.

### Sistemas Externos (Si aplica)

No aplica.

---

## Contexto y Referencias

**Épica origen:** [Espacio de Investigación del Analista](../../../epicas.md#épica-007-espacio-de-investigación-del-analista)

**Exclusiones de la Épica:**
- NO incluye casos compartidos ni colaboración entre analistas.
- NO incluye login social (Google, Microsoft) ni SSO.
- NO incluye exportación del expediente (candidata, ÉPICA-009).
- NO incluye publicación de casos ni un canal de denuncia a entes de control.

**Historias relacionadas:** HU-096 (abrir y retomar un caso), HU-097 (privacidad), HU-090 y HU-091 (crear casos)

---

## Supuestos

> Elementos inferidos por la IA que NO estaban explícitos en el PRD o la Épica. Todos los supuestos han sido resueltos: convertidos en reglas de negocio explícitas o eliminados mediante reformulación. Si aparece algún supuesto no resuelto, esta HU NO está lista para desarrollo.

- La lista se ordena por última actualización y se pagina de a 20 casos (RN-02, RN-05).
- Búsqueda o filtros dentro de "Mis casos" no están en FR-080 y quedan fuera del MVP.

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
