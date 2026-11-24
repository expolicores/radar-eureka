"""Contextual, deterministic experience assertions and conservative process decisions."""

import re

from spike_licitaciones_info import normalized

NUMBER_PREFIX = re.compile(r"^(?:(?:\d+(?:[.-]\d+)*)(?:[.\s_):–-]+|$))+")
PRIMARY = re.compile(
    r"\b(?:invitacion|inv\s*mc|pliegos?|condiciones definitivas|terminos de referencia)\b"
)
AMENDMENT = re.compile(
    r"\b(?:adendas?|modificaciones?|modificacion|aclaraciones?|aclaracion|enmiendas?)\b"
)
SUPPORT = re.compile(
    r"\b(?:estudios? previos?|anexos?|requisitos?|especificaciones|ficha tecnica|reglamento)\b"
)
EXCLUDED = re.compile(
    r"^(?:acta (?:de cierre|de liquidacion|de entrega|de inicio)|contrato (?:firmado|suscrito)|"
    r"poliza|liquidacion|informe de evaluacion|proyecto (?:de )?pliego|borrador|"
    r"cotizaciones?\b|cotizacion\b|proforma\b)"
)
EXPERIENCE = re.compile(r"\bexperiencia\b")
EXPERIENCE_HEADING = re.compile(
    r"^(?:requisito(?:s)?(?: habilitante)? de |acreditacion de (?:la )?)?experiencia"
    r"(?: (?:contractual|minima|requerida|habilitante|del (?:oferente|proponente)))*$"
)
SCOPE = re.compile(
    r"\b(?:proponentes?|oferentes?|licitantes?|experiencia contractual|experiencia habilitante|"
    r"contratos? ejecutados?|requisito habilitante)\b"
)
OTHER_CONTEXT = re.compile(
    r"\b(?:del (?:personal|fabricante|equipo humano|profesional|director|coordinador)|"
    r"de (?:los (?:profesionales|tecnicos)|la empresa fabricante)|desempates?|"
    r"puntajes?|puntuacion|ponderacion|evaluad[ao] con puntos|"
    r"factor de calificacion|criterio de evaluacion)\b"
)
PREFERENCE_SHARE = re.compile(
    r"\b(?:mipymes?|cooperativa|asociacion mutual)\b.{0,250}"
    r"\baport[a-z ]{1,35}.{0,110}\bde la experiencia\b.{0,45}\bacreditada en la oferta\b"
)
NEGATIVE = re.compile(
    r"\b(?:no se (?:exige|exigira|requiere|requerira|solicita|solicitara)(?: acreditar)?|"
    r"no (?:se )?debe(?:ra)? acreditar|no sera necesario acreditar)"
    r"\s+(?:de\s+)?(?:(?:la|una|ninguna)\s+)?experiencia\b|"
    r"\bexperiencia(?: contractual| habilitante)?(?: del (?:proponente|oferente))?"
    r"\s+no (?:aplica|(?:es|sera) (?:un )?requisito(?: habilitante)?)\b"
)
SHORT_NEGATIVE = re.compile(r"^(?:no aplica|no se (?:exige|requiere|solicita))\s*[.!]?$")
POSITIVE = re.compile(
    r"\b(?:debe(?:ra|ran)?\s+(?:acreditar|certificar|demostrar|presentar|contar con)|"
    r"se (?:exige|exigira|requiere|requerira)|requisito obligatori[ao]|"
    r"rige como requisito habilitante)\b"
)
DOUBLE_NEGATIVE = re.compile(
    r"\bno se (?:aceptaran|aceptan|admitiran|admiten) (?:las )?ofertas "
    r"que no acredit(?:en|an)\s+(?:(?:la|su)\s+)?experiencia\b"
)
GENERAL_OR_HYPOTHETICAL = re.compile(
    r"\b(?:no (?:estan|estaran) obligadas|podra(?:n)? (?:exigir|establecer)|"
    r"si (?:la|el|se)|cuando (?:sea[n]?|se|resulte[n]?)|en caso de|si aplica)\b"
)
LIMITED_APPLICABILITY = re.compile(
    r"\b(?:lotes?|grupos?|segmentos?|excepto|salvo|siempre que|alternativamente|"
    r"para (?:la )?(?:inscripcion|registro|precalificacion|subsanacion))\b"
)
DEPENDENCY = re.compile(
    r"\b(?:reglamento interno(?: de contratacion)?|"
    r"(?:segun|conforme al|vease|consultar|remite a|se detallan en|establecidos en)"
    r".{0,40}\b(?:anexo|archivo|documento|numeral)\b)"
)
NUMBERED_SECTION = re.compile(r"^\d+(?:[.-]\d+)*[.\s_):–-]+")
GENERAL_EXPERIENCE_SECTION = re.compile(
    r"^experiencia (?:general|especifica|habilitante)(?: del (?:proponente|oferente))?"
    r"(?: \(admisible/no admisible\))?$"
)
LIMITED_SECTION = re.compile(
    r"\b(?:mipymes?|proponentes? plurales?|desempates?|lotes?|subsanacion)\b"
)
LIMITED_SUBJECT = re.compile(
    r"\b(?:en el caso de los|tratandose de|si (?:la oferta|el proponente) .{0,50})"
    r"\s+(?:consorcios|uniones temporales|proponentes? plurales?)\b|"
    r"\b(?:solo|unicamente|exclusivamente) (?:para|a) (?:las? |los? )?"
    r"(?:mipymes?|consorcios|uniones temporales|proponentes? plurales?)\b"
)
ADMISSIBILITY = re.compile(r"^acreditar experiencia\b.{0,180}\bcontratos?\b")
CONDITIONAL = "NORMATIVA_CONDICIONAL"
NEG = "NEG_CONCLUSIVA"
REQ = "EXIGENCIA"
OTHER = "OTRO"
ASSERTION_TYPES = (NEG, REQ, CONDITIONAL, OTHER)
STATUSES = ("experience_required", "no_experience_required", "experience_ambiguous", "not_resolved")


