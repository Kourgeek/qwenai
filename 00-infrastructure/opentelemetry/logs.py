"""Structured JSON logging with correlation-ID injection for HyperScale Marketplace.

Provides a ``get_logger`` that returns a ``logging.Logger`` configured with
a JSON formatter which automatically adds ``correlation_id``, ``service_name``,
``span_id``, and ``trace_id`` fields to every log record.

Usage (in a service's main.py or module)::

    from opentelemetry_common.logs import init_logging, get_logger

    init_logging(service_name="order-service", log_level="INFO")
    logger = get_logger(__name__)
    logger.info("Order created", extra={"order_id": order_id})
"""

from __future__ import annotations

import json
import logging
import os
import sys
import time
import uuid
from contextvars import ContextVar
from typing import Any

from opentelemetry import trace

# Context variable that holds the current correlation ID per-request
_correlation_id_ctx: ContextVar[str] = ContextVar("correlation_id", default="")

# ---------------------------------------------------------------------------
# Correlation ID helpers
# ---------------------------------------------------------------------------


def set_correlation_id(correlation_id: str) -> None:
    """Set the correlation ID for the current context (request)."""
    _correlation_id_ctx.set(correlation_id)


def get_correlation_id() -> str:
    """Return the current correlation ID."""
    return _correlation_id_ctx.get() or _generate_correlation_id()


def _generate_correlation_id() -> str:
    """Generate a short random correlation ID."""
    return uuid.uuid4().hex[:16]


def log_correlation_id() -> str:
    """Return the current correlation ID (convenience alias for tracing)."""
    return get_correlation_id()


# ---------------------------------------------------------------------------
# JSON Formatter
# ---------------------------------------------------------------------------


class JsonFormatter(logging.Formatter):
    """JSON log formatter that adds OTel trace context automatically."""

    def __init__(
        self,
        service_name: str = "unknown-service",
        log_level: str = "INFO",
    ):
        super().__init__()
        self.service_name = service_name
        self.log_level = log_level.upper()

    def format(self, record: logging.LogRecord) -> str:
        """Format a log record as a JSON string."""
        # Build base dict
        log_entry: dict[str, Any] = {
            "timestamp": self._format_time(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "service_name": self.service_name,
            "correlation_id": record.correlation_id if hasattr(record, "correlation_id") else get_correlation_id(),
        }

        # OTel trace context
        span = trace.get_current_span()
        ctx = span.get_span_context()
        if ctx.is_valid:
            log_entry["trace_id"] = ctx.trace_id.to_hex()
            log_entry["span_id"] = ctx.span_id.to_hex()
        else:
            log_entry["trace_id"] = ""
            log_entry["span_id"] = ""

        # Extra fields
        if hasattr(record, "extra_fields") and record.extra_fields:
            log_entry.update(record.extra_fields)

        # Exception info
        if record.exc_info and record.exc_info[0] is not None:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "stack_trace": self.formatException(record.exc_info),
            }

        # Additional standard fields
        log_entry["file"] = record.filename
        log_entry["line"] = record.lineno
        log_entry["function"] = record.funcName

        return json.dumps(log_entry, default=str, ensure_ascii=False)

    @staticmethod
    def _format_time(record: logging.LogRecord) -> str:
        """Format timestamp in ISO-8601-like format."""
        dt = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(record.created))
        ms = f".{record.msecs:03d}" if record.msecs else ""
        return dt + ms + "Z"


# ---------------------------------------------------------------------------
# Module-level state
# ---------------------------------------------------------------------------

_service_name: str = "unknown-service"
_log_level: str = "INFO"


# ------------------------------------------------------------------
# Public API
# ------------------------------------------------------------------


def init_logging(
    service_name: str = "unknown-service",
    log_level: str = "INFO",
    log_format: str = "json",  # "json" | "text"
    log_file: str | None = None,
) -> logging.Logger:
    """Initialise structured logging for the service.

    Parameters
    ----------
    service_name:
        Logical service name included in every log record.
    log_level:
        Minimum log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
    log_format:
        Output format: ``json`` (default) or ``text``.
    log_file:
        Optional file path to also write logs to a file.

    Returns
    -------
    The root application logger.
    """
    global _service_name, _log_level
    _service_name = service_name
    _log_level = log_level.upper()

    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, _log_level, logging.INFO))

    # Remove existing handlers to avoid duplicates on re-init
    root_logger.handlers.clear()

    # ── Console handler ───────────────────────────────────────────────
    if log_format == "json":
        formatter = JsonFormatter(service_name=service_name, log_level=_log_level)
    else:
        formatter = logging.Formatter(
            f"%(asctime)s [%(levelname)s] {service_name} %(name)s — %(message)s"
        )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(getattr(logging, _log_level, logging.INFO))
    root_logger.addHandler(console_handler)

    # ── File handler (optional) ───────────────────────────────────────
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_formatter = JsonFormatter(service_name=service_name, log_level=_log_level)
        file_handler.setFormatter(file_formatter)
        file_handler.setLevel(getattr(logging, _log_level, logging.INFO))
        root_logger.addHandler(file_handler)

    # ── Silence noisy OTel / gRPC loggers ─────────────────────────────
    logging.getLogger("opentelemetry").setLevel(logging.WARNING)
    logging.getLogger("grpc").setLevel(logging.WARNING)
    logging.getLogger("google.rpc").setLevel(logging.WARNING)

    return root_logger


def get_logger(name: str | None = None) -> logging.Logger:
    """Return a logger configured for structured logging.

    Parameters
    ----------
    name:
        Logger name (typically ``__name__``).  If ``None``, uses the
        service name as the logger name.

    Returns
    -------
    A ``logging.Logger`` instance.
    """
    logger_name = name or f"{_service_name}.logger"
    logger = logging.getLogger(logger_name)

    # Add correlation_id and trace context to every record
    original_call = logger.makeRecord

    def _make_record_with_context(*args, **kwargs):
        record = original_call(*args, **kwargs)
        record.correlation_id = get_correlation_id()
        # Merge any extra fields passed as 'extra' kwarg
        if kwargs.get("extra"):
            record.extra_fields = kwargs["extra"]
        elif args and len(args) > 5 and isinstance(args[5], dict):
            record.extra_fields = args[5]
        else:
            record.extra_fields = {}
        return record

    logger.makeRecord = _make_record_with_context  # type: ignore[method-assign]
    return logger


def inject_correlation_id(headers: dict[str, str]) -> dict[str, str]:
    """Inject the current correlation ID into *headers*.

    Useful for propagating the correlation ID across service boundaries.
    """
    headers["X-Correlation-Id"] = get_correlation_id()
    return headers


# Expose the service name for metrics
__all__ = [
    "init_logging",
    "get_logger",
    "set_correlation_id",
    "get_correlation_id",
    "log_correlation_id",
    "inject_correlation_id",
]
