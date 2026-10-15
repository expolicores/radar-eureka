"""Worker privado de una extracción; sin base de datos ni servicios externos."""

import hashlib
import json
import logging
import os
import sys
from dataclasses import asdict
from pathlib import Path

from ..domain.content import ExtractionError, ExtractionLimits


def memory_limit(max_bytes: int) -> None:
    if os.name != "nt":
        import resource

        resource.setrlimit(resource.RLIMIT_AS, (max_bytes, max_bytes))  # type: ignore[attr-defined]
        return
    import ctypes
    from ctypes import wintypes

    class Basic(ctypes.Structure):
        _fields_ = [
            ("process_time", ctypes.c_longlong),
            ("job_time", ctypes.c_longlong),
            ("flags", wintypes.DWORD),
            ("min_working", ctypes.c_size_t),
            ("max_working", ctypes.c_size_t),
            ("active", wintypes.DWORD),
            ("affinity", ctypes.c_size_t),
            ("priority", wintypes.DWORD),
            ("scheduling", wintypes.DWORD),
        ]

    class Counters(ctypes.Structure):
        _fields_ = [
            (name, ctypes.c_ulonglong)
            for name in (
                "read_ops",
                "write_ops",
                "other_ops",
                "read_bytes",
                "write_bytes",
                "other_bytes",
            )
        ]

    class Extended(ctypes.Structure):
        _fields_ = [
            ("basic", Basic),
            ("io", Counters),
            ("process_memory", ctypes.c_size_t),
            ("job_memory", ctypes.c_size_t),
            ("peak_process", ctypes.c_size_t),
            ("peak_job", ctypes.c_size_t),
        ]

    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
    kernel.CreateJobObjectW.restype = wintypes.HANDLE
    kernel.GetCurrentProcess.restype = wintypes.HANDLE
    kernel.SetInformationJobObject.argtypes = [
        wintypes.HANDLE,
        ctypes.c_int,
        ctypes.c_void_p,
        wintypes.DWORD,
    ]
    kernel.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
    handle = kernel.CreateJobObjectW(None, None)
    information = Extended()
    information.basic.flags = 0x100 | 0x200 | 0x2000  # process/job memory + kill on close
    information.process_memory = max_bytes
    information.job_memory = max_bytes
    if (
        not handle
        or not kernel.SetInformationJobObject(
            handle, 9, ctypes.byref(information), ctypes.sizeof(information)
        )
        or not kernel.AssignProcessToJobObject(handle, kernel.GetCurrentProcess())
    ):
        raise ExtractionError(
            "isolation_unavailable", "No fue posible aplicar el límite de memoria del lector."
        )
    # El handle permanece abierto durante la vida corta del worker y se libera al finalizar.


def main() -> None:
    logging.disable(logging.CRITICAL)
    try:
        request = json.loads(sys.stdin.read(16384))
        limits = ExtractionLimits(**request["limits"])
        memory_limit(request.get("ocr_policy", {}).get("memory_bytes", 512 * 1024 * 1024))
        path = Path(request["path"])
        if path.stat().st_size > limits.max_bytes:
            raise ExtractionError("too_large", "La entrada excede el límite de tamaño.")
        with path.open("rb") as file:
            digest = hashlib.file_digest(file, "sha256").hexdigest()
        if digest != request["input_sha256"]:
            raise ExtractionError(
                "hash_mismatch", "El snapshot no coincide con el hash registrado."
            )
        suffix = request["suffix"]
        if request.get("mode") == "ocr":
            from ..ocr_config import OcrPolicy
            from .ocr import extract_ocr

            parsed = extract_ocr(
                path,
                limits,
                OcrPolicy.model_validate(request["ocr_policy"]),
                request["pages"],
                request["engine"],
            )
        elif suffix == ".pdf":
            from .pdf import extract_pdf

            parsed = extract_pdf(path, limits)
        elif suffix == ".docx":
            from .docx import extract_docx

            parsed = extract_docx(path, limits)
        elif suffix == ".xlsx":
            from .xlsx import extract_xlsx

            parsed = extract_xlsx(path, limits)
        else:
            raise ExtractionError(
                "unsupported_format", "Formato no soportado: solo PDF, DOCX y XLSX."
            )
        print(json.dumps(asdict(parsed), ensure_ascii=True))
    except ExtractionError as error:
        print(json.dumps(dict(error_code=error.code, error_message=str(error))))
    except MemoryError:
        print(
            json.dumps(
                dict(
                    error_code="memory_limit",
                    error_message="El lector excedió el límite de memoria.",
                )
            )
        )
    except Exception:
        print(
            json.dumps(
                dict(
                    error_code="corrupt_file",
                    error_message="Documento corrupto o no legible por el extractor.",
                )
            )
        )


if __name__ == "__main__":
    main()
