"""Código legible y estable de una señal: `SG-<año>-<número>`."""

import re

from .facts import PurchaseSource

_DIGITS = re.compile(r"\d+")


def signal_code(
    source: PurchaseSource, source_record_id: str, year: int, line_number: int | None = None
) -> str:
    """SECOP II: número del contrato sin ceros a la izquierda (mín. 4 dígitos); TVEC: `T` + orden.

    `line_number` se agrega solo cuando la compra tiene más de un televisor con señal.
    """
    digits = "".join(_DIGITS.findall(source_record_id.split(".")[-1])) or "0"
    number = f"T{digits}" if source is PurchaseSource.TVEC else digits.lstrip("0").zfill(4)
    code = f"SG-{year}-{number}"
    return f"{code}-{line_number}" if line_number is not None else code
