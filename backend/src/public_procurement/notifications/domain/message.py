import hashlib
import html
import json
import re
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

TEMPLATE_VERSION = "notification-v1"
STATUSES = ("pending", "processing", "captured", "sent", "retryable", "failed", "skipped")
PRIORITIES = {"high": "Alta", "medium": "Media", "low": "Baja"}


def recipient(value: str) -> str:
    value = value.strip().lower()
    if (
        len(value) > 254
        or not re.fullmatch(
            r"[a-z0-9.!#$%&'*+/=?^_`{|}~-]{1,64}@"
            r"[a-z0-9](?:[a-z0-9-]*[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]*[a-z0-9])?)+",
            value,
        )
        or ".." in value.split("@", 1)[0]
        or value.startswith(".")
        or ".@" in value
    ):
        raise ValueError(
            "Destinatario inválido; usa una dirección email sin encabezados ni controles."
        )
    return value


def utc(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


def identity(
    alerts: list[dict[str, Any]],
    address: str,
    scope: str,
    kind: str,
    window: tuple[datetime, datetime] | None,
) -> str:
    data = {
        "alerts": sorted(str(a["id"]) for a in alerts),
        "recipient": address,
        "scope": scope,
        "channel": "email",
        "kind": kind,
        "window": [v.isoformat() for v in window] if window else None,
    }
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()


def scalar(value: Any) -> str:
    if value is None or value == "unknown":
        return "No determinado"
    if value == "not_required":
        return "No requerida"
    if value == "required":
        return "Requerida"
    if value is True:
        return "Sí"
    if value is False:
        return "No"
    return str(value)


def money(value: Any) -> str:
    if value is None:
        return "No determinado"
    try:
        return "$" + f"{int(value):,}".replace(",", ".") + " COP"
    except (ValueError, TypeError):
        return "No determinado"


def product(value: dict[str, Any]) -> str:
    name = str(value.get("name") or "Producto no determinado")
    name = " ".join(
        w.capitalize() if i == 0 or (i == 1 and name.startswith("jugo ")) else w
        for i, w in enumerate(name.split())
    )
    return " ".join(
        str(v)
        for v in (name, value.get("presentation_value"), value.get("presentation_unit"))
        if v is not None
    )


def sort_alerts(alerts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    # Affinity uses recorded matches only; it never re-evaluates commercial rules.
    return sorted(
        alerts,
        key=lambda a: (
            -{"high": 3, "medium": 2, "low": 1}.get(a["priority"], 0),
            -utc(datetime.fromisoformat(str(a["created_at"]))).timestamp(),
            -len(a["snapshot"].get("confirmed_matches", [])),
            str(a["id"]),
        ),
    )


REASONS = {
    "region_match": "Región objetivo",
    "new_process": "Proceso nuevo para Radar",
    "confirmed_commercial_match": "Afinidad comercial confirmada documentalmente",
    "unspsc_match": "UNSPSC documental relevante",
    "budget": "Presupuesto registrado",
    "budget_review": "Presupuesto requiere revisión",
    "conditions_review": "Condiciones por revisar",
    "participation_review": "Requisitos por revisar",
    "review": "Revisión de vigencia/fase",
}


def compose(
    alerts: list[dict[str, Any]], address: str, base_url: str, kind: str, sender: str
) -> dict[str, Any]:
    alerts = sort_alerts(alerts)
    # Freeze the historical inputs used by this message without copying full
    # documentary evidence or unrelated diagnostics into notification storage.
    fields = (
        "secop_id",
        "title",
        "entity",
        "department",
        "municipality",
        "budget",
        "category",
        "products",
        "score",
        "execution_days",
        "payment_days",
        "guarantee_required",
        "confirmed_matches",
    )
    frozen = json.loads(
        json.dumps(
            [
                {
                    **{
                        k: a[k]
                        for k in (
                            "id",
                            "opportunity_id",
                            "created_at",
                            "priority",
                            "review_required",
                        )
                    },
                    "snapshot": {k: a["snapshot"].get(k) for k in fields},
                    "reasons": [
                        {k: r[k] for k in ("code", "concept", "value", "field", "origin") if k in r}
                        for r in a["reasons"]
                        if r.get("code") in REASONS
                    ],
                }
                for a in alerts
            ],
            default=str,
        )
    )
    lines = [
        "Nueva oportunidad Eureka"
        if kind == "immediate"
        else f"Eureka encontró {len(alerts)} oportunidades nuevas"
    ]
    links = []
    for number, alert in enumerate(frozen, 1):
        snapshot = alert["snapshot"]
        priority = PRIORITIES.get(alert["priority"], scalar(alert["priority"]))
        municipality = scalar(snapshot.get("municipality"))
        link = base_url.rstrip("/") + "/eureka/" + str(uuid.UUID(alert["opportunity_id"]))
        links.append(link)
        labels = list(
            dict.fromkeys(
                str(m["label"]) for m in snapshot.get("confirmed_matches") or [] if m.get("label")
            )
        )
        lines.extend(
            [
                "",
                f"{number}. {municipality} — {priority}",
                "Entidad: " + scalar(snapshot.get("entity")),
                "Ubicación: " + municipality + ", " + scalar(snapshot.get("department")),
                "Categoría: " + (", ".join(labels) or "No determinada"),
                "Presupuesto: " + money(snapshot.get("budget")),
                "Score Eureka: " + scalar(snapshot.get("score")),
                "Productos detectados:",
            ]
        )
        products = snapshot.get("products") or []
        lines.extend("- " + product(p) for p in products)
        if not products:
            lines.append("- No determinados en el snapshot de alerta")
        if kind == "immediate":
            lines.extend(
                [
                    "Plazo: " + scalar(snapshot.get("execution_days")) + " días",
                    "Pago: " + scalar(snapshot.get("payment_days")) + " días",
                    "Póliza: " + scalar(snapshot.get("guarantee_required")),
                    "Motivos de alerta:",
                ]
            )
            for reason in alert["reasons"]:
                if reason.get("code") in REASONS:
                    detail = reason.get("concept", reason.get("value"))
                    lines.append(
                        "- "
                        + REASONS[reason["code"]]
                        + (": " + scalar(detail) if detail is not None else "")
                    )
        lines.extend(
            [
                "Requiere revisión: " + ("Sí" if alert["review_required"] else "No indicada"),
                "Confirmar vigencia y requisitos antes de participar.",
                "Ver oportunidad: " + link,
            ]
        )
    if kind == "immediate":
        a = frozen[0]
        subject = (
            f"Nueva oportunidad Eureka — {PRIORITIES.get(a['priority'], a['priority'])}"
            f" — {scalar(a['snapshot'].get('municipality'))}"
        )
    else:
        subject = f"Eureka encontró {len(alerts)} oportunidades nuevas"
    subject = re.sub(r"[\x00-\x1f\x7f]+", " ", subject)[:200]
    body = "\n".join(lines)
    rendered = "<div>" + "".join("<p>" + html.escape(line) + "</p>" for line in lines) + "</div>"
    rendered += "".join(
        '<p><a href="' + html.escape(link, quote=True) + '">Ver oportunidad</a></p>'
        for link in links
    )
    return {
        "template_version": TEMPLATE_VERSION,
        "recipient": address,
        "from": sender,
        "subject": subject,
        "text": body,
        "html": rendered,
        "links": links,
        "alerts": frozen,
    }


@dataclass(frozen=True)
class DeliveryReceipt:
    message_id: str
    status_code: int | None = None


class DeliveryError(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        *,
        retryable: bool = False,
        ambiguous: bool = False,
        retry_after: int = 0,
        status_code: int | None = None,
    ):
        super().__init__(message)
        self.code, self.message = code, message
        self.retryable, self.ambiguous = retryable, ambiguous
        self.retry_after, self.status_code = retry_after, status_code


def retry_at(now: datetime, attempt: int, base_seconds: int, retry_after: int = 0) -> datetime:
    return now + timedelta(seconds=max(min(base_seconds * 2 ** (attempt - 1), 3600), retry_after))


def blocked_attempt(
    value: dict[str, Any], provider: str, at: datetime, max_retries: int, margin_seconds: int = 0
) -> str | None:
    deadline = value.get("provider_idempotency_until")
    if (
        value["delivery_scope"] == "real"
        and value["delivery_ambiguous"]
        and (
            value["provider"] != provider
            or deadline is None
            or at + timedelta(seconds=margin_seconds) >= utc(deadline)
        )
    ):
        return "delivery_unknown_review"
    if value["attempt_count"] >= max_retries + 1:
        return "retry_exhausted"
    if value["provider"] != provider:
        return "provider_changed_review"
    return None
