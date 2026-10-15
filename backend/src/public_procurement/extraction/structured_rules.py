"""Reglas explícitas, sin interpretación jurídica ni inferencias de ausencia."""

import re
import unicodedata
import uuid
from dataclasses import dataclass
from decimal import Decimal
from itertools import pairwise
from typing import TypedDict

from .domain.content import EvidenceFragment
from .domain.structured import RULE_VERSION, StructuredFact, make_fact
from .domain.text import normalize_extracted_text
from .structured_tables import AMOUNT, UNIT, ItemRow, parse_cop, table_items, unit_name


@dataclass(frozen=True)
class TextView:
    original: str
    folded: str
    starts: tuple[int, ...]
    ends: tuple[int, ...]

    @classmethod
    def of(cls, text: str) -> "TextView":
        chars: list[str] = []
        starts: list[int] = []
        ends: list[int] = []
        for index, character in enumerate(text):
            for folded in unicodedata.normalize("NFKD", character.casefold()):
                if unicodedata.combining(folded):
                    if ends:
                        ends[-1] = index + 1
                    continue
                if folded.isspace():
                    folded = " "
                    if chars and chars[-1] == " ":
                        ends[-1] = index + 1
                        continue
                chars.append(folded)
                starts.append(index)
                ends.append(index + 1)
        return cls(text, "".join(chars), tuple(starts), tuple(ends))

    def span(self, start: int, end: int) -> tuple[int, int]:
        return self.starts[start], self.ends[end - 1]

    def original_group(self, match: re.Match[str], group: str | int = 0) -> str:
        start, end = self.span(*match.span(group))
        return self.original[start:end]


SIZE_UNIT = r"mililitros?|ml|litros?|l|kilogramos?|kg|gramos?|gr\.?|g|unidades?"
SIZE = rf"(?P<size>\d+(?:[.,]\d+)?)\s*(?P<sizeunit>{SIZE_UNIT})(?![a-z])"
PRODUCT = re.compile(rf"(?P<name>[a-z][a-z0-9]*(?:\s+[a-z][a-z0-9]*){{0,5}})\s+x\s*{SIZE}")
SIZE_PATTERN = re.compile(rf"\b{SIZE}")
DAYS = (
    r"(?:(?P<word>uno|un|dos|tres|cuatro|cinco|seis|siete|ocho|nueve|diez)\s*\(\s*)?"
    r"(?P<days>\d{1,3})\s*\)?\s*dias?\s+(?P<daykind>calendarios?|habiles)"
)
WORD_NUMBERS = {
    "uno": 1,
    "un": 1,
    "dos": 2,
    "tres": 3,
    "cuatro": 4,
    "cinco": 5,
    "seis": 6,
    "siete": 7,
    "ocho": 8,
    "nueve": 9,
    "diez": 10,
}


def size_unit(value: str) -> str:
    if value.startswith(("mililitro", "ml")):
        return "ml"
    if value.startswith(("litro", "l")):
        return "l"
    if value.startswith(("kilogramo", "kg")):
        return "kg"
    if value.startswith(("gramo", "gr", "g")):
        return "g"
    return "UNIDAD"


def pdf_items(fragments: list[EvidenceFragment]) -> list[ItemRow]:
    pattern = re.compile(
        rf"\b\d{{1,4}}\s+(?P<description>[a-z].{{3,800}}?)\s+"
        rf"(?P<quantity>\d+(?:,\d+)?)\s+(?P<unit>{UNIT})\s+"
        rf"\$?\s*(?P<price>{AMOUNT}|x{{3,}})\s+\$?\s*"
        rf"(?P<total>{AMOUNT}|x{{3,}})(?![\d,]|[.'\u2019]\d)",
    )
    rows = []
    for fragment in fragments:
        if fragment.source_locator.get("kind") != "pdf_page":
            continue
        view = TextView.of(fragment.text)
        header = re.search(
            r"\bitem\s+descripcion\b.{0,100}?\b(?:cant|cantidad)\b.{0,120}?"
            r"\bvalor unitario\s+valor total\b",
            view.folded,
        )
        if not header:
            continue
        section = view.folded[header.end() :]
        stop = re.search(r"\btotal\s+(?:\$\s*)?\d|\b\d+\.\s+(?:plazo|valor|forma|sitio)\b", section)
        end = header.end() + stop.start() if stop else len(view.folded)
        for match in pattern.finditer(view.folded, header.end(), end):
            rows.append(
                ItemRow(
                    view.original_group(match, "description").strip(),
                    Decimal(match["quantity"].replace(",", ".")),
                    unit_name(match["unit"]),
                    parse_cop(match["price"]),
                    parse_cop(match["total"]),
                    (fragment,),
                    f"{fragment.extraction_run_id}:{fragment.id}:item:{match.start()}",
                    "0.8",
                    view.span(*match.span()),
                )
            )
    return rows


