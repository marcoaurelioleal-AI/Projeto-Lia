from __future__ import annotations

import logging
import time
import uuid
from collections import Counter, deque
from datetime import UTC, datetime
from threading import Lock
from typing import Any

from fastapi import Request

from ..config import settings
from ..database import engine
from .audit_service import record_request_audit

logger = logging.getLogger("projeto_lia.request")
STARTED_AT = datetime.now(UTC)


class RequestMetrics:
    def __init__(self) -> None:
        self._lock = Lock()
        self._total_requests = 0
        self._error_requests = 0
        self._status_counts: Counter[str] = Counter()
        self._path_counts: Counter[str] = Counter()
        self._latencies_ms: deque[int] = deque(maxlen=500)
        self._last_request_at: datetime | None = None

    def observe(self, *, path: str, status_code: int, duration_ms: int) -> None:
        with self._lock:
            self._total_requests += 1
            if status_code >= 500:
                self._error_requests += 1
            self._status_counts[str(status_code)] += 1
            self._path_counts[path] += 1
            self._latencies_ms.append(duration_ms)
            self._last_request_at = datetime.now(UTC)

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            latencies = sorted(self._latencies_ms)
            average_latency = round(sum(latencies) / len(latencies), 2) if latencies else 0.0
            p95_latency = float(latencies[int((len(latencies) - 1) * 0.95)]) if latencies else 0.0
            return {
                "total_requests": self._total_requests,
                "error_requests": self._error_requests,
                "average_latency_ms": average_latency,
                "p95_latency_ms": p95_latency,
                "by_status": dict(self._status_counts),
                "by_path": dict(self._path_counts.most_common(20)),
                "last_request_at": self._last_request_at,
            }


request_metrics = RequestMetrics()


async def request_observability_middleware(request: Request, call_next):
    request_id = request.headers.get("x-request-id") or uuid.uuid4().hex
    request.state.request_id = request_id
    started = time.perf_counter()

    try:
        response = await call_next(request)
    except Exception:
        duration_ms = _duration_ms(started)
        request_metrics.observe(path=request.url.path, status_code=500, duration_ms=duration_ms)
        logger.exception(
            "request_failed",
            extra={"request_id": request_id, "method": request.method, "path": request.url.path},
        )
        raise

    duration_ms = _duration_ms(started)
    request_metrics.observe(path=request.url.path, status_code=response.status_code, duration_ms=duration_ms)
    response.headers["X-Request-ID"] = request_id
    logger.info(
        "request_completed",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": duration_ms,
        },
    )
    record_request_audit(request, status_code=response.status_code, duration_ms=duration_ms, request_id=request_id)
    return response


def build_observability_status() -> dict[str, Any]:
    return {
        "status": "ok",
        "service": settings.app_name,
        "environment": settings.app_env,
        "database": engine.url.get_backend_name(),
        "storage_provider": settings.storage_provider,
        "started_at": STARTED_AT,
        "request_metrics": request_metrics.snapshot(),
    }


def _duration_ms(started: float) -> int:
    return round((time.perf_counter() - started) * 1000)
