"""Exact SECOP identity shared by providers; never infer REQ from NTC numbers."""

import re
from urllib.parse import parse_qs, urlsplit


def canonical_process_identity(identifier: str, source_url: str | None = None) -> str:
    if source_url:
        parsed = urlsplit(source_url)
        if parsed.scheme == "https" and parsed.hostname == "community.secop.gov.co":
            notice = parse_qs(parsed.query).get("noticeUID", [""])[0]
            if re.fullmatch(r"CO1\.NTC\.\d+", notice):
                return "secop:" + notice
    if re.fullmatch(r"CO1\.(?:NTC|REQ)\.\d+", identifier):
        return "secop:" + identifier
    if identifier.startswith(("licitaciones_info:", "secop1:")):
        return identifier
    return "secop-process:" + identifier
