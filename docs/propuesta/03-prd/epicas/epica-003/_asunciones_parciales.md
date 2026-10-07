# Asunciones parciales — ÉPICA-003: Normalización y Emparejamiento de Televisores

**Fecha:** 2026-10-02 | **Autor:** Juan Camilo | **Total de asunciones:** 20

> Supuestos resueltos durante la generación de las HUs de esta épica (IDs temporales). El consolidador los integra en `asunciones.md` global.

| Asunción | Categoría | HUs Relacionadas (IDs temporales) | Impacto | Estado |
|---|---|---|---|---|
| Solo se normalizan ítems con clasificación "incluido" y observaciones retail; los ítems "requiere revisión" esperan la revisión humana y los que dejan de ser incluidos se inactivan sin borrarse | Datos | HU-031 | Medio | Resuelta |
| Las tablas iniciales (alias de marca, prefijos de catálogo, expresiones de referencia, sinónimos de resolución, rango de tamaño 10–120") son valores iniciales configurables propuestos desde D1 y D4 | Datos | HU-031 | Medio | Resuelta |
| El tamaño no se infiere del código de modelo | Datos | HU-031 | Bajo | Resuelta |
| Ante conflicto entre un campo estructurado y el texto libre prevalece el campo estructurado, marcando el conflicto | Datos | HU-031, HU-032 | Bajo | Resuelta |
| La normalización y el emparejamiento son determinísticos y no usan IA (funcionan con la extracción con IA desactivada) | Técnico | HU-031, HU-032, HU-033, HU-034 | Medio | Resuelta |
| Catálogo de tecnologías `LED`, `QLED`, `MINI_LED`, `OLED` con sinónimos iniciales configurables; términos no mapeados (ej. `QNED`) quedan nulos hasta que el Administrador los mapee | Datos | HU-032 | Medio | Resuelta |
| La ausencia de un término Smart no implica "no Smart": queda nulo | Negocio | HU-032 | Medio | Resuelta |
| La generación solo se toma de un año explícito con calificador o de reglas por código de modelo cargadas por el Administrador (tabla inicial vacía); nunca de fechas de compra u observación | Negocio | HU-032 | Alto | Resuelta |
| Forma de un candidato a modelo en texto libre (6–20 caracteres, ≥ 2 letras y ≥ 2 dígitos, sin espacios) y patrones de exclusión configurables | Datos | HU-033 | Medio | Resuelta |
| Códigos internos del catálogo (inicial: `AMEPIE` + dígitos, D6) se detectan por patrones configurables y no se usan como modelo | Datos | HU-033 | Medio | Resuelta |
| Un modelo acompañado de "o equivalente" / "tipo" es una referencia del pliego y no se usa como modelo ni como marca | Negocio | HU-031, HU-033 | Alto | Resuelta |
| "Formatos equivalentes" de modelo = separadores, etiquetas iniciales y marca antepuesta con separador; los sufijos se conservan (prevalece FR-036 sobre la "tolerancia de sufijos" de D6) | Negocio | HU-034, HU-035 | Alto | Resuelta |
| Ítems objetivo del emparejamiento = compras públicas (SECOP II y TVEC); las observaciones retail solo son candidatos | Negocio | HU-035, HU-036, HU-038, HU-039 | Medio | Resuelta |
| Un par con misma marca y modelo (o mismo EAN) pero con tamaño, resolución o tecnología contradictorios se clasifica como insuficiente/no confiable | Negocio | HU-035, HU-036, HU-039 | Alto | Resuelta |
| Ventanas temporales, precio y base tributaria no forman parte del emparejamiento; se aplican en los benchmarks | Negocio | HU-035, HU-038 | Medio | Resuelta |
| Solo se usa como EAN un identificador declarado EAN/GTIN/UPC, normalizado a GTIN-14 y validado con dígito de control GS1; EAN distinto con marca y modelo iguales sigue siendo mismo modelo | Datos | HU-036 | Medio | Resuelta |
| Configuración inicial de equivalencia: tamaño, resolución, tecnología y Smart exactos y obligatorios; generación ±1 año y marca solo si ambos se conocen (a validar por el PO) | Negocio | HU-037, HU-038 | Alto | Resuelta |
| Piso no configurable (tamaño y resolución obligatorios, tolerancia de tamaño ≤ 1", ≥ 3 criterios obligatorios), justificación obligatoria y efecto prospectivo de cada versión de reglas | Negocio | HU-037, HU-041 | Alto | Resuelta |
| Un dato desconocido en un criterio obligatorio cuenta como no cumplido; no hay puntaje parcial ni reintento con criterios menores; los descartes se guardan como conteo por criterio | Negocio | HU-038, HU-040 | Alto | Resuelta |
| La clasificación por ítem es la de mayor confianza disponible; un ítem sin clasificación vigente queda pendiente y no se usa en comparaciones; la muestra de verificación de 50 se reparte 25/25 con metas configurables ≥ 95 % / ≥ 90 % | Negocio | HU-039, HU-040, HU-041 | Medio | Resuelta |
