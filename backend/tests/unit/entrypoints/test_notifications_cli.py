import json
from unittest.mock import Mock

from typer.testing import CliRunner

from public_procurement.entrypoints.cli import __main__ as cli
from public_procurement.notifications.repositories import DispatcherBusyError


def dispatcher(monkeypatch):
    service = Mock()
    service.policy.enabled = True
    service.run.return_value = {
        "disabled": False,
        "prepared": 1,
        "sent": 0,
        "captured": 1,
        "retryable": 0,
        "failed": 0,
        "skipped": 0,
        "preview": [],
        "items": [],
    }
    monkeypatch.setattr(cli, "build_notification_dispatcher", lambda *args: service)
    monkeypatch.setattr(cli, "ensure_schema", lambda *args: None)
    return service


def test_cli_file_json_overrides_for_this_invocation(monkeypatch):
    service = dispatcher(monkeypatch)
    result = CliRunner().invoke(
        cli.app,
        [
            "send-eureka-notifications",
            "--pending",
            "--mode",
            "file",
            "--recipient",
            "r@example.invalid",
            "--json",
        ],
    )
    assert result.exit_code == 0, result.output
    assert json.loads(result.output)["captured"] == 1
    assert service.run.call_args.kwargs["allow_real_send"] is False


def test_cli_dry_run_and_bogota_day(monkeypatch):
    service = dispatcher(monkeypatch)
    result = CliRunner().invoke(
        cli.app,
        [
            "send-eureka-notifications",
            "--digest",
            "daily",
            "--date",
            "2026-10-14",
            "--recipient",
            "r@example.invalid",
            "--dry-run",
            "--json",
        ],
    )
    assert result.exit_code == 0, result.output
    args = service.run.call_args.kwargs
    assert args["dry_run"]
    assert args["window"][0].isoformat() == "2026-10-14T05:00:00+00:00"
    assert args["window"][1].isoformat() == "2026-10-15T05:00:00+00:00"


def test_cli_conflicting_selection_and_busy(monkeypatch):
    service = dispatcher(monkeypatch)
    assert (
        CliRunner()
        .invoke(cli.app, ["send-eureka-notifications", "--pending", "--digest", "daily"])
        .exit_code
        != 0
    )
    service.run.side_effect = DispatcherBusyError("Ya hay un dispatcher activo")
    result = CliRunner().invoke(cli.app, ["send-eureka-notifications", "--pending", "--json"])
    assert result.exit_code == 2
    assert json.loads(result.output)["status"] == "busy"


def test_cli_disabled_works_without_notifications_schema(monkeypatch):
    service = dispatcher(monkeypatch)
    service.policy.enabled = False
    service.run.return_value = {"disabled": True, "failed": 0, "retryable": 0}
    result = CliRunner().invoke(cli.app, ["send-eureka-notifications", "--json"])
    assert result.exit_code == 0
    assert json.loads(result.output)["disabled"]


def test_json_stdout_stays_parseable_when_dispatcher_logs(monkeypatch):
    import logging

    from public_procurement.shared.logging import log_event

    service = dispatcher(monkeypatch)
    value = service.run.return_value

    def send(*args, **kwargs):
        log_event(
            logging.getLogger("public_procurement.notifications.services"),
            "notification_attempt",
            notification_id="test",
        )
        return value

    service.run.side_effect = send
    result = CliRunner().invoke(
        cli.app,
        [
            "send-eureka-notifications",
            "--mode",
            "file",
            "--recipient",
            "r@example.invalid",
            "--json",
        ],
    )
    assert result.exit_code == 0
    assert json.loads(result.stdout)["captured"] == 1
    assert "notification_attempt" in result.stderr
