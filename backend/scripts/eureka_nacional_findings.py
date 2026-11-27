"""Presentation layer for EN-01 findings: high sensitivity, separate human review.

The four formal statuses produced by ``classify_experience`` are never modified here. This
module reads the classification together with document coverage and a generalizable detector
of apparently exhaustive habilitating-requirement lists, and decides how a process is shown:

- confirmed: formal ``no_experience_required``.
- priority_review: not formally resolved, but the governing documents carry a closed
  habilitating-requirement list without contractual experience (or an explicit waiver that
  still needs corroboration) and no documentary gap is known.
- uncertain: anything else that is not an experience requirement. Always visible.
- experience_required: formal ``experience_required`` or an explicit requirement review.

No process is ever excluded here: uncertainty lowers priority and adds warnings only. Human
review evidence is attached as a separate annotation and never changes category or status.
"""

import json
import re
from pathlib import Path

from eureka_nacional_experience import NON_GOVERNING_TITLE, document_title
from spike_licitaciones_info import normalized

CATEGORIES = ("confirmed", "priority_review", "uncertain", "experience_required")
LABELS = {
    "confirmed": "Hallazgo confirmado",
    "priority_review": "Hallazgo prioritario para revisión",
    "uncertain": "Hallazgo con incertidumbre",
    "experience_required": "Experiencia exigida",
}
RANK = {"confirmed": 1, "priority_review": 2, "uncertain": 3, "experience_required": 4}
METHOD = "en01-findings-v1"
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


def assess_finding(classification, documents, *, identifiers=(), human_reviews=None):
    """Presentation category for one process; never alters ``classification``."""
    status, review = classification["status"], classification["review_category"]
    evidence = [
        item
        for item in classification.get("evidence", [])
        if item.get("role") in {"primary", "amendment", "support"}
    ]
    requirement_signals = [item for item in evidence if item["assertion_type"] == "EXIGENCIA"]
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
    elif status == "experience_required" or review == "explicit_requirement":
        category = "experience_required"
        basis = (
            "formal_experience_required"
            if status == "experience_required"
            else "explicit_requirement_review"
        )
    elif status != "not_resolved":
        category, basis = "uncertain", f"formal_{status}"
    elif review == "explicit_favorable" and not requirement_signals:
        category = "priority_review" if not coverage["not_verified_by_system"] else "uncertain"
        basis = "explicit_waiver_pending_corroboration"
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
            "requirement_signal_without_formal_conclusion"
            if requirement_signals
            else "habilitating_list_mentions_experience"
            if sections_with_experience
            else "closed_list_with_unverified_documents"
            if closed_without_experience
            else "no_closed_habilitating_list"
        )
    reviews = human_reviews_for(identifiers, human_reviews or [])
    return {
        "method": METHOD,
        "category": category,
        "label": LABELS[category],
        "rank": RANK[category],
        "basis": basis,
        "visible": True,
        "formal_status": status,
        "formal_status_unchanged": True,
        "review_category": review,
        "warnings": warnings,
        "habilitating_sections": sections,
        "coverage": coverage,
        "human_review": reviews,
        "human_review_changes_category": False,
    }
