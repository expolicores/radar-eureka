"""Pure URL normalization and explicit MCO listing IDs, never catalog-to-item guesses."""

import re
from urllib.parse import parse_qs, parse_qsl, urlencode, urlsplit, urlunsplit


def canonical_url(url: str) -> str:
    parsed = urlsplit(url)
    query = urlencode(
        sorted(
            (k, v)
            for k, v in parse_qsl(parsed.query)
            if not k.lower().startswith("utm_") and k.lower() not in {"gclid", "fbclid", "srsltid"}
        )
    )
    return urlunsplit((parsed.scheme, parsed.netloc.lower(), parsed.path.rstrip("/"), query, ""))


def extract_mco_listing_id(url: str) -> str | None:
    try:
        parsed = urlsplit(url)
    except ValueError:
        return None
    if parsed.scheme not in {"https", "http"} or parsed.username or parsed.password:
        return None
    host = parsed.hostname or ""
    if not (host == "mercadolibre.com.co" or host.endswith(".mercadolibre.com.co")):
        return None
    params = parse_qs(parsed.query)
    for key in ("wid", "item_id"):
        values = params.get(key, [])
        if len(values) == 1 and re.fullmatch(r"MCO\d+", values[0], re.I):
            return values[0].upper()
    if re.search(r"/p/MCO", parsed.path, re.I):
        return None  # product catalog URLs do not identify a seller's listing
    match = re.search(r"(?:/|_)MCO-?(\d+)(?=[/_-]|$)", parsed.path, re.I)
    return "MCO" + match[1] if match else None
