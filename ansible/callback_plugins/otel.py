from __future__ import annotations
import logging
import os
from ansible.plugins.callback import CallbackBase

from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from opentelemetry._logs import set_logger_provider
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor

CALLBACK_VERSION = 2.0
CALLBACK_TYPE = 'notification'
CALLBACK_NAME = 'otel'

# OpenTelemetry setup
_service_name = os.getenv("OTEL_SERVICE_NAME", "ansible-playbook")
_resource = Resource.create({"service.name": _service_name})

# Tracing
_tracer_provider = TracerProvider(resource=_resource)
trace.set_tracer_provider(_tracer_provider)
_span_exporter = OTLPSpanExporter(
    endpoint=os.getenv("OTEL_EXPORTER_OTLP_TRACES_ENDPOINT", "http://localhost:4318/v1/traces"),
    insecure=True,
)
_tracer_provider.add_span_processor(BatchSpanProcessor(_span_exporter))
_tracer = trace.get_tracer(__name__)

# Logs
_logger_provider = LoggerProvider(resource=_resource)
set_logger_provider(_logger_provider)
_log_exporter = OTLPLogExporter(
    endpoint=os.getenv("OTEL_EXPORTER_OTLP_LOGS_ENDPOINT", "http://localhost:4318/v1/logs"),
    insecure=True,
)
_logger_provider.add_log_record_processor(BatchLogRecordProcessor(_log_exporter))
_handler = LoggingHandler(level=logging.INFO, logger_provider=_logger_provider)
_logger = logging.getLogger("ansible.otel")
_logger.setLevel(logging.INFO)
_logger.addHandler(_handler)


class CallbackModule(CallbackBase):
    def __init__(self):
        super().__init__()
        self._task_spans = {}
        self._play_span = None

    def v2_playbook_on_start(self, playbook):
        self._play_span = _tracer.start_span(
            "playbook",
            attributes={"playbook.file": getattr(playbook, "_file_name", "unknown")},
        )
        _logger.info("playbook_start", extra={"playbook.file": getattr(playbook, "_file_name", "unknown")})

    def v2_playbook_on_task_start(self, task, is_conditional):
        name = task.get_name().strip()
        span = _tracer.start_span(
            f"task:{name}",
            attributes={
                "task.name": name,
                "task.action": getattr(task, "action", "unknown"),
            },
        )
        self._task_spans[task._uuid] = span
        _logger.info("task_start", extra={"task.name": name, "task.action": getattr(task, "action", "unknown")})

    def _end_task(self, result, status: str):
        task = result._task
        host = result._host.get_name()
        name = task.get_name().strip()
        span = self._task_spans.pop(task._uuid, None)
        if span is not None:
            span.set_attribute("task.status", status)
            span.set_attribute("host.name", host)
            if status == "failed":
                span.set_status(Status(StatusCode.ERROR))
                span.record_exception(Exception(str(result._result)))
            span.end()
        _logger.info("task_end", extra={"task.name": name, "host.name": host, "task.status": status})

    def v2_runner_on_ok(self, result):
        self._end_task(result, "ok")

    def v2_runner_on_failed(self, result, ignore_errors=False):
        self._end_task(result, "failed")

    def v2_runner_on_skipped(self, result):
        self._end_task(result, "skipped")

    def v2_playbook_on_stats(self, stats):
        if self._play_span is not None:
            try:
                self._play_span.set_attribute("stats.ok", sum(stats.ok.values()))
                self._play_span.set_attribute("stats.failures", sum(stats.failures.values()))
                self._play_span.set_attribute("stats.skipped", sum(stats.skipped.values()))
                self._play_span.set_attribute("stats.unreachable", sum(stats.dark.values()))
            finally:
                self._play_span.end()
        _logger.info(
            "playbook_end",
            extra={
                "stats.ok": sum(stats.ok.values()),
                "stats.failures": sum(stats.failures.values()),
                "stats.skipped": sum(stats.skipped.values()),
                "stats.unreachable": sum(stats.dark.values()),
            },
        )
