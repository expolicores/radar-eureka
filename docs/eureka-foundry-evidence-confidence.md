# Eureka Assistant — política de evidencia y confianza

Cambio limitado a las instrucciones de investigación en `policy.py`, tests y
documentación. No cambia schemas, dispatch, readers, scoring, reglas comerciales,
filtros, límites, frontend, adquisición ni OCR. No se ejecuta discovery/corrida.

## Reglas añadidas, antes de la prueba

1. `documentary_evidence_available=false`, o falta de facts/canonicals/documentos,
   significa evidencia insuficiente e incertidumbre documental alta. No autoriza
   «limpio», «menos problemático», «validado» o «documentalmente favorable».
2. commercial_decision/score/no_alert_reason/funnel_state/has_alert son señales del
   pipeline, no verdades definitivas. Evidencia relevante puede matizarlas; debe
   explicarse la discrepancia sin alterar la decisión persistida ni el score.
3. Prioridad conceptual: encaje comercial, monto frente al perfil, deadline,
   ejecución, pago, evidencia documental, complejidad/requisitos, señales del
   pipeline e incertidumbre restante. No ordenar solo por score, monto o warnings.
4. suspicious_fact no descarta por sí solo. Explicar el hecho si hay detalle; si no:
   «Existe una bandera de revisión documental cuyo detalle requiere inspección adicional».
5. Distinguir A: interesante por metadata; B: interesante con evidencia documental;
   C: incierto por falta de evidencia; D: poco atractivo por evidencia concreta.
6. Antes de recomendar, detalle por proceso y evidencia ante incertidumbre/revisión.
   Explicar interés, soporte, incertidumbre y validación manual pendiente.
7. Separar metadata/documento/inferencia y nunca completar campos no confirmados.

La política completa es `INVESTIGATION_POLICY`, con la sección «POLÍTICA DE EVIDENCIA
Y CONFIANZA». Se sustituye solo su bloque delimitado en las instrucciones remotas;
el resto de la definición y las seis tools deben permanecer idénticos.

## Ejemplos conceptuales de aceptación

Estos casos suministrados por el usuario solo viven en tests/documentación, nunca
en el prompt de producción. No son una nueva consulta ni confirmación del portal.

| Caso | Respuesta esperada |
|---|---|
| Cubará | Interesante preliminarmente por metadata, pero con alta incertidumbre documental. Superar el monto preferido no lo descarta automáticamente. Validar documentos y condiciones. |
| Corrales | Bien alineado por papelería/cafetería/aseo/tecnología y monto aproximado de 17,68M. Si las tools acreditan ejecución de 10 días y pago contra entrega, citar ese soporte. Explicar que la evidencia matiza el «No elegible» previo y merece revisión humana. |
| Duitama | Potencialmente interesante y manejable para aseo, alrededor de 10M, con facts/documentos disponibles. Validar detalles técnicos y requisitos antes de decidir; no inventar condiciones ausentes. |

## Tests y alcance

Tests con Foundry mockeado comprueban que el mensaje real enviado al modelo contiene
estas reglas, que el flujo permite una recomendación pese a «No elegible» cuando
hay evidencia, que se conserva la decisión/score y que la salida documental no
inventa campos. También verifican categorías de confianza, fallback de suspicious
sin detalle y ausencia de nombres de estos casos en la política productiva.

Estos son contratos de instrucciones y transporte; no prueban por sí solos la
obediencia del modelo real. La única prueba autorizada debe evaluarse contra los
criterios anteriores, conservando respuesta y tool calls tal como sean generados.

## Resultado de la única prueba real

Versión creada y verificada: **10**, basada en la versión actual 9.
Modelo y las seis tools idénticos; todos los campos de la definición excepto
instructions permanecen iguales y la versión anterior no se modificó.
Hash de instrucciones: `6f6ca24d77cf33483200dc4e53c10f889f31b28878efa5ef4a1ae274dfc28008`.

**63 tests del agente pasan**, Ruff/formato/mypy y los 13 contratos de arquitectura
pasan. No se alteraron tools/readiness/runtime, scoring, filtros ni frontend en esta
iteración. Se ejecutó una sola pregunta de aceptación sobre la versión 10, sin
crear una corrida CDP/Radar ni adquirir/extraer documentos.

Tool calls reales, en orden:

1. get_eureka_commercial_profile({})
2. get_latest_cdp_run({})
3. get_run_review_candidates(run_id=9e578b72-0e2d-4582-bbd6-4491d9764437)
4. get_process_detail(identity=secop:CO1.NTC.11146017) — Cubará
5. get_process_detail(identity=secop:CO1.NTC.11135083) — Villanueva
6. get_process_evidence(identity=secop:CO1.NTC.11135083)
7. get_process_evidence(identity=secop:CO1.NTC.11146017)

No consultó get_run_alerts porque alerts_created=0. No investigó Corrales ni Duitama
en esta prueba; sus ejemplos se validaron solamente como contratos mockeados.

### Cambios de comportamiento observados

- Cubará (34.999.000): reconoce explícitamente falta de documentos/facts y alta
  incertidumbre; no lo llama limpio ni validado. Superar el preferido no lo descarta.
- Villanueva (14.940.993): lo prioriza en la conclusión por encaje, monto y documento,
  pese al No elegible previo; indica revisión manual y cobertura parcial (20/50).
- Ambas recomendaciones tienen lectura de detalle/evidencia. Mantiene el score y
  la decisión persistida; no afirma haber creado alertas o haber cambiado el pipeline.

### Reservas: aceptación parcial de la calidad final

La respuesta no es una validación definitiva de oportunidad ni del ranking óptimo.
Contiene una expresión sin soporte: «día límite para evaluación debido a límite de
procesamiento», al interpretar el diferido de Cubará. No hay tal fecha de evaluación
en la tool. Ese texto no debe usarse para decidir plazos.

En Villanueva, la tool devuelve PAYMENT_METHOD=conflict, además de fragments
«contra entrega» (p4) y «único pago equivalente al 100%» (p12). El modelo menciona
ambos hallazgos pero no explicita suficientemente el conflicto del canonical.
También habla de hechos sospechosos sin identificar un hecho individual, pues la
bandera de revisión no trae detalle concreto. No los usa como descarte, pero su
explicación aún puede ser más precisa.

No se retocó nuevamente la política ni se ejecutó otra pregunta para mejorar el
resultado reportado. Evidencia íntegra en
`backend/.local/audits/foundry-evidence-confidence/result.json`, `spike-output.txt`,
`updated-version.json` y `added-policy.txt`.
