import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any

from ..domain.message import DeliveryError, DeliveryReceipt


class DevEmailSender:
    provider, scope = "file", "capture"
    idempotency_seconds: int | None = None

    def __init__(self, directory: Path):
        self.directory = directory

    def send(self, payload: dict[str, Any], key: str) -> DeliveryReceipt:
        self.directory.mkdir(parents=True, exist_ok=True)
        target = self.directory / (hashlib.sha256(key.encode()).hexdigest() + ".json")
        content = json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2).encode()
        if target.exists():
            if target.read_bytes() != content:
                raise DeliveryError("capture_conflict", "La clave local ya tiene otro contenido.")
            return DeliveryReceipt("file:" + target.stem)
        temporary: str | None = None
        try:
            with tempfile.NamedTemporaryFile(
                dir=self.directory, prefix=".capture-", delete=False
            ) as f:
                temporary = f.name
                f.write(content)
                f.flush()
                os.fsync(f.fileno())
            os.replace(temporary, target)
            temporary = None
        except OSError as error:
            raise DeliveryError(
                "capture_io", "No fue posible capturar el correo local.", retryable=True
            ) from error
        finally:
            if temporary is not None:
                Path(temporary).unlink(missing_ok=True)
        return DeliveryReceipt("file:" + target.stem)