def document_role(name):
    text = NUMBER_PREFIX.sub("", normalized(name).strip()).replace("_", " ").replace("-", " ")
    if EXCLUDED.search(text):
        return "excluded"
    if re.match(r"^(?:formatos?|formularios?)\b", text):
        return "support"
    if AMENDMENT.search(text):
        return "amendment"
    if PRIMARY.search(text):
        return "primary"
    if SUPPORT.search(text):
        return "support"
    return "unknown"


def document_priority(name, role):
    text = normalized(name)
    if role == "primary":
        return (0, not bool(re.search(r"\b(?:definitiv[oa]|final|vigente)\b", text)))
    return (
        {"amendment": 1, "support": 2, "unknown": 3, "excluded": 4}[role],
        "habilitante" not in text,
    )


def document_cover_metadata(first_page):
    # Cover cues are auditable and never imply that an amendment supersedes another version.
    lines = [line.strip() for line in first_page.splitlines() if line.strip()][:8]
    heading = " ".join(normalized(" ".join(lines)).split())
    marker = re.search(
        r"\b(?:definitiv[oa]|version final|vigente|borrador|proyecto (?:de )?pliego)\b", heading
    )
    date = re.search(
        r"\bfecha(?: de (?:publicacion|expedicion|emision))?\s*:\s*"
        r"(\d{4}-\d{2}-\d{2}|\d{1,2}[/-]\d{1,2}[/-]\d{4})\b",
        heading,
    )
    role = next((document_role(line) for line in lines if document_role(line) == "excluded"), None)
    if role is None and any(
        re.match(
            r"^(?:invitacion|pliego(?: de condiciones)?)\b", NUMBER_PREFIX.sub("", normalized(line))
        )
        for line in lines
    ):
        role = "primary"
    return role, {
        "version_marker": marker.group() if marker else None,
        "labeled_date": date[1] if date else None,
    }


