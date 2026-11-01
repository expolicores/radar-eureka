# Eureka Assistant — operación interna, plazos y conflictos

Cambio exclusivamente de instrucciones: se amplía el bloque delimitado de política
en `policy.py`. No cambia el código de tools, readers, guard/readiness, scoring,
filtros, pipeline ni frontend. No agrega Web Search.

## Reglas incorporadas

- no_alert_reason/funnel_state/manual_review_required/manual_review_reasons/
  review_first_seen_at/review_membership_persisted/associated_runs/limit_deferred
  explican operación interna. No son condiciones ni requisitos contractuales.
- «Diferido por límite de procesamiento» solo explica que Eureka no completó el
  procesamiento de esa corrida por un límite interno; no crea plazo de evaluación.
- El deadline procede de metadata.deadline/campo equivalente explícito de la tool
  o evidencia documental/canonical de cronograma. Nunca de timestamps de corridas
  o revisiones ni del motivo de no alerta. Si falta: deadline no confirmado.
- Conflictos explícitos o valores incompatibles se presentan como evidencia
  conflictiva, sin elegir silenciosamente uno. Se atribuyen alternativas a fuentes.
- Estados por condición: confirmed (consistente), uncertain (incompleta),
  conflicting (incompatible/conflicto explícito), absent (sin evidencia).
- PAYMENT_METHOD conflict no permite confirmar «contra entrega». Se informa el
  conflicto entre fuentes/extracciones y la necesidad de verificar el documento.
- Una afirmación contractual necesita procedencia conceptual metadata/fact/canonical/
  documento. Una bandera operativa no puede suministrar un requisito o plazo.
- Las recomendaciones separan atractivo, evidencia contractual confirmada,
  incertidumbres, conflictos y señales internas.

## Validación

Tests con Foundry mockeado comprueban el contrato de instrucciones enviado al modelo,
el payload con deadline=null y PAYMENT_METHOD=conflict, sin transformar el motivo
interno en condición ni completar campos ausentes. No equivalen a certificar el
comportamiento del LLM real: la única prueba autorizada se evalúa separadamente.

No se añaden casos concretos ni condiciones contractuales de ejemplo a producción.
La definición remota debe diferir únicamente en instructions; tools/modelo y
versiones anteriores se verifican sin cambios antes de la prueba.

## Única prueba real: versión 11

Se creó la versión 11 de eureka-assistant desde la versión 10, conservando modelo,
las seis tools y todos los demás campos de definición. Solo cambió instructions.
Las versiones anteriores permanecen disponibles.

Validación local: 69 tests de agents aprobados; Ruff check/format, Mypy (10
archivos) e import-linter (13 contratos) aprobados.

Pregunta: «Revisa la última corrida CDP y dime si viste algo interesante para mí.»

Se realizaron nueve llamadas, secuenciales:

1. get_eureka_commercial_profile
2. get_latest_cdp_run
3. get_run_review_candidates (9e578b72-0e2d-4582-bbd6-4491d9764437)
4. get_process_detail (secop:CO1.NTC.11146017 / Cubará)
5. get_process_detail (secop:CO1.NTC.11146179 / SENA Boyacá)
6. get_process_detail (secop:CO1.NTC.11147197 / Corrales)
7. get_process_evidence (Cubará)
8. get_process_evidence (SENA Boyacá)
9. get_process_evidence (Corrales)

No se consultó get_run_alerts porque no había alertas nuevas. El guard existente
pidió detalle y luego evidencia antes de aceptar la respuesta. No se cambiaron
sus reglas. No se ejecutó otra prueba.

Resultado observado: priorizó MC-CMC-003-2026 (Corrales), seguido por SENA
MC-RB-DR-0034-2026 y Cubará MC-131-2026. Explicó incertidumbre documental alta
en Cubará. Reportó explícitamente conflicto de PAYMENT_METHOD en SENA y no afirmó
una forma de pago confirmada para ese caso. La forma de pago de Corrales sí tiene
canonical PAYMENT_METHOD con status=confirmed en la evidencia entregada.

No convirtió limit_deferred en una condición contractual ni derivó deadlines de
timestamps operativos en esta respuesta. Sin embargo, no prueba por sí solo todos
los escenarios negativos posibles.

Limitaciones de la respuesta real: omitió el canonical QUANTITY con status=conflict
de SENA; por ello la política de destacar todos los conflictos relevantes no quedó
plenamente validada. También describió el monto de SENA como «fuera de rango»,
aunque el perfil define un máximo preferido, no una exclusión automática, y llamó
«buena cobertura» a Corrales pese a cobertura parcial. Son límites del resultado,
no cambios en scoring o reglas comerciales. No se retocó código ni se repitió la
pregunta para ocultarlos.

La respuesta completa y los outputs compactos originales se conservan localmente:
backend/.local/audits/foundry-contractual-provenance/spike-output.txt y result.json.
