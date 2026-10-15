from collections.abc import Callable
from typing import Any, Protocol

Observer = Callable[[str, dict[str, Any]], None]


class CycleLogSink(Protocol):
    def write(self, cycle: dict[str, Any]) -> None: ...
    def cleanup(self, active_ids: set[str]) -> int: ...
