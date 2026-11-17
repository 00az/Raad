"""C2 producer: publish UserConfirmed after a Cognito sign-up confirmation.

Runs as the user pool's post-confirmation trigger. Account confirmation never depends on the
event: every outcome, including a publication failure, returns the original Cognito event
unchanged, and PUT /wallet remains the authoritative safety net (C2). Only a sign-up
confirmation publishes; a password-reset confirmation never does.

Values come only from the trusted trigger (verified subject, confirmed email and name) plus a
new event ID and this function's own UTC clock. Logs and metrics carry the event ID, the
environment and a fixed outcome category; never the trigger, profile, email or name.
"""

from __future__ import annotations

import json
import os
import re
import uuid
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

SIGN_UP_TRIGGER = "PostConfirmation_ConfirmSignUp"
EVENT_SOURCE = "raad.identity"
EVENT_DETAIL_TYPE = "raad.identity.user-confirmed.v1"
SPEC_VERSION = "1.0"
EMITTED_FIELDS = (
    "specVersion",
    "eventId",
    "occurredAt",
    "environment",
    "userId",
    "email",
    "displayName",
)
ENVIRONMENTS = frozenset({"dev", "stg", "prd"})
NAMESPACE = "Raad/Platform"
# Cognito waits at most 5 seconds for a trigger; the function timeout is 3 seconds.
SDK_CONFIG = Config(connect_timeout=0.5, read_timeout=1, retries={"total_max_attempts": 2})
_EMAIL = re.compile(r"^[^@\s]{1,64}@[^@\s]+\.[^@\s]+$")
_client: Any = None


class PublicationSkipped(ValueError):
    """The trigger carries no complete, verified profile; nothing is published."""


class PublicationRejected(RuntimeError):
    """The bus did not accept the entry; ``reason`` is the provider's error code only."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


def build_detail(
    event: dict[str, Any], *, environment: str, occurred_at: datetime, event_id: str
) -> dict[str, str]:
    """Return exactly the C2 fields, from trusted trigger attributes only."""
    attributes = (event.get("request") or {}).get("userAttributes")
    if not isinstance(attributes, dict):
        raise PublicationSkipped("missing-attributes")
    subject = attributes.get("sub")
    email = attributes.get("email")
    name = attributes.get("name")
    if not isinstance(subject, str) or not 1 <= len(subject) <= 128 or subject != subject.strip():
        raise PublicationSkipped("invalid-subject")
    if attributes.get("email_verified") != "true":
        raise PublicationSkipped("unverified-email")
    if not isinstance(email, str) or len(email) > 254 or not _EMAIL.fullmatch(email):
        raise PublicationSkipped("invalid-email")
    if not isinstance(name, str) or not 1 <= len(name.strip()) <= 200:
        raise PublicationSkipped("invalid-name")
    if occurred_at.tzinfo is None:
        raise ValueError("occurredAt must carry an offset")
    return {
        "specVersion": SPEC_VERSION,
        "eventId": event_id,
        "occurredAt": occurred_at.astimezone(UTC).isoformat(timespec="milliseconds"),
        "environment": environment,
        "userId": subject,
        "email": email,
        "displayName": name.strip(),
    }


def publish(client: Any, bus: str, detail: dict[str, str]) -> None:
    """Send one entry; a thrown error and a per-entry failure both raise."""
    response = client.put_events(
        Entries=[
            {
                "Source": EVENT_SOURCE,
                "DetailType": EVENT_DETAIL_TYPE,
                "Detail": json.dumps(detail, separators=(",", ":")),
                "EventBusName": bus,
            }
        ]
    )
    entries = response.get("Entries") or []
    if response.get("FailedEntryCount", 0) or len(entries) != 1 or not entries[0].get("EventId"):
        code = entries[0].get("ErrorCode") if entries else None
        raise PublicationRejected(_safe_code(code) or "no-event-id")


def process(
    event: dict[str, Any],
    *,
    client_factory: Callable[[], Any],
    environment: str,
    bus: str,
    clock: Callable[[], datetime],
    new_id: Callable[[], str],
) -> dict[str, Any]:
    """Publish for a sign-up confirmation; always hand Cognito its original event back."""
    if not isinstance(event, dict) or event.get("triggerSource") != SIGN_UP_TRIGGER:
        return event
    event_id = new_id()
    try:
        if environment not in ENVIRONMENTS or not bus.startswith("arn:aws:events:"):
            raise PublicationRejected("configuration")
        detail = build_detail(
            event, environment=environment, occurred_at=clock(), event_id=event_id
        )
        publish(client_factory(), bus, detail)
    except PublicationSkipped as skipped:
        _record(environment, "skipped", str(skipped), event_id)
    except PublicationRejected as rejected:
        _record(environment, "failed", rejected.reason, event_id)
    except ClientError as error:
        code = _safe_code(error.response.get("Error", {}).get("Code"))
        _record(environment, "failed", code or "client-error", event_id)
    except BotoCoreError:
        _record(environment, "failed", "sdk-unavailable", event_id)
    # Trigger boundary: confirmation must never fail because of the event (C2), so an
    # unforeseen error is recorded by category and the original event is still returned.
    except Exception:  # noqa: BLE001
        _record(environment, "failed", "unexpected", event_id)
    else:
        _record(environment, "published", "accepted", event_id)
    return event


def handle(event: dict[str, Any], _context: object) -> dict[str, Any]:
    """Lambda entry point for the PostConfirmation trigger."""
    return process(
        event,
        client_factory=_events_client,
        environment=os.environ.get("ENVIRONMENT", ""),
        bus=os.environ.get("EVENT_BUS_ARN", ""),
        clock=lambda: datetime.now(UTC),
        new_id=lambda: str(uuid.uuid4()),
    )


def _events_client() -> Any:
    global _client
    if _client is None:
        _client = boto3.client("events", config=SDK_CONFIG)
    return _client


def _safe_code(code: object) -> str | None:
    """Provider error codes only (for example ThrottlingException); never a message."""
    if isinstance(code, str) and re.fullmatch(r"[A-Za-z][A-Za-z0-9.]{0,63}", code):
        return code
    return None


def _record(environment: str, result: str, reason: str, event_id: str) -> None:
    """One structured line with an embedded metric; environment is the only dimension."""
    metric = {
        "published": "IdentityEventsPublished",
        "skipped": "IdentityEventsSkipped",
        "failed": "IdentityEventPublishFailures",
    }[result]
    print(
        json.dumps(
            {
                "_aws": {
                    "Timestamp": int(datetime.now(UTC).timestamp() * 1000),
                    "CloudWatchMetrics": [
                        {
                            "Namespace": NAMESPACE,
                            "Dimensions": [["Environment"]],
                            "Metrics": [{"Name": metric, "Unit": "Count"}],
                        }
                    ],
                },
                "Environment": environment if environment in ENVIRONMENTS else "unknown",
                metric: 1,
                "component": "identity-publisher",
                "result": result,
                "reason": reason,
                "eventId": event_id,
            }
        )
    )
