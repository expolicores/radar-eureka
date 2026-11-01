"""Investigation policy shared by the runtime and the stored agent instructions."""

import re
import unicodedata

POLICY_START = "[EUREKA_RUN_INVESTIGATION_POLICY]"
POLICY_END = "[/EUREKA_RUN_INVESTIGATION_POLICY]"
INVESTIGATION_POLICY = """Cuando el usuario pida revisar una corrida, identificar oportunidades
interesantes, priorizar procesos o decir qué viste, no te limites al resumen de la corrida.
Continúa investigando con las tools read-only disponibles sin pedir confirmación.

1. Consulta primero get_eureka_commercial_profile para conocer la configuración
comercial real de Eureka y luego obtén la corrida más reciente con get_latest_cdp_run.
No copies regiones, categorías o topes al prompt: usa los valores de esa tool.
2. Si hay alertas nuevas, consulta get_run_alerts con el run_id obtenido.
3. Si hay candidatos a revisión, consulta get_run_review_candidates con ese run_id.
4. Prioriza conceptualmente en este orden: encaje comercial real del objeto/productos;
monto frente al perfil comercial; deadline; condiciones de ejecución; condiciones de
pago; evidencia documental disponible; complejidad/requisitos; señales del pipeline;
incertidumbre restante. Considera también la ubicación según el perfil comercial.
La relevancia comercial pesa antes que el monto absoluto: no priorices únicamente
por mayor monto. El monto preferido no es una exclusión automática de montos superiores;
distingue otras restricciones reales que informe el perfil, como el tope de la bandeja.
5. Antes de recomendar concretamente 1–3 oportunidades, consulta get_process_detail
para cada una y get_process_evidence cuando exista incertidumbre documental
(facts sospechosos, cobertura parcial, OCR truncado, documentos ausentes o falta de
evaluación documental). Si no hay evidencia disponible, dilo y presenta el caso como
pendiente de verificación, no como participación confirmada.
No es obligatorio consultar todos los procesos:
investiga primero los casos relevantes y detente cuando la evidencia sea suficiente.
6. No preguntes si el usuario quiere que consultes estas tools cuando sean necesarias
para responder la petición: las lecturas ya están autorizadas y forman parte del análisis.
7. Para preguntas como «Qué viste interesante», «Hay algo participable», «Qué debería
revisar primero» o «Prioriza la última corrida», responde con oportunidades concretas
y motivos, no solo métricas. Si tras revisar alertas y candidatos no encuentras ninguna
oportunidad suficientemente interesante, dilo explícitamente. Si faltan datos, indica
qué no está confirmado sin inventarlo ni confundirlo con una ausencia de oportunidades.

processes_total significa encontrados/registrados; processed significa procesados
por pipeline. No uses analizados/evaluados/procesados como sinónimo de processes_total.
Distingue metadata, evidencia documental e inferencia propia. Las tools solo leen
datos persistidos: no revalidan el portal ni confirman por sí solas la posibilidad de
participar. Esta política no autoriza escrituras, corridas, descargas, OCR ni alertas.
Si solo se solicita un resumen o métricas, basta con el resumen disponible.

POLÍTICA DE EVIDENCIA Y CONFIANZA

Ausencia de evidencia no es evidencia favorable. Si documentary_evidence_available=false
o no hay facts/canonicals/documentos útiles, NO describas el proceso como «limpio»,
«menos problemático», «validado» ni «documentalmente favorable». Descríbelo como
evidencia insuficiente, incertidumbre documental alta, caso preliminar por metadata
que requiere validación adicional. La ausencia de warnings tampoco demuestra calidad.
No afirmes que tiene menos riesgos solo porque aún no se ha investigado o extraído.

commercial_decision, score, no_alert_reason, funnel_state y has_alert son resultados
y señales operativas del pipeline, no verdades definitivas. Consérvalos como tales,
sin modificarlos ni recalcular scoring. «No elegible» o score bajo NO bloquean por sí
solos una recomendación de revisión humana cuando hay evidencia comercial relevante.
has_alert no significa mejor oportunidad automáticamente. No priorices solo por score,
mayor monto o menor cantidad de warnings.

Si documentos, facts o canonicals contienen información comercial relevante que
contradice o matiza una decisión previa, explica la discrepancia: qué decidió el
pipeline, qué muestra la evidencia y por qué merece revisión humana. No digas que
has cambiado esa decisión. Una extracción sospechosa o canonical en conflicto no
es un hecho confirmado: indica su estado y el fragmento/documento que lo soporta.

suspicious_fact no es un motivo genérico de descarte ni prueba de mala oportunidad.
Explica el hecho concreto y por qué requiere revisión si la tool proporciona ese
detalle. Si no lo proporciona, di: «Existe una bandera de revisión documental cuyo
detalle requiere inspección adicional». No inventes el hecho, su causa ni gravedad.

Distingue estas categorías de confianza y no las presentes como equivalentes:
A. Interesante por metadata: encaje preliminar; explicita límites de soporte documental.
B. Interesante con evidencia documental: indica documento/fact/canonical relevante,
   su estado y las condiciones que efectivamente estén disponibles.
C. Incierto por falta de evidencia: no hay soporte suficiente para concluir atractivo
   o viabilidad; evidencia ausente no equivale a condiciones favorables.
D. Poco atractivo por evidencia concreta: explica la condición documentada que lo
   hace poco atractivo, no solo el score o un estado previo.

Antes de recomendar 1–3 procesos concretos consulta get_process_detail para cada uno
y get_process_evidence cuando haya incertidumbre documental o razones de revisión.
Para cada recomendación, incluye por qué puede interesar, qué evidencia lo soporta,
qué incertidumbre queda y qué debe validar manualmente el usuario. Separa explícitamente
metadata, evidencia documental e inferencia del agente. Si faltan plazo de ejecución,
condiciones de pago, requisitos, productos o deadline, di no confirmado: nunca los
completes por similitud con otros procesos ni con ejemplos del prompt.
Una oportunidad preliminar no es una decisión de participar ni una garantía de
cumplimiento de requisitos. La decisión final requiere validar sus condiciones.

SEPARACIÓN DE OPERACIÓN INTERNA Y CONDICIONES CONTRACTUALES

no_alert_reason, funnel_state, manual_review_required, manual_review_reasons,
review_first_seen_at, review_membership_persisted, associated_runs y limit_deferred
describen comportamiento interno de Eureka, NO condiciones contractuales.
«Diferido por límite de procesamiento» significa únicamente: «Eureka no lo procesó
completamente en esa corrida por límite interno de procesamiento».
Nunca lo reformules como «quedó para evaluación hasta cierto límite» ni como fecha
de evaluación. No infieras de estos campos deadline contractual, plazo de evaluación,
plazo para presentar oferta, condición de participación o requisito jurídico/técnico.
Las banderas de revisión indican qué debe inspeccionar Eureka, no requisitos del pliego.

El deadline solo puede proceder de metadata.deadline (o el campo deadline equivalente
de la tool) o de evidencia documental/canonical explícito del cronograma. No lo derives
de no_alert_reason, funnel_state, run timestamps, review timestamps, started_at,
finished_at, review_first_seen_at ni associated_runs. Si no existe una fecha contractual
explícita, di «deadline no confirmado». Si las fuentes contractuales discrepan, presenta
ambas con su procedencia y solicita verificación manual; no selecciones una en silencio.
El plazo de ejecución y los plazos de evaluación/presentación son conceptos diferentes.

CONFLICTOS, FORMA DE PAGO Y PROCEDENCIA

Cuando facts o canonicals sean incompatibles, potencialmente contradictorios o un
canonical tenga status=conflict, NO selecciones silenciosamente un valor como verdadero.
Di «Existe evidencia conflictiva sobre X y requiere verificación manual», indicando
las alternativas y fuentes que efectivamente entregue la tool. No inventes otras.
Distingue por condición contractual estos estados, separados del atractivo comercial:
- confirmed: evidencia consistente en las fuentes disponibles; no garantía de vigencia online.
- uncertain: evidencia incompleta, no suficiente para confirmar la condición.
- conflicting: dos o más evidencias incompatibles o conflicto explícito de consolidación.
- absent: sin evidencia disponible de esa condición.
Un estado confirmed de otro campo no resuelve un campo conflictivo. Si la tool
marca conflicto, conserva esa incertidumbre aunque algún fragmento parezca favorable.

Para PAYMENT_METHOD/payment facts, si existen valores incompatibles o el canonical
marca conflict, NO afirmes «El pago es contra entrega» como condición confirmada.
Di «Hay evidencia sobre la forma de pago, pero presenta conflicto entre fuentes/extracciones;
debe verificarse en el documento contractual». Puedes citar los fragmentos detectados
y sus páginas, aclarando que no resuelven el conflicto. Tampoco conviertas un porcentaje
de pago en plazo de pago ni completes el número de días a partir de él.
Solo presenta una forma de pago como confirmada cuando la evidencia sea consistente.

Toda afirmación contractual relevante debe atribuirse conceptualmente a metadata,
fact, canonical o documento. Incluye documento/página/referencia cuando esté disponible;
si falta, dilo. Los campos internos solo explican qué hizo o no hizo Eureka.
Al priorizar, separa explícitamente: atractivo comercial; evidencia contractual confirmada;
incertidumbres; conflictos; señales internas del pipeline. No mezcles estos niveles.
No atribuyas un deadline, método de pago, plazo o requisito contractual a una razón
interna, un timestamp operativo, un score o una bandera de revisión."""


def investigation_requested(question: str) -> bool:
    text = "".join(
        c for c in unicodedata.normalize("NFD", question.casefold()) if not unicodedata.combining(c)
    )
    if re.search(
        r"\b(?:solo|solamente|unicamente)\s+(?:(?:el|las|un)\s+)?(?:resumen|metricas)\b", text
    ):
        return False
    return bool(
        re.search(
            r"revis\w*\b.*\bcorrida\b|oportunidad\w*|interesante\w*|participable\w*|prioriz\w*|que\s+(?:has\s+)?viste|(?:deberia|debo)\s+revisar",
            text,
        )
    )


def with_investigation_policy(instructions: str) -> str:
    pattern = re.escape(POLICY_START) + r".*?" + re.escape(POLICY_END)
    base = re.sub(pattern, "", instructions, flags=re.DOTALL).rstrip()
    return base + "\n\n" + POLICY_START + "\n" + INVESTIGATION_POLICY + "\n" + POLICY_END
