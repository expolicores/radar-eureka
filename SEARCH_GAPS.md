# Brechas de búsqueda transversal · Fase 4.3

Evaluación del 14 de octubre de 2026. Fuente real: copia aislada del único proceso SECOP
persistido en desarrollo, Covarachía `CO1.REQ.11172521`: 3 documentos, 99 fragments,
39 structured facts y 18 canonical facts. Se excluyeron los 5.000 procesos sintéticos del
benchmark mediante `municipality=Covarachía`. Las 1.280 compras de demostración no forman
parte de search. Un resultado vacío no prueba por sí solo una brecha semántica.

Clases: **A** resuelta determinísticamente; **B** resoluble con alias/regla simple;
**C** probablemente semántica, pendiente de evaluación; **D** sin datos suficientes.

| Query | Resultados reales | Clase | Diagnóstico / siguiente evaluación |
|---|---:|---|---|
| silla ergonómica | 0 | D | No existe un proceso real de sillas en este corpus. Incorporar un caso real antes de evaluar recall. |
| asiento operativo con soporte lumbar | 0 | D | Falta el mismo dominio documental. No se demuestra que deba corresponder a una silla ergonómica ni se añade ese alias. |
| televisor | 0 | D | No hay proceso SECOP real de televisores. Las compras demo no son evidencia de cobertura real. El término sí funciona con PRODUCT en pruebas sintéticas. |
| pantalla para sala de reuniones | 0 | D | Sin un proceso real de pantallas, no puede distinguirse ausencia de datos de una relación conceptual. Puede referirse también a un proyector o monitor. |
| refrigerios | 1 | A | Encuentra Covarachía por PURCHASE_ITEM canónico vigente; metadata y documentos también proporcionan coincidencias. Score 65 intacto. |
| complemento alimentario individual | 0 | C | Hay un caso real de refrigerios PACK y la frase no coincide. La equivalencia comercial es una hipótesis, no una identidad demostrada: requiere ejemplos anotados y revisión humana antes de evaluar búsqueda semántica. No se introduce alias que la fuerce. |
| papelería | 0 | D | No existe un proceso real de papelería en el corpus disponible. |
| insumos de oficina | 0 | D | Falta un caso real. La expresión puede abarcar consumibles, equipos o mobiliario; no se transforma automáticamente en papelería. |

## Controles adicionales

| Query | Resultado | Clase | Evidencia |
|---|---|---|---|
| jugo hit / JÚGO HIT | Covarachía, score 65 | A | PRODUCT canónico, nombre exacto normalizado. |
| chocorramo | Covarachía, score 65 | A | Alias explícito del catálogo existente, sin modificarlo. |
| 50192703 | Covarachía, score 65 | A | UNSPSC canónico; el filtro `unspsc` compara el código estructurado. |
| Covarachía / Boyacá | Covarachía, score 65 | A | Evidencia canónica y metadata; los filtros geográficos comparan campos de metadata. |
| Presupuesto 2.000.000–3.000.000, filtros explícitos | Covarachía, score 65 | A | BUDGET_COP canónico de 2.080.000; no parser de lenguaje libre. |
| tv ↔ televisor, prueba de PRODUCT sintético | Coincidencia por alias | B → A con alias existente | Comprueba expansión determinista, no existencia de una oportunidad real de TV. |

## Qué evaluar después

Primero ampliar el corpus real y anotar equivalencias comerciales aceptables. Los alias
deben ser explícitos y unívocos. Las relaciones entre uso, función y producto —por ejemplo
equipamiento para una sala o complementos alimentarios— podrían beneficiarse de búsqueda
semántica, pero esta fase no implementa ni valida modelos. No se atribuyen las clases D a
un fallo de búsqueda semántica.
