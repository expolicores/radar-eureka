import uuid
from datetime import datetime
from typing import Annotated, Any, Literal, cast

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel

from .domain.message import recipient as normalize_recipient
from .services import NotificationQueries, NotificationSchemaPendingError

router = APIRouter(prefix="/api/eureka/notifications", tags=["Eureka notifications"])
Status = Literal["pending", "processing", "captured", "sent", "retryable", "failed", "skipped"]


class NotificationSummary(BaseModel):
    id: uuid.UUID
    alert_id: uuid.UUID | None
    alert_ids: list[uuid.UUID]
    channel: str
    recipient: str
    notification_type: str
    delivery_scope: str
    delivery_mode: str
    provider: str
    status: Status
    created_at: datetime
    updated_at: datetime
    sent_at: datetime | None
    captured_at: datetime | None
    failed_at: datetime | None
    processing_started_at: datetime | None
    next_retry_at: datetime | None
    provider_idempotency_until: datetime | None
    delivery_ambiguous: bool
    attempt_count: int
    retry_count: int
    provider_message_id: str | None
    error_code: str | None
    error_message: str | None
    idempotency_key: str
    digest_from: datetime | None
    digest_to: datetime | None


class NotificationDetail(NotificationSummary):
    payload_snapshot: dict[str, Any]
    attempt_history: list[dict[str, Any]]


class NotificationsPage(BaseModel):
    items: list[NotificationSummary]
    total: int
    page: int
    page_size: int
    counts: dict[str, int]


def get_queries(request: Request) -> NotificationQueries:
    return cast(NotificationQueries, request.app.state.notification_queries)


@router.get("", response_model=NotificationsPage)
def listing(
    service: Annotated[NotificationQueries, Depends(get_queries)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 25,
    status: Status | None = None,
    channel: Literal["email"] | None = None,
    recipient: str | None = None,
    alert_id: uuid.UUID | None = None,
    delivery_scope: Literal["capture", "real"] | None = None,
    created_from: datetime | None = None,
    created_before: datetime | None = None,
) -> Any:
    if (created_from and created_from.tzinfo is None) or (
        created_before and created_before.tzinfo is None
    ):
        raise HTTPException(422, "Las fechas deben incluir zona horaria.")
    if created_from and created_before and created_from >= created_before:
        raise HTTPException(422, "Rango de fechas inválido.")
    try:
        return service.listing(
            page,
            page_size,
            {
                "status": status,
                "channel": channel,
                "recipient": normalize_recipient(recipient) if recipient else None,
                "alert_id": alert_id,
                "delivery_scope": delivery_scope,
                "created_from": created_from,
                "created_before": created_before,
            },
        )
    except ValueError as error:
        raise HTTPException(422, str(error)) from error
    except NotificationSchemaPendingError as error:
        raise HTTPException(503, str(error)) from error


@router.get("/{notification_id}", response_model=NotificationDetail)
def detail(
    notification_id: uuid.UUID, service: Annotated[NotificationQueries, Depends(get_queries)]
) -> Any:
    try:
        value = service.detail(notification_id)
        value["alert_ids"] = [a["id"] for a in value["payload_snapshot"]["alerts"]]
        return value
    except LookupError as error:
        raise HTTPException(404, str(error)) from error
    except NotificationSchemaPendingError as error:
        raise HTTPException(503, str(error)) from error
