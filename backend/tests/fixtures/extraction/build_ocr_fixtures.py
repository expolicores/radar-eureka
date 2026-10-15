"""Fixtures sintéticos, sin SECOP ni datos privados; ejecutar desde backend."""

import io
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from pypdf import PdfWriter
from pypdf.generic import (
    DecodedStreamObject,
    DictionaryObject,
    NameObject,
    NumberObject,
)

TEXT = "\n".join(
    [
        "SUMINISTRO DE REFRIGERIOS - DOCUMENTO DE PRUEBA.",
        "JUGO HIT TETRA X 200 ML.",
        "CHOCORRAMO TRADICIONAL X 65 GR.",
        "CANTIDAD 400 PACK",
        "VALOR UNITARIO: $5.200",
        "VALOR TOTAL: $2.080.000",
        "Los productos deben entregarse en su empaque original.",
    ]
)
NATIVE = (
    "Texto nativo legible de prueba. Este documento tiene suficiente contenido "
    "para conservar la evidencia original sin activar OCR."
)


def add_native(writer: PdfWriter, text: str) -> None:
    page = writer.add_blank_page(width=612, height=792)
    font = DictionaryObject(
        {
            NameObject("/Type"): NameObject("/Font"),
            NameObject("/Subtype"): NameObject("/Type1"),
            NameObject("/BaseFont"): NameObject("/Helvetica"),
        }
    )
    page[NameObject("/Resources")] = DictionaryObject(
        {NameObject("/Font"): DictionaryObject({NameObject("/F1"): writer._add_object(font)})}
    )
    stream = DecodedStreamObject()
    escaped = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    stream.set_data(f"BT /F1 12 Tf 30 720 Td ({escaped}) Tj ET".encode("ascii"))
    page[NameObject("/Contents")] = writer._add_object(stream)


def add_scan(writer: PdfWriter) -> None:
    with Image.new("RGB", (1800, 1400), "white") as image:
        draw = ImageDraw.Draw(image)
        try:
            font = ImageFont.truetype("DejaVuSans.ttf", 34)
        except OSError:
            font = ImageFont.truetype("arial.ttf", 34)
        draw.multiline_text((70, 80), TEXT, font=font, fill="black", spacing=35)
        data = io.BytesIO()
        image.save(data, "JPEG", quality=95)
    page = writer.add_blank_page(width=612, height=476)
    raster = DecodedStreamObject()
    raster.set_data(data.getvalue())
    raster.update(
        {
            NameObject("/Type"): NameObject("/XObject"),
            NameObject("/Subtype"): NameObject("/Image"),
            NameObject("/Width"): NumberObject(1800),
            NameObject("/Height"): NumberObject(1400),
            NameObject("/ColorSpace"): NameObject("/DeviceRGB"),
            NameObject("/BitsPerComponent"): NumberObject(8),
            NameObject("/Filter"): NameObject("/DCTDecode"),
        }
    )
    page[NameObject("/Resources")] = DictionaryObject(
        {NameObject("/XObject"): DictionaryObject({NameObject("/Im1"): writer._add_object(raster)})}
    )
    stream = DecodedStreamObject()
    stream.set_data(b"q 612 0 0 476 0 0 cm /Im1 Do Q")
    page[NameObject("/Contents")] = writer._add_object(stream)


def main() -> None:
    directory = Path(__file__).resolve().parent
    for name, types in (
        ("native_refrigerios", ["native"]),
        ("scanned_refrigerios", ["scan"]),
        ("mixed_refrigerios", ["native", "scan", "native"]),
    ):
        writer = PdfWriter()
        for kind in types:
            add_native(writer, NATIVE) if kind == "native" else add_scan(writer)
        writer.write(directory / f"{name}.pdf")


if __name__ == "__main__":
    main()