def normalized_for_matching(clause, method=None):
    text = " ".join(normalized(clause).split())
    text = re.sub(r"\bap ort", "aport", text)
    text = re.sub(r"\bacredita r(?=\s+(?:(?:la|su)\s+)?experiencia\b)", "acreditar", text)
    if method == "ocr_text":
        # Repair narrow OCR confusions without changing the polarity token.
        text = re.sub(r"\bexperienc[1l]a\b", "experiencia", text)
        text = re.sub(r"\brequ[1l]ere\b", "requiere", text)
    return text


def assertion(clause, *, heading=None, section=None, immediate=False, method=None):
    text = normalized_for_matching(clause, method)
    experience = bool(EXPERIENCE.search(text))
    section_text = normalized_for_matching(section or "", method)
    if experience and (
        LIMITED_SUBJECT.search(text)
        or (
            GENERAL_EXPERIENCE_SECTION.search(section_text) is None
            and "experiencia" in section_text
            and LIMITED_SECTION.search(section_text)
        )
    ):
        return CONDITIONAL, "limited_applicability"
    if OTHER_CONTEXT.search(text) or PREFERENCE_SHARE.search(text) or heading == "other":
        return (OTHER, "other_subject_or_criterion") if experience else None
    dependency = DEPENDENCY.search(text)
    if dependency and (
        experience or "reglamento interno" in dependency.group() or "habilitante" in text
    ):
        return CONDITIONAL, "document_dependency"
    scoped_waiver = heading == "experience" and immediate and SHORT_NEGATIVE.fullmatch(text)
    scoped_requirement = (
        heading == "experience" and POSITIVE.search(text) and re.search(r"\bcontratos?\b", text)
    )
    if not (experience or scoped_waiver or scoped_requirement):
        return None
    if LIMITED_APPLICABILITY.search(text):
        return CONDITIONAL, "limited_applicability"
    if GENERAL_OR_HYPOTHETICAL.search(text):
        return CONDITIONAL, "general_or_hypothetical"
    if (
        "admisible/no admisible" in section_text
        and GENERAL_EXPERIENCE_SECTION.search(section_text)
        and ADMISSIBILITY.search(text)
        and not re.search(r"\bno\b", text[: text.find("contrato")])
    ):
        return REQ, "explicit_bidder_requirement"
    if scoped_waiver:
        return NEG, "heading_scoped_waiver"
    if DOUBLE_NEGATIVE.search(text):
        return REQ, "offer_rejected_without_experience"
    if match := NEGATIVE.search(text):
        rest = NEGATIVE.sub("", text)
        if (
            not re.search(r"\bno\b", text[: match.start()])
            and not POSITIVE.search(rest)
            and not re.search(
                r"\b(?:minima|especifica|general|adicional|previa|diferente|distinta)\b", rest
            )
        ):
            return NEG, "explicit_waiver"
    if (
        POSITIVE.search(text)
        and not re.search(r"\bno\b", text)
        and (SCOPE.search(text) or heading == "experience")
    ):
        return REQ, "explicit_bidder_requirement"
    return CONDITIONAL, "scope_or_obligation_unclear"


def clause_rule(clause):
    result = assertion(clause)
    return result[0] if result else None


