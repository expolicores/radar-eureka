"""Presentation layer for EN-01 findings: high sensitivity, separate human review.

The four formal statuses produced by ``classify_experience`` are never modified here. This
module reads the classification together with document coverage and a generalizable detector
of apparently exhaustive habilitating-requirement lists, and decides how a process is shown:

- confirmed: formal ``no_experience_required``.
- priority_review: not formally resolved, but the governing documents carry an explicit
  waiver that still needs corroboration (shown even with unverified documents, as a
  warning), or a closed habilitating-requirement list without contractual experience and
  no known documentary gap.
- uncertain: no documentary signal either way strong enough to prioritize. Always visible.
- experience_indications: documentary signals of an experience requirement without a formal
  conclusion (a requirement clause, an explicit-requirement review or contractual-experience
  terms inside a habilitating list); shown with their clauses, pages, coverage and why no
  conclusion was reached. Capacity-only terms (financial indicators, RUP) stay uncertain.
- experience_required: reserved for the formal ``experience_required`` status.

No process is ever excluded here: uncertainty lowers priority and adds warnings only. Human
review evidence is attached as a separate annotation and never changes category or status.
"""

import json
import re
from pathlib import Path

from eureka_nacional_experience import NON_GOVERNING_TITLE, document_title
from spike_licitaciones_info import normalized

CATEGORIES = (
    "confirmed",
    "priority_review",
    "uncertain",
    "experience_indications",
    "experience_required",
)
LABELS = {
    "confirmed": "Hallazgo confirmado",
    "priority_review": "Hallazgo prioritario para revisión",
    "uncertain": "Hallazgo con incertidumbre",
    "experience_indications": "Indicios de experiencia exigida — requiere revisión",
    "experience_required": "Experiencia exigida",
}
RANK = {category: index for index, category in enumerate(CATEGORIES, start=1)}
ATTENTION = {"priority_review", "uncertain", "experience_indications"}
# Review effort, used only to order human review inside a category (never to exclude).
EFFORT = {"lectura_humana": 1, "documento_pendiente": 2, "formato_no_soportado": 3}
METHOD = "en01-findings-v2"
HUMAN_REVIEWS_FILE = Path(__file__).with_name("eureka_nacional_human_reviews.v1.json")

# Heading of a habilitating-requirements section, optionally numbered ("2.9") or lettered
# ("A."). Matched on normalized lines; "verificacion de los requisitos habilitantes" and
# similar prose do not start with the heading words and are not sections.
SECTION_HEADING = re.compile(
    r"^\s*(?P<number>\d+(?:[.-]\d+)*)?[.)]?\s*(?:(?P<letter>[a-z])[.)]\s*)?"
    r"requisitos?\s+(?:minimos\s+)?habilitantes?\b"
)
NUMBERED_HEADING = re.compile(r"^\s*(?P<number>\d+(?:[.-]\d+)*)[.)]?\s+(?P<title>\S.*)$")
LETTER_HEADING = re.compile(r"^\s*(?P<letter>[A-Z])[.)]\s+(?P<title>\S.*)$")
ITEM = re.compile(r"^\s*(?:[a-z]\)|\d{1,2}[.)]\s|[-•▪●*]\s)")
# Experience or capacity terms that make a habilitating list not "free of experience".
EXPERIENCE_TERMS = re.compile(
    r"\b(?:experiencia|capacidad (?:tecnica|financiera|organizacional|residual)|"
    r"contratos? (?:ejecutados?|similares|celebrados?|terminados?)|"
    r"certificaciones? de (?:experiencia|contratos?|cumplimiento contractual)|"
    r"indicadores? financieros?|registro unico de proponentes|rup)\b"
)
# Subset that points to contractual experience itself (not only financial capacity or RUP):
# inside a habilitating list it is a documentary indication of an experience requirement.
CONTRACT_EXPERIENCE_TERMS = re.compile(
    r"^(?:experiencia|contratos? .+|certificaciones? de (?:experiencia|contratos?|cumplimiento"
    r" contractual))$"
)
MAX_LISTED_ACTIONS = 5
ANNEX_REFERENCE = re.compile(r"\b(?:anexos?|formatos?|formularios?)\s*(?:no\.?\s*)?\d+\b")
MIN_ITEMS = 3


