"""Probe one archived SECOP download directly, with no discovery or inventory calls."""

import argparse
import json
import re
import tempfile
import time
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from eureka_nacional_en01 import DOCUMENT_BYTES, OUTPUT_ROOT, write_json
from spike_licitaciones_info import SpikeDocument

from public_procurement.documents.adapters.local_storage import LocalBinaryStorage
from public_procurement.documents.adapters.secop import RETRIEVE_PATH, SecopDownloader, validate_url
from public_procurement.documents.domain.document import AcquisitionError


def archived_document(run, process_code):
    if not re.fullmatch(r"en01-[a-z0-9_]+", run.name) or run.resolve() != run:
        raise ValueError("Directorio de corrida inválido.")
    rows = json.loads((run / "processes.json").read_text(encoding="utf-8"))["processes"]
    keys = [row["process_reference"] for row in rows if row["codigo_proceso"] == process_code]
    if len(keys) != 1:
        raise ValueError("La referencia de proceso debe identificar una sola fila.")
    inventories = json.loads((run / "documents.json").read_text(encoding="utf-8"))
    candidates = [
        doc
        for inventory in inventories
        if inventory["process_reference"] == keys[0]
        for doc in inventory["documents"]
        if doc["role"] == "primary"
        and doc["extension"] == "pdf"
        and doc["selection"] == "selected"
        and doc["status"] == "download_failed"
    ]
    if len(candidates) != 1:
        raise ValueError("Se requiere un único PDF rector intentado y fallido.")
    doc = candidates[0]
    url = doc["url"]
    validate_url(url)
    parts = urlsplit(url)
    if (
        parts.path != RETRIEVE_PATH
        or parts.fragment
        or parse_qs(parts.query, keep_blank_values=True) != {"DocumentId": [doc["document_id"]]}
    ):
        raise ValueError("El enlace archivado no corresponde al documento SECOP seleccionado.")
    name = doc["name"]
    if not name.lower().endswith(".pdf"):
        name += ".pdf"
    return SpikeDocument(name, "pdf", url, doc["document_id"])


def probe(document, output, attempts):
    storage = LocalBinaryStorage(output / "binaries")
    downloader = SecopDownloader(12, DOCUMENT_BYTES)
    results = []
    for attempt in range(1, attempts + 1):
        if attempt > 1:
            time.sleep(2.1)
        diagnostics = {}
        try:
            stored = downloader.download(document, storage, diagnostics=diagnostics)
            diagnostics["bytes"] = stored.observed_size
        except AcquisitionError as error:
            diagnostics["rejection_reason"] = error.code
        except OSError:
            diagnostics["rejection_reason"] = "os_error"
        results.append(diagnostics)
        write_json(output / "download_probe.json", results)
        if "bytes" in diagnostics:
            break
    return results


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", help="Nombre de una corrida local EN-01.")
    parser.add_argument("--process-code", required=True)
    parser.add_argument("--attempts", type=int, choices=(1, 2), default=1)
    args = parser.parse_args(argv)
    if not re.fullmatch(r"en01-[a-z0-9_]+", args.run):
        parser.error("Se requiere un nombre de corrida local EN-01.")
    try:
        document = archived_document(OUTPUT_ROOT / args.run, args.process_code)
        if OUTPUT_ROOT.resolve() != OUTPUT_ROOT:
            raise ValueError("Salida fuera del almacenamiento local.")
        output = Path(tempfile.mkdtemp(prefix="download-probe-", dir=OUTPUT_ROOT))
        print(json.dumps({"output": output.name}), flush=True)
        results = probe(document, output, args.attempts)
    except (AcquisitionError, OSError, ValueError, KeyError, TypeError):
        print("No se pudo preparar o guardar la prueba local de descarga.")
        return 1
    print(json.dumps(results))
    return 0 if "bytes" in results[-1] else 2


if __name__ == "__main__":
    raise SystemExit(main())
