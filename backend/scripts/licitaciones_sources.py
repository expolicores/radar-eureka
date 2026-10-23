"""Public source provenance and verified document capability, independent of eligibility."""

import re
from urllib.parse import parse_qs, urlsplit


def public_url(value):
    try:
        return urlsplit(value)
    except ValueError:
        return urlsplit("")


def source_kind(process):
    key = str(process.get("key_config") or "").casefold()
    link = str(process.get("raw_source_reference", {}).get("Link") or process.get("Link") or "")
    host = (public_url(link).hostname or "").lower()
    if key in {"secop2", "secopii"}:
        return "secop2"
    if key in {"secop1", "secopi"}:
        return "secop1"
    if host == "community.secop.gov.co":
        return "secop2"
    if host in {"contratos.gov.co", "www.contratos.gov.co"}:
        return "secop1"
    if host in {"fao.org", "fao.taleo.net"} or host.endswith(".fao.org") or key == "fao":
        return "fao"
    if "cruzroja" in host or key == "cruz_roja":
        return "cruz_roja"
    if host.endswith(".edu.co") or key == "universidad":
        return "universidad"
    if key == "unknown":
        return "unknown"
    if str(process.get("id_fuente_contract")) == "3":
        return "secop2"
    if str(process.get("id_fuente_contract")) == "2":
        return "secop1"
    return "otro_portal" if host else "unknown"


def process_identity(process):
    reference = str(process.get("id_ultima_fase") or "")
    link = str(process.get("raw_source_reference", {}).get("Link") or "")
    parsed = public_url(link)
    if parsed.hostname == "community.secop.gov.co":
        notice = parse_qs(parsed.query).get("noticeUID", [""])[0]
        if re.fullmatch(r"CO1\.(?:NTC|REQ)\.\d+", notice):
            return notice
    if re.fullmatch(r"CO1\.(?:NTC|REQ)\.\d+", reference):
        return reference
    if source_kind(process) == "secop1":
        constancy = parse_qs(parsed.query).get("numConstancia", [""])[0]
        if constancy and re.fullmatch(r"[A-Za-z0-9_-]{1,80}", constancy):
            return "secop1:" + constancy
    # Provider contract ID is stable within the existing provider/profile namespace.
    identifier = str(process.get("id_contrato") or "")
    profile = str(process.get("profile_id") or "1086005")
    if identifier and re.fullmatch(r"[A-Za-z0-9_-]{1,64}", identifier):
        return f"licitaciones_info:{profile}:{identifier}"
    return None


def document_capable(process):
    # Only a demonstrated strategy, not origin alone, authorizes an inventory request.
    capability = process.get("document_capability", {})
    verified = (
        capability.get("verified") is True
        and capability.get("strategy") == "licitaciones_inventory"
    )
    supported = source_kind(process) == "secop2" or verified
    identity = process_identity(process) or ""
    phase = process.get("id_ultima_fase") or (
        identity
        if source_kind(process) == "secop2" and re.fullmatch(r"CO1\.NTC\.\d+", identity)
        else None
    )
    return bool(
        supported and process.get("id_contrato") and process.get("id_fuente_contract") and phase
    )


def annotate_source(process):
    return {
        **process,
        "provider_source": source_kind(process),
        "source_identity": process_identity(process),
        "document_capable": document_capable(process),
    }
