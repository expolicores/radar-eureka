"""Passive SECOP I session preflight for a disposable context.

Pure classification of what the provider app already did in the disposable context.
It never issues requests, never stores identifiers, cookies, tokens, queries or bodies.
The feed stays blocked; the provider's URL notice caused by that block is not an
authentication failure.
"""

import json
import re
import unicodedata
from dataclasses import dataclass, field
from urllib.parse import parse_qs, urlsplit

CONTRACTS = ("https", "col.licitaciones.info", "/cliente/contratos")
CONFIG_PATH = "/cliente/get-config-user"
PROFILE_FEED_PATH = "/cliente/contratos/get-info/MP"
FEED_KEYS = ("get-info", "get-conteo")
INVENTORY_KEY = "obtener-documentos-proceso"
OFFICIAL_SUFFIXES = ("contratos.gov.co", "secop.gov.co")
LANDING = "https://licitaciones.info/"
EXPIRED = (401, 419)
URL_NOTICE = re.compile(
    r"\bno\s+(?:existe|encuentro|encontramos|se\s+encontro|se\s+encuentra)\s+(?:la\s+|una\s+)?url\b"
)


def dedicated_browser_checks(listener, *, port, profile_dir):
    """Validate the OS listener of the CDP port; only booleans leave this function."""
    command = (listener.get("command_line") or "").casefold()
    addresses = listener.get("addresses") or []
    checks = {
        "single_owner": listener.get("owners") == 1,
        "loopback_only": bool(addresses) and all(a in ("127.0.0.1", "::1") for a in addresses),
        "is_msedge": (listener.get("name") or "").casefold() == "msedge.exe",
        "port_flag": f"--remote-debugging-port={port}" in command,
        "dedicated_profile": str(profile_dir).casefold() in command,
        "no_automation_flag": "--enable-automation" not in command,
    }
    return all(checks.values()), checks


def normalized_text(text):
    plain = unicodedata.normalize("NFD", text or "")
    return "".join(c for c in plain if unicodedata.category(c) != "Mn").casefold()


def url_notice_visible(text):
    """Recognize the provider notice: «No existe URL», «No encuentro URL» and variants."""
    return URL_NOTICE.search(normalized_text(text)) is not None


def _host(url):
    return (urlsplit(url).hostname or "").casefold()


def is_provider(url):
    host = _host(url)
    return host == "licitaciones.info" or host.endswith(".licitaciones.info")


def is_official(url):
    host = _host(url)
    return any(host == s or host.endswith("." + s) for s in OFFICIAL_SUFFIXES)


def is_contracts_url(url):
    u = urlsplit(url)
    return (u.scheme, u.hostname, u.path.rstrip("/")) == CONTRACTS


def classify_request(url):
    """Route decision for the disposable context: official, inventory, feed or allowed."""
    if is_official(url):
        return "official"
    if not is_provider(url):
        return "allowed"
    path = urlsplit(url).path.casefold()
    if INVENTORY_KEY in path:
        return "inventory"
    if any(key in path for key in FEED_KEYS):
        return "feed"
    return "allowed"


PROFILE_KEY = re.compile(r"^(?:id_?)?perfil(?:es|_id|_ids)?$", re.IGNORECASE)


def _ids_from_values(values):
    ids = []
    for value in values:
        items = value if isinstance(value, list) else [value]
        for item in items:
            if isinstance(item, bool) or item is None:
                continue
            ids.extend(part.strip() for part in str(item).split(",") if part.strip())
    return ids


def _body_profile_values(body, depth=0):
    """Profile-like keys anywhere in a JSON object; values stay in memory only."""
    if depth > 4:
        return []
    found = []
    if isinstance(body, dict):
        for key, value in body.items():
            if isinstance(key, str) and PROFILE_KEY.fullmatch(key):
                found.append(value)
            elif isinstance(value, (dict, list)):
                found.extend(_body_profile_values(value, depth + 1))
    elif isinstance(body, list):
        for value in body:
            found.extend(_body_profile_values(value, depth + 1))
    return found


def _parse_body(post_data):
    if not post_data or len(post_data) > 65536:
        return None
    try:
        return json.loads(post_data)
    except ValueError:
        pass
    try:
        return parse_qs(post_data, strict_parsing=True)
    except ValueError:
        return None


