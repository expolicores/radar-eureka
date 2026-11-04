"""Opt-in research rules for explicit PDF TV pricing rows; not used by Radar."""

import re
import uuid

from .domain.content import EvidenceFragment
from .domain.structured import StructuredFact, make_fact
from .structured_rules import RowOptions, TextView, extract_facts
from .structured_tables import AMOUNT, parse_cop

RESEARCH_TV_RULE_VERSION = "structured-tv-research-v3"


def extract_tv_research_facts(
    process_id: uuid.UUID, fragments: list[EvidenceFragment], version: str
) -> list[StructuredFact]:
    results = extract_facts(process_id, fragments, version)
    # This is deliberately narrow: an explicit description/quantity/prices table,
    # TV as row head, two monetary cells and verified row arithmetic. No dividing
    # a contract's global amount and no using a stand-alone budget as item price.
    delimiter = r"[\s|]+"
    pattern = re.compile(
        rf"(?P<description>\btelevisor(?:es)?\b[^$]{{5,350}}?)\s+"
        rf"(?P<quantity>\d{{1,4}}){delimiter}(?:(?:unidades?|und|un|u){delimiter})?\$?\s*(?P<price>{AMOUNT})\s+"
        rf"\$?\s*(?P<total>{AMOUNT})(?![\d,.])"
    )
    quantity_first = re.compile(
        rf"(?P<quantity>\d{{1,4}}){delimiter}(?:(?:unidades?|und|un|u){delimiter})?"
        rf"(?P<description>\btelevisor(?:es)?\b[^$]{{5,500}}?){delimiter}"
        rf"\$?\s*(?P<price>{AMOUNT}){delimiter}\$?\s*(?P<total>{AMOUNT})(?![\d,.])"
    )
    for fragment in fragments:
        if fragment.source_locator.get("kind") != "pdf_page":
            continue
        view = TextView.of(fragment.text)
        header = re.search(
            r"\b(?:descripcion|producto|articulo)\b.{0,160}?\b(?:cant|cantidad)\b.{0,160}?\b(?:valor|precio|v\.?\s*unit|valorunitario)\b",
            view.folded,
        )
        if not header:
            header = re.search(
                r"\b(?:cant|cantidad)\b.{0,100}?\b(?:descripcion|producto|articulo)\b.{0,160}?\b(?:valor|precio|valorunitario)\b",
                view.folded,
            )
        if not header:
            continue
        explicit = bool(
            re.search(
                r"(?:valor|precio|vr\.?|v\.?)\s*unit(?:ari[oa])?\b|\bv\.?\s*unit\b",
                view.folded[header.start() : header.end() + 130],
            )
        )
        if re.search(
            r"estimad|promedio|cotizaci[oó]n", view.folded[header.start() : header.end() + 180]
        ):
            explicit = False
        candidates = list(pattern.finditer(view.folded, header.end()))
        if view.folded[header.start() : header.end()].find("cant") < view.folded[
            header.start() : header.end()
        ].find("descripcion"):
            candidates.extend(quantity_first.finditer(view.folded, header.end()))
        for match in candidates:
            start, _ = view.span(*match.span("description"))
            prefix = fragment.text[:start].rsplit("\n", 1)[-1].strip()
            if prefix and not re.fullmatch(r"\d{1,3}", prefix):
                continue
            quantity = parse_cop(match["quantity"])
            price, total = parse_cop(match["price"]), parse_cop(match["total"])
            if not quantity or not price or not total or abs(quantity * price - total) > 1:
                continue
            description = view.original_group(match, "description")
            group = f"tv-research:{fragment.id}:{match.start()}"
            rule = "tv_row_price_explicit" if explicit else "tv_row_price_requires_review"
            common: RowOptions = {
                "confidence": "0.8" if explicit else "0.6",
                "span": view.span(*match.span()),
                "group": group,
            }
            results.append(
                make_fact(
                    process_id,
                    (fragment,),
                    "purchase_item",
                    rule,
                    version,
                    string=description,
                    normalized={
                        "description": description,
                        "quantity": str(quantity),
                        "unit": None,
                        "unit_price_cop": str(price),
                        "total_cop": str(total),
                    },
                    **common,
                )
            )
            for kind, value in (
                ("quantity", quantity),
                ("unit_price_cop", price),
                ("total_cop", total),
            ):
                results.append(
                    make_fact(
                        process_id,
                        (fragment,),
                        kind,
                        rule,
                        version,
                        number=value,
                        unit="COP" if kind != "quantity" else None,
                        **common,
                    )
                )
    return results
