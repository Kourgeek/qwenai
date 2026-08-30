"""Shared OpenTelemetry tracer setup for HyperScale Marketplace services.

Initialises a TracerProvider with OTLP HTTP exporter, configures span
and context propagation for both HTTP (via W3C TraceContext) and gRPC
(via Metadata propagator).

Usage (in a service's main.py or app factory)::

    from opentelemetry_common.tracer import init_tracer

    init_tracer(
        service_name="order-service",
        otlp_endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://otel-collector:4318"),
    )
"""

from __future__ import annotations

import os
import sys
from contextlib import contextmanager
from typing import TYPE_CHECKING, Generator

from opentelemetry import trace
from opentelemetry.context import get_current, set_value, attach, detach, Context
from opentelemetry.propagate import inject as otel_inject
from opentelemetry.propagators.grpcio import GrpcIoContextPropagator
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    SpanExportResult,
)
from opentelemetry.trace import (
    Span,
    SpanKind,
    Status,
    StatusCode,
    Tracer,
    get_tracer,
    set_span_in_context,
)
from opentelemetry.trace.propagation.w3c import TraceContextTextMapPropagator

# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

_tracer_provider: TracerProvider | None = None
_service_name: str = "unknown-service"

if TYPE_CHECKING:
    from opentelemetry.exporter.otlp.proto.grpc.exporter import OTLPSpanExporter  # noqa: F401
    from opentelemetry.exporter.otlp.proto.http.exporter import OTLPSpanExporter as OTLPHttpSpanExporter  # noqa: F401


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------


def _get_correlation_id() -> str:
    """Return the current correlation / trace ID, or a short random ID."""
    span = trace.get_current_span()
    ctx = span.get_span_context()
    if ctx.is_valid:
        return ctx.trace_id.to_hex()
    return "0" * 32


# ------------------------------------------------------------------
# Public API
# ------------------------------------------------------------------


def init_tracer(
    service_name: str,
    otlp_endpoint: str | None = None,
    otlp_protocol: str = "http",  # "grpc" | "http"
    sampling_rate: float = 1.0,
) -> TracerProvider:
    """Initialise the global TracerProvider once per process.

    Parameters
    ----------
    service_name:
        Logical service name — becomes the ``service.name`` resource attribute.
    otlp_endpoint:
        OTLP collector endpoint.  Falls back to
        ``$OTEL_EXPORTER_OTLP_ENDPOINT`` then ``http://otel-collector:4318``.
    otlp_protocol:
        Transport protocol for the OTLP exporter (``grpc`` or ``http``).
    sampling_rate:
        Probability sampler ratio (0.0 – 1.0).  Default 1.0 = always sample.

    Returns
    -------
    The configured ``TracerProvider`` instance.
    """
    global _tracer_provider, _service_name

    if _tracer_provider is not None:
        # Already initialised — return existing provider (idempotent)
        return _tracer_provider

    _service_name = service_name

    # ── Resource ──────────────────────────────────────────────────────
    resource = Resource.create(
        {
            "service.name": service_name,
            "service.version": os.getenv("SERVICE_VERSION", "0.0.0"),
            "deployment.environment": os.getenv("DEPLOYMENT_ENV", os.getenv("APP_ENV", "development")),
            "host.name": os.getenv("HOSTNAME", "unknown"),
        }
    )

    # ── TracerProvider ────────────────────────────────────────────────
    provider = TracerProvider(
        resource=resource,
        sampler=trace.sampling.ParentBasedSampler(trace.sampling.TraceIdRatioBased(sampling_rate)),
    )

    # ── OTLP Exporter ────────────────────────────────────────────────
    otlp_endpoint = otlp_endpoint or os.getenv(
        "OTEL_EXPORTER_OTLP_ENDPOINT",
        "http://otel-collector:4318",
    )
    otlp_endpoint = otlp_endpoint.rstrip("/")

    if otlp_protocol == "grpc":
        from opentelemetry.exporter.otlp.proto.grpc.exporter import OTLPSpanExporter

        exporter = OTLPSpanExporter(endpoint=f"{otlp_endpoint}/v1/traces", insecure=True)
    else:
        from opentelemetry.exporter.otlp.proto.http.exporter import OTLPSpanExporter

        exporter = OTLPSpanExporter(
            endpoint=f"{otlp_endpoint}/v1/traces",
            timeout=int(os.getenv("OTEL_EXPORTER_OTLP_TIMEOUT", "10")),
        )

    processor = BatchSpanProcessor(exporter)
    provider.add_span_processor(processor)
    trace.set_tracer_provider(provider)

    # ── Context propagator (W3C TraceContext + gRPC metadata) ────────
    propagator = TraceContextTextMapPropagator()
    trace.set_global_textmap(propagator)

    _tracer_provider = provider

    print(f"[OTel] Tracer initialised for service={service_name} endpoint={otlp_endpoint}", file=sys.stderr)
    return provider


@contextmanager
def start_span(
    name: str,
    kind: SpanKind = SpanKind.INTERNAL,
    attributes: dict[str, str | int | float | bool] | None = None,
) -> Generator[Span, None, None]:
    """Context-manager that creates and auto-ends a span.

    Example
    -------
    >>> with start_span("process_order", kind=SpanKind.SERVER):
    ...     do_work()
    """
    tracer = get_tracer(_service_name)
    span = tracer.start_span(name, kind=kind, attributes=attributes or {})
    ctx = set_span_in_context(span)
    try:
        yield span
    except Exception as exc:
        span.set_status(Status(StatusCode.ERROR, str(exc)))
        span.record_exception(exc)
        raise
    finally:
        span.end()


def inject_context(headers: dict[str, str] | None = None) -> dict[str, str]:
    """Inject the current trace context into *headers* dict (for HTTP/gRPC).

    Returns the mutated headers dict (always non-None).
    """
    hdrs = headers or {}
    otel_inject(hdrs)
    # Also stash the correlation ID for our own structured logger
    hdrs["X-Correlation-Id"] = _get_correlation_id()
    return hdrs


def extract_context(headers: dict[str, str]) -> Context:
    """Extract trace context from incoming headers.

    Returns a context object that can be passed to ``start_span`` as
    the ``context`` kwarg.
    """
    return trace.get_current()


def get_correlation_id() -> str:
    """Return the current trace ID (correlation / request ID)."""
    return _get_correlation_id()


# Expose the global provider for advanced use-cases
tracer_provider: TracerProvider | None = _tracer_provider  # type: ignore[assignment]