# Only these categories (and a count) leave the module; never the identifiers.
ONLY_CONFIGURED = "only_configured"
CONFIGURED_WITH_OTHERS = "configured_with_others"
WITHOUT_CONFIGURED = "without_configured"
ABSENT = "absent"
NO_FEED_REQUEST = "undetermined_no_feed_request"


def _category(ids, expected_profile_id):
    """Return (category, distinct profile count); duplicates count as one profile."""
    distinct = set(ids)
    if not distinct:
        return ABSENT, 0
    if str(expected_profile_id).strip() not in distinct:
        return WITHOUT_CONFIGURED, len(distinct)
    if len(distinct) == 1:
        return ONLY_CONFIGURED, 1
    return CONFIGURED_WITH_OTHERS, len(distinct)


def profile_match(url, expected_profile_id, post_data=None):
    """Compare the app's own blocked feed request with the configured profile.

    The query is checked first; only if it has no `perfiles` is the body parsed in memory.
    Returns (category, source, distinct_count); identifiers and body never leave it.
    """
    if urlsplit(url).path.rstrip("/") != PROFILE_FEED_PATH:
        return None
    ids = _ids_from_values(parse_qs(urlsplit(url).query).get("perfiles", []))
    if ids:
        category, count = _category(ids, expected_profile_id)
        return category, "query", count
    body = _parse_body(post_data)
    if body is None:
        return ABSENT, None, 0
    ids = _ids_from_values(_body_profile_values(body))
    category, count = _category(ids, expected_profile_id)
    return category, "body" if ids else None, count


