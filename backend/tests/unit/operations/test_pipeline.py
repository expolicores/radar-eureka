"""Real Radar decisions and file dispatcher coordinated with isolated in-memory persistence."""

import uuid
from dataclasses import replace
from datetime import date
from unittest.mock import Mock

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from public_procurement.eureka.radar_config import load_radar_config
from public_procurement.eureka.radar_services import RadarService
from public_procurement.notifications.adapters.file import DevEmailSender
from public_procurement.notifications.repositories import (
    NotificationAlertRecord,
    NotificationRecord,
    SqlNotificationRepository,
)
from public_procurement.notifications.services import DispatchPolicy, NotificationDispatcher
from tests.unit.eureka.test_affinity import details, process
from tests.unit.eureka.test_radar import MemoryRepository
from tests.unit.notifications.test_dispatch import Source, golden


@pytest.mark.parametrize("interrupt", ["none", "before_notifications", "after_capture"])
def test_repeated_cycles_and_restart_do_not_duplicate_alert_or_capture(setup, interrupt):
    cycle, _, _, _, path = setup
    alerts = []

    class RadarRepository(MemoryRepository):
        def alert(self, *args):
            created = super().alert(*args)
            if created:
                alerts.append(golden())
            return created

    repository = RadarRepository()
    pipeline = Mock()
    pipeline.enrich.return_value = replace(details(), opportunity_id=uuid.uuid4())
    pipeline.evidence.return_value = []

    def radar(identifier, observe):
        return RadarService(
            repository,
            pipeline,
            load_radar_config(cycle.settings.eureka_radar_config_path),
            30_000_000,
            observer=observe,
        ).run(
            [process()],
            start=date(2026, 10, 7),
            before=date(2026, 10, 15),
            regions=("Boyacá",),
            run_id=identifier,
        )

    engine = create_engine("sqlite://")
    with engine.connect() as c:
        c.execute(text("ATTACH DATABASE ':memory:' AS notifications"))
        NotificationRecord.__table__.create(c)
        NotificationAlertRecord.__table__.create(c)
    sessions = sessionmaker(engine, expire_on_commit=False)
    dispatcher = NotificationDispatcher(
        SqlNotificationRepository(sessions),
        Source(alerts),
        DevEmailSender(path / "capture"),
        DispatchPolicy(enabled=True, base_url="http://localhost:5173"),
    )
    cycle.radar = radar

    def notify():
        return dispatcher.run(["fixture@example.invalid"], retry=True)

    if interrupt == "before_notifications":
        cycle.notify = Mock(side_effect=KeyboardInterrupt)
    elif interrupt == "after_capture":

        def interrupted():
            notify()
            raise KeyboardInterrupt

        cycle.notify = interrupted
    else:
        cycle.notify = notify
    if interrupt != "none":
        with pytest.raises(KeyboardInterrupt):
            cycle.run()
    else:
        first = cycle.run()
        assert first["metrics"]["alert_created"] == first["metrics"]["notification_captured"] == 1
    cycle.notify = notify
    repeated = cycle.run()
    assert len(repository.alerts) == 1
    assert len(list((path / "capture").glob("*.json"))) == 1
    assert repeated["metrics"]["alert_created"] == 0
    assert cycle.run()["metrics"]["notification_captured"] == 0
    engine.dispose()
