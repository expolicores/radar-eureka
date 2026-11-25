"""Offline tests for assisted SECOP imports."""

import sys
from pathlib import Path
from types import SimpleNamespace
from zipfile import ZipFile

import pytest
from docx import Document
from pypdf import PdfWriter

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

import eureka_nacional_manual_import as manual


@pytest.fixture
def batch(tmp_path):
    source = tmp_path / "en01-source"
    output = tmp_path / "en01-manual_source"
    source.mkdir()
    output.mkdir()
    reference = "notice-1"
    other = "notice-2"
    for name, value in (
        (
            "processes",
            {
                "processes": [
                    {
                        "process_reference": ref,
                        "codigo_proceso": code,
                        "sampled": True,
                        "source": "secop2",
                    }
                    for ref, code in ((reference, "MC-01"), (other, "MC-02"))
                ]
            },
        ),
        (
            "experience_requirements",
            [{"process_reference": ref, "status": "not_resolved"} for ref in (reference, other)],
        ),
        (
            "documents",
            [
                {
                    "process_reference": reference,
                    "documents": [
                        {"document_id": "11", "name": "Invitacion publica", "extension": "pdf"},
                        {"document_id": "12", "name": "Anexo habilitante", "extension": "docx"},
                    ],
                }
            ],
        ),
    ):
        manual.write_json(source / f"{name}.json", value)
    manifest = tmp_path / "manifest.json"
    settings = manual.settings_for_run(output, "tesseract", None, 0)
    return source, output, manifest, settings


def pdf(path, width=100):
    writer = PdfWriter()
    writer.add_blank_page(width=width, height=100)
    with path.open("wb") as file:
        writer.write(file)


def submit(batch, *items):
    source, output, manifest, settings = batch
    manual.write_json(
        manifest,
        [
            {"process_reference": reference, "document_id": identifier, "file": filename}
            for reference, identifier, filename in items
        ],
    )
    return manual.resume(source, output, manifest, settings, ocr_pages=0)


def test_import_reuses_receipt_and_extraction_with_missing_corroboration(batch, monkeypatch):
    _, output, manifest, _ = batch
    local = manifest.parent / "arbitrary.bin"
    pdf(local)
    extracted = []

    def extract(document, stored, storage, settings, entry, *, ocr_pages):
        extracted.append(document.document_id)
        entry.update(
            complete=True,
            status="completed",
            ocr_pages=[],
            pending_pages=[],
            fragments=[
                SimpleNamespace(
                    text="No se exige experiencia contractual al proponente.",
                    source_locator={"page_number": 1, "extraction_method": "native_pdf_text"},
                )
            ],
        )

    monkeypatch.setattr(manual, "extract_document", extract)
    first = submit(batch, ("notice-1", "11", local.name))
    repeated = submit(batch, ("notice-1", "11", local.name))
    local.unlink()
    resumed = submit(batch)
    assert first["imported"] == first["extractions_run"] == 1
    assert repeated["already_imported"] == repeated["extractions_reused"] == 1
    assert resumed["extractions_reused"] == 1
    assert extracted == ["11"]
    assert resumed["request_credits"] == 0
    cases = manual.read_json(output / "experience_requirements.json")
    assert cases[0]["status"] == "not_resolved"
    assert cases[0]["review_category"] == "explicit_favorable"
    assert cases[0]["pending_document_ids"] == ["12"]
    assert cases[1]["status"] == "not_resolved"
    assert cases[1]["review_category"] == "insufficient_evidence"
    assert cases[1]["inventory_complete"] is False
    entries = manual.read_json(output / "documents.json")[0]["documents"]
    assert entries[0]["provenance"] == "manual_portal_download"
    assert len(entries[0]["sha256"]) == 64
    assert entries[1]["status"] == "not_imported"


@pytest.mark.parametrize(("document_id", "reference"), [("11", "notice-2"), ("99", "notice-1")])
def test_rejects_unmatched_identity(batch, document_id, reference):
    with pytest.raises(ValueError, match="DocumentId"):
        submit(batch, (reference, document_id, "a.pdf"))


@pytest.mark.parametrize(
    ("fixture", "expected"),
    [
        ("missing", "FileNotFoundError"),
        ("html", "invalid_content"),
        ("truncated", "invalid_content"),
        ("large", "too_large"),
        ("fake_docx", "invalid_content"),
    ],
)
def test_rejects_missing_or_invalid_files(batch, fixture, expected):
    _, output, manifest, _ = batch
    local = manifest.parent / "file"
    if fixture == "html":
        local.write_bytes(b"<html>login</html>")
    if fixture == "truncated":
        local.write_bytes(b"%PDF-1.5\n")
    if fixture == "large":
        with local.open("wb") as file:
            file.write(b"%PDF-")
            file.truncate(manual.DOCUMENT_BYTES + 1)
    if fixture == "fake_docx":
        with ZipFile(local, "w") as archive:
            archive.writestr("notes.txt", "test")
    summary = submit(batch, ("notice-1", "12" if fixture == "fake_docx" else "11", local.name))
    assert summary["errors"] == 1
    assert summary["statuses"] == {"not_resolved": 2}
    assert not (output / "download_receipts.json").exists()
    assert manual.read_json(output / "errors.json")[0]["code"] == expected


def test_keeps_verified_copy_when_replacement_differs(batch, monkeypatch):
    _, output, manifest, _ = batch
    local = manifest.parent / "file"
    pdf(local)
    monkeypatch.setattr(
        manual,
        "extract_document",
        lambda *args, **kwargs: args[4].update(complete=True, fragments=[], pending_pages=[]),
    )
    submit(batch, ("notice-1", "11", local.name))
    receipts = output / "download_receipts.json"
    original = manual.read_json(receipts)
    pdf(local, width=200)
    result = submit(batch, ("notice-1", "11", local.name))
    assert result["errors"] == 1
    assert result["extractions_reused"] == 1
    assert manual.read_json(receipts) == original
    assert manual.read_json(output / "errors.json")[0]["code"] == "document_conflict"


def test_docx_uses_shared_reader_and_preserves_locator(batch):
    _, output, manifest, _ = batch
    local = manifest.parent / "office.bin"
    document = Document()
    document.add_paragraph("No se exige experiencia contractual al proponente.")
    document.save(local)
    result = submit(batch, ("notice-1", "12", local.name))
    assert result["errors"] == 0
    docx = manual.read_json(output / "documents.json")[0]["documents"][1]
    assert docx["docx_fragments"] == 1
    assert docx["coverage_unit"] == "docx_fragment"
    evidence = manual.read_json(output / "experience_requirements.json")[0]["evidence"]
    assert len(evidence) == 1
    assert evidence[0]["document_id"] == "12"
