"""Inventario documental oficial por portafolio; sin descarga de binarios."""

import json
import time
from datetime import datetime
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from ..domain.document import DOCUMENT_DATASET, SourceDocument

ENDPOINT = f"https://www.datos.gov.co/resource/{DOCUMENT_DATASET}.json"


def map_document(row: dict[str, Any], portfolio_id: str) -> SourceDocument:
    if row.get("proceso") != portfolio_id:
        raise ValueError("Socrata devolvió un documento de otro portafolio.")
    identifier, name = row.get("id_documento"), row.get("nombre_archivo")
    if not isinstance(identifier, str) or not isinstance(name, str):
        raise ValueError("Identificador o nombre documental inválido.")
    url = row.get("url_descarga_documento")
    if isinstance(url, dict):
        url = url.get("url")
    if url is not None and not isinstance(url, str):
        raise ValueError("URL documental inválida.")
    loaded = row.get("fecha_carga")
    if loaded is not None and not isinstance(loaded, str):
        raise ValueError("Fecha de carga inválida.")
    # Socrata publica calendar_date sin zona: preservar ese valor, no inventar UTC.
    fecha_carga = datetime.fromisoformat(loaded) if loaded else None
    if fecha_carga is not None and fecha_carga.tzinfo is not None:
        raise ValueError("Fecha de carga con zona inesperada.")
    return SourceDocument(identifier, portfolio_id, name, fecha_carga, url)


class SocrataDocumentSource:
    def _page(self, params: dict[str, str]) -> list[dict[str, Any]]:
        request = Request(  # noqa: S310 — origen HTTPS fijo
            ENDPOINT + "?" + urlencode(params),
            headers={
                "Accept": "application/json",
                "User-Agent": "PublicProcurement/0.1",
            },
        )
        for attempt in range(3):
            try:
                with urlopen(request, timeout=45) as response:  # noqa: S310
                    payload = json.load(response)
                if not isinstance(payload, list) or any(not isinstance(r, dict) for r in payload):
                    raise ValueError("Inventario Socrata inválido.")
                return payload
            except HTTPError as exc:
                code = exc.code
                exc.close()
                if code not in (429, 500, 502, 503, 504) or attempt == 2:
                    raise RuntimeError(f"Socrata respondió HTTP {code}.") from None
            except (URLError, TimeoutError):
                if attempt == 2:
                    raise RuntimeError("No fue posible consultar el inventario Socrata.") from None
            time.sleep(2 ** (attempt + 1))
        raise RuntimeError("Consulta de inventario agotada.")

    def fetch(self, portfolio_id: str) -> list[SourceDocument]:
        return self._fetch_identifier(portfolio_id, "proceso")

    def fetch_by_contract(self, contract_id: str) -> list[SourceDocument]:
        """Official contract column; a PCCNTR is not the proceso/BDOS column."""
        return self._fetch_identifier(contract_id, "n_mero_de_contrato")

    def _fetch_identifier(self, identifier: str, field: str) -> list[SourceDocument]:
        portfolio_id = identifier
        if not portfolio_id or len(portfolio_id) > 128:
            raise ValueError("Portafolio inválido.")
        escaped = portfolio_id.replace("'", "''")
        cursor = None
        seen_cursors: set[str] = set()
        unique: dict[str, SourceDocument] = {}
        for _ in range(100):
            where = f"{field} = '{escaped}'"
            if cursor:
                where += " AND :id > '" + cursor.replace("'", "''") + "'"
            rows = self._page(
                {
                    "$select": (
                        ":id AS source_row_id,id_documento,proceso,nombre_archivo,"
                        "fecha_carga,url_descarga_documento"
                        + (",n_mero_de_contrato" if field == "n_mero_de_contrato" else "")
                    ),
                    "$where": where,
                    "$order": ":id ASC",
                    "$limit": "1000",
                }
            )
            for row in rows:
                next_cursor = row.get("source_row_id")
                if (
                    not isinstance(next_cursor, str)
                    or not next_cursor
                    or next_cursor in seen_cursors
                ):
                    raise ValueError("Cursor documental ausente o sin avance.")
                # :id es un rowIdentifier opaco; su orden lo define Socrata, no Python.
                seen_cursors.add(next_cursor)
                cursor = next_cursor
                source_portfolio = portfolio_id
                if field == "n_mero_de_contrato":
                    if row.get(field) != identifier:
                        raise ValueError("Socrata devolvió un documento de otro contrato.")
                    provider_key = row.get("proceso")
                    if not isinstance(provider_key, str) or not provider_key:
                        raise ValueError("Documento contractual sin llave de proceso oficial.")
                    source_portfolio = provider_key
                document = map_document(row, source_portfolio)
                previous = unique.get(document.id_documento)
                if previous and previous != document:
                    raise ValueError(
                        "Inventario con versiones contradictorias del mismo documento."
                    )
                unique[document.id_documento] = document
            if len(rows) < 1000:
                return list(unique.values())
        raise ValueError("Inventario demasiado grande; no se persiste una consulta truncada.")
