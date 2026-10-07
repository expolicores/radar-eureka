# Asunciones parciales — ÉPICA-005: Señales que Merecen Revisión, con Evidencia

**Fecha:** 2026-10-02 | **Autor:** Juan Camilo (PO) | **Total de asunciones:** 26

| Asunción | Categoría | HUs Relacionadas (IDs temporales) | Impacto | Estado |
|---|---|---|---|---|
| Selección escalonada del Benchmark 1: mismo modelo ±6 → mismo modelo ±12 → +equivalentes ±6 → +equivalentes ±12; si nada alcanza el mínimo se usa mismo modelo ±12 o, si está vacío, equivalentes ±12 | Negocio | HU-054 | Alto | Resuelta |
| Se excluyen de los comparables el propio ítem y los ítems del mismo contrato SECOP II u orden TVEC | Datos | HU-054 | Medio | Resuelta |
| Cada línea de ítem es una observación; no se pondera por cantidad ni por valor | Negocio | HU-054, HU-057 | Medio | Resuelta |
| Fecha de la compra: fecha de firma (SECOP II) o fecha de la orden (TVEC); sin fecha no se compara | Datos | HU-054, HU-055 | Medio | Resuelta |
| Ítems con datos pendientes de revisión o rechazados no son elegibles ni como objetivo ni como comparables | Datos | HU-054, HU-055 | Medio | Resuelta |
| La ventana del Benchmark 2 (±30 días) no se amplía automáticamente | Negocio | HU-055 | Medio | Resuelta |
| Una observación por tienda y producto (SKU, si no EAN, si no marca+modelo), la más cercana a la fecha de compra | Datos | HU-055 | Medio | Resuelta |
| El Benchmark 2 usa solo observaciones retail; las compras públicas solo entran al Benchmark 1 | Negocio | HU-055 | Medio | Resuelta |
| Los precios condicionados (tarjeta, cupón, financiación, membresía) se excluyen del conjunto del Benchmark 2 | Negocio | HU-055 | Medio | Resuelta |
| Conversión sin IVA → con IVA con IVA explícito del documento o, si no, con tarifa general configurable (inicial 19 %), marcada como "convertido" | Negocio | HU-056 | Alto | Resuelta |
| Base tributaria de la TVEC como parámetro (inicial: indeterminada) hasta que se resuelva INV-01 | Datos | HU-056 | Alto | Resuelta |
| Si las observaciones con base determinada alcanzan el mínimo, se excluyen las indeterminadas; si no, se usan todas y la comparación se marca incompleta | Negocio | HU-056 | Medio | Resuelta |
| Cuartiles por interpolación lineal inclusiva; mediana y montos redondeados al peso; desviación a 1 decimal (valor redondeado usado por las reglas) | Técnico | HU-057, HU-058, HU-059 | Medio | Resuelta |
| Con evidencia limitada se calcula la desviación frente a la mediana de las observaciones disponibles, sin cuartiles | Negocio | HU-057, HU-058 | Medio | Resuelta |
| Un error técnico del Benchmark 2 deja su estado "No disponible / evidencia insuficiente – error de cálculo" sin afectar el Benchmark 1 | Técnico | HU-058 | Medio | Resuelta |
| "Muestra suficiente y homogénea" = referencia estadística + un solo tipo de emparejamiento + base tributaria completa + IQR > 0 | Negocio | HU-059, HU-060 | Alto | Resuelta |
| Una señal por ítem y benchmark, con versiones y estado Vigente/No vigente; las señales nunca se eliminan | Negocio | HU-059, HU-062, HU-066 | Alto | Resuelta |
| Comparaciones con base tributaria incompleta sí pueden generar señal, con marca visible y confianza limitada a Baja | Negocio | HU-059, HU-061 | Alto | Resuelta |
| "Precio anormalmente bajo" con regla simétrica (Q1 − 1,5 × IQR; −30 % mismo modelo; −50 % equivalente) y parámetros propios | Negocio | HU-060 | Medio | Resuelta |
| Confianza = 100 − penalizaciones configurables por factor (equivalente 20, evidencia limitada 25, IVA convertido 10 / incompleto 30, extracción automática 10, derivado 15, manuales 5/10); Alta ≥ 75, Media ≥ 50 | Negocio | HU-061 | Alto | Resuelta |
| Señales con evidencia de trazabilidad crítica incompleta quedan "Retenidas" y van a la cola de revisión, no se publican | Negocio | HU-062, HU-063 | Alto | Resuelta |
| Texto exacto de la advertencia de no conclusión y formatos de presentación (COP, %, DD/MM/AAAA) | UI-UX | HU-063 | Medio | Resuelta |
| Se muestra la copia del documento según el hash de la instantánea; no se muestra al Analista quién registró una observación manual | Seguridad | HU-064, HU-062 | Medio | Resuelta |
| Lista inicial de términos prohibidos con variantes; búsqueda por palabra completa sin tildes ni mayúsculas; aplica solo a textos generados por el sistema | Negocio | HU-065 | Alto | Resuelta |
| Calificación por Analista y versión de la señal; el Administrador no califica; los Analistas no ven calificaciones ajenas; comentario ≤ 1.000 caracteres | Negocio | HU-066 | Alto | Resuelta |
| Reportes de error: catálogo de objetos y tipos, estados Recibido/En revisión/Corregido/Descartado sin reapertura, aviso público de reportes abiertos, sin notificación por correo | Negocio | HU-067, HU-068 | Medio | Resuelta |