def _number(value):
    return tuple(int(part) for part in re.split(r"[.-]", value) if part)


def _uppercase(title):
    letters = [char for char in title[:60] if char.isalpha()]
    return len(letters) >= 4 and sum(char.isupper() for char in letters) / len(letters) >= 0.8


def _document_lines(document):
    for fragment in document.get("fragments", ()):
        page = fragment.source_locator.get("page_number")
        for line in str(fragment.text).splitlines():
            if line.strip():
                yield page, line


def _terminates(line, section):
    """A closing heading: an uppercase sibling or later section, never a list item.

    A line that continues the section's own item sequence (item 6 after item 5, letter f
    after letter e) is an item even when written in uppercase, so a long list cannot be cut
    short and look exhaustive."""
    numbered = NUMBERED_HEADING.match(line)
    if numbered and _uppercase(numbered["title"]):
        number = _number(numbered["number"])
        reference = section["_number"] or section["_outer"]
        continues = len(number) == 1 and number[0] == section["_last_item"] + 1
        if (
            reference
            and not continues
            and number > reference
            and number[: len(reference)] != reference
        ):
            return True
    lettered = LETTER_HEADING.match(line)
    if lettered and section["_letter"] and _uppercase(lettered["title"]):
        letter = lettered["letter"].lower()
        continues = section["_last_letter"] and ord(letter) == ord(section["_last_letter"]) + 1
        return letter > section["_letter"] and not continues
    return False


def _track_item(section, line):
    numeric = re.match(r"^\s*(\d{1,2})[.)]\s", line)
    if numeric:
        section["_last_item"] = int(numeric.group(1))
    letter = re.match(r"^\s*([a-z])\)", line)
    if letter:
        section["_last_letter"] = letter.group(1)


def habilitating_sections(document):
    """Detect habilitating-requirement sections and whether each closes in the read text."""
    sections, current, outer_number = [], None, None
    for page, line in _document_lines(document):
        text = normalized(line)
        if current is not None:
            if _terminates(line, current):
                current["closed"] = True
                current["terminator"] = " ".join(line.split())[:120]
                sections.append(current)
                current = None
            else:
                current["pages"].add(page)
                current["_lines"].append(line)
                _track_item(current, line)
                continue
        numbered = NUMBERED_HEADING.match(line)
        if numbered and _uppercase(numbered["title"]):
            outer_number = _number(numbered["number"])
        heading = SECTION_HEADING.match(text)
        # Prose wrapped onto a new line ("requisitos habilitantes y evaluara las ...") is not a
        # heading: a section heading is numbered, lettered or written in uppercase.
        if heading and (heading["number"] or heading["letter"] or _uppercase(line.strip())):
            current = {
                "heading": " ".join(line.split())[:160],
                "heading_page": page,
                "pages": {page},
                "closed": False,
                "terminator": None,
                "_number": _number(heading["number"]) if heading["number"] else None,
                "_letter": heading["letter"],
                "_outer": None if heading["number"] else outer_number,
                "_lines": [],
                "_last_item": 0,
                "_last_letter": None,
            }
    if current is not None:
        sections.append(current)
    found = []
    for section in sections:
        lines = section.pop("_lines")
        for key in ("_number", "_letter", "_outer", "_last_item", "_last_letter"):
            section.pop(key)
        body = " ".join(normalized(line) for line in lines)
        terms = sorted({match.group() for match in EXPERIENCE_TERMS.finditer(body)})
        items = [" ".join(line.split())[:80] for line in lines if ITEM.match(normalized(line))]
        found.append(
            {
                "document_id": document["document_id"],
                "document": document["name"],
                "role": document["role"],
                **section,
                "pages": sorted(page for page in section["pages"] if page is not None),
                "item_count": len(items),
                "items": items[:30],
                "experience_terms": terms,
                "annex_references": sorted(
                    {match.group() for match in ANNEX_REFERENCE.finditer(body)}
                ),
                "excerpt": " ".join(" ".join(lines).split())[:900],
                "apparently_exhaustive": section["closed"] and len(items) >= MIN_ITEMS,
            }
        )
    return found


def load_human_reviews(path=HUMAN_REVIEWS_FILE):
    if not Path(path).is_file():
        return []
    return json.loads(Path(path).read_text(encoding="utf-8"))["reviews"]


