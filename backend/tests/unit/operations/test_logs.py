import os
import time

from public_procurement.operations.adapters.file_logs import CycleLogs


def test_retention_only_owned_inactive_files(tmp_path):
    logs = CycleLogs(tmp_path, 1)
    active = "11111111-1111-4111-8111-111111111111"
    expired = "22222222-2222-4222-8222-222222222222"
    for name in (
        f"eureka-cycle-20260101-070000-{active}.log",
        f"eureka-cycle-20260101-070000-{expired}.json",
        "unrelated.json",
    ):
        path = tmp_path / name
        path.write_text("test")
        os.utime(path, (time.time() - 200000, time.time() - 200000))
    assert logs.cleanup({active}) == 1
    assert len(list(tmp_path.iterdir())) == 2
