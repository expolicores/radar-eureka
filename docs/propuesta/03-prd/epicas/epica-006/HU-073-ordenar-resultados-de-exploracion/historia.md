# Historia #073: Ordenar los resultados de la exploración por desviación, valor, fecha o confianza

**Estado:** Borrador (PO)  
**Release:** Release MVP  
**Épica:** [Exploración y Ficha del Contrato](../../../epicas.md#épica-006-exploración-y-ficha-del-contrato)  
**Feature:** Búsqueda y Filtrado de Compras  
**Prioridad:** Crítica  
**FRs relacionados:** FR-072

Escrita por el flujo generar-historias-usuario (Método Ceiba) — MVP propio, no comercial

---

## Historia de Usuario

**Como** Analista que investiga contratación pública,  
**Quiero** ordenar los resultados de la exploración por desviación, valor, fecha o nivel de confianza, en sentido ascendente o descendente,  
**Para** ver primero los contratos o ítems que más me interesa revisar.

## Descripción

Esta HU agrega a la vista "Exploración" (HU-069) un control de orden con cuatro criterios: **Desviación**, **Valor**, **Fecha** y **Nivel de confianza**, cada uno ascendente o descendente. El orden se aplica sobre todo el conjunto filtrado (no solo sobre la página visible), funciona en los modos "Contratos" e "Ítems de televisor" y se conserva al paginar, al cambiar filtros y al volver de la ficha.

La desviación y el nivel de confianza son resultados calculados por el proceso de comparación y señales de la plataforma; esta HU solo los usa para ordenar. Los registros sin el dato del criterio elegido siempre quedan al final.

---

## Criterios de Aceptación

### Escenario 1: Ordenar por desviación de mayor a menor (happy path)

- **Dado** que el Analista está en la exploración en modo "Contratos"
- **Cuando** elige "Desviación" y sentido "Mayor a menor"
- **Entonces** el listado muestra primero el registro con la mayor desviación porcentual, seguido de los demás en orden descendente, con los registros sin desviación calculada al final, y vuelve a la página 1

### Escenario 2: Ordenar por valor

- **Dado** que el Analista está en la exploración
- **Cuando** elige "Valor" y "Mayor a menor"
- **Entonces** en modo "Contratos" se ordena por valor del contrato u orden y en modo "Ítems de televisor" por precio unitario del ítem, de mayor a menor, con los registros sin valor al final

### Escenario 3: Ordenar por fecha ascendente

- **Dado** que el Analista está en la exploración
- **Cuando** elige "Fecha" y "Más antigua primero"
- **Entonces** el listado se ordena por fecha de compra de la más antigua a la más reciente, con los registros sin fecha al final

### Escenario 4: Ordenar por nivel de confianza

- **Dado** que el Analista está en la exploración
- **Cuando** elige "Nivel de confianza" y "Mayor a menor"
- **Entonces** el listado muestra primero los registros con confianza "Alta", luego "Media", luego "Baja" y al final los registros sin señal (sin nivel de confianza)

### Escenario 5: Empates

- **Dado** que dos o más registros tienen el mismo valor en el criterio elegido
- **Cuando** se aplica el orden
- **Entonces** los empates se resuelven por fecha de compra más reciente primero y, si persiste el empate, por identificador ascendente, de modo que el orden es siempre el mismo para los mismos datos

### Escenario 6: Cambiar el sentido del orden

- **Dado** que hay un orden aplicado
- **Cuando** el Analista cambia el sentido (ascendente/descendente) o activa el encabezado de la columna ordenada
- **Entonces** se invierte el orden de los registros con dato, los registros sin dato siguen al final y el listado vuelve a la página 1

### Escenario 7: Orden conservado al paginar, filtrar y cambiar de modo

- **Dado** que el Analista eligió un orden
- **Cuando** cambia de página, agrega o quita filtros, o cambia de modo
- **Entonces** el criterio y el sentido elegidos se mantienen y se aplican sobre el nuevo conjunto de resultados

### Escenario 8: Orden por defecto

- **Dado** que el Analista abre la exploración sin un orden en la URL, o con un valor de orden inválido
- **Cuando** se carga el listado
- **Entonces** se aplica el orden por defecto "Fecha — Más reciente primero" y el control lo refleja

### Escenario 9: Ningún registro tiene el dato del criterio

- **Dado** que en el conjunto filtrado ningún registro tiene desviación calculada (o nivel de confianza)
- **Cuando** el Analista ordena por ese criterio
- **Entonces** el listado se muestra en el orden de desempate (fecha más reciente, identificador) y aparece la nota "Ningún resultado tiene todavía un valor calculado de {desviación | nivel de confianza}; se muestran por fecha."

---

## Información Recopilada

### Usuario y Contexto

- **Tipo de usuario:** Analista que investiga contratación pública; el Administrador puede usar el mismo control.
- **Permisos requeridos:** Sesión iniciada con rol Analista o Administrador.
- **Valor de negocio:** Ordenar por desviación o confianza lleva al analista directamente a los casos que más merecen revisión, que es el segundo paso de su recorrido principal.

### Reglas de Negocio

- **RN-01 Desviación del ítem:** la mayor desviación porcentual calculada para el ítem frente a sus referencias disponibles (Benchmark 1 de compras públicas o Benchmark 2 de mercado), con signo: valores negativos (precio por debajo de la referencia) también se ordenan. Sin ninguna desviación calculada → sin dato.
- **RN-02 Desviación del contrato u orden:** la mayor desviación entre sus ítems "incluido". Sin ítems con desviación → sin dato.
- **RN-03 Valor:** modo "Contratos" = valor del contrato SECOP II (`valor_del_contrato`) o valor total de la orden TVEC; modo "Ítems de televisor" = precio unitario del ítem (explícito o derivado). Sin valor → sin dato.
- **RN-04 Fecha:** fecha de firma (SECOP II) o fecha de la orden (TVEC). Sin fecha → sin dato.
- **RN-05 Nivel de confianza:** escala ordinal Alta > Media > Baja, tal como la entrega el cálculo de señales para cada señal vigente. Ítem: confianza de su señal vigente. Contrato u orden: la mayor confianza entre las señales vigentes de sus ítems. Sin señal → sin dato.
- **RN-06 Sentidos y etiquetas:** Desviación, Valor y Nivel de confianza: "Mayor a menor" (por defecto al elegir el criterio) y "Menor a mayor". Fecha: "Más reciente primero" (por defecto) y "Más antigua primero".
- **RN-07 Nulos:** los registros sin dato del criterio elegido quedan siempre al final, en cualquier sentido, ordenados entre sí por el desempate.
- **RN-08 Desempate:** fecha de compra más reciente primero; luego identificador del registro ascendente (ID de contrato `CO1.PCCNTR.…` o número de orden TVEC, comparados como texto).
- **RN-09 Alcance:** el orden se aplica sobre el conjunto completo filtrado, antes de paginar.
- **RN-10 Orden por defecto e inválidos:** "Fecha — Más reciente primero". Un criterio o sentido no reconocido en la URL se reemplaza por el orden por defecto sin mostrar error.
- **RN-11 Persistencia:** criterio y sentido se guardan en la URL de la exploración y se restauran al recargar o volver de la ficha. Cambiar criterio o sentido devuelve a la página 1; cambiar de página no cambia el orden.
- **RN-12 Tiempo de respuesta:** cambiar el orden responde en ≤ 3 segundos (p95) con el volumen del MVP y 20 usuarios concurrentes (objetivo inicial de diseño, configurable y recalibrable).
- **RN-13 Accesibilidad (WCAG 2.1 AA, valor inicial de diseño):** el control de orden es operable con teclado; los encabezados de columna ordenables indican el criterio y el sentido activos de forma programática y visual (flecha + texto "orden descendente/ascendente" para lectores de pantalla).

### Interfaz

- Control "Ordenar por" sobre el listado con las opciones "Desviación", "Valor", "Fecha" y "Nivel de confianza", y un selector de sentido con las etiquetas de RN-06.
- Encabezados de las columnas Desviación / Mayor desviación, Valor / Precio unitario, Fecha y Nivel de confianza activables para ordenar por ese criterio; una segunda activación invierte el sentido.
- Indicador visual (flecha) en la columna ordenada.
- Nota informativa del Escenario 9 cuando aplique.
- En móvil (vista de tarjetas), el control "Ordenar por" se mantiene visible encima de las tarjetas.

### Sistemas Externos (Si aplica)

No consulta sistemas externos. Usa los valores de fecha y valor ingeridos de SECOP II y TVEC, el precio unitario extraído y la desviación y confianza calculadas por la plataforma.

---

## Contexto y Referencias

**Épica origen:** [Exploración y Ficha del Contrato](../../../epicas.md#épica-006-exploración-y-ficha-del-contrato)

**Exclusiones de la Épica:**
- NO incluye fichas de entidad ni de proveedor (candidatas, ÉPICA-009).
- NO incluye dashboards nacionales ni de otras categorías.
- NO incluye exploración pública anónima.
- NO incluye la consulta conversacional (chatbot).

**Historias relacionadas:** HU-069 (vista de exploración), HU-075 (orden en la lista de señales)

---

## Supuestos

> Elementos inferidos por la IA que NO estaban explícitos en el PRD o la Épica. Todos los supuestos han sido resueltos: convertidos en reglas de negocio explícitas o eliminados mediante reformulación. Si aparece algún supuesto no resuelto, esta HU NO está lista para desarrollo.

- **Resuelto (RN-01, RN-02):** la desviación usada para ordenar es la mayor desviación porcentual calculada del ítem y, para el contrato, la mayor de sus ítems.
- **Resuelto (RN-05):** el nivel de confianza se trata como escala ordinal Alta > Media > Baja; si el cálculo de señales usa otra escala ordinal, se respeta su orden de mayor a menor confianza.
- **Resuelto (RN-03):** "Valor" es el valor del contrato u orden en modo contratos y el precio unitario en modo ítems.
- **Resuelto (RN-07, RN-08):** nulos siempre al final y desempate determinístico por fecha e identificador.

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
