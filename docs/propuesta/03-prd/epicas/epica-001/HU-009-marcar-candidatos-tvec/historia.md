# Historia #009: Marcar candidatos a televisor en ítems de la TVEC

**Estado:** Borrador (PO)  
**Release:** Release MVP  
**Épica:** [Universo de Compras Públicas de Televisores](../../../epicas.md#épica-001-universo-de-compras-públicas-de-televisores)  
**Feature:** Identificar Candidatos a Televisor  
**Prioridad:** Crítica  
**FRs relacionados:** FR-012

Escrita por el flujo generar-historias-usuario (Método Ceiba) — MVP propio, no comercial

---

## Historia de Usuario

**Como** Administrador del MVP,  
**Quiero** que el sistema marque como candidato todo ítem de la TVEC cuya descripción contenga los términos definidos, registrando los términos encontrados,  
**Para** llevar a la clasificación estricta solo los ítems que pueden ser televisores y descartar desde el inicio los que solo contienen fragmentos de texto parecidos.

## Descripción

La carga de ítems TVEC (HU-003) trae los ítems con un prefiltro amplio ("TV" como subcadena) y los deja "Pendiente de marcación". Esta historia aplica la regla precisa: coincidencia de los términos configurados como **palabras completas** en la descripción del ítem, después de normalizar el texto (la TVEC no estandariza el texto: mayúsculas, prefijos como "GSF01-" y códigos internos).

Cada ítem queda "Candidato" (con los términos encontrados) o "No candidato". Los candidatos quedan "Pendiente de clasificación". Los ítems TVEC no tienen UNSPSC, por lo que la candidatura es solo por texto.

---

## Criterios de Aceptación

### Escenario 1: Ítem candidato

- **Dado** que un ítem pendiente tiene descripción "GSF01-SMART TV LG 43LR6500PSA"
- **Cuando** se ejecuta la marcación TVEC
- **Entonces** queda `candidatura = Candidato`, `motivo_candidatura = Texto`, `terminos_encontrados = [smart tv, tv]`, `estado_clasificacion = Pendiente de clasificación`, con fecha y versión de términos

### Escenario 2: Ítem con plural

- **Dado** que un ítem tiene descripción "TELEVISORES SAMSUNG 55 PULGADAS"
- **Cuando** se ejecuta la marcación
- **Entonces** queda "Candidato" con el término "televisor"

### Escenario 3: Ítem con fragmento que no es término

- **Dado** que un ítem tiene descripción "ACTIVIDADES TVEC CAPACITACION" o "SOPORTE PARA TELEVISION"
- **Cuando** se ejecuta la marcación
- **Entonces** queda "No candidato" con el motivo "No contiene términos de televisor"

### Escenario 4: Descripción modificada en la fuente

- **Dado** que un ítem "Candidato" ya clasificado volvió a "Pendiente de marcación" porque cambió su descripción
- **Cuando** se ejecuta la marcación
- **Entonces** si sigue siendo candidato, su `estado_clasificacion` vuelve a "Pendiente de clasificación" (salvo clasificación manual vigente, que se mantiene y se marca `texto_cambio_tras_clasificacion_manual = sí`); si deja de serlo, pasa a "No candidato" con el evento "Dejó de ser candidato" y su historial de clasificación se conserva

### Escenario 5: Ejecución automática, manual y remarcación total

- **Dado** que terminó una carga de ítems TVEC que dejó ítems pendientes, o el Administrador cambió la lista de términos
- **Cuando** termina la carga o el Administrador ejecuta el comando correspondiente
- **Entonces** la marcación corre automáticamente sobre los pendientes al terminar la carga, y por comando sobre los pendientes o sobre todos los ítems TVEC (remarcación total) con la versión vigente de términos

### Escenario 6: Sin ítems pendientes

- **Dado** que no hay ítems TVEC "Pendiente de marcación"
- **Cuando** se ejecuta la marcación
- **Entonces** termina sin cambios y registra "No hay ítems TVEC pendientes de marcación."

---

## Información Recopilada

### Usuario y Contexto

- **Tipo de usuario:** Administrador del MVP (PO); el sistema ejecuta la marcación automática.
- **Permisos requeridos:** rol Administrador para ejecución manual.
- **Valor de negocio:** la TVEC es la base principal del Benchmark 1; una candidatura precisa evita llevar a clasificación líneas que no son televisores.

### Reglas de Negocio

- **RN-01 Normalización:** minúsculas; sin tildes ni diéresis; todo carácter que no sea letra o dígito se reemplaza por espacio; espacios colapsados; recorte de extremos. Ej.: "GSF01-SMART TV LG 43LR6500PSA" → "gsf01 smart tv lg 43lr6500psa".
- **RN-02 Coincidencia:** cada término normalizado coincide si aparece como secuencia de palabras completas; su última palabra admite los sufijos "s" o "es". "tv" no coincide con "tvec" ni con "43tv" (una sola palabra).
- **RN-03 Términos:** la misma lista configurable y versionada usada para SECOP II (valor inicial: "televisor", "smart tv", "tv"; cada término de 2 a 50 caracteres; lista no vacía).
- **RN-04 Campo evaluado:** solo `descripcion_item`. Si es nula o vacía, el ítem queda "No candidato" con el motivo "Descripción vacía" (la carga normalmente ya lo habría rechazado).
- **RN-05 Resultado:** "Candidato" (motivo "Texto", términos encontrados) o "No candidato" (motivo "No contiene términos de televisor" o "Descripción vacía"); se registran `fecha_marcacion` y `version_terminos`.
- **RN-06 Efecto sobre la clasificación y pérdida de candidatura:** reglas del Escenario 4. Los ítems nunca se eliminan.
- **RN-07 Idempotencia:** marcar sin cambios de descripción ni de términos produce el mismo resultado y no genera eventos.
- **RN-08 Resumen:** "Marcación TVEC: {n} evaluados. Candidatos: {n}. No candidatos: {n}. Dejaron de ser candidatos: {n}."

### Interfaz

No requiere interfaz gráfica. Comandos "marcar candidatos TVEC" y "remarcar todos los candidatos TVEC". Resumen en consola o log (RN-08).

### Sistemas Externos (Si aplica)

No aplica: trabaja sobre los ítems TVEC ya ingeridos desde datos.gov.co.

---

## Contexto y Referencias

**Épica origen:** [Universo de Compras Públicas de Televisores](../../../epicas.md#épica-001-universo-de-compras-públicas-de-televisores)

**Exclusiones de la Épica:**
- NO incluye SECOP I (Adenda 1).
- NO incluye categorías distintas a televisores.
- NO incluye el dataset de Procesos (`p6dx-8zbt`) como unidad base.
- NO incluye adiciones, modificaciones ni ejecución del contrato (ciclo de vida).
- NO incluye scraping del portal SECOP.

**Historias relacionadas:** HU-003 (ingesta de ítems TVEC), HU-008 (candidatos SECOP II, misma lista de términos), HU-010 (clasificación de ítems por reglas).

---

## Supuestos

> Elementos inferidos por la IA que NO estaban explícitos en el PRD o la Épica. Todos los supuestos han sido resueltos: convertidos en reglas de negocio explícitas o eliminados mediante reformulación. Si aparece algún supuesto no resuelto, esta HU NO está lista para desarrollo.

- La TVEC usa la misma lista de términos que SECOP II → resuelto en RN-03 (FR-012 remite a "los términos definidos").
- Los prefijos y códigos internos del texto TVEC no impiden la coincidencia → resuelto con la normalización de RN-01.
- Un ítem que solo menciona "televisión" (ej. un soporte) no es candidato con los términos iniciales → resuelto: la clasificación de accesorios se hace en HU-010 para los que sí son candidatos.

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
| 2026-10-02 | 1.0 | Historia generada desde Épica ÉPICA-001 | Juan Camilo (PO) |

---

> **Método Ceiba estimar hus** v6.1.95 | Modelo: claude-opus-5-5 | Usuario: Juan Camilo | Fecha: 2026-10-05
