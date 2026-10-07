# Asunciones parciales — ÉPICA-006: Exploración y Ficha del Contrato

| Asunción | Categoría | HUs Relacionadas (IDs temporales) | Impacto | Estado |
|---|---|---|---|---|
| El universo visible en exploración excluye los registros cuyos ítems candidatos fueron todos excluidos; el modo ítems muestra solo ítems "incluido"; los ítems "requiere revisión" se ven en la ficha | Negocio | HU-069, HU-076, HU-077 | Alto | Resuelta |
| La orden de compra TVEC se trata como registro equivalente a un contrato en exploración y ficha, identificada por fuente y número de orden | Negocio | HU-069, HU-076 | Medio | Resuelta |
| Las órdenes TVEC sin modalidad publicada se agrupan como "Tienda Virtual del Estado (TVEC)"; los contratos sin modalidad como "Sin modalidad registrada" | Datos | HU-070, HU-075, HU-076 | Bajo | Resuelta |
| Entidad y proveedor se filtran solo eligiendo sugerencias (mínimo 3 caracteres, máximo 10 valores), identificando al actor por NIT/documento y, en su defecto, por nombre normalizado | UI-UX | HU-070, HU-075 | Bajo | Resuelta |
| El rango de valor se aplica al valor del contrato u orden publicado en datos abiertos, presentado como dato de referencia y nunca como precio unitario | Negocio | HU-071, HU-075, HU-076 | Medio | Resuelta |
| El filtro UNSPSC usa la categoría principal de SECOP II; las órdenes TVEC no publican UNSPSC y quedan fuera cuando el filtro está activo | Datos | HU-071, HU-075 | Bajo | Resuelta |
| Rangos de fechas predefinidos (30 días, 6 meses, 12 meses, año en curso) recalculados con la fecha del día | UI-UX | HU-071, HU-075 | Bajo | Resuelta |
| El territorio es el de la entidad compradora publicado por la fuente; sin dato se agrupa en "Sin información territorial" y no se infiere; regla explícita para combinar departamento y municipio | Datos | HU-072, HU-075 | Medio | Resuelta |
| "Con señal" significa al menos un ítem con señal vigente según el último cálculo; los precios anormalmente bajos no son señales y se muestran como "En revisión de calidad" | Negocio | HU-072, HU-074, HU-079 | Alto | Resuelta |
| La desviación de ordenamiento es la mayor desviación porcentual calculada del ítem; la del contrato, la mayor de sus ítems; la confianza del contrato, la mayor entre sus señales vigentes | Negocio | HU-069, HU-073 | Medio | Resuelta |
| El nivel de confianza se trata como escala ordinal Alta > Media > Baja; si el cálculo de señales usa otra escala ordinal, se respeta su orden | Datos | HU-073, HU-074, HU-075, HU-079 | Medio | Resuelta |
| "Valor" para ordenar es el valor del contrato u orden en modo contratos y el precio unitario en modo ítems y en la lista de señales | Negocio | HU-073, HU-075 | Bajo | Resuelta |
| Nulos siempre al final y desempate determinístico por fecha más reciente e identificador | UI-UX | HU-073, HU-075 | Bajo | Resuelta |
| Prioridad por defecto de la lista de señales: confianza descendente, desviación descendente, fecha más reciente, identificador; es una regla de presentación configurable que solo ordena la revisión | Negocio | HU-074, HU-075 | Alto | Resuelta |
| Paginación de 25 registros por defecto con opciones 25/50/100; estado (modo, filtros, orden, página) conservado en la URL y al volver de la ficha | UI-UX | HU-069, HU-074, HU-075 | Bajo | Resuelta |
| Formatos: fechas DD/MM/AAAA en hora de Colombia, pesos sin decimales con punto de miles, porcentajes con signo y coma decimal | UI-UX | HU-069, HU-074, HU-076, HU-083 | Bajo | Resuelta |
| Acceso a exploración, señales y ficha solo con sesión (Analista o Administrador); sin sesión se redirige al inicio de sesión; tiempo máximo de espera de 15 s antes de mostrar error (valor inicial configurable) | Seguridad | HU-069, HU-074, HU-076 | Medio | Resuelta |
| La ficha de un registro descartado no muestra datos e informa que fue descartado; "Volver" restaura la vista de origen o lleva a Exploración | UI-UX | HU-076 | Bajo | Resuelta |
| Al Analista se le muestra el estado de validación del dato extraído (no el puntaje numérico del extractor), el valor corregido con su fecha y el valor original, sin la identidad del revisor | Negocio | HU-077 | Medio | Resuelta |
| La distribución del Benchmark 1 se visualiza como gráfico de puntos con mediana y Q1–Q3, siempre con tabla equivalente y resumen textual; la ficha muestra los parámetros realmente usados en el cálculo | UI-UX | HU-078 | Medio | Resuelta |
| Las observaciones de mercado con condición especial se listan como evidencia con la nota "No se usa como precio general de mercado" y no entran en la referencia agregada | Negocio | HU-078 | Medio | Resuelta |
| Las órdenes TVEC no tienen documentos en el MVP; catálogo de estados de documento y límite de 50 documentos visibles con "Mostrar todos" | Datos | HU-080 | Bajo | Resuelta |
| Etapas de procesamiento con cuatro estados (Completada, En curso o pendiente, Incompleta, No aplica), reglas de cálculo explícitas, "No aplica" para documentos y extracción en TVEC, y estado general = última etapa completada consecutivamente | Negocio | HU-081 | Alto | Resuelta |
| Catálogo de motivos de información insuficiente agrupado en "Limitación de la fuente" y "Limitación del procesamiento", con tratamiento de motivos no catalogados | Negocio | HU-082 | Alto | Resuelta |
| La fecha de actualización combina la fecha de corte por fuente (última carga exitosa), la última actualización publicada del registro y la fecha del último cálculo de comparaciones; una carga fallida no cambia la fecha mostrada | Datos | HU-083 | Medio | Resuelta |
