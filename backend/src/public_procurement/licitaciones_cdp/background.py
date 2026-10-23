"""Manual worker with persisted-start acknowledgement, no scheduling or auto-start."""

import threading
import uuid
from collections.abc import Callable
from typing import Any

from sqlalchemy.orm import Session, sessionmaker

from public_procurement.shared.config import Settings

from .services import build_run_service


class ManualCdpRunner:
    def __init__(
        self,
        sessions: sessionmaker[Session],
        settings: Settings,
        factory: Callable[..., Any] = build_run_service,
    ) -> None:
        self.sessions, self.settings, self.factory = sessions, settings, factory
        self.guard = threading.Lock()
        self.active = False
        self.closed = False

    def close(self) -> None:
        with self.guard:
            self.closed = True

    def start(self) -> dict[str, Any]:
        identifier = uuid.uuid4()
        ready = threading.Event()
        result: dict[str, Any] = {}

        def persisted(run: dict[str, Any]) -> None:
            result.update(id=run["id"], status=run["status"])
            ready.set()

        def execute() -> None:
            try:
                self.factory(self.sessions, self.settings).run(identifier, persisted)
            except Exception:
                result["error"] = (
                    "No fue posible iniciar; revisa si Radar u otra corrida está activa."
                )
                ready.set()
            finally:
                with self.guard:
                    self.active = False

        with self.guard:
            if self.closed or self.active:
                raise RuntimeError(
                    "Ya hay una corrida Licitaciones.info activa o el backend está cerrando."
                )
            self.active = True
            threading.Thread(
                target=execute, name=f"licitaciones-cdp-{identifier}", daemon=True
            ).start()
        if not ready.wait(8) or "id" not in result:
            raise RuntimeError(
                result.get("error", "No se confirmó el inicio persistido de la corrida.")
            )
        return result
