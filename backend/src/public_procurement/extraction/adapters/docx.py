from pathlib import Path

from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph

from ..domain.content import ExtractionLimits, ExtractionStatus, ParsedContent
from .common import FragmentBuilder, check_archive


def extract_docx(path: Path, limits: ExtractionLimits) -> ParsedContent:
    check_archive(path, limits)
    document = Document(str(path))
    builder = FragmentBuilder(limits)
    paragraph_number = table_number = cell_count = 0
    for block_index, block in enumerate(document.iter_inner_content(), 1):
        if isinstance(block, Paragraph):
            paragraph_number += 1
            builder.add(
                block.text,
                {
                    "kind": "docx_paragraph",
                    "paragraph_number": paragraph_number,
                    "block_index": block_index,
                },
                paragraph_number=paragraph_number,
            )
        elif isinstance(block, Table):
            table_number += 1
            for row_number, row in enumerate(block.rows, 1):
                for column_number, cell in enumerate(row.cells, 1):
                    cell_count += 1
                    if cell_count > limits.max_cells:
                        from ..domain.content import ExtractionError

                        raise ExtractionError("cell_limit", "La tabla excede el límite de celdas.")
                    builder.add(
                        cell.text,
                        {
                            "kind": "docx_table_cell",
                            "table_number": table_number,
                            "row_number": row_number,
                            "column_number": column_number,
                            "block_index": block_index,
                        },
                        table_number=table_number,
                        row_number=row_number,
                        column_number=column_number,
                    )
    return ParsedContent(
        ExtractionStatus.COMPLETED if builder.fragments else ExtractionStatus.EMPTY_TEXT,
        tuple(builder.fragments),
        format_counts={"paragraphs": paragraph_number, "tables": table_number},
    )
