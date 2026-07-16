"""OpenTelemetry setup (dev: logging exporter) and trace-id helpers."""

from __future__ import annotations

import uuid

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
)

_configured = False


def configure_tracing() -> None:
    """Install a console span exporter once (dev default per plan/TRD §14)."""
    global _configured
    if _configured:
        return
    provider = TracerProvider()
    provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
    trace.set_tracer_provider(provider)
    _configured = True


def new_trace_id() -> str:
    """Generate a request trace id."""
    return uuid.uuid4().hex