class RowOptions(TypedDict):
    confidence: str
    span: tuple[int, int] | None
    group: str


def extract_facts(
    process_id: uuid.UUID,
    fragments: list[EvidenceFragment],
    version: str = RULE_VERSION,
) -> list[StructuredFact]:
    facts: list[StructuredFact] = []
    rows = [*table_items(fragments), *pdf_items(fragments)]
    for row in rows:
        sources = (*row.header_sources, *row.sources)
        values = {
            "description": row.description,
            "quantity": str(row.quantity),
            "unit": row.unit,
            "unit_price_cop": str(row.unit_price) if row.unit_price is not None else None,
            "total_cop": str(row.total) if row.total is not None else None,
        }
        options: RowOptions = dict(confidence=row.confidence, span=row.span, group=row.group)
        facts.append(
            make_fact(
                process_id,
                sources,
                "purchase_item",
                "item_row",
                version,
                string=row.description,
                normalized=values,
                **options,
            )
        )
        facts.append(
            make_fact(
                process_id,
                sources,
                "item_description",
                "item_row",
                version,
                string=row.description,
                normalized=normalize_extracted_text(row.description),
                **options,
            )
        )
        facts.append(
            make_fact(
                process_id,
                sources,
                "quantity",
                "item_row",
                version,
                number=row.quantity,
                unit=row.unit,
                **options,
            )
        )
        for kind, value in (("unit_price_cop", row.unit_price), ("total_cop", row.total)):
            if value is not None:
                facts.append(
                    make_fact(
                        process_id,
                        sources,
                        kind,
                        "item_row",
                        version,
                        number=value,
                        unit="COP",
                        **options,
                    )
                )

    for fragment in fragments:
        view = TextView.of(fragment.text)

        def emit(
            match: re.Match[str],
            kind: str,
            rule: str,
            *,
            string: str | None = None,
            number: Decimal | None = None,
            unit: str | None = None,
            normalized: object = None,
            confidence: str = "0.8",
            boolean: bool | None = None,
            subject: str | None = None,
            group: str | None = None,
            source: EvidenceFragment = fragment,
            text_view: TextView = view,
        ) -> None:
            facts.append(
                make_fact(
                    process_id,
                    (source,),
                    kind,
                    rule,
                    version,
                    string=string,
                    number=number,
                    unit=unit,
                    normalized=normalized,
                    confidence=confidence,
                    boolean=boolean,
                    subject=subject,
                    span=text_view.span(*match.span()),
                    group=group or f"{source.extraction_run_id}:{source.id}:span:{match.start()}",
                )
            )

        product_matches = list(PRODUCT.finditer(view.folded))
        for match in product_matches:
            name = view.original_group(match, "name").strip()
            amount, unit = Decimal(match["size"].replace(",", ".")), size_unit(match["sizeunit"])
            start, end = view.span(*match.span())
            item_group = next(
                (
                    row.group
                    for row in rows
                    if any(source.id == fragment.id for source in row.sources)
                    and (row.span is None or row.span[0] <= start < end <= row.span[1])
                ),
                None,
            )
            emit(
                match,
                "product",
                "product_presentation",
                string=name,
                normalized={
                    "name": normalize_extracted_text(name),
                    "presentation": str(amount),
                    "unit": unit,
                },
                group=item_group,
                subject=normalize_extracted_text(name),
            )
            emit(
                match,
                "presentation",
                "product_presentation",
                number=amount,
                unit=unit,
                confidence="1.0",
                group=item_group,
                subject=normalize_extracted_text(name),
            )
        for match in SIZE_PATTERN.finditer(view.folded):
            if any(
                product.start() <= match.start() < match.end() <= product.end()
                for product in product_matches
            ):
                continue
            if size_unit(match["sizeunit"]) == "UNIDAD":
                continue
            emit(
                match,
                "presentation",
                "explicit_size",
                number=Decimal(match["size"].replace(",", ".")),
                unit=size_unit(match["sizeunit"]),
                confidence="1.0",
            )
        for match in re.finditer(
            r"\bmarca\s*:\s*(?P<brand>[a-z0-9]+(?:[ -][a-z0-9]+){0,2})", view.folded
        ):
            emit(match, "brand", "explicit_brand", string=view.original_group(match, "brand"))
        for match in re.finditer(
            rf"\b(?P<count>\d+(?:,\d+)?)\s+(?P<unit>{UNIT})(?![a-z])", view.folded
        ):
            emit(
                match,
                "quantity",
                "quantity_unit",
                number=Decimal(match["count"].replace(",", ".")),
                unit=unit_name(match["unit"]),
                confidence="1.0",
            )
        for match in re.finditer(r"\bunspsc\b.{0,180}?\b(?P<code>\d{8})\b", view.folded):
            emit(match, "unspsc", "explicit_unspsc", string=match["code"], confidence="0.6")
        budget = (
            rf"\bpresupuesto oficial(?: estimado)?\b[^;]{{0,240}}?\$\s*(?P<amount>{AMOUNT})"
            r"(?![\d,]|[.'\u2019]\d)"
        )
        for match in re.finditer(budget, view.folded):
            emit(
                match,
                "official_budget_cop",
                "labelled_budget",
                number=parse_cop(match["amount"]),
                unit="COP",
            )
        for kind, label in (
            ("unit_price_cop", r"(?:valor|precio) unitario"),
            ("total_cop", r"valor total"),
            ("official_budget_cop", r"presupuesto oficial(?: estimado)?"),
        ):
            for match in re.finditer(
                rf"\b{label}\s*:\s*\$?\s*(?P<amount>{AMOUNT})(?![\d,]|[.'\u2019]\d)",
                view.folded,
            ):
                emit(match, kind, "labelled_cop", number=parse_cop(match["amount"]), unit="COP")
        for kind, pattern in (
            ("execution_term", rf"\bplazo de ejecucion\b.{{0,240}}?{DAYS}"),
            (
                "payment_term",
                rf"\b(?:pagar|pagara|pago(?=\s+(?:dentro|se realizara|de la factura)))"
                rf"\b.{{0,100}}?\bdentro de (?:los )?{DAYS}",
            ),
        ):
            pattern += (
                r"(?:\s*,?\s*(?P<trigger>(?:siguientes a|despues de|contados a partir de)"
                r"[^.;]{1,120}))?"
            )
            for match in re.finditer(pattern, view.folded):
                days = int(match["days"])
                if match["word"] and WORD_NUMBERS[match["word"]] != days:
                    continue
                unit = "días hábiles" if match["daykind"] == "habiles" else "días calendario"
                emit(
                    match,
                    kind,
                    "labelled_deadline",
                    number=Decimal(days),
                    unit=unit,
                    string=view.original_group(match),
                    normalized={
                        "days": days,
                        "day_kind": unit,
                        "trigger": view.original_group(match, "trigger").strip()
                        if match["trigger"]
                        else None,
                    },
                )
        for match in re.finditer(
            r"\b(?:unico pago|pago unico)(?:.{0,90}?100\s*%)?"
            r"|\bpagos parciales\b|\bcontra entrega\b",
            view.folded,
        ):
            explicit = match[0]
            mode = (
                "single_payment"
                if "unico" in explicit
                else "partial_payments"
                if "parciales" in explicit
                else "on_delivery"
            )
            emit(
                match,
                "payment_method",
                "explicit_payment",
                string=view.original_group(match),
                normalized={
                    "mode": mode,
                    "percent": 100 if re.search(r"100\s*%", explicit) else None,
                },
            )
        for match in re.finditer(
            r"\b100\s*%\s+del valor(?: total)?(?: del contrato)?", view.folded
        ):
            if not re.search(
                r"\bpago\b|\bpagar\b", view.folded[max(0, match.start() - 80) : match.start()]
            ):
                continue
            emit(
                match,
                "payment_percentage",
                "explicit_payment_percent",
                number=Decimal(100),
                unit="percent",
            )
        for match in re.finditer(
            r"\b(?:sitio|lugar) de entrega\s*:\s*(?P<place>.{5,500}?)(?=;|\s+\d+\.\s+[a-z]|$)",
            view.folded,
        ):
            emit(
                match,
                "delivery_location",
                "labelled_delivery",
                string=view.original_group(match, "place").strip(),
            )
        for kind, noun in (
            ("guarantee", r"(?:poliza|garantia)(?:s)?"),
            ("rup", r"rup|registro unico de proponentes"),
            ("experience", r"experiencia(?: contractual| previa)?"),
        ):
            negative = (
                r"\b(?:no se requiere|no se requieren|no requiere|no se exige|no es obligatori[oa])"
                rf"\s+(?:ningun tipo de |ninguna |el |la |tener |acreditar )?(?:{noun})\b"
            )
            negatives = list(re.finditer(negative, view.folded))
            for match in negatives:
                subject = "policy" if kind == "guarantee" and "poliza" in match[0] else kind
                emit(
                    match,
                    kind,
                    "explicit_requirement",
                    string="not_required",
                    boolean=False,
                    subject=subject,
                )
            positive = (
                r"\b(?:se requiere|se exige|debera acreditar|debe acreditar"
                r"|debera presentar|debe presentar)"
                rf"\s+(?:una |el |la |su |estar inscrito en el )?(?:{noun})\b"
            )
            for match in re.finditer(positive, view.folded):
                if any(
                    match.start() < neg.end() and match.end() > neg.start() for neg in negatives
                ):
                    continue
                if re.search(
                    r"\b(?:no|si|podra)\s*$",
                    view.folded[max(0, match.start() - 30) : match.start()],
                ):
                    continue
                emit(
                    match,
                    kind,
                    "explicit_requirement",
                    string="required",
                    boolean=True,
                    subject="policy" if kind == "guarantee" and "poliza" in match[0] else kind,
                )
        for match in re.finditer(r"\bgarantia de cumplimiento\b", view.folded):
            prefix = view.folded[max(0, match.start() - 60) : match.start()]
            prefix = re.split(r"[.;]", prefix)[-1]
            if not re.search(r"\bno\b|\bsi\b|\bpodra\b", prefix):
                emit(
                    match,
                    "guarantee",
                    "named_guarantee",
                    string="required",
                    boolean=True,
                    subject="performance_guarantee",
                )
        for match in re.finditer(
            r"\b(?:una unica entrega|entrega unica|una sola entrega|entregas parciales"
            r"|varias entregas|multiples entregas)\b",
            view.folded,
        ):
            emit(
                match,
                "delivery_count",
                "explicit_deliveries",
                string="multiple" if "entregas" in match[0] else "single",
            )
        for match in re.finditer(
            r"\b(?:anexando certificado de garantia"
            r"|reemplazar los productos que salgan defectuosos)\b",
            view.folded,
        ):
            emit(
                match,
                "operational_observation",
                "explicit_operation",
                string=view.original_group(match),
            )
    # Exact repeats from independent rules retain their evidence, never merge conflicting documents.
    facts.extend(adjacent_facts(process_id, fragments, version))
    return list({fact.fingerprint: fact for fact in facts}.values())


