"""Offline tests for the passive SECOP I preflight. Synthetic URLs and IDs only."""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from eureka_nacional_secop1_preflight import (
    LANDING,
    MARKER_TEXT,
    PassivePreflight,
    classify_request,
    closure_record,
    dedicated_browser_checks,
    marker_release_allowed,
    profile_match,
    read_closure,
    url_notice_visible,
)

PROFILE = "1234"
CONTRACTS = "https://col.licitaciones.info/cliente/contratos"
CONFIG = "https://col.licitaciones.info/cliente/get-config-user"
FEED = "https://col.licitaciones.info/cliente/contratos/get-info/MP?perfiles="


class PreflightBuilder:
    """Test Data Builder: the healthy observed boot, then targeted deviations."""

    def __init__(self):
        self.preflight = PassivePreflight(expected_profile_id=PROFILE)
        self.landing = [LANDING]
        self.contracts = {"url": CONTRACTS, "status": 200}
        self.config = {"url": CONFIG, "status": 200, "json": True, "before_contracts": False}
        self.feed = [FEED + PROFILE]
        self.page = {
            "url": CONTRACTS,
            "password_field": False,
            "client": True,
            "download_control": True,
            "ready_state": "complete",
            "text": "Contratos",
        }
        self.extra_responses = []

    def with_own_navigation(self, url):
        self.landing.append(url)
        return self

    def without_contracts(self):
        self.contracts = None
        self.page["url"] = LANDING
        return self

    def with_config(self, **changes):
        self.config.update(changes)
        return self

    def without_config(self):
        self.config = None
        return self

    def with_feed(self, *urls):
        self.feed = list(urls)
        return self

    def with_page(self, **changes):
        self.page.update(changes)
        return self

    def with_response(self, url, status, resource_type="xhr"):
        self.extra_responses.append((url, status, resource_type))
        return self

    def build(self):
        p = self.preflight
        for url in self.landing:
            p.record_own_navigation(url)
        config = self.config
        if config and config["before_contracts"]:
            self._config(config)
        if self.contracts:
            p.observe_response(
                self.contracts["url"],
                method="GET",
                resource_type="document",
                status=self.contracts["status"],
            )
        if config and not config["before_contracts"]:
            self._config(config)
        for url in self.feed:
            assert p.observe_request(url) == "feed"
            p.observe_failure(url, blocked_by_us=True)
        for url, status, resource_type in self.extra_responses:
            p.observe_response(url, method="GET", resource_type=resource_type, status=status)
        p.observe_page(self.page)
        return p

    def _config(self, config):
        self.preflight.observe_response(
            config["url"],
            method="GET",
            resource_type="xhr",
            status=config["status"],
            json=config["json"],
        )


def test_observed_boot_with_blocked_feed_is_valid_session_and_ready():
    # Arrange
    preflight = PreflightBuilder().with_page(text="¡No encuentro URL!").build()

    # Act
    verdict = preflight.verdict()

    # Assert
    assert verdict["session"] == "valid"
    assert verdict["navigation"] == "ui_navigation"
    assert verdict["feed"] == {"blocked": 1, "state": "blocked_by_guard"}
    assert verdict["url_notice"] == "attributed_to_feed_block"
    assert verdict["profile"] == "only_configured"
    assert verdict["profile_count"] == 1
    assert verdict["profile_changed"] is False
    assert verdict["ready_for_acquisition"] is True
    assert verdict["reasons"] == []


@pytest.mark.parametrize(
    "text",
    ["No encuentro URL", "No existe URL", "no existe la URL", "NO SE ENCONTRÓ LA URL"],
)
def test_url_notice_variants_are_recognized(text):
    # Arrange / Act / Assert
    assert url_notice_visible(text) is True


@pytest.mark.parametrize("text", ["Contratos", "URL del proceso", "", None])
def test_unrelated_text_is_not_a_url_notice(text):
    assert url_notice_visible(text) is False


def test_url_notice_with_provider_error_is_unexplained_and_blocks():
    # Arrange
    preflight = (
        PreflightBuilder()
        .with_page(text="No encuentro URL")
        .with_response("https://col.licitaciones.info/otra-ruta", 404)
        .build()
    )

    # Act
    verdict = preflight.verdict()

    # Assert
    assert verdict["session"] == "valid"
    assert verdict["url_notice"] == "unexplained"
    assert "url_notice_unexplained" in verdict["reasons"]
    assert verdict["ready_for_acquisition"] is False