def human_reviews_for(identifiers, reviews):
    wanted = {str(value) for value in identifiers if value}
    return [review for review in reviews if wanted & set(review["identifiers"])]


def _coverage(documents, classification):
    considered = [doc for doc in documents if doc.get("role") != "excluded"]
    gaps = [
        {
            "document": doc["name"],
            "role": doc.get("role"),
            "reason": doc.get("validation_gap") or "no_procesado_por_el_sistema",
        }
        for doc in considered
        if not doc.get("complete")
        and not (
            doc.get("role") == "unknown" and NON_GOVERNING_TITLE.search(document_title(doc["name"]))
        )
    ]
    return {
        "inventory_complete": classification.get("inventory_complete", True),
        "system_verified": [
            {
                "document": doc["name"],
                "role": doc.get("role"),
                "pages_seen": len(doc.get("pages_seen") or []),
                "total_pages": doc.get("total_pages"),
            }
            for doc in considered
            if doc.get("complete")
        ],
        "not_verified_by_system": gaps,
        "non_governing_pending": [
            doc["name"]
            for doc in considered
            if not doc.get("complete")
            and doc.get("role") == "unknown"
            and NON_GOVERNING_TITLE.search(document_title(doc["name"]))
        ],
    }


def resolution_actions(category, coverage, classification, sections):
    """Documentary actions that would resolve the doubt; descriptive, never automatic."""
    actions = []
    gaps = sorted(
        coverage["not_verified_by_system"],
        key=lambda gap: {"primary": 0, "amendment": 1, "support": 2}.get(gap.get("role"), 3),
    )
    for gap in gaps[:MAX_LISTED_ACTIONS]:
        if gap["reason"] == "formato_no_procesable":
            actions.append(
                f"Revisar manualmente «{gap['document']}» (formato no soportado por el sistema)."
            )
        else:
            actions.append(f"Obtener y verificar «{gap['document']}» ({gap['reason']}).")
    if len(gaps) > MAX_LISTED_ACTIONS:
        actions.append(
            f"Y {len(gaps) - MAX_LISTED_ACTIONS} documentos más sin verificar "
            "(lista completa en la cobertura)."
        )
    if not coverage["inventory_complete"]:
        actions.append("Recuperar el inventario documental completo del proceso.")
    if classification.get("dependencies"):
        actions.append("Verificar el documento al que remite la cláusula de dependencia.")
    if category == "experience_indications":
        actions.append(
            "Confirmar en el documento rector si la cláusula de experiencia aplica a todo "
            "proponente y si hay adendas que la modifiquen."
        )
    elif category == "priority_review":
        actions.append(
            "Revisión humana confirmatoria de la lista habilitante y del estudio previo; "
            "comprobar adendas publicadas."
        )
    elif category == "uncertain" and not sections:
        actions.append("Ubicar manualmente la sección de requisitos habilitantes.")
    elif category == "uncertain":
        actions.append("Revisión humana de la sección habilitante y de las advertencias.")
    return actions


