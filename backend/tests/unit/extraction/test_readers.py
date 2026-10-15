import io
from dataclasses import replace

import pytest
from docx import Document
from openpyxl import Workbook  # type: ignore[import-untyped]
from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

from public_procurement.extraction.adapters.docx import extract_docx
from public_procurement.extraction.adapters.pdf import extract_pdf
from public_procurement.extraction.adapters.xlsx import extract_xlsx
from public_procurement.extraction.domain.content import (
    ExtractionError,
    ExtractionLimits,
    ExtractionStatus,
)
from public_procurement.extraction.domain.text import normalize_extracted_text


def pdf_bytes(text="Refrigerios Hit", blank_page=False):
    writer = PdfWriter()
    page = writer.add_blank_page(width=300, height=300)
    font = DictionaryObject(
        {
            NameObject("/Type"): NameObject("/Font"),
            NameObject("/Subtype"): NameObject("/Type1"),
            NameObject("/BaseFont"): NameObject("/Helvetica"),
        }
    )
    page[NameObject("/Resources")] = DictionaryObject(
        {NameObject("/Font"): DictionaryObject({NameObject("/F1"): font})}
    )
    stream = DecodedStreamObject()
    stream.set_data(f"BT /F1 12 Tf 30 200 Td ({text}) Tj ET".encode("ascii"))
    page[NameObject("/Contents")] = stream
    if blank_page:
        writer.add_blank_page(width=300, height=300)
    result = io.BytesIO()
    writer.write(result)
    return result.getvalue()


def test_pdf_with_text_and_empty_page_has_page_evidence(tmp_path) -> None:
    path = tmp_path / "sample.pdf"
    path.write_bytes(pdf_bytes(blank_page=True))
    result = extract_pdf(path, ExtractionLimits())
    assert result.status is ExtractionStatus.PARTIAL_TEXT
    assert result.page_count == 2
    assert result.pages_without_text == (2,)
    assert result.fragments[0].page_number == 1
    assert "Hit" in result.fragments[0].text
    assert result.fragments[0].source_locator["char_start"] == 0


def test_pdf_without_embedded_text_is_ocr_candidate(tmp_path) -> None:
    writer = PdfWriter()
    writer.add_blank_page(width=300, height=300)
    path = tmp_path / "blank.pdf"
    writer.write(path)
    result = extract_pdf(path, ExtractionLimits())
    assert result.status is ExtractionStatus.REQUIRES_OCR
    assert not result.fragments


def test_docx_preserves_paragraphs_tables_and_exact_accented_text(tmp_path) -> None:
    document = Document()
    document.add_paragraph("Garantía y forma de pago")
    document.add_paragraph("")
    document.add_paragraph("Entrega puntual")
    table = document.add_table(rows=1, cols=2)
    table.cell(0, 0).text = "Chocorramo"
    table.cell(0, 1).text = "100 unidades"
    path = tmp_path / "sample.docx"
    document.save(path)
    result = extract_docx(path, ExtractionLimits())
    assert result.fragments[0].text == "Garantía y forma de pago"
    assert result.fragments[1].paragraph_number == 3
    product = result.fragments[2]
    assert product.table_number == 1
    assert product.row_number == product.column_number == 1
    assert product.source_locator["kind"] == "docx_table_cell"
    assert result.format_counts == {"paragraphs": 3, "tables": 1}


def test_xlsx_preserves_cells_sheets_and_formula_without_execution(tmp_path) -> None:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Oferta"
    sheet["A1"] = "Hit"
    sheet["B1"] = 20
    sheet["C1"] = "=2+3"
    path = tmp_path / "offer.xlsx"
    workbook.save(path)
    result = extract_xlsx(path, ExtractionLimits())
    assert len(result.fragments) == 3
    assert result.fragments[0].sheet_name == "Oferta"
    assert result.fragments[0].cell_range == "A1"
    assert result.fragments[2].text == "=2+3"
    assert result.fragments[2].source_locator["data_type"] == "f"
    assert result.format_counts == {"sheets": 1}


@pytest.mark.parametrize(
    ("limits", "code"),
    [
        (replace(ExtractionLimits(), max_pages=1), "page_limit"),
        (replace(ExtractionLimits(), max_chars=1), "text_limit"),
        (replace(ExtractionLimits(), fragment_chars=2, max_fragments=1), "fragment_limit"),
    ],
)
def test_pdf_limits_do_not_return_partial_valid_results(tmp_path, limits, code) -> None:
    path = tmp_path / "limited.pdf"
    path.write_bytes(pdf_bytes(blank_page=True))
    with pytest.raises(ExtractionError) as error:
        extract_pdf(path, limits)
    assert error.value.code == code


def test_office_expansion_limit_precedes_parsing(tmp_path) -> None:
    path = tmp_path / "large.docx"
    Document().save(path)
    with pytest.raises(ExtractionError) as error:
        extract_docx(path, replace(ExtractionLimits(), max_archive_bytes=1))
    assert error.value.code == "archive_limit"


def test_normalization_does_not_modify_original_and_matches_accents_linebreaks() -> None:
    original = "GARANTI\u0301A\r\n  Forma\tde   pago"
    assert normalize_extracted_text(original) == "garantia forma de pago"
    assert original.startswith("GARANTI\u0301A")
