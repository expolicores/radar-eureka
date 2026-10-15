# Fixtures OCR

`build_ocr_fixtures.py` genera PDFs sintéticos sin datos SECOP:

- `native_refrigerios.pdf`: página con texto embebido suficiente.
- `scanned_refrigerios.pdf`: una página JPEG dentro de PDF, sin texto embebido.
- `mixed_refrigerios.pdf`: páginas 1/3 nativas, página 2 JPEG sin texto.

La imagen incluye Hit 200 ml, Chocorramo 65 g, 400 PACK, $5.200 unitario y $2.080.000 total.
El generador usa Pillow/pypdf, fuente DejaVuSans o Arial, y no requiere motor OCR.
Las pruebas verifican que el scan carece de fragments nativos y puede renderizarse.
La regeneración puede variar los bytes entre versiones; no es una identidad de producción.

Desde la raíz del proyecto:

```powershell
backend/.venv/Scripts/python.exe backend/tests/fixtures/extraction/build_ocr_fixtures.py
```

La aceptación real y configuración Windows se describen en
[`extraction/OCR.md`](../../../src/public_procurement/extraction/OCR.md).