def assess_finding(classification, documents, *, identifiers=(), human_reviews=None):
    """Presentation category for one process; never alters ``classification``."""
    status, review = classification["status"], classification["review_category"]
    evidence = [
        item
        for item in classification.get("evidence", [])
        if item.get("role") in {"primary", "amendment", "support"}
    ]
    requirement_signals = [item for item in evidence if item["assertion_type"] == "EXIGENCIA"]
    waiver_signals = [item for item in evidence if item["assertion_type"] == "NEG_CONCLUSIVA"]
    conditional_signals = [
        item for item in evidence if item["assertion_type"] == "NORMATIVA_CONDICIONAL"
    ]
    coverage = _coverage(documents, classification)
    sections = [
        section
        for doc in documents
        if doc.get("complete") and doc.get("role") in {"primary", "amendment"}
        for section in habilitating_sections(doc)
    ]
    closed_without_experience = [
        section
        for section in sections
        if section["apparently_exhaustive"] and not section["experience_terms"]
    ]
    sections_with_experience = [section for section in sections if section["experience_terms"]]
    experience_sections = [
        section
        for section in sections_with_experience
        if any(CONTRACT_EXPERIENCE_TERMS.match(term) for term in section["experience_terms"])
    ]
    warnings = []
    if coverage["not_verified_by_system"]:
        warnings.append("documentos_no_verificados_por_el_sistema")
    if not coverage["inventory_complete"]:
        warnings.append("inventario_incompleto")
    if classification.get("dependencies"):
        warnings.append("dependencia_documental")
    if conditional_signals:
        warnings.append("clausula_normativa_condicional")
    if sections and not closed_without_experience and not sections_with_experience:
        warnings.append("lista_habilitante_no_cerrada_en_texto_leido")
    if sections_with_experience:
        warnings.append("lista_habilitante_menciona_experiencia_o_capacidad")
    if not sections:
        warnings.append("sin_lista_habilitante_detectada")

    if status == "no_experience_required":
        category, basis = "confirmed", "formal_no_experience_required"
    elif status == "experience_required":
        category, basis = "experience_required", "formal_experience_required"
    elif (
        review == "explicit_requirement" or requirement_signals or experience_sections
    ) and not waiver_signals:
        category = "experience_indications"
        basis = (
            "explicit_requirement_review_without_formal_conclusion"
            if review == "explicit_requirement"
            else "requirement_signal_without_formal_conclusion"
            if requirement_signals
            else "experience_terms_in_habilitating_list"
        )
    elif status != "not_resolved":
        category, basis = "uncertain", f"formal_{status}"
    elif review == "explicit_favorable" and not requirement_signals:
        # An explicit waiver is a favorable candidate for human review even while other
        # documents are unverified; the gap stays as a warning, never as a demotion.
        category, basis = "priority_review", "explicit_waiver_pending_corroboration"
    elif (
        closed_without_experience
        and not sections_with_experience
        and not requirement_signals
        and not conditional_signals
        and not classification.get("dependencies")
        and coverage["inventory_complete"]
        and not coverage["not_verified_by_system"]
    ):
        category, basis = "priority_review", "closed_habilitating_list_without_experience"
    else:
        category = "uncertain"
        basis = (
            "conflicting_requirement_and_waiver_signals"
            if requirement_signals
            else "habilitating_list_mentions_experience"
            if experience_sections
            else "habilitating_list_mentions_capacity"
            if sections_with_experience
            else "closed_list_with_unverified_documents"
            if closed_without_experience
            else "no_closed_habilitating_list"
        )
    reviews = human_reviews_for(identifiers, human_reviews or [])
    names = {doc["document_id"]: doc["name"] for doc in documents}
    indications = [
        {
            "document": names.get(item["document_id"], item["document_id"]),
            "role": item.get("role"),
            "page": item.get("page"),
            "basis": item.get("basis"),
            "scope": item.get("scope"),
            "excerpt": " ".join(str(item.get("excerpt", "")).split())[:400],
        }
        for item in requirement_signals
    ] + [
        {
            "document": section["document"],
            "role": section["role"],
            "page": section["heading_page"],
            "basis": "experience_terms_in_habilitating_list",
            "scope": "habilitating_section",
            "excerpt": f"{section['heading']}: {', '.join(section['experience_terms'])}",
        }
        for section in experience_sections
    ]
    gaps = coverage["not_verified_by_system"]
    effort = (
        "formato_no_soportado"
        if any(gap["reason"] == "formato_no_procesable" for gap in gaps)
        else "documento_pendiente"
        if gaps or not coverage["inventory_complete"]
        else "lectura_humana"
    )
    return {
        "method": METHOD,
        "category": category,
        "label": LABELS[category],
        "rank": RANK[category],
        "basis": basis,
        "visible": True,
        "needs_human_attention": category in ATTENTION,
        "review_effort": effort,
        "formal_status": status,
        "formal_status_unchanged": True,
        "formal_reason": classification.get("reason"),
        "review_category": review,
        "review_reason": classification.get("review_reason"),
        "why_not_formal": (
            None
            if status in {"experience_required", "no_experience_required"}
            else {
                "reason": classification.get("reason"),
                "review_reason": classification.get("review_reason"),
                "documents_not_verified": [gap["document"] for gap in gaps],
                "dependencies": len(classification.get("dependencies") or []),
            }
        ),
        "requirement_indications": indications,
        "resolution_actions": resolution_actions(category, coverage, classification, sections),
        "warnings": warnings,
        "habilitating_sections": sections,
        "coverage": coverage,
        "human_review": reviews,
        "human_review_changes_category": False,
    }
