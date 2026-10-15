"""Prueba de Radar Eureka: consulta documentos Socrata y descarga archivos SECOP.
Instalar dependencia: pip install requests
Ejecutar: python radar_eureka_prueba.py
"""
from pathlib import Path
from urllib.parse import urlparse
import json
import re
import requests

API = "https://www.datos.gov.co/api/v3/views/dmgg-8hin/query.json"
PORTAFOLIO = "CO1.BDOS.10985405"  # I.E. San Luis Beltrán, Covarachía, 012-2026
OUTPUT = Path("descargas_covarachia")
QUERY = f"""
SELECT `id_documento`, `proceso`, `nombre_archivo`, `fecha_carga`,
       `entidad`, `url_descarga_documento`
WHERE `proceso` = '{PORTAFOLIO}'
"""


def rows_from_payload(payload):
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for key in ("data", "results", "rows"):
            if isinstance(payload.get(key), list):
                return payload[key]
    raise ValueError(f"Formato JSON inesperado: {str(payload)[:300]}")


def safe_name(name):
    name = Path(str(name or "documento")).name
    return re.sub(r'[^\w.() -]', '_', name)[:160]


def main():
    OUTPUT.mkdir(exist_ok=True)
    session = requests.Session()
    session.headers.update({"User-Agent": "RadarEureka-POC/0.1", "Accept": "application/json"})

    print("Consultando API Socrata...")
    response = session.get(API, params={"query": QUERY}, timeout=45)
    print("Socrata HTTP:", response.status_code)
    response.raise_for_status()
    payload = response.json()
    rows = rows_from_payload(payload)
    print("Documentos registrados:", len(rows))
    (OUTPUT / "respuesta_socrata.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    for i, doc in enumerate(rows, 1):
        if not isinstance(doc, dict):
            print(f"[{i}] Registro no interpretable: {str(doc)[:150]}")
            continue
        enlace = doc.get("url_descarga_documento")
        url = enlace.get("url", "") if isinstance(enlace, dict) else (enlace or "")
        nombre = safe_name(doc.get("nombre_archivo"))
        doc_id = str(doc.get("id_documento", i)).replace(".", "")
        print(f"\n[{i}] {nombre} / ID {doc_id}")
        if not url or not url.startswith("https://community.secop.gov.co/"):
            print("  Sin URL SECOP pública reconocida; se omite")
            continue
        path = OUTPUT / f"{doc_id}_{nombre}"
        try:
            with session.get(url, timeout=(15, 60), stream=True, allow_redirects=True) as r:
                print("  Descarga HTTP:", r.status_code)
                print("  Content-Type:", r.headers.get("Content-Type", "(sin cabecera)"))
                print("  URL final:", r.url)
                r.raise_for_status()
                with path.open("wb") as f:
                    for chunk in r.iter_content(chunk_size=65536):
                        if chunk:
                            f.write(chunk)
            header = path.read_bytes()[:12]
            is_pdf = header.startswith(b"%PDF-")
            is_zip = header.startswith(b"PK\x03\x04")  # DOCX/XLSX suelen ser ZIP
            if is_pdf or is_zip:
                print(f"  OK: {path} ({path.stat().st_size:,} bytes)")
            else:
                print(f"  AVISO: no parece PDF/DOCX. Cabecera={header!r}")
                print("  Revisar si SECOP devolvió HTML de autenticación o error")
                path.rename(path.with_suffix(path.suffix + ".respuesta"))
        except requests.RequestException as exc:
            print("  ERROR:", exc)


if __name__ == "__main__":
    main()
