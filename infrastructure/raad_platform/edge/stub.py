"""Dev-only nonfinancial stub service attached by its own path mapping (NFR13.10).

It shows that a new service can be mapped next to /money without changing MoneyService or C1.
It answers one read-only path, applies the same constant-time origin check as the money edge,
reads no token, touches no money data and logs nothing about the caller. Outside dev it refuses
every request even if it were ever deployed there.
"""

from __future__ import annotations

import json
import os
from typing import Any

from raad_platform.edge import handler

PING_PATH = "/stub/v1/ping"


def _reply(status: int, body: dict[str, str], correlation: str) -> dict[str, Any]:
    return {
        "statusCode": status,
        "headers": {
            "content-type": "application/json",
            "x-correlation-id": correlation,
            "cache-control": "no-store",
        },
        "body": json.dumps(body),
    }


def entry(event: dict[str, Any], _context: object) -> dict[str, Any]:
    rejected = handler._origin_rejection(event)
    if rejected is not None:
        return rejected
    correlation = handler._correlation(event.get("headers") or {})
    method = event.get("requestContext", {}).get("http", {}).get("method", "").upper()
    is_ping = method == "GET" and event.get("rawPath") == PING_PATH
    if os.environ.get("ENVIRONMENT") == "dev" and is_ping:
        return _reply(
            200, {"service": "platform-stub", "environment": "dev", "status": "ok"}, correlation
        )
    return _reply(
        404,
        {
            "code": "NOT_FOUND",
            "message": "The requested path does not exist.",
            "correlationId": correlation,
        },
        correlation,
    )
