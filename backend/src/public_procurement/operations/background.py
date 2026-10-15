"""Local, in-process launch with a persisted-start handshake. Not a durable worker queue."""

import threading
import uuid
from typing import Any

from .services import build_cycle_service, record_startup_failure


class ManualCycleStartError(RuntimeError):
    pass


class ManualCycleRunner:
    def __init__(
        self,
        sessions: Any,
        settings: Any,
        factory: Any = build_cycle_service,
        startup_timeout: float = 8,
    ) -> None:
        self.sessions, self.settings, self.factory = sessions, settings, factory
        self.startup_timeout = startup_timeout
        self._closing = False
        self._guard = threading.Lock()
        self._threads: set[threading.Thread] = set()

    def close(self) -> None:
        with self._guard:
            self._closing = True
        # Process termination interrupts daemon threads. DB state/lock recovery is authoritative.

    def start(self) -> dict[str, Any]:
        identifier = uuid.uuid4()
        ready = threading.Event()
        handshake = threading.Lock()
        state: dict[str, Any] = {"cancelled": False}

        def persisted(cycle: dict[str, Any]) -> None:
            with handshake:
                if state["cancelled"]:
                    raise ManualCycleStartError("Startup acknowledgement expired before Radar.")
                state["result"] = {
                    "cycle_id": cycle["id"],
                    "status": cycle["status"],
                    "started_at": cycle["started_at"],
                    "reason": cycle.get("reason"),
                }
                ready.set()

        def execute() -> None:
            try:
                self.factory(self.sessions, self.settings).run(
                    trigger="manual_ui", cycle_id=identifier, on_started=persisted
                )
            except Exception as error:
                # Do not put provider/driver exception bodies in HTTP responses or logs.
                with handshake:
                    if "result" not in state:
                        state["error"] = type(error).__name__
                        ready.set()
                record_startup_failure(self.settings, type(error).__name__, "manual_ui")
            finally:
                with self._guard:
                    self._threads.discard(threading.current_thread())

        thread = threading.Thread(target=execute, name=f"eureka-manual-{identifier}", daemon=True)
        with self._guard:
            if self._closing:
                raise ManualCycleStartError("Backend shutting down.")
            self._threads.add(thread)
            thread.start()
        if not ready.wait(self.startup_timeout):
            with handshake:
                if "result" not in state:
                    state["cancelled"] = True
                    raise ManualCycleStartError(
                        "Startup timeout; inspect configuration and database."
                    )
        if "result" not in state:
            raise ManualCycleStartError(
                "Could not persist/start cycle; inspect configuration and database."
            )
        return dict(state["result"])
