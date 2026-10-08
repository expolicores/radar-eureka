# Historia de Usuario

**Como** Analista,
**Quiero** que cada televisor comprado se compare con compras públicas equivalentes (Benchmark 1) y con referencias de mercado (Benchmark 2), y que el sistema marque como «señal que merece revisión» solo las desviaciones al alza, con su nivel de confianza,
**Para** priorizar qué compras revisar, sabiendo siempre contra qué se comparó y qué tan sólida es la comparación

## Descripción

Cuarto *vertical slice* del MVP Beta: el núcleo analítico determinístico. Crea el módulo `market` (observaciones de mercado **simuladas**, de solo inserción, con el puerto de fuente retail y su adaptador seed) y el módulo `comparison` (selección de comparables, Benchmark 1 y 2, regla híbrida de señal, precios bajos a revisión de calidad, confianza 0–100 con penalizaciones, resultados versionados de solo inserción con `config_version_id`). La exploración incorpora los estados «con señal», «comparado sin señal» y «comparables insuficientes», y el filtro «Con señal». El recálculo lo ejecuta la CLI.

HUs del backlog tomadas como referencia: HU-042/043 (observaciones trazables e inmutables), HU-054/055 (comparables con ventanas), HU-057/058 (Benchmarks 1 y 2), HU-059 (señal híbrida), HU-060 (bajos a calidad), HU-061 (confianza), HU-062 (evidencia reproducible: vínculo con cada observación), HU-101 (parámetros versionados, en su versión mínima: una configuración analítica identificada).

**No incluye:** API y pantalla de señales (slice 5), detalle con gráfico (slice 6), captura retail real, carga manual de observaciones, edición de la configuración desde la UI, calificación y reportes de error.

---

## Criterios de Aceptación

### Escenario 1: Flujo Principal

- **Dado** las compras seed y las observaciones de mercado simuladas
- **Cuando** se ejecuta el recálculo de señales
- **Entonces** cada ítem de televisor con precio unitario e IVA incluido se compara con los ítems de televisor **equivalentes** (mismo tamaño, resolución y panel; «mismo modelo» si coinciden marca y modelo) de **otras** compras con IVA incluido dentro de **±6 meses** (ampliable a ±12 si hay menos de 5); con **≥ 5** comparables se calculan Q1, mediana, Q3 y umbral, y la desviación porcentual frente a la mediana; y el resultado queda guardado con la versión de la configuración analítica y el vínculo con cada comparable

### Escenario 2: Validaciones (regla de señal)

- **Dado** un ítem comparado
- **Cuando** su precio supera la referencia
- **Entonces** se genera una **señal que merece revisión** si: con muestra suficiente y homogénea (≥ 10 comparables y RIC/mediana ≤ 0,5) el precio supera **Q3 + 1,5 × RIC**; en otro caso, si supera la mediana en **≥ +30 %** (mismo modelo) o **≥ +50 %** (equivalente). Los precios **anormalmente bajos** (por debajo de Q1 − 1,5 × RIC o de la mitad de la mediana) **no** generan señal: quedan en revisión de calidad

### Escenario 3: Casos Extremos

- **Dado** un ítem sin precio publicado, con precio en revisión, con IVA indeterminado o excluido, o con menos de 5 comparables incluso a ±12 meses
- **Cuando** se recalcula
- **Entonces** queda con el estado explícito correspondiente (`sin precio unitario`, `revisión de calidad`, `IVA: comparación incompleta`, `comparables insuficientes`) y nunca genera señal

### Escenario 4: Benchmark 2 – Mercado

- **Dado** observaciones de mercado del mismo televisor equivalente, vendidas por la tienda, sin condiciones especiales y con IVA incluido, dentro de **±30 días** de la compra
- **Cuando** se calcula el Benchmark 2
- **Entonces** con **≥ 3 observaciones de ≥ 2 tiendas** hay referencia de mercado (mediana) y desviación; con menos, «referencia de mercado disponible · evidencia limitada» con las observaciones y la desviación frente a la más alta; sin observaciones, «no disponible»; el Benchmark 1 se mantiene en todos los casos

### Escenario 5: Confianza

