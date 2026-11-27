"""Validate a local, normalized SECOP I inventory for EN-01. No network access."""

import argparse
import hashlib
import json
import re
from pathlib import Path

from eureka_nacional_cdp_stream import DOCUMENT_BYTES
from eureka_nacional_experience import document_priority, document_role, document_role_hint

CONSTANCIA = re.compile(r"[0-9]{2}-[0-9]{1,3}-[0-9]{1,14}")
PATH = re.compile(r"/(?:[A-Za-z0-9_-]+/)+[A-Za-z0-9_-][A-Za-z0-9_.-]*")
EXTENSION = re.compile(r"[a-z0-9]{1,8}")


def normalize_document(row, constancia):
    if not isinstance(row, dict):
        raise ValueError("invalid_row")
    name, extension = row.get("name"), row.get("extension")
    path, size = row.get("relative_path"), row.get("size_bytes")
    if (
        not isinstance(name, str)
        or not name.strip()
        or len(name) > 250
        or not name.isprintable()
        or not isinstance(extension, str)
        or not EXTENSION.fullmatch(extension)
    ):
        raise ValueError("invalid_document_metadata")
    if not isinstance(path, str) or len(path) > 512 or not PATH.fullmatch(path):
        raise ValueError("invalid_relative_path")
    *directories, filename = path.split("/")
    identities = [part for part in directories if CONSTANCIA.fullmatch(part)]
    filename_reference = re.search(r"_PROCESO_([0-9]+-[0-9]+-[0-9]+)_", filename, re.I)
    if identities != [constancia] or (filename_reference and filename_reference[1] != constancia):
        raise ValueError("constancia_mismatch")
    if not filename.lower().endswith("." + extension):
        raise ValueError("format_mismatch")
    if size is not None and (type(size) is not int or size <= 0):
        raise ValueError("invalid_size")

    role = document_role(name)
    role_hint = document_role_hint(name, role)
    return {
        "document_id": f"secop1:{constancia}:{hashlib.sha256(path.encode('ascii')).hexdigest()}",
        "name": name,
        "extension": extension,
        "size_bytes": size,
        "role": role,
        "role_hint": role_hint,
        "role_source": "filename",
        "within_size_limit": size is not None and size <= DOCUMENT_BYTES,
        "complete": False,
    }


def normalize_inventory(archive):
    if not isinstance(archive, dict):
        raise ValueError("invalid_inventory")
    constancia = archive.get("constancia")
    reference = archive.get("process_reference")
    rows = archive.get("documents")
    if (
        not isinstance(constancia, str)
        or not CONSTANCIA.fullmatch(constancia)
        or not isinstance(reference, str)
        or not reference.strip()
        or len(reference) > 120
        or not reference.isprintable()
        or not isinstance(rows, list)
    ):
        raise ValueError("invalid_inventory")

    unique, issues, conflicts = {}, [], set()
    for index, row in enumerate(rows, 1):
        try:
            document = normalize_document(row, constancia)
        except ValueError as error:
            issues.append({"row": index, "code": str(error)})
            continue
        key = document["document_id"]
        if key in conflicts:
            issues.append({"row": index, "code": "conflicting_metadata"})
        elif key in unique and unique[key] != document:
            issues.append({"row": index, "code": "conflicting_metadata"})
            conflicts.add(key)
            del unique[key]
        else:
            unique[key] = document
    return {
        "source": "secop1",
        "constancia": constancia,
        "process_reference": reference,
        "automatic_acquisition_enabled": False,
        "documents": sorted(
            unique.values(),
            key=lambda item: document_priority(item["name"], item["role"], item["role_hint"]),
        ),
        "issues": issues,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inventory", type=Path)
    args = parser.parse_args(argv)
    try:
        report = normalize_inventory(json.loads(args.inventory.read_text(encoding="utf-8-sig")))
    except (OSError, ValueError):
        print(json.dumps({"error": "invalid_local_inventory"}))
        return 1
    print(json.dumps(report, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
