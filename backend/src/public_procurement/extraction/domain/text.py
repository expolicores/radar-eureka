import re
import unicodedata

NORMALIZATION_VERSION = "text-normalization-v1"


def normalize_extracted_text(text: str) -> str:
    """Solo para búsqueda: Unicode, espacios, casefold y tolerancia a acentos."""
    consistent = unicodedata.normalize("NFKC", text).casefold()
    decomposed = unicodedata.normalize("NFKD", consistent)
    folded = "".join(c for c in decomposed if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", folded).strip()
