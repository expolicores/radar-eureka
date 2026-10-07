# Historia #072: Filtrar la exploración por territorio, fuente y existencia de señal

**Estado:** Borrador (PO)  
**Release:** Release MVP  
**Épica:** [Exploración y Ficha del Contrato](../../../epicas.md#épica-006-exploración-y-ficha-del-contrato)  
**Feature:** Búsqueda y Filtrado de Compras  
**Prioridad:** Crítica  
**FRs relacionados:** FR-071

Escrita por el flujo generar-historias-usuario (Método Ceiba) — MVP propio, no comercial

---

## Historia de Usuario

**Como** Analista que investiga contratación pública,  
**Quiero** filtrar la exploración por departamento y municipio, por fuente (SECOP II o TVEC) y por la existencia de una señal que merece revisión,  
**Para** concentrarme en el territorio que vigilo, en una fuente concreta y en las compras que ya tienen una señal para revisar.

## Descripción

Esta HU agrega al panel de filtros de la vista "Exploración" (HU-069) tres criterios: **Territorio** (departamento y municipio), **Fuente** y **Señal**. Funcionan en los modos "Contratos" e "Ítems de televisor" y se combinan con los demás filtros (Y entre criterios distintos, O entre valores del mismo criterio).

El territorio corresponde a la ubicación de la entidad compradora tal como la publica la fuente. La señal es la "señal que merece revisión" calculada por el proceso de comparación de la plataforma; esta HU solo la usa para filtrar y no la calcula. Que un registro tenga señal no significa que exista una irregularidad: solo indica que su precio merece revisión.

---

## Criterios de Aceptación

### Escenario 1: Filtrar por departamento (happy path)

- **Dado** que el Analista está en la exploración
- **Cuando** marca el departamento "Boyacá" en la sección "Territorio"
- **Entonces** el listado muestra solo los registros cuya entidad compradora está en Boyacá y aparece la etiqueta "Departamento: Boyacá"

### Escenario 2: Filtrar por municipio dentro de los departamentos elegidos

- **Dado** que el Analista marcó uno o más departamentos
- **Cuando** abre el selector "Municipio"
- **Entonces** solo se listan los municipios de los departamentos marcados; al marcar "Tunja" el listado muestra solo los registros de ese municipio y aparece la etiqueta "Municipio: Tunja (Boyacá)"

### Escenario 3: Municipio sin departamento elegido

- **Dado** que el Analista no ha marcado ningún departamento
- **Cuando** observa el selector "Municipio"
- **Entonces** el selector está deshabilitado con la ayuda "Elige primero uno o más departamentos."

### Escenario 4: Quitar un departamento con municipios elegidos

- **Dado** que el Analista marcó "Boyacá" y "Santander" y el municipio "Tunja (Boyacá)"
- **Cuando** desmarca "Boyacá"
- **Entonces** se quita también el municipio "Tunja (Boyacá)" y su etiqueta, y el listado se recalcula con "Santander"

### Escenario 5: Registros sin territorio publicado

- **Dado** que algunos registros no tienen departamento ni municipio publicados
- **Cuando** el Analista abre la sección "Territorio"
- **Entonces** existe la opción "Sin información territorial ({n})" que permite ver esos registros, y esos registros no aparecen al filtrar por cualquier departamento o municipio

### Escenario 6: Filtrar por fuente

- **Dado** que la sección "Fuente" muestra "SECOP II" y "TVEC" marcadas por defecto
- **Cuando** el Analista desmarca "TVEC"
- **Entonces** el listado muestra solo registros de SECOP II y aparece la etiqueta "Fuente: SECOP II"

### Escenario 7: No se pueden desmarcar ambas fuentes

- **Dado** que solo una fuente está marcada
- **Cuando** el Analista intenta desmarcarla
- **Entonces** la casilla no cambia y se muestra la ayuda "Debe quedar al menos una fuente seleccionada."

### Escenario 8: Filtrar compras con señal

- **Dado** que la sección "Señal" muestra "Todos" seleccionado por defecto
- **Cuando** el Analista elige "Con señal que merece revisión"
- **Entonces** el listado muestra, en modo "Contratos", los registros con al menos un ítem con señal vigente y, en modo "Ítems de televisor", los ítems con señal vigente; aparece la etiqueta "Señal: con señal que merece revisión"

### Escenario 9: Filtrar compras sin señal

- **Dado** que el Analista está en la sección "Señal"
- **Cuando** elige "Sin señal"
- **Entonces** el listado muestra los registros o ítems que no tienen ninguna señal vigente, incluidos los que aún no tienen comparación calculada, y aparece la etiqueta "Señal: sin señal"

### Escenario 10: No hay señales en el universo

- **Dado** que todavía no se ha generado ninguna señal
- **Cuando** el Analista elige "Con señal que merece revisión"
- **Entonces** se muestra "Todavía no hay señales que merezcan revisión con los filtros aplicados." y el botón "Limpiar filtros"

### Escenario 11: Combinar territorio, fuente y señal

- **Dado** que el Analista marcó el departamento "Santander", la fuente "SECOP II" y "Con señal que merece revisión"
- **Cuando** el listado se actualiza
- **Entonces** solo aparecen los registros que cumplen los tres criterios a la vez, en la página 1

---

## Información Recopilada

### Usuario y Contexto

- **Tipo de usuario:** Analista que investiga contratación pública (por ejemplo, un veedor que vigila su territorio); el Administrador puede usar los mismos filtros.
- **Permisos requeridos:** Sesión iniciada con rol Analista o Administrador.
- **Valor de negocio:** Acota el universo al territorio de interés y a los casos que ya tienen una señal, que es el primer paso del recorrido principal del analista (filtrar por departamento y abrir señales).

### Reglas de Negocio

- **RN-01 Origen del territorio:** SECOP II: departamento y ciudad/municipio publicados en el registro del contrato para la entidad compradora. TVEC: departamento y municipio de la entidad compradora publicados en los datos de la orden. No se infiere territorio a partir del nombre de la entidad.
- **RN-02 Normalización de nombres territoriales:** los valores se agrupan sin distinguir mayúsculas, minúsculas, tildes, puntos, comas ni espacios repetidos (ej. "BOGOTA D.C.", "Bogotá, D.C." → un solo valor). Se muestra la forma escrita más frecuente en el universo. Un municipio se identifica por el par municipio + departamento ("Tunja (Boyacá)"), para distinguir municipios homónimos.
- **RN-03 Opciones:** departamentos y municipios presentes en el universo visible, con el número de registros "({n})", ordenados alfabéticamente. Selección múltiple sin límite.
- **RN-04 Lógica territorial:** O entre departamentos; O entre municipios. Si hay municipios elegidos, el criterio territorial es: el registro está en alguno de los municipios elegidos **o** en algún departamento elegido que no tenga municipios elegidos. Ej.: departamentos Boyacá y Santander + municipio Tunja (Boyacá) → registros de Tunja + todos los de Santander.
- **RN-05 Sin información territorial:** registros sin departamento publicado se agrupan en la opción "Sin información territorial"; esa opción se combina con O con los departamentos elegidos. Registros con departamento pero sin municipio no cumplen ningún filtro de municipio, pero sí el de su departamento.
- **RN-06 Fuente:** opciones "SECOP II" y "TVEC", ambas marcadas por defecto (equivale a no filtrar y no genera etiqueta). Debe quedar al menos una marcada.
- **RN-07 Señal vigente:** un ítem tiene señal si el último cálculo de comparación de la plataforma le generó una "señal que merece revisión" que sigue vigente. Un contrato u orden tiene señal si al menos uno de sus ítems tiene señal vigente. Los precios anormalmente bajos no generan señal y no cuentan como "con señal".
- **RN-08 Opciones de señal:** "Todos" (por defecto, sin etiqueta), "Con señal que merece revisión" y "Sin señal" (selección única). "Sin señal" incluye registros e ítems sin comparación calculada todavía.
- **RN-09 Modo ítems:** en modo "Ítems de televisor", territorio y fuente se evalúan con el contrato u orden del ítem; la señal se evalúa con la señal del propio ítem.
- **RN-10 Lenguaje:** las etiquetas y mensajes usan "señal que merece revisión"; nunca "sobreprecio", "corrupción", "fraude" ni "hallazgo fiscal".
- **RN-11 Combinación y persistencia:** Y con los demás criterios; vuelve a la página 1 en cada cambio; los valores se guardan en la URL y se restauran al recargar o volver de la ficha.
- **RN-12 Tiempo de respuesta:** aplicar cualquiera de estos filtros responde en ≤ 3 segundos (p95) con el volumen del MVP y 20 usuarios concurrentes (objetivo inicial de diseño, configurable y recalibrable).
- **RN-13 Accesibilidad (WCAG 2.1 AA, valor inicial de diseño):** casillas y opciones operables con teclado, etiquetas visibles, estado deshabilitado del selector de municipio anunciado con su ayuda.

### Interfaz

- Sección "Territorio": lista de casillas "Departamento ({n})" con búsqueda por texto dentro de la lista; selector "Municipio" (deshabilitado sin departamento) agrupado por departamento; opción "Sin información territorial ({n})".
- Sección "Fuente": casillas "SECOP II" y "TVEC".
- Sección "Señal": opciones excluyentes "Todos", "Con señal que merece revisión" y "Sin señal".
- Etiquetas: "Departamento: {nombre}", "Municipio: {municipio} ({departamento})", "Territorio: sin información", "Fuente: {fuente}", "Señal: con señal que merece revisión" / "Señal: sin señal".
- En tablet y móvil, las secciones están dentro del panel plegable "Filtros ({n})".

### Sistemas Externos (Si aplica)

No consulta sistemas externos en tiempo real. Usa la ubicación de la entidad ya ingerida de SECOP II (`jbjy-vk9h`) y de la TVEC, la fuente de cada registro y el resultado de señales ya calculado por la plataforma.

---

## Contexto y Referencias

**Épica origen:** [Exploración y Ficha del Contrato](../../../epicas.md#épica-006-exploración-y-ficha-del-contrato)

**Exclusiones de la Épica:**
- NO incluye fichas de entidad ni de proveedor (candidatas, ÉPICA-009).
- NO incluye dashboards nacionales ni de otras categorías.
- NO incluye exploración pública anónima.
- NO incluye la consulta conversacional (chatbot).

**Historias relacionadas:** HU-069 (vista de exploración), HU-070, HU-071 (otros filtros), HU-074 (lista priorizada de señales), HU-075 (filtros en la lista de señales)

---

## Supuestos

> Elementos inferidos por la IA que NO estaban explícitos en el PRD o la Épica. Todos los supuestos han sido resueltos: convertidos en reglas de negocio explícitas o eliminados mediante reformulación. Si aparece algún supuesto no resuelto, esta HU NO está lista para desarrollo.

- **Resuelto (RN-01, RN-05):** el territorio es el de la entidad compradora tal como lo publica la fuente; sin dato se agrupa en "Sin información territorial" y no se infiere.
- **Resuelto (RN-07):** "con señal" significa al menos un ítem con señal vigente según el último cálculo; los precios anormalmente bajos no cuentan.
- **Resuelto (RN-04):** combinación de departamento y municipio definida explícitamente.

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
| 2026-10-02 | 1.0 | Historia generada desde Épica ÉPICA-006 | Juan Camilo (PO) |

---

> **Método Ceiba estimar hus** v6.1.95 | Modelo: claude-opus-5-5 | Usuario: Juan Camilo | Fecha: 2026-10-05
