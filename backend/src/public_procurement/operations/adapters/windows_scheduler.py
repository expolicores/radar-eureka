import base64
import json
import os
import subprocess
import time
from pathlib import Path
from typing import Any

_cache: dict[str, tuple[float, dict[str, Any]]] = {}


def scheduler_status(task_name: str) -> dict[str, Any]:
    if os.name != "nt":
        return {"status": "unknown", "next_run": None, "reason": "not_windows"}
    cached = _cache.get(task_name)
    if cached and time.monotonic() - cached[0] < 30:
        return cached[1]
    # Name is passed as data, never interpolated in executable code.
    script = """
    $ErrorActionPreference='Stop'
    try {
        $task=Get-ScheduledTask -TaskPath '\\' -ErrorAction Stop |
            Where-Object TaskName -eq $env:EUREKA_TASK_QUERY
        if (-not $task) {
            @{status='not_registered';next_run=$null} | ConvertTo-Json -Compress
            exit 0
        }
        $info=$task | Get-ScheduledTaskInfo
        $next=$null
        if ($task.State -ne 'Disabled' -and $info.NextRunTime.Year -gt 2000) {
            $next=$info.NextRunTime.ToUniversalTime().ToString('o')
        }
        $state=if ($task.State -eq 'Disabled') {'disabled'} else {'active'}
        @{status=$state; next_run=$next} | ConvertTo-Json -Compress
    } catch {
        @{status='unknown';next_run=$null;reason='scheduler_query_failed'} |
            ConvertTo-Json -Compress
    }
    """
    try:
        executable = (
            Path(os.environ.get("SYSTEMROOT", "C:/Windows"))
            / "System32/WindowsPowerShell/v1.0/powershell.exe"
        )
        result = subprocess.run(  # noqa: S603 - fixed executable/code; name is environment data
            [
                str(executable),
                "-NoProfile",
                "-NonInteractive",
                "-EncodedCommand",
                base64.b64encode(script.encode("utf-16le")).decode("ascii"),
            ],
            env={**os.environ, "EUREKA_TASK_QUERY": task_name},
            capture_output=True,
            text=True,
            timeout=8,
            creationflags=subprocess.CREATE_NO_WINDOW,
            check=True,
        )
        value: dict[str, Any] = json.loads(result.stdout)
    except (OSError, subprocess.SubprocessError, ValueError):
        value = {"status": "unknown", "next_run": None, "reason": "scheduler_query_failed"}
    _cache[task_name] = (time.monotonic(), value)
    return value
