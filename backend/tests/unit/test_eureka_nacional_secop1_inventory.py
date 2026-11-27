"""Offline tests of the SECOP I inventory boundary."""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

import eureka_nacional_secop1_inventory as secop1

CONSTANCIA = "26-13-12345678"
PDF = f"/2020/2020Q2/2026/INVMC/100/{CONSTANCIA}/INVMC_PROCESO_{CONSTANCIA}_100_200.pdf"


def row(**overrides):
    return {
        "name": "Invitaci\u00f3n P\u00fablica",
        "extension": "pdf",
        "size_bytes": 12345,
        "relative_path": PDF,
        **overrides,
    }


def inventory(*rows):
    return {
        "constancia": CONSTANCIA,
        "process_reference": "SECOP-I fixture",
        "documents": list(rows),
    }


def test_inventory_ranks_and_deduplicates_without_exporting_paths(tmp_path, capsys):
    source = tmp_path / "inventory.json"
    studies = row(name="Estudios previos", relative_path=PDF.replace("INVMC_PROCESO", "EP"))
    annex = row(name="Anexo habilitante", relative_path=PDF.replace("INVMC_PROCESO", "ANEXO"))
    source.write_text(json.dumps(inventory(studies, annex, row(), row())), encoding="utf8")
    assert secop1.main([str(source)]) == 0
    output = capsys.readouterr().out
    report = json.loads(output)
    assert PDF not in output
    assert report["constancia"] == CONSTANCIA
    assert not report["automatic_acquisition_enabled"]
    assert [d["role"] for d in report["documents"]] == ["primary", "support", "support"]
    assert all(d["document_id"].startswith(f"secop1:{CONSTANCIA}:") for d in report["documents"])
    assert all(not d["complete"] and d["within_size_limit"] for d in report["documents"])
    assert not report["issues"]


@pytest.mark.parametrize(
    ("overrides", "code"),
    [
        ({"relative_path": "https://example.org" + PDF}, "invalid_relative_path"),
        ({"relative_path": "/" + PDF}, "invalid_relative_path"),
        ({"relative_path": "/safe/../" + PDF[1:]}, "invalid_relative_path"),
        ({"relative_path": "/safe/%2e%2e/" + PDF[1:]}, "invalid_relative_path"),
        ({"relative_path": PDF + "?token=fixture"}, "invalid_relative_path"),
        ({"relative_path": PDF.replace(CONSTANCIA, "26-13-123")}, "constancia_mismatch"),
        (
            {"relative_path": PDF.replace(f"_PROCESO_{CONSTANCIA}", "_PROCESO_26-13-123")},
            "constancia_mismatch",
        ),
        ({"extension": "docx"}, "format_mismatch"),
        ({"size_bytes": "1.80 MB"}, "invalid_size"),
    ],
)
def test_invalid_row_is_isolated(overrides, code):
    report = secop1.normalize_inventory(inventory(row(**overrides), row()))
    assert report["issues"] == [{"row": 1, "code": code}]
    assert len(report["documents"]) == 1


def test_conflicting_metadata_removes_candidate():
    report = secop1.normalize_inventory(inventory(row(), row(size_bytes=600), row()))
    assert not report["documents"]
    assert [e["code"] for e in report["issues"]] == ["conflicting_metadata"] * 2


@pytest.mark.parametrize("size", [None, secop1.DOCUMENT_BYTES + 1])
def test_missing_or_excessive_size_is_preserved_without_acquisition(size):
    report = secop1.normalize_inventory(inventory(row(size_bytes=size)))
    assert report["documents"][0]["size_bytes"] == size
    assert not report["documents"][0]["within_size_limit"]
    assert not report["automatic_acquisition_enabled"]


def test_maximum_exact_size_is_valid_metadata():
    document = secop1.normalize_document(row(size_bytes=secop1.DOCUMENT_BYTES), CONSTANCIA)
    assert document["within_size_limit"]