def test_password_field_means_login_required_not_feed_block():
    preflight = PreflightBuilder().with_page(password_field=True).build()

    verdict = preflight.verdict()

    assert verdict["session"] == "login_required"
    assert verdict["feed"]["state"] == "blocked_by_guard"
    assert verdict["ready_for_acquisition"] is False


@pytest.mark.parametrize("status", [401, 419])
def test_provider_expired_status_means_login_required(status):
    preflight = (
        PreflightBuilder()
        .with_response("https://col.licitaciones.info/get-contadores", status)
        .build()
    )

    assert preflight.verdict()["session"] == "login_required"


@pytest.mark.parametrize(
    ("changes", "reason"),
    [
        ({"status": 404}, "config_user_not_200_json_same_endpoint"),
        ({"json": False}, "config_user_not_200_json_same_endpoint"),
        (
            {"url": "https://licitaciones.info/cliente/get-config-user"},
            "config_user_not_200_json_same_endpoint",
        ),
        ({"before_contracts": True}, "config_user_before_contracts"),
    ],
)
def test_config_user_must_be_app_boot_200_json_on_contracts_host(changes, reason):
    preflight = PreflightBuilder().with_config(**changes).build()

    verdict = preflight.verdict()

    assert verdict["session"] == "unverified"
    assert reason in verdict["reasons"]


def test_missing_config_user_observation_is_unverified():
    verdict = PreflightBuilder().without_config().build().verdict()

    assert verdict["session"] == "unverified"
    assert "config_user_not_observed" in verdict["reasons"]


def test_contracts_opened_by_script_is_rejected():
    verdict = PreflightBuilder().with_own_navigation(CONTRACTS).build().verdict()

    assert verdict["navigation"] == "contracts_forced_by_script"
    assert verdict["ready_for_acquisition"] is False


def test_contracts_not_reached_is_rejected():
    verdict = PreflightBuilder().without_contracts().build().verdict()

    assert verdict["navigation"] == "contracts_not_reached"
    assert verdict["session"] == "unverified"


def test_contracts_with_query_is_rejected():
    verdict = PreflightBuilder().with_page(url=CONTRACTS + "?x=1").build().verdict()

    assert verdict["session"] == "unverified"


@pytest.mark.parametrize(
    ("feed", "profile", "count", "ready"),
    [
        # Only the configured profile: the single acquisition-eligible case.
        ([FEED + PROFILE], "only_configured", 1, True),
        ([FEED + PROFILE + "," + PROFILE], "only_configured", 1, True),
        # Configured profile together with others (the 2026-11-26 real run).
        ([FEED + PROFILE + ",999"], "configured_with_others", 2, False),
        ([FEED + "999&perfiles=" + PROFILE], "configured_with_others", 2, False),
        # One or several profiles, none of them the configured one.
        ([FEED + "999"], "without_configured", 1, False),
        ([FEED + "999,888"], "without_configured", 2, False),
        # Absent or undetermined.
        (["https://col.licitaciones.info/cliente/contratos/get-info/MP"], "absent", 0, False),
        ([FEED], "absent", 0, False),
        ([], "undetermined_no_feed_request", 0, False),
    ],
)
def test_profile_situations_are_distinguished(feed, profile, count, ready):
    # Arrange
    builder = PreflightBuilder().with_feed(*feed)

    # Act
    verdict = builder.build().verdict()

    # Assert
    assert verdict["profile"] == profile
    assert verdict["profile_count"] == count
    assert verdict["ready_for_acquisition"] is ready
    assert (f"profile_{profile}" in verdict["reasons"]) is not ready


def test_last_feed_request_is_the_current_selection_and_change_is_flagged():
    builder = PreflightBuilder().with_feed(FEED + PROFILE + ",999", FEED + PROFILE)

    verdict = builder.build().verdict()

    assert verdict["profile"] == "only_configured"
    assert verdict["profile_changed"] is True
    assert verdict["ready_for_acquisition"] is True


def test_switching_away_from_configured_profile_blocks_acquisition():
    verdict = PreflightBuilder().with_feed(FEED + PROFILE, FEED + "999").build().verdict()

    assert verdict["profile"] == "without_configured"
    assert verdict["ready_for_acquisition"] is False


def test_profile_verdict_leaks_no_ids_urls_or_bodies():
    builder = PreflightBuilder().with_feed(FEED + PROFILE + ",987654")
    builder.preflight.observe_request(
        "https://col.licitaciones.info/cliente/contratos/get-info/MP",
        '{"perfiles": "555111", "query": {"Objeto": "secreto"}}',
    )

    text = repr(builder.build().verdict())

    for leaked in (PROFILE, "987654", "555111", "secreto", "perfiles=", "get-info", "https://"):
        assert leaked not in text


