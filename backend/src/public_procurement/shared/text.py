"""Normalización de texto en español para comparar y buscar (sin tildes ni mayúsculas)."""

import unicodedata


def normalize_text(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text.lower())
    return "".join(char for char in decomposed if not unicodedata.combining(char))
