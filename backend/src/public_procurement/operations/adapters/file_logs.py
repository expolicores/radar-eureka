import json
import os
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any


class CycleLogs:
    def __init__(self, root: Path, retention_days: int):
        self.root = root.resolve()
        self.retention_days = retention_days

    def write(self, cycle: dict[str, Any]) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        stamp = datetime.fromisoformat(cycle["started_at"]).strftime("%Y%m%d-%H%M%S")
        stem = f"eureka-cycle-{stamp}-{cycle['id']}"
        for suffix, body in (
            (".json", json.dumps(cycle, ensure_ascii=False, indent=2, default=str)),
            (
                ".log",
                "\n".join(json.dumps(e, ensure_ascii=False, default=str) for e in cycle["events"])
                + "\n",
            ),
        ):
            path = self.root / (stem + suffix)
            temporary = path.with_suffix(suffix + ".tmp")
            # Never follow an existing symlink, including temporary names.
            if path.is_symlink() or temporary.is_symlink():
                raise ValueError("Ruta de log insegura.")
            with temporary.open("w", encoding="utf-8") as stream:
                stream.write(body)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, path)

    def cleanup(self, active_ids: set[str]) -> int:
        import re

        if not self.root.exists():
            return 0
        cutoff = (datetime.now(UTC) - timedelta(days=self.retention_days)).timestamp()
        removed = 0
        pattern = re.compile(r"eureka-cycle-\d{8}-\d{6}-([0-9a-f-]{36})\.(?:json|log)$")
        for path in self.root.iterdir():
            match = pattern.fullmatch(path.name)
            if not match or match[1] in active_ids or path.is_symlink() or not path.is_file():
                continue
            if path.resolve().parent == self.root and path.stat().st_mtime < cutoff:
                path.unlink()
                removed += 1
        return removed