def page_clauses(text, method=None, *, page=None, inherited_section=None):
    heading = None
    heading_text = None
    lines = []
    clauses_found = []
    section = inherited_section

    def flush():
        clauses = re.split(r"(?<=[.;!?])\s+(?=[A-ZÁÉÍÓÚÑ])", " ".join(lines))
        for i, clause in enumerate(clauses):
            if clause:
                clauses_found.append((clause, heading, heading_text, i == 0, section))

    for raw in text.splitlines():
        line = " ".join(raw.split())
        if not line:
            continue
        stripped = NUMBER_PREFIX.sub("", line)
        label, separator, body = stripped.partition(":")
        clean_label = normalized_for_matching(label, method).rstrip(".")
        # Some native/OCR outputs retain the title and response on the same line.
        if not separator:
            inline = re.match(
                r"(?i)^(.+?)\s+(no aplica|no se requiere|no se exige)[.!]?$", stripped
            )
            if inline and EXPERIENCE_HEADING.fullmatch(normalized_for_matching(inline[1], method)):
                clean_label, body = normalized(inline[1]), inline[2]
        experience_header = bool(EXPERIENCE_HEADING.fullmatch(clean_label))
        section_header = (
            len(label) <= 95
            and not SHORT_NEGATIVE.fullmatch(normalized_for_matching(stripped, method))
            and label.isupper()
            and bool(re.search(r"[A-ZÁÉÍÓÚÑ]", label))
            and (stripped != line or separator or len(label.split()) <= 5)
        )
        general_section = GENERAL_EXPERIENCE_SECTION.fullmatch(clean_label)
        if experience_header or section_header or general_section:
            flush()
            if NUMBERED_SECTION.match(line) or general_section:
                section = (label, page)
            lines = [body.strip()] if body.strip() else []
            heading = (
                "experience"
                if experience_header
                else "other"
                if OTHER_CONTEXT.search(clean_label)
                else None
            )
            heading_text = (inline[1] if not separator and inline else label) if heading else None
        else:
            lines.append(line)
    flush()
    return clauses_found, section


def document_assertions(document):
    if document["role"] == "excluded":
        return
    previous_section = None
    for fragment in document.get("fragments", ()):
        locator = fragment.source_locator
        method = locator.get("extraction_method")
        page = locator.get("page_number")
        # Carry an explicit numbered/experience section only into the adjacent native page.
        inherited = (
            previous_section
            if method == "native_pdf_text"
            and page
            and previous_section
            and previous_section[1] in {page - 1, page}
            else None
        )
        clauses, section = page_clauses(
            fragment.text, method, page=page, inherited_section=inherited
        )
        if method == "native_pdf_text":
            previous_section = section
        for clause, heading, heading_text, immediate, context in clauses:
            section_label, section_page = context or (None, None)
            section_text = normalized_for_matching(section_label or "", method)
            result = assertion(
                clause, heading=heading, section=section_label, immediate=immediate, method=method
            )
            if not result:
                continue
            kind, basis = result
            anchor = EXPERIENCE.search(normalized(clause)) or DEPENDENCY.search(normalized(clause))
            start = max(0, anchor.start() - 240) if anchor else 0
            yield {
                "assertion_type": kind,
                "basis": basis,
                "document_id": document["document_id"],
                "document": document["name"],
                "role": document["role"],
                "url": document.get("url"),
                "sha256": document.get("sha256"),
                "page": locator.get("page_number"),
                "locator": locator,
                "method": method,
                "heading": heading_text,
                "section": section_label,
                "section_page": section_page,
                "scope": (
                    "limited"
                    if basis == "limited_applicability"
                    else "general_bidder"
                    if kind == REQ
                    and GENERAL_EXPERIENCE_SECTION.fullmatch(section_text)
                    and not LIMITED_SECTION.search(section_text)
                    else "unspecified"
                ),
                "excerpt": clause[start : start + 620],
            }


