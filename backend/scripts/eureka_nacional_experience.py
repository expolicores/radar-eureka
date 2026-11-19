"""Conservative, deterministic EN-01 rules for supply and contractual experience."""

import re

from spike_licitaciones_info import normalized

SUPPLY = re.compile(
    r"\b(?:suministro(?: e instalacion)?|adquisicion|compraventa|compra|dotacion)"
    r"\s+(?:de|del|para)\b"
)
SERVICE = re.compile(
    r"\b(?:obra civil|obras publicas|interventoria|consultoria|arrendamiento|"
    r"transporte|servicios? profesionales?|prestacion de servicios?|"
    r"servicio de (?:aseo|vigilancia|mantenimiento|conectividad)|"
    r"(?:compra|adquisicion|contratacion) de servicios?)\b"
)
PRIMARY = re.compile(r"\b(?:invitacion|pliegos?|condiciones definitivas|terminos de referencia)\b")
AMENDMENT = re.compile(r"\b(?:adendas?|modificaci(?:on|ones)|aclaraci(?:on|ones)|enmiendas?)\b")
SUPPORT = re.compile(
    r"\b(?:estudios? previos?|anexos?|requisitos?|especificaciones|ficha tecnica)\b"
)
POST_AWARD = re.compile(
    r"^(?:acta (?:de cierre|de liquidacion|de entrega|de inicio)|"
    r"contrato (?:firmado|suscrito)|poliza|liquidacion|informe de evaluacion|"
    r"proyecto (?:de )?pliego|borrador)\b"
)
EXPERIENCE = re.compile(r"\bexperiencia\b")
SCOPE = re.compile(
    r"\b(?:proponentes?|oferentes?|licitantes?|experiencia contractual|"
    r"experiencia habilitante|contratos? ejecutados?|requisito habilitante)\b"
)
PERSONNEL = re.compile(
    r"\b(?:del (?:personal|fabricante|equipo humano|profesional|director|coordinador)|"
    r"de los (?:profesionales|tecnicos))\b"
)
NEGATIVE = re.compile(
    r"\b(?:no se (?:exige|exigira|requiere|requerira|solicita|solicitara)(?: acreditar)?|"
    r"no (?:se )?debe(?:ra)? acreditar|no sera necesario acreditar)"
    r"\s+(?:(?:la|una|ninguna)\s+)?experiencia\b|"
    r"\bexperiencia(?: contractual| habilitante)?(?: del (?:proponente|oferente))?"
    r"\s+no (?:aplica|(?:es|sera) (?:un )?requisito(?: habilitante)?)\b"
)
POSITIVE = re.compile(
    r"\b(?:debe(?:ra|ran)?\s+(?:acreditar|certificar|demostrar|presentar|contar con)|"
    r"se (?:exige|exigira|requiere|requerira)|"
    r"requisito obligatori[ao]|"
    r"rige como requisito habilitante)\b"
)
CONDITIONAL = re.compile(
    r"\b(?:lotes?|grupos?|segmentos?|segun el anexo|conforme al anexo|"
    r"remite a|vease|consultar el anexo|segun el numeral|"
    r"si aplica|cuando aplique|excepto|salvo|siempre que|alternativamente|"
    r"para (?:la )?(?:inscripcion|registro|precalificacion|subsanacion)|"
    r"puntajes?|puntuacion|ponderacion|factor de calificacion|criterio de evaluacion)\b"
)
REQUIREMENT_REFERENCE = re.compile(
    r"\b(?:requisitos? habilitantes?|condiciones de habilitacion)\b.{0,120}"
    r"\b(?:segun|vease|remite a|se detallan en|establecidos en|establecidas en)\b.{0,40}"
    r"\b(?:anexo|archivo|documento)\b"
)
STATUSES = ("experience_required", "no_experience_required", "experience_ambiguous", "not_resolved")


def supply_candidate(description):
    text = normalized(description)
    return bool(SUPPLY.search(text) and not SERVICE.search(text))


def document_role(name):
    text = normalized(name).replace("_", " ").replace("-", " ")
    if POST_AWARD.search(text):
        return "excluded"
    if AMENDMENT.search(text):
        return "amendment"
    if PRIMARY.search(text):
        return "primary"
    if SUPPORT.search(text):
        return "support"
    return "unknown"


def clause_rule(clause):
    text = normalized(clause)
    if REQUIREMENT_REFERENCE.search(text):
        return "ambiguous"
    if not EXPERIENCE.search(text) or (PERSONNEL.search(text) and not SCOPE.search(text)):
        return None
    if PERSONNEL.search(text) or CONDITIONAL.search(text) or not SCOPE.search(text):
        return "ambiguous"
    if NEGATIVE.search(text):
        rest = NEGATIVE.sub("", text)
        if not POSITIVE.search(rest) and not re.search(
            r"\b(?:minima|especifica|general|adicional|previa|diferente|distinta)\b", rest
        ):
            return "negative"
    if re.search(r"\bno\b", text):
        return "ambiguous"
    return "positive" if POSITIVE.search(text) else "ambiguous"


def classify_experience(documents):
    evidence = []
    for doc in documents:
        for fragment in doc.get("fragments", ()):
            page_text = " ".join(fragment.text.split())
            for clause in re.split(r"(?<=[.;!?])\s+(?=[A-ZÁÉÍÓÚÑ])", page_text):
                rule = clause_rule(clause)
                if rule is None:
                    continue
                match = EXPERIENCE.search(normalized(clause))
                start = max(0, match.start() - 240) if match else 0
                evidence.append(
                    {
                        "rule": rule,
                        "document_id": doc["document_id"],
                        "document": doc["name"],
                        "role": doc["role"],
                        "url": doc["url"],
                        "sha256": doc["sha256"],
                        "page": fragment.source_locator.get("page_number"),
                        "locator": fragment.source_locator,
                        "method": fragment.source_locator.get("extraction_method"),
                        "excerpt": clause[start : start + 620],
                    }
                )
    primary_complete = any(doc["role"] == "primary" and doc["complete"] for doc in documents)
    pending = [
        doc["document_id"] for doc in documents if doc["role"] != "excluded" and not doc["complete"]
    ]
    modifiers_pending = any(
        doc["role"] in {"amendment", "primary", "unknown"} and not doc["complete"]
        for doc in documents
    )
    credible = {doc["document_id"] for doc in documents if doc["complete"]}
    decisive = {
        item["rule"]
        for item in evidence
        if item["role"] in {"primary", "amendment"} and item["document_id"] in credible
    }
    related = {item["rule"] for item in evidence}
    if {"positive", "negative"} <= related:
        status, reason = "experience_ambiguous", "conflicting_clauses"
    elif not primary_complete or modifiers_pending:
        status, reason = "not_resolved", "governing_documents_incomplete"
    elif "positive" in decisive and "ambiguous" not in related:
        status, reason = "experience_required", "explicit_bidder_requirement"
    elif "negative" in decisive and pending:
        status, reason = "not_resolved", "supporting_documents_incomplete"
    elif "negative" in decisive and related == {"negative"}:
        status, reason = "no_experience_required", "explicit_waiver_with_document_coverage"
    elif evidence:
        status, reason = "experience_ambiguous", "clause_or_scope_not_resolved"
    else:
        status, reason = "not_resolved", "no_decisive_clause"
    return {
        "status": status,
        "reason": reason,
        "classification_method": "en01-rules-v1",
        "evidence": evidence,
        "pending_document_ids": pending,
    }
