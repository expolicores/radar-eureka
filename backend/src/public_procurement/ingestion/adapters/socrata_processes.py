"""SODA v2: procesos públicos, consulta acotada y paginación por cursor interno :id."""

import json
import time
from collections.abc import Iterable
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from ..domain.process import SECOP_PROCESS_DATASET, ProcessQuery, SecopProcess

ENDPOINT = f"https://www.datos.gov.co/resource/{SECOP_PROCESS_DATASET}.json"
PUBLICATION_FIELD = "fecha_de_publicacion_del"
FIELDS = (
    "id_del_proceso",
    "id_del_portafolio",
    "referencia_del_proceso",
    "entidad",
    "departamento_entidad",
    "ciudad_entidad",
    "nombre_del_procedimiento",
    "descripci_n_del_procedimiento",
    "modalidad_de_contratacion",
    "fase",
    "estado_del_procedimiento",
    "fecha_de_publicacion_del",
    "fecha_de_ultima_publicaci",
    "fecha_de_recepcion_de",
    "precio_base",
    "codigo_principal_de_categoria",
    "urlproceso",
)


def _literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def _text(row: dict[str, Any], key: str) -> str | None:
    value = row.get(key)
    if value is None or value == "":
        return None
    if not isinstance(value, str):
        raise ValueError(f"Campo Socrata no textual: {key}.")
    return value


def _day(row: dict[str, Any], key: str) -> date | None:
    value = _text(row, key)
    return date.fromisoformat(value[:10]) if value else None


def _price(row: dict[str, Any]) -> int | None:
    value = row.get("precio_base")
    if value is None or value == "":
        return None
    try:
        amount = Decimal(str(value))
        if not amount.is_finite() or amount < 0 or amount != amount.to_integral_value():
            raise ValueError("Precio base inválido o no expresable en COP enteros.")
        if amount > 9_223_372_036_854_775_807:
            raise ValueError("Precio base fuera del rango de almacenamiento.")
        return int(amount)
    except InvalidOperation as exc:
        raise ValueError("Precio base inválido.") from exc


def map_process(row: dict[str, Any]) -> SecopProcess:
    identifier = _text(row, "id_del_proceso")
    if identifier is None:
        raise ValueError("El registro Socrata no tiene id_del_proceso.")
    url = row.get("urlproceso")
    if isinstance(url, dict):
        url = url.get("url")
    if url is not None and not isinstance(url, str):
        raise ValueError("URL de proceso inválida.")
    return SecopProcess(
        id_del_proceso=identifier,
        id_del_portafolio=_text(row, "id_del_portafolio"),
        reference=_text(row, "referencia_del_proceso"),
        entity_name=_text(row, "entidad"),
        department=_text(row, "departamento_entidad"),
        municipality=_text(row, "ciudad_entidad"),
        title=_text(row, "nombre_del_procedimiento"),
        description=_text(row, "descripci_n_del_procedimiento"),
        modality=_text(row, "modalidad_de_contratacion"),
        phase=_text(row, "fase"),
        status=_text(row, "estado_del_procedimiento"),
        published_on=_day(row, "fecha_de_publicacion_del"),
        last_published_on=_day(row, "fecha_de_ultima_publicaci"),
        base_price_cop=_price(row),
        category_code=_text(row, "codigo_principal_de_categoria"),
        source_url=url,
        offer_deadline_raw=row.get("fecha_de_recepcion_de"),
    )


class SocrataProcessSource:
    def _page(self, params: dict[str, str]) -> list[dict[str, Any]]:
        request = Request(  # noqa: S310 — origen HTTPS constante, parámetros codificados
            ENDPOINT + "?" + urlencode(params),
            headers={"Accept": "application/json", "User-Agent": "PublicProcurement/0.1"},
        )
        for attempt in range(3):
            try:
                # URL fija del proveedor; los filtros se codifican como parámetros.
                with urlopen(request, timeout=45) as response:  # noqa: S310
                    payload = json.load(response)
                if not isinstance(payload, list) or any(not isinstance(r, dict) for r in payload):
                    raise ValueError(
                        "Respuesta Socrata inesperada; se esperaba una lista de objetos."
                    )
                return payload
            except HTTPError as exc:
                if exc.code not in (429, 500, 502, 503, 504) or attempt == 2:
                    raise RuntimeError(f"Socrata respondió HTTP {exc.code}.") from None
            except (URLError, TimeoutError):
                if attempt == 2:
                    raise RuntimeError("No fue posible consultar Socrata.") from None
            time.sleep(2 ** (attempt + 1))
        raise RuntimeError("Consulta Socrata agotada.")

    def fetch_processes(self, query: ProcessQuery) -> Iterable[SecopProcess]:
        conditions = []
        if query.portfolio_id:
            conditions.append("id_del_portafolio = " + _literal(query.portfolio_id))
        if query.departments:
            conditions.append(
                "lower(departamento_entidad) IN ("
                + ",".join(_literal(value.casefold()) for value in query.departments)
                + ")"
            )
        if query.published_from and query.published_before:
            conditions.extend(
                (
                    PUBLICATION_FIELD + " >= " + _literal(query.published_from.isoformat()),
                    PUBLICATION_FIELD + " < " + _literal(query.published_before.isoformat()),
                )
            )
        cursor: str | None = None
        seen_cursors: set[str] = set()
        for _ in range(query.max_pages):
            where = [*conditions]
            if cursor is not None:
                where.append(":id > " + _literal(cursor))
            rows = self._page(
                {
                    "$select": ":id AS source_row_id," + ",".join(FIELDS),
                    "$where": " AND ".join(where),
                    "$order": ":id ASC",
                    "$limit": str(query.page_size),
                }
            )
            if len(rows) > query.page_size:
                raise ValueError("Socrata devolvió más filas que el tamaño solicitado.")
            if len(rows) < query.page_size:
                for row in rows:
                    yield map_process(row)
                return
            # :id es opaco: su orden en Socrata no equivale al orden textual de Python.
            # El mismo campo ordena y filtra en origen; detectar repeticiones evita ciclos.
            for row in rows:
                row_cursor = _text(row, "source_row_id")
                if not row_cursor or row_cursor in seen_cursors:
                    raise ValueError("Cursor Socrata ausente o sin avance; se cancela la carga.")
                seen_cursors.add(row_cursor)
                cursor = row_cursor
            for row in rows:
                yield map_process(row)
        raise ValueError("Se alcanzó max-pages; acota la consulta o aumenta el límite.")