def classify_experience(documents, *, inventory_complete=True):
    evidence = [item for doc in documents for item in document_assertions(doc)]
    pending = [
        doc["document_id"] for doc in documents if doc["role"] != "excluded" and not doc["complete"]
    ]
    pending_ids = set(pending)
    primary_complete = any(doc["role"] == "primary" and doc["complete"] for doc in documents)
    credible = {doc["document_id"] for doc in documents if doc["complete"]}
    relevant = [item for item in evidence if item["role"] in {"primary", "amendment", "support"}]
    observed = {item["assertion_type"] for item in relevant}
    decisive = {
        item["assertion_type"]
        for item in relevant
        if item["role"] in {"primary", "amendment"} and item["document_id"] in credible
    }
    dependencies = [item for item in relevant if item["basis"] == "document_dependency"]
    restricted = any(item["basis"] == "limited_applicability" for item in relevant)
    governing_pending = any(
        doc["role"] in {"primary", "amendment", "unknown"} and not doc["complete"]
        for doc in documents
    )
    known_governing_pending = any(
        doc["role"] in {"primary", "amendment"} and not doc["complete"] for doc in documents
    )
    applicable = [
        item
        for item in relevant
        if item["assertion_type"] == REQ
        and item["scope"] == "general_bidder"
        and item["role"] == "primary"
        and item["document_id"] in credible
    ]
    conflict = {NEG, REQ} <= observed
    if conflict:
        status, reason = "experience_ambiguous", "conflicting_clauses"
    elif restricted and not applicable:
        status, reason = "experience_ambiguous", "limited_applicability"
    elif dependencies and observed.intersection({NEG, REQ}):
        status, reason = "experience_ambiguous", "unverified_document_dependency"
    elif REQ in decisive and primary_complete and inventory_complete and not governing_pending:
        status, reason = "experience_required", "explicit_bidder_requirement"
    elif NEG in decisive and primary_complete and inventory_complete and not pending:
        status, reason = "no_experience_required", "explicit_waiver_with_document_coverage"
    else:
        status = "not_resolved"
        if NEG in observed:
            reason = "favorable_requires_corroboration"
        elif REQ in observed:
            reason = "requirement_requires_corroboration"
        elif primary_complete:
            reason = "document_dependency" if dependencies else "no_decisive_clause"
        else:
            reason = "governing_documents_incomplete"

    if conflict:
        review, review_reason = "limited_or_ambiguous", "conflicting_clauses"
        review_evidence = [item for item in relevant if item["assertion_type"] in {NEG, REQ}]
    elif NEG in observed:
        review, review_reason = "explicit_favorable", reason
        review_evidence = [item for item in relevant if item["assertion_type"] == NEG]
    elif applicable and inventory_complete and not known_governing_pending and not dependencies:
        review = "explicit_requirement"
        review_reason = "general_bidder_clause_in_complete_primary"
        review_evidence = applicable
    elif restricted or (dependencies and REQ in observed):
        review, review_reason = "limited_or_ambiguous", reason
        review_evidence = [
            item
            for item in relevant
            if item["basis"] in {"limited_applicability", "document_dependency"}
        ]
    elif primary_complete and REQ not in observed:
        review, review_reason = "documentary_silence", reason
        review_evidence = relevant
    else:
        review = "insufficient_evidence"
        review_reason = (
            "governing_coverage_pending"
            if applicable and (known_governing_pending or not inventory_complete)
            else "general_bidder_scope_unconfirmed"
            if REQ in observed
            else reason
        )
        review_evidence = relevant
    return {
        "status": status,
        "reason": reason,
        "review_category": review,
        "review_reason": review_reason,
        "review_evidence": review_evidence,
        "review_priority": {
            "explicit_favorable": 1,
            "documentary_silence": 2,
            "limited_or_ambiguous": 3,
            "insufficient_evidence": 4,
            "explicit_requirement": 5,
        }[review],
        "classification_method": "en01-contextual-v3",
        "inventory_complete": inventory_complete,
        "evidence": evidence,
        "pending_document_ids": pending,
        "document_coverage": {
            "complete_primary": primary_complete,
            "pending": [
                {"document_id": doc["document_id"], "document": doc["name"], "role": doc["role"]}
                for doc in documents
                if doc["document_id"] in pending_ids
            ],
        },
        "dependencies": [
            {"document_id": item["document_id"], "page": item["page"], "excerpt": item["excerpt"]}
            for item in dependencies
        ],
    }
