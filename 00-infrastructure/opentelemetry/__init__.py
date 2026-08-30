"""Common OpenTelemetry instrumentation package for HyperScale Marketplace.

Provides shared tracer, metrics, logging, and gRPC/HTTP instrumentation
that every service can import without duplicating setup code.
"""

from .tracer import init_tracer, get_tracer, tracer_provider
from .logs import init_logging, get_logger, log_correlation_id
from .metrics import init_metrics, get_metrics, metrics_reader

__all__ = [
    "init_tracer",
    "get_tracer",
    "tracer_provider",
    "init_logging",
    "get_logger",
    "log_correlation_id",
    "init_metrics",
    "get_metrics",
    "metrics_reader",
]