def adjacent_facts(
    process_id: uuid.UUID,
    fragments: list[EvidenceFragment],
    version: str,
) -> list[StructuredFact]:
    """Solo encabezado aislado + párrafo inmediatamente siguiente, dentro del mismo run."""
    headings = {
        "plazo de ejecucion": {"execution_term"},
        "plazo de ejecucion del contrato": {"execution_term"},
        "forma de pago": {"payment_method", "payment_term", "payment_percentage"},
        "presupuesto oficial": {"official_budget_cop"},
        "presupuesto oficial estimado": {"official_budget_cop"},
        "lugar de entrega": {"delivery_location"},
        "sitio de entrega": {"delivery_location"},
    }
    results = []
    ordered = sorted(fragments, key=lambda f: (str(f.extraction_run_id), f.ordinal))
    for heading, value in pairwise(ordered):
        label = normalize_extracted_text(heading.text).strip(" :")
        label = re.sub(r"^\d+(?:\.\d+)*\.?\s+", "", label)
        if label not in headings or heading.source_locator.get("kind") != "docx_paragraph":
            continue
        if (
            heading.extraction_run_id != value.extraction_run_id
            or heading.document_version_id != value.document_version_id
            or value.ordinal != heading.ordinal + 1
            or value.source_locator.get("kind") != "docx_paragraph"
            or len(value.text) > 2000
        ):
            continue
        combined = EvidenceFragment(
            heading.id,
            heading.document_version_id,
            heading.extraction_run_id,
            heading.original_name,
            heading.ordinal,
            heading.text.rstrip(" :") + ":\n" + value.text,
            heading.source_locator,
        )
        for candidate in extract_facts(process_id, [combined], version):
            if candidate.fact_type not in headings[label]:
                continue
            results.append(
                make_fact(
                    process_id,
                    (heading, value),
                    candidate.fact_type,
                    "adjacent_label",
                    version,
                    string=candidate.string_value,
                    number=candidate.numeric_value,
                    boolean=candidate.boolean_value,
                    unit=candidate.unit,
                    normalized=candidate.normalized_value,
                    confidence="0.6",
                    group=f"adjacent:{heading.id}:{value.id}",
                    subject=candidate.source_locator["subject"],
                )
            )
    return results
