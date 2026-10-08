"""Clasificación por reglas de un ítem contra el límite de la categoría «televisores».

Decide por el sustantivo principal (la primera palabra): «Soporte de pared para TV» es un accesorio,
«Mantenimiento de televisores» es un servicio y «Televisor… con soporte incluido» es un televisor.
"""

import re
from enum import StrEnum

from public_procurement.shared.text import normalize_text


class ItemClassification(StrEnum):
    INCLUDED = "included"
    EXCLUDED_ACCESSORY = "excluded_accessory"
    EXCLUDED_SERVICE = "excluded_service"
    UNDETERMINED = "undetermined"


SERVICE_HEADS = frozenset(
    {
        "mantenimiento",
        "instalacion",
        "reparacion",
        "servicio",
        "servicios",
        "arrendamiento",
        "alquiler",
        "calibracion",
    }
)
ACCESSORY_HEADS = frozenset(
    {
        "soporte",
        "soportes",
        "base",
        "bases",
        "cable",
        "cables",
        "control",
        "controles",
        "antena",
        "rack",
        "bracket",
        "kit",
        "repuesto",
        "repuestos",
    }
)
_TV_PATTERN = re.compile(r"\b(televisor|televisores|tv|smart\s?tv)\b")
_WORD_PATTERN = re.compile(r"[a-z0-9]+")


def classify_item(description: str) -> ItemClassification:
    normalized = normalize_text(description)
    words = _WORD_PATTERN.findall(normalized)
    head = words[0] if words else ""
    if head in SERVICE_HEADS:
        return ItemClassification.EXCLUDED_SERVICE
    if head in ACCESSORY_HEADS:
        return ItemClassification.EXCLUDED_ACCESSORY
    if _TV_PATTERN.search(normalized):
        return ItemClassification.INCLUDED
    return ItemClassification.UNDETERMINED
