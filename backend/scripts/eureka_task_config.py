"""Print only allowlisted scheduler configuration, never secrets."""

import json

from public_procurement.shared.config import load_settings

settings = load_settings()
print(
    json.dumps(
        {
            "enabled": settings.eureka_automation_enabled,
            "name": settings.eureka_automation_task_name,
            "times": settings.eureka_automation_run_times,
            "interval": settings.eureka_automation_interval_hours,
            "timezone": settings.eureka_automation_timezone,
        }
    )
)