def test_undetermined_profile_blocks_acquisition_without_inventing_a_match():
    verdict = PreflightBuilder().with_feed().build().verdict()

    assert verdict["ready_for_acquisition"] is False
    assert "profile_undetermined_no_feed_request" in verdict["reasons"]


def test_verdict_never_contains_the_profile_identifier():
    verdict = PreflightBuilder().with_feed(FEED + "987654").build().verdict()

    assert "987654" not in repr(verdict)
    assert PROFILE not in repr(verdict)


def test_profile_match_ignores_other_paths():
    assert profile_match("https://col.licitaciones.info/get-contadores?perfiles=1", "1") is None


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("https://www.contratos.gov.co/consultas/VerDocumento", "official"),
        ("https://community.secop.gov.co/Public/x", "official"),
        ("https://col.licitaciones.info/cliente/contratos/obtener-documentos-proceso", "inventory"),
        ("https://col.licitaciones.info/cliente/contratos/get-conteo/MP", "feed"),
        ("https://col.licitaciones.info/cliente/contratos/get-info/MP", "feed"),
        (CONFIG, "allowed"),
        ("https://evil-licitaciones.info/cliente/contratos/get-info/MP", "allowed"),
    ],
)
def test_request_classification(url, expected):
    assert classify_request(url) == expected


def test_official_or_inventory_request_blocks_acquisition():
    builder = PreflightBuilder()
    builder.preflight.observe_request("https://www.contratos.gov.co/consultas/VerDocumento")

    verdict = builder.build().verdict()

    assert verdict["official_blocked"] == 1
    assert "unexpected_official_or_inventory_request" in verdict["reasons"]


def test_unblocked_provider_network_failure_is_a_provider_error():
    builder = PreflightBuilder().with_page(text="No encuentro URL")
    builder.preflight.observe_failure(CONFIG, blocked_by_us=False)

    assert builder.build().verdict()["url_notice"] == "unexplained"


def test_missing_download_control_blocks_acquisition():
    verdict = PreflightBuilder().with_page(download_control=False).build().verdict()

    assert "download_control_missing" in verdict["reasons"]


def listener(**changes):
    base = {
        "owners": 1,
        "addresses": ["127.0.0.1"],
        "name": "msedge.exe",
        "command_line": (
            '"msedge.exe" --remote-debugging-address=127.0.0.1 --remote-debugging-port=9232 '
            '--user-data-dir="C:\\Users\\u\\AppData\\Local\\EurekaNacional\\EdgeCDP"'
        ),
    }
    return {**base, **changes}


PROFILE_DIR = r"C:\Users\u\AppData\Local\EurekaNacional\EdgeCDP"


def test_dedicated_browser_accepted():
    ok, checks = dedicated_browser_checks(listener(), port=9232, profile_dir=PROFILE_DIR)

    assert ok is True
    assert all(checks.values())


@pytest.mark.parametrize(
    ("changes", "failed"),
    [
        ({"owners": 2}, "single_owner"),
        ({"addresses": ["192.168.0.10"]}, "loopback_only"),
        ({"name": "chrome.exe"}, "is_msedge"),
        (
            {"command_line": "msedge.exe --remote-debugging-port=9222 EurekaNacional\\EdgeCDP"},
            "port_flag",
        ),
        (
            {"command_line": "msedge.exe --remote-debugging-port=9232 --user-data-dir=X"},
            "dedicated_profile",
        ),
        (
            {"command_line": listener()["command_line"] + " --enable-automation"},
            "no_automation_flag",
        ),
    ],
)
def test_dedicated_browser_rejections(changes, failed):
    ok, checks = dedicated_browser_checks(listener(**changes), port=9232, profile_dir=PROFILE_DIR)

    assert ok is False
    assert checks[failed] is False


BARE_FEED = "https://col.licitaciones.info/cliente/contratos/get-info/MP"


