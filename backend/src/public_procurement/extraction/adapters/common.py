import zipfile
from pathlib import Path
from typing import Any

from ..domain.content import ExtractionError, ExtractionLimits, Fragment


def check_archive(path: Path, limits: ExtractionLimits) -> None:
    try:
        with zipfile.ZipFile(path) as archive:
            entries = archive.infolist()
            if (
                len(entries) > limits.max_archive_entries
                or sum(e.file_size for e in entries) > limits.max_archive_bytes
            ):
                raise ExtractionError(
                    "archive_limit", "El paquete Office excede los límites de expansión."
                )
            if any(e.flag_bits & 1 for e in entries):
                raise ExtractionError("encrypted_file", "El documento está protegido o cifrado.")
    except zipfile.BadZipFile as exc:
        raise ExtractionError("corrupt_file", "El contenedor Office no es legible.") from exc


class FragmentBuilder:
    def __init__(self, limits: ExtractionLimits) -> None:
        self.limits = limits
        self.fragments: list[Fragment] = []
        self.chars = 0

    def add(self, text: str, locator: dict[str, Any], **location: Any) -> None:
        if not text.strip():
            return
        if "\x00" in text:
            raise ExtractionError("invalid_text", "El texto contiene caracteres no persistibles.")
        self.chars += len(text)
        if self.chars > self.limits.max_chars:
            raise ExtractionError("text_limit", "El texto excede el límite configurado.")
        for start in range(0, len(text), self.limits.fragment_chars):
            if len(self.fragments) >= self.limits.max_fragments:
                raise ExtractionError(
                    "fragment_limit", "Demasiados fragmentos para el límite configurado."
                )
            end = min(len(text), start + self.limits.fragment_chars)
            self.fragments.append(
                Fragment(
                    len(self.fragments) + 1,
                    text[start:end],
                    {**locator, "char_start": start, "char_end": end},
                    **location,
                )
            )
