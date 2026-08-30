"""Shared OpenTelemetry metrics setup for HyperScale Marketplace services.

Initialises a MeterProvider with Prometheus exposition reader (for scraping)
and registers common counters, histograms, and gauges that every service
can reuse.

Usage (in a service's main.py)::

    from opentelemetry_common.metrics import init_metrics, get_metrics

    init_metrics(service_name="order-service", port=9090)
    metrics = get_metrics()
    metrics.http_requests_total.labels(method="GET", path="/health").inc()
"""

from __future__ import annotations

import os
import sys
from typing import TYPE_CHECKING

from opentelemetry import metrics
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource

if TYPE_CHECKING:
    from prometheus_client import generate_latest  # noqa: F401


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

_meter_provider: MeterProvider | None = None
_meter: metrics.Meter | None = None
_prometheus_reader: PrometheusMetricReader | None = None

# Pre-created common metrics — populated on first access
_http_requests_total: metrics.Counter | None = None
_http_request_duration: metrics.Histogram | None = None
_db_query_duration: metrics.Histogram | None = None
_db_queries_total: metrics.Counter | None = None
_grpc_calls_total: metrics.Counter | None = None
_grpc_call_duration: metrics.Histogram | None = None
_kafka_messages_total: metrics.Counter | None = None
_kafka_message_size: metrics.Histogram | None = None


# ------------------------------------------------------------------
# Public API
# ------------------------------------------------------------------


def init_metrics(
    service_name: str,
    prometheus_port: int = 9090,
    otlp_endpoint: str | None = None,
) -> MeterProvider:
    """Initialise the global MeterProvider.

    Parameters
    ----------
    service_name:
        Logical service name.
    prometheus_port:
        Port for the Prometheus /metrics HTTP endpoint.
    otlp_endpoint:
        OTLP collector endpoint for remote metrics (optional).
        Falls back to ``$OTEL_EXPORTER_OTLP_METRICS_ENDPOINT``.

    Returns
    -------
    The configured ``MeterProvider``.
    """
    global _meter_provider, _meter, _prometheus_reader

    if _meter_provider is not None:
        return _meter_provider

    resource = Resource.create(
        {
            "service.name": service_name,
            "service.version": os.getenv("SERVICE_VERSION", "0.0.0"),
            "deployment.environment": os.getenv("DEPLOYMENT_ENV", os.getenv("APP_ENV", "development")),
        }
    )

    # ── Prometheus reader (local scraping) ────────────────────────────
    _prometheus_reader = PrometheusMetricReader()
    readers = [_prometheus_reader]

    # ── OTLP remote exporter (optional) ───────────────────────────────
    otlp_endpoint = otlp_endpoint or os.getenv(
        "OTEL_EXPORTER_OTLP_METRICS_ENDPOINT",
        os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://otel-collector:4318"),
    ).rstrip("/")

    if otlp_endpoint:
        from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter

        remote_reader = PeriodicExportingMetricReader(
            exporter=OTLPMetricExporter(endpoint=otlp_endpoint, insecure=True),
            export_interval_ms=int(os.getenv("OTEL_METRIC_EXPORT_INTERVAL", "15000")),
        )
        readers.append(remote_reader)

    _meter_provider = MeterProvider(resource=resource, metric_readers=readers)
    metrics.set_meter_provider(_meter_provider)

    _meter = _meter_provider.get_meter(service_name, version="0.1.0")

    # ── Pre-create common instruments ─────────────────────────────────
    _http_requests_total = _meter.create_counter(
        name="http_requests_total",
        unit="1",
        description="Total number of HTTP requests",
    )

    _http_request_duration = _meter.create_histogram(
        name="http_request_duration_seconds",
        unit="s",
        description="HTTP request duration in seconds",
    )

    _db_query_duration = _meter.create_histogram(
        name="db_query_duration_seconds",
        unit="s",
        description="Database query duration in seconds",
    )

    _db_queries_total = _meter.create_counter(
        name="db_queries_total",
        unit="1",
        description="Total number of database queries",
    )

    _grpc_calls_total = _meter.create_counter(
        name="grpc_calls_total",
        unit="1",
        description="Total number of gRPC calls",
    )

    _grpc_call_duration = _meter.create_histogram(
        name="grpc_call_duration_seconds",
        unit="s",
        description="gRPC call duration in seconds",
    )

    _kafka_messages_total = _meter.create_counter(
        name="kafka_messages_total",
        unit="1",
        description="Total number of Kafka messages published/consumed",
    )

    _kafka_message_size = _meter.create_histogram(
        name="kafka_message_size_bytes",
        unit="By",
        description="Size of Kafka messages in bytes",
    )

    print(f"[OTel] Metrics initialised for service={service_name} prometheus_port={prometheus_port}", file=sys.stderr)
    return _meter_provider


def get_metrics() -> dict:
    """Return a dict-like namespace of pre-created metrics.

    Each metric is keyed by its short name and carries the underlying
    OpenTelemetry instrument object.
    """
    return {
        "http_requests_total": _http_requests_total,
        "http_request_duration": _http_request_duration,
        "db_query_duration": _db_query_duration,
        "db_queries_total": _db_queries_total,
        "grpc_calls_total": _grpc_calls_total,
        "grpc_call_duration": _grpc_call_duration,
        "kafka_messages_total": _kafka_messages_total,
        "kafka_message_size": _kafka_message_size,
    }


def get_meter() -> metrics.Meter:
    """Return the service-specific Meter instance."""
    return _meter or metrics.get_meter(_service_name or "unknown", version="0.1.0")


# Internal reference for the service name (used by metrics)
_service_name: str = "unknown-service"


def _set_service_name(name: str) -> None:
    """Internal: set the service name for metrics (called by init_metrics)."""
    global _service_name
    _service_name = name