@pytest.mark.parametrize(
    ("body", "expected"),
    [
        ('{"query": {}, "perfiles": "1234"}', ("only_configured", "body", 1)),
        ('{"query": {"perfil_id": 1234}, "limit": 30}', ("only_configured", "body", 1)),
        ('{"perfiles": [1234]}', ("only_configured", "body", 1)),
        ('{"perfiles": "999"}', ("without_configured", "body", 1)),
        ('{"perfiles": "1234,999"}', ("configured_with_others", "body", 2)),
        ("perfiles=1234&page=1", ("only_configured", "body", 1)),
        ('{"query": {}, "limit": 30}', ("absent", None, 0)),
        ("not a body", ("absent", None, 0)),
        (None, ("absent", None, 0)),
    ],
)
def test_profile_in_body_is_checked_only_when_query_lacks_it(body, expected):
    # Arrange / Act
    result = profile_match(BARE_FEED, PROFILE, body)

    # Assert
    assert result == expected


def test_query_profile_takes_precedence_over_body():
    result = profile_match(FEED + PROFILE, PROFILE, '{"perfiles": "999"}')

    assert result == ("only_configured", "query", 1)


def test_body_profile_reaches_verdict_with_source_and_without_identifier():
    # Arrange
    builder = PreflightBuilder().with_feed()
    body = '{"query": {"Objeto": "secreto"}, "perfiles": "1234"}'
    builder.preflight.observe_request(BARE_FEED, body)

    # Act
    verdict = builder.build().verdict()

    # Assert
    assert verdict["profile"] == "only_configured"
    assert verdict["profile_source"] == ["body"]
    assert verdict["ready_for_acquisition"] is True
    assert "secreto" not in repr(verdict)
    assert PROFILE not in repr(verdict)


def test_oversized_body_is_not_parsed():
    body = '{"perfiles": "1234", "pad": "' + "x" * 70000 + '"}'

    assert profile_match(BARE_FEED, PROFILE, body) == ("absent", None, 0)


def safe_closure(**changes):
    verified = closure_record(marker_owned=True, context_closed=True, disconnected=True)
    return {**verified, **changes}


def test_closure_record_is_false_unless_each_fact_is_verified_true():
    # Arrange / Act
    record = closure_record(marker_owned=None, context_closed="yes", disconnected=1)

    # Assert
    assert record == {"marker_owned": False, "context_closed": False, "disconnected": False}


def test_marker_released_only_with_complete_safe_closure_evidence():
    released = marker_release_allowed(
        safe_closure(), worker_exit_code=0, marker_text=MARKER_TEXT + "\n"
    )

    assert released is True


@pytest.mark.parametrize(
    ("closure", "exit_code", "marker_text"),
    [
        (None, 0, MARKER_TEXT),  # no closure evidence written by this run
        (safe_closure(context_closed=False), 0, MARKER_TEXT),  # context not verified closed
        (safe_closure(disconnected=False), 0, MARKER_TEXT),  # CDP disconnect not verified
        (safe_closure(marker_owned=False), 0, MARKER_TEXT),  # marker of another attempt
        (safe_closure(), 1, MARKER_TEXT),  # worker did not exit cleanly
        (safe_closure(), 0, "other-attempt"),  # foreign marker content
        (safe_closure(), 0, None),
        ({"context_closed": True}, 0, MARKER_TEXT),  # legacy partial evidence
        ([], 0, MARKER_TEXT),
    ],
)
def test_marker_kept_without_safe_closure_evidence(closure, exit_code, marker_text):
    released = marker_release_allowed(closure, worker_exit_code=exit_code, marker_text=marker_text)

    assert released is False


def test_not_ready_verdict_still_yields_releasable_closure(tmp_path):
    # Arrange: the 2026-11-26 case, a not-ready preflight followed by a verified closure.
    verdict = PreflightBuilder().with_feed(FEED + PROFILE + ",999").build().verdict()
    path = tmp_path / "closure.json"
    evidence = closure_record(marker_owned=True, context_closed=True, disconnected=True)
    path.write_text(json.dumps(evidence), encoding="utf8")

    # Act
    released = marker_release_allowed(
        read_closure(path), worker_exit_code=0, marker_text=MARKER_TEXT
    )

    # Assert
    assert verdict["ready_for_acquisition"] is False
    assert released is True


@pytest.mark.parametrize("content", [None, "", "{not json", "[1, 2]"])
def test_unreadable_or_missing_closure_is_no_evidence(tmp_path, content):
    path = tmp_path / "closure.json"
    if content is not None:
        path.write_text(content, encoding="utf8")

    assert read_closure(path) is None


def test_marker_text_matches_the_guard_reservation():
    source = Path(__file__).resolve().parents[2] / "scripts" / "eureka_nacional_secop1_popup.py"

    assert f'lock.write("{MARKER_TEXT}\\n")' in source.read_text(encoding="utf8")