@dataclass
class PassivePreflight:
    expected_profile_id: str
    own_navigations: list = field(default_factory=list)
    contracts_document: dict | None = None
    config_user: dict | None = None
    page_state: dict | None = None
    feed_blocked: int = 0
    inventory_blocked: int = 0
    official_blocked: int = 0
    profile_checks: list = field(default_factory=list)
    profile_sources: list = field(default_factory=list)
    provider_errors: list = field(default_factory=list)
    expired: bool = False
    sequence: int = 0

    def _tick(self):
        self.sequence += 1
        return self.sequence

    def record_own_navigation(self, url):
        self.own_navigations.append(url)

    def observe_request(self, url, post_data=None):
        """Classify a request before routing; the caller aborts anything not 'allowed'."""
        decision = classify_request(url)
        if decision == "official":
            self.official_blocked += 1
        elif decision == "inventory":
            self.inventory_blocked += 1
        elif decision == "feed":
            self.feed_blocked += 1
            check = profile_match(url, self.expected_profile_id, post_data)
            if check is not None:
                category, source, count = check
                self.profile_checks.append((category, count))
                self.profile_sources.append(source)
        return decision

    def observe_response(self, url, *, method, resource_type, status, json=None):
        if not is_provider(url):
            return
        seq = self._tick()
        path = urlsplit(url).path
        if status in EXPIRED:
            self.expired = True
        if resource_type == "document" and method == "GET" and is_contracts_url(url):
            self.contracts_document = {
                "seq": seq,
                "status": status,
                "has_query": bool(urlsplit(url).query),
            }
            return
        if resource_type in ("xhr", "fetch") and method == "GET" and path == CONFIG_PATH:
            self.config_user = {
                "seq": seq,
                "status": status,
                "same_endpoint": _host(url) == CONTRACTS[1] and urlsplit(url).scheme == "https",
                "json": json is True,
            }
            return
        if resource_type in ("document", "xhr", "fetch") and status >= 400:
            self.provider_errors.append(status)

    def observe_failure(self, url, *, blocked_by_us):
        """Network failures not caused by our own guard are provider errors."""
        if is_provider(url) and not blocked_by_us:
            self.provider_errors.append("network")

    def observe_page(self, state):
        """Latest state of the single desktop Contratos tab in the disposable context."""
        self.page_state = {
            "contracts": is_contracts_url(state.get("url", "")),
            "has_query": bool(urlsplit(state.get("url", "")).query),
            "password_field": state.get("password_field") is True,
            "client": state.get("client") is True,
            "download_control": state.get("download_control") is True,
            "url_notice": url_notice_visible(state.get("text", "")),
            "ready": state.get("ready_state") == "complete",
        }

    def _navigation(self):
        # The script may only open the public landing; Contratos must come from the UI.
        own_ok = all(u == LANDING for u in self.own_navigations)
        doc = self.contracts_document
        if doc is None:
            return "contracts_not_reached", False
        if not own_ok:
            return "contracts_forced_by_script", False
        if doc["status"] != 200 or doc["has_query"]:
            return "contracts_document_unexpected", False
        return "ui_navigation", True

    def _session(self):
        state = self.page_state
        config = self.config_user
        if state is None or not state["contracts"]:
            return "unverified", "contracts_tab_missing"
        if state["has_query"]:
            return "unverified", "contracts_tab_with_query"
        if state["password_field"]:
            return "login_required", "password_field_present"
        if self.expired:
            return "login_required", "provider_401_or_419"
        if config is None:
            return "unverified", "config_user_not_observed"
        if self.contracts_document and config["seq"] < self.contracts_document["seq"]:
            return "unverified", "config_user_before_contracts"
        if config["status"] != 200 or not config["same_endpoint"] or not config["json"]:
            return "unverified", "config_user_not_200_json_same_endpoint"
        if not state["client"]:
            return "unverified", "app_client_missing"
        return "valid", None

    def _profile(self):
        """Last observed request = current UI selection; earlier ones only flag a change."""
        if not self.profile_checks:
            return NO_FEED_REQUEST, 0, False
        category, count = self.profile_checks[-1]
        changed = len(set(self.profile_checks)) > 1
        return category, count, changed

    def _notice(self):
        state = self.page_state
        if state is None or not state["url_notice"]:
            return "absent"
        if self.feed_blocked and not self.provider_errors:
            return "attributed_to_feed_block"
        return "unexplained"

    def verdict(self):
        navigation, navigation_ok = self._navigation()
        session, session_reason = self._session()
        profile, profile_count, profile_changed = self._profile()
        notice = self._notice()
        reasons = [r for r in (session_reason,) if r]
        if not navigation_ok:
            reasons.append(navigation)
        # Acquisition requires exactly one profile and it must be the configured one.
        if profile != ONLY_CONFIGURED:
            reasons.append(f"profile_{profile}")
        if notice == "unexplained":
            reasons.append("url_notice_unexplained")
        if self.page_state is not None and not self.page_state["download_control"]:
            reasons.append("download_control_missing")
        if self.official_blocked or self.inventory_blocked:
            reasons.append("unexpected_official_or_inventory_request")
        return {
            "session": session,
            "navigation": navigation,
            "feed": {"blocked": self.feed_blocked, "state": "blocked_by_guard"},
            "url_notice": notice,
            "profile": profile,
            "profile_count": profile_count,
            "profile_changed": profile_changed,
            "profile_source": sorted({src or "none" for src in self.profile_sources}),
            "official_blocked": self.official_blocked,
            "inventory_blocked": self.inventory_blocked,
            "provider_errors": len(self.provider_errors),
            "ready_for_acquisition": not reasons,
            "reasons": reasons,
        }


# Closure evidence. The worker writes it in its outermost `finally`, whatever the verdict.
# The parent releases the preventive marker only on complete evidence of a safe closure.
MARKER_TEXT = "secop1-disposable-context"


def closure_record(*, marker_owned, context_closed, disconnected):
    """Facts verified by the worker; anything not verified is recorded as False."""
    return {
        "marker_owned": marker_owned is True,
        "context_closed": context_closed is True,
        "disconnected": disconnected is True,
    }


def read_closure(path):
    """Closure written by this worker run, or None if missing or unreadable."""
    try:
        data = json.loads(path.read_text(encoding="utf8"))
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def marker_release_allowed(closure, *, worker_exit_code, marker_text):
    return (
        isinstance(closure, dict)
        and closure.get("marker_owned") is True
        and closure.get("context_closed") is True
        and closure.get("disconnected") is True
        and worker_exit_code == 0
        and isinstance(marker_text, str)
        and marker_text.strip() == MARKER_TEXT
    )
