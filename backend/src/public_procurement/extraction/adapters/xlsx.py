from pathlib import Path

from openpyxl import load_workbook  # type: ignore[import-untyped]

from ..domain.content import ExtractionError, ExtractionLimits, ExtractionStatus, ParsedContent
from .common import FragmentBuilder, check_archive


def extract_xlsx(path: Path, limits: ExtractionLimits) -> ParsedContent:
    check_archive(path, limits)
    workbook = load_workbook(path, read_only=True, data_only=False, keep_links=False)
    builder = FragmentBuilder(limits)
    scanned = 0
    try:
        for sheet in workbook.worksheets:
            for row in sheet.iter_rows():
                for cell in row:
                    scanned += 1
                    if scanned > limits.max_cells:
                        raise ExtractionError(
                            "cell_limit", "El libro excede el límite de celdas recorridas."
                        )
                    if cell.value is None:
                        continue
                    builder.add(
                        str(cell.value),
                        {
                            "kind": "xlsx_cell",
                            "sheet_name": sheet.title,
                            "cell_range": cell.coordinate,
                            "data_type": cell.data_type,
                            "number_format": cell.number_format,
                        },
                        sheet_name=sheet.title,
                        cell_range=cell.coordinate,
                        row_number=cell.row,
                        column_number=cell.column,
                    )
    finally:
        workbook.close()
    return ParsedContent(
        ExtractionStatus.COMPLETED if builder.fragments else ExtractionStatus.EMPTY_TEXT,
        tuple(builder.fragments),
        format_counts={"sheets": len(workbook.worksheets)},
    )