- **Dado** una comparación con señal o sin ella
- **Cuando** se calcula la confianza
- **Entonces** parte de 100 y resta: emparejamiento equivalente −20; precio derivado −10; Benchmark 2 con evidencia limitada −10 o no disponible −15; menos de 10 comparables −10; ventana ampliada a ±12 meses −10; regla porcentual por muestra no homogénea −10. Nivel: **alta** ≥ 75, **media** 50–74, **baja** < 50. Cada penalización queda registrada

### Escenario 6: Versionado y reproducibilidad

- **Dado** un recálculo anterior
- **Cuando** se recalcula de nuevo
- **Entonces** se inserta un nuevo resultado por ítem (nunca se modifica ni borra uno anterior) y solo el del último recálculo queda vigente; cada resultado guarda la versión de la configuración, los comparables y las observaciones usadas

### Escenario 7: Exploración

- **Dado** el recálculo hecho
- **Cuando** el Analista explora compras
- **Entonces** ve «⚑ Con señal», «✓ Comparado · sin señal» o «Comparables insuficientes» según el resultado vigente, y puede filtrar «Con señal» / «Sin señal»

---

## Información Recopilada

### Usuario y Contexto

- **Tipo de usuario:** Analista (consume); Administrador (ejecuta el recálculo).
- **Permisos requeridos:** ninguno en el MVP Beta.
- **Valor de negocio:** las señales son el producto: priorizan la revisión humana con evidencia.

### Reglas de Negocio

- Una señal **no es una conclusión**: no se usan los términos «sobreprecio», «corrupción», «fraude» ni «hallazgo fiscal» (FR-064).
- Solo se compara en la misma base tributaria (IVA incluido); nunca se asume el 19 % (FR-057).
- Benchmark 1: ±6 meses, ampliable a ±12; mínimo 5 comparables (P-01, P-02).
- Benchmark 2: ±30 días; mínimo 3 observaciones de 2 tiendas; solo vendedor = la tienda y sin condiciones especiales; nunca un precio actual para una compra antigua (FR-044, FR-046, FR-056).
- Regla híbrida de señal y precios bajos a calidad (P-03, P-04).
- Confianza 0–100 menos penalizaciones (FR-068); niveles alta/media/baja.
- Resultados de solo inserción con `config_version_id` (ADR-012); la configuración inicial es `analitica-v1`.
- Código de señal: `SG-<año de la compra>-<número>` (número del contrato SECOP II sin ceros a la izquierda, mínimo 4 dígitos; `T` + número de orden en TVEC); sufijo `-<línea>` si la compra tiene más de un televisor con señal.
- Las observaciones de mercado del seed son **simuladas** y así se identifican (método `simulado`, tienda «Alkosto (simulado)» / «Falabella (simulado)»).

### Interfaz

CLI: `load-seed` carga compras, observaciones y recalcula; `recalculate-signals` solo recalcula. Exploración: insignias nuevas y filtro «Con señal».

### Sistemas Externos

Mercado retail (Alkosto, Falabella): simulado con el adaptador seed del puerto de fuente retail.

### Disparadores

- El Administrador ejecuta el recálculo (relanzable: inserta una nueva versión).
- El Administrador carga el seed (incluye observaciones y recálculo).

### Entidades del Dominio

- Ítem de compra
- Observación de mercado
- Comparación de ítem (resultado versionado)
- Señal que merece revisión
- Ejecución de recálculo
- Configuración analítica

### Alcance y Continuidad

Habilita los slices 5 (API y pantalla de señales) y 6 (detalle con distribución). La configuración editable y la carga manual de observaciones quedan para después.

### Preview de Interfaz

Mockup: insignias «⚑ Con señal» y «✓ Comparado · sin señal» en «Explorar».

---

## Contexto y Referencias

**Arquitectura:** `docs/architecture/index.md` (núcleo determinístico, hechos de solo inserción con `config_version_id`), PRD FR-042…FR-068 y P-01…P-04.
**Historias relacionadas:** #2, #3, #4.
**Lecciones aprendidas:** TVEC: la base tributaria real está en validación (INV-01); el seed declara IVA incluido de forma explícita, el adaptador real deberá respetar INV-01

---

## Definición de Terminado (Inicial)

- [ ] Funcionalidad implementada según criterios de aceptación
- [ ] Validaciones funcionando correctamente
- [ ] Mensajes implementados
