"""Exact verified-caller rate windows in the platform-owned PlatformRateWindows table.

Each counter item covers one environment, one HMAC-protected subject, one counter and one
server-clock minute. Its key names the minute, so a new minute is always a new item: delayed
TTL deletion can never reopen a window, and the admission condition never reads the expiry.
Every counter a request needs (a transfer also charges the recipient-lookup budget) is charged
in one DynamoDB transaction, so they are consumed together or not at all.

While a rotated HMAC key is present, every counter is charged under every held key version, so
the previous key's counters keep governing the window in which the rotation happens.

Items hold only the protected key, a count and an expiry: no sub, profile, request key or money
data.
"""

from __future__ import annotations

import hashlib
import hmac
import math
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any

from botocore.exceptions import BotoCoreError, ClientError

WINDOW_SECONDS = 60
# TTL is cleanup only; it is set two hours after the window ends.
RETENTION_SECONDS = 7200
LIMITS = {"recipient_lookup": 30, "transfer": 10, "other": 60}
POLICIES: dict[str, tuple[str, ...]] = {
    "recipient_lookup": ("recipient_lookup",),
    "transfer": ("transfer", "recipient_lookup"),
    "other": ("other",),
}
_ROUTES = {
    ("POST", "/money/v1/recipients/resolve"): "recipient_lookup",
    ("POST", "/money/v1/transfers"): "transfer",
}
_DERIVATION_LABEL = b"raad-platform-rate-limit-v1"
_RETRYABLE = {
    "TransactionConflictException",
    "ProvisionedThroughputExceededException",
    "ThrottlingException",
    "RequestLimitExceeded",
}
_ENVIRONMENTS = frozenset({"dev", "stg", "prd"})


class RateStoreUnavailable(RuntimeError):
    """The counters could not be read or charged; the caller must fail closed (503)."""


@dataclass(frozen=True, slots=True)
class Decision:
    admitted: bool
    retry_after: int


def classify(method: str, path: str) -> str:
    """Exact C1 operations get their own budget; every other request shares 'other'."""
    return _ROUTES.get((method, path), "other")


def protected_subject(key: bytes, environment: str, subject: str) -> str:
    """Domain-separated HMAC-SHA256 of the verified subject; the raw sub is never stored."""
    derived = hmac.new(key, _DERIVATION_LABEL, hashlib.sha256).digest()
    message = environment.encode() + b"\x00" + subject.encode()
    return hmac.new(derived, message, hashlib.sha256).hexdigest()


def counter_key(environment: str, counter: str, window: int, version: str, protected: str) -> str:
    return f"{environment}#{counter}#{window}#{version}#{protected}"


class RateLimiter:
    """Charges one request's counters atomically; bounded attempts on contention."""

    def __init__(
        self,
        client: Any,
        table: str,
        environment: str,
        keys: Sequence[tuple[str, bytes]],
        *,
        clock: Callable[[], float] = time.time,
        sleep: Callable[[float], None] = time.sleep,
        max_attempts: int = 3,
    ) -> None:
        if environment not in _ENVIRONMENTS or not table:
            raise ValueError("rate store configuration is invalid")
        if not keys or any(not version or not key for version, key in keys):
            raise ValueError("rate key material is unavailable")
        if not 1 <= max_attempts <= 5:
            raise ValueError("attempts must be bounded")
        self.client, self.table, self.environment = client, table, environment
        self.keys = tuple(keys)
        self.clock, self.sleep, self.max_attempts = clock, sleep, max_attempts

    def consume(self, subject: str, policy: str) -> Decision:
        if not isinstance(subject, str) or not 1 <= len(subject) <= 256:
            raise ValueError("a verified subject is required")
        counters = POLICIES[policy]
        attempt = 0
        while True:
            attempt += 1
            now = self.clock()
            window = int(now // WINDOW_SECONDS)
            retry_after = max(1, math.ceil((window + 1) * WINDOW_SECONDS - now))
            try:
                self.client.transact_write_items(
                    TransactItems=self._items(subject, counters, window)
                )
                return Decision(True, retry_after)
            except ClientError as error:
                if _quota_refused(error):
                    return Decision(False, retry_after)
                if not _retryable(error) or attempt >= self.max_attempts:
                    raise RateStoreUnavailable(_code(error)) from error
            except BotoCoreError as error:
                raise RateStoreUnavailable("transport") from error
            self.sleep(0.01 * attempt)

    def _items(self, subject: str, counters: Sequence[str], window: int) -> list[dict[str, Any]]:
        expires = (window + 1) * WINDOW_SECONDS + RETENTION_SECONDS
        items = []
        for counter in counters:
            for version, key in self.keys:
                protected = protected_subject(key, self.environment, subject)
                items.append(
                    {
                        "Update": {
                            "TableName": self.table,
                            "Key": {
                                "pk": {
                                    "S": counter_key(
                                        self.environment, counter, window, version, protected
                                    )
                                }
                            },
                            "UpdateExpression": (
                                "SET #count = if_not_exists(#count, :zero) + :one, "
                                "#expires = :expires"
                            ),
                            "ConditionExpression": (
                                "attribute_not_exists(#count) OR #count < :limit"
                            ),
                            "ExpressionAttributeNames": {
                                "#count": "count",
                                "#expires": "expiresAt",
                            },
                            "ExpressionAttributeValues": {
                                ":zero": {"N": "0"},
                                ":one": {"N": "1"},
                                ":limit": {"N": str(LIMITS[counter])},
                                ":expires": {"N": str(expires)},
                            },
                        }
                    }
                )
        return items


def _code(error: ClientError) -> str:
    return str(error.response.get("Error", {}).get("Code", "unknown"))


def _reasons(error: ClientError) -> set[str]:
    reasons = error.response.get("CancellationReasons") or []
    return {str(reason.get("Code", "None")) for reason in reasons if isinstance(reason, dict)}


def _quota_refused(error: ClientError) -> bool:
    """A failed admission condition on any counter is a definitive quota refusal."""
    return _code(error) == "TransactionCanceledException" and "ConditionalCheckFailed" in _reasons(
        error
    )


def _retryable(error: ClientError) -> bool:
    if _code(error) in _RETRYABLE:
        return True
    reasons = _reasons(error) - {"None"}
    return (
        _code(error) == "TransactionCanceledException"
        and bool(reasons)
        and reasons
        <= {
            "TransactionConflict",
            "ThrottlingError",
            "ProvisionedThroughputExceeded",
        }
    )
