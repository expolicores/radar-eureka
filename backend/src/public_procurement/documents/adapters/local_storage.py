"""Binarios direccionados por hash; temporales fuera del espacio de documentos disponibles."""

import hashlib
import os
import tempfile
import zipfile
from collections.abc import Iterable, Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import BinaryIO

from ..domain.document import AcquisitionError, StoredBinary


def _validate(path: Path, name: str) -> None:
    with path.open("rb") as file:
        header = file.read(512)
    if not header:
        raise AcquisitionError("empty_file", "El archivo descargado está vacío.")
    lowered = header.lstrip().lower()
    if lowered.startswith((b"<!doctype html", b"<html", b"<?xml")):
        raise AcquisitionError("invalid_content", "La respuesta no es un documento binario válido.")
    if header.startswith(b"%PDF-"):
        # Validación estructural mínima sin extraer contenido.
        with path.open("rb") as file:
            file.seek(max(0, path.stat().st_size - 4096))
            if b"%%EOF" not in file.read():
                raise AcquisitionError(
                    "invalid_content", "PDF incompleto: falta el marcador final."
                )
        return
    if header.startswith(b"PK\x03\x04"):
        try:
            with zipfile.ZipFile(path) as archive:
                entries = set(archive.namelist())
                suffix = Path(name).suffix.lower()
                required = {".docx": "word/document.xml", ".xlsx": "xl/workbook.xml"}.get(suffix)
                if required and (required not in entries or "[Content_Types].xml" not in entries):
                    raise AcquisitionError(
                        "invalid_content", "El archivo Office no tiene su estructura mínima."
                    )
        except zipfile.BadZipFile as exc:
            raise AcquisitionError(
                "invalid_content", "Contenedor ZIP incompleto o inválido."
            ) from exc
        return
    if header.startswith(
        (
            b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1",
            b"Rar!",
            b"7z\xbc\xaf\x27\x1c",
            b"\x89PNG\r\n\x1a\n",
            b"\xff\xd8\xff",
        )
    ):
        return
    raise AcquisitionError("unsupported_type", "Formato binario no reconocido para adquisición.")


class LocalBinaryStorage:
    def __init__(self, root: Path) -> None:
        self.root = root.resolve()

    @contextmanager
    def open_verified(
        self,
        storage_path: str,
        sha256: str,
        observed_size: int,
        max_bytes: int,
    ) -> Iterator[BinaryIO]:
        if len(sha256) != 64 or any(c not in "0123456789abcdef" for c in sha256):
            raise AcquisitionError("invalid_hash", "Hash documental inválido.")
        expected_path = f"sha256/{sha256[:2]}/{sha256}"
        path = (self.root / storage_path).resolve()
        if storage_path != expected_path or not path.is_relative_to(self.root):
            raise AcquisitionError(
                "unsafe_path", "La versión no tiene una ruta documental permitida."
            )
        try:
            with path.open("rb") as file:
                actual_size = os.fstat(file.fileno()).st_size
                if actual_size > max_bytes:
                    raise AcquisitionError(
                        "too_large", "La versión excede el límite de procesamiento."
                    )
                if actual_size != observed_size:
                    raise AcquisitionError(
                        "size_mismatch", "El tamaño no coincide con la versión registrada."
                    )
                digest = hashlib.sha256()
                for chunk in iter(lambda: file.read(65536), b""):
                    digest.update(chunk)
                if digest.hexdigest() != sha256:
                    raise AcquisitionError(
                        "hash_mismatch", "El archivo no coincide con el hash registrado."
                    )
                file.seek(0)
                yield file
        except OSError as exc:
            raise AcquisitionError(
                "missing_file", "No fue posible abrir el archivo documental conservado."
            ) from exc

    def store(
        self,
        chunks: Iterable[bytes],
        *,
        original_name: str,
        content_type: str,
        expected_size: int | None,
        max_bytes: int,
    ) -> StoredBinary:
        if expected_size is not None and expected_size > max_bytes:
            raise AcquisitionError("too_large", "El archivo excede el límite de tamaño.")
        temp_dir = self.root / ".tmp"
        if not temp_dir.resolve().is_relative_to(self.root):
            raise AcquisitionError(
                "unsafe_path", "El temporal sale del almacenamiento configurado."
            )
        temp_dir.mkdir(parents=True, exist_ok=True)
        descriptor, temporary = tempfile.mkstemp(prefix="download-", suffix=".part", dir=temp_dir)
        path = Path(temporary)
        digest, size = hashlib.sha256(), 0
        try:
            with os.fdopen(descriptor, "wb") as file:
                for chunk in chunks:
                    size += len(chunk)
                    if size > max_bytes:
                        raise AcquisitionError(
                            "too_large", "El archivo excede el límite de tamaño."
                        )
                    file.write(chunk)
                    digest.update(chunk)
                file.flush()
                os.fsync(file.fileno())
            if expected_size is not None and size != expected_size:
                raise AcquisitionError(
                    "size_mismatch", "La descarga no coincide con el tamaño declarado."
                )
            _validate(path, original_name)
            sha256 = digest.hexdigest()
            relative = Path("sha256") / sha256[:2] / sha256
            destination = self.root / relative
            if not destination.resolve().is_relative_to(self.root):
                raise AcquisitionError(
                    "unsafe_path", "El destino sale del almacenamiento configurado."
                )
            destination.parent.mkdir(parents=True, exist_ok=True)
            # Bajo concurrencia solo reemplaza por bytes con el mismo hash.
            os.replace(path, destination)
            return StoredBinary(sha256, relative.as_posix(), size, content_type)
        finally:
            path.unlink(missing_ok=True)
