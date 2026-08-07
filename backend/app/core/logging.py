"""
Structured JSON logging with request correlation.

Fixes:
- Use UTC alias (datetime.UTC) for modern Python.
- JSONFormatter safely extracts `extra` fields without expecting attribute `extra_fields` on LogRecord.
- JSONLogger._log correctly forwards extra via standard logging mechanism instead of custom attribute hack.
- Avoid duplicate handlers setup.
- Thread-safe context vars.
"""

from __future__ import annotations

import json
import logging
from contextvars import ContextVar
from datetime import UTC, datetime
from typing import Any

request_id_var: ContextVar[str] = ContextVar("request_id", default="")
correlation_id_var: ContextVar[str] = ContextVar("correlation_id", default="")
user_id_var: ContextVar[str] = ContextVar("user_id", default="")
org_id_var: ContextVar[str] = ContextVar("org_id", default="")


def get_request_id() -> str:
    return request_id_var.get()


def set_request_id(rid: str) -> None:
    request_id_var.set(rid)


def set_correlation_id(cid: str) -> None:
    correlation_id_var.set(cid)


def set_user_context(user_id: str = "", org_id: str = "") -> None:
    if user_id:
        user_id_var.set(user_id)
    if org_id:
        org_id_var.set(org_id)


def reset_request_context() -> None:
    request_id_var.set("")
    correlation_id_var.set("")
    user_id_var.set("")
    org_id_var.set("")


class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        entry: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "service": "omniai-api",
            "message": record.getMessage(),
        }

        # Correlation IDs from context vars
        rid = request_id_var.get()
        if rid:
            entry["request_id"] = rid
        cid = correlation_id_var.get()
        if cid:
            entry["correlation_id"] = cid
        uid = user_id_var.get()
        if uid:
            entry["user_id"] = uid
        oid = org_id_var.get()
        if oid:
            entry["org_id"] = oid

        if record.exc_info and record.exc_info[0] is not None:
            entry["exception"] = self.formatException(record.exc_info)

        # Standard way: any extra passed via logger.info(..., extra={...}) is available
        # as attributes on record. We intentionally capture known extra fields from `extra`
        # kwarg style via reserved attribute `extra_data` alternative? Simpler:
        # If caller used `extra={...}`, those keys become attributes on record.
        # We should not log internal logging attributes; filter.
        reserved = {
            "name", "msg", "args", "levelname", "levelno", "pathname",
            "filename", "module", "exc_info", "exc_text", "stack_info",
            "lineno", "funcName", "created", "msecs", "relativeCreated",
            "thread", "threadName", "processName", "process",
        }
        # Include any non-reserved attributes as extra fields
        for k, v in record.__dict__.items():
            if k not in reserved and k not in entry and not k.startswith("_"):
                # Avoid logging large objects that are not JSON serializable gracefully via default=str
                entry[k] = v

        # Backwards compatibility: if old code set `extra_fields` attr, merge it
        extra_fields = getattr(record, "extra_fields", None)
        if isinstance(extra_fields, dict):
            entry.update(extra_fields)

        return json.dumps(entry, default=str)


class JSONLogger(logging.Logger):
    """
    Logger that accepts `extra` dict as keyword and forwards correctly.
    Avoids overriding internal makeRecord logic incorrectly.
    """

    def _log(
        self,
        level: int,
        msg: object,
        args: tuple[object, ...],
        exc_info: bool | tuple[type[BaseException], BaseException, Any] | None = None,
        extra: dict[str, Any] | None = None,
        stack_info: bool = False,
        stacklevel: int = 1,
    ) -> None:
        # Let base class handle extra properly
        super()._log(level, msg, args, exc_info, extra, stack_info, stacklevel)


# Set our logger class globally before any logger creation
logging.setLoggerClass(JSONLogger)


def setup_logging() -> None:
    """Configure root logger to use JSONFormatter exactly once."""
    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())

    root = logging.getLogger()
    # Avoid adding duplicate handlers on reload
    if not any(isinstance(h, logging.StreamHandler) and isinstance(h.formatter, JSONFormatter) for h in root.handlers):
        # Clear default handlers to avoid double logging, then add ours
        # But keep if already configured; simply ensure single JSON handler
        if not root.handlers:
            root.addHandler(handler)
        else:
            # Replace first handler formatter or add if missing
            has_json = False
            for h in root.handlers:
                if isinstance(h.formatter, JSONFormatter):
                    has_json = True
            if not has_json:
                root.addHandler(handler)

    root.setLevel(logging.INFO)

    # Configure uvicorn loggers to use same handler without duplicating
    for name in ("uvicorn.access", "uvicorn.error", "uvicorn"):
        lg = logging.getLogger(name)
        # Avoid duplicate handlers
        if not lg.handlers:
            lg.addHandler(handler)
        lg.setLevel(logging.INFO)
        lg.propagate = False

    logging.info("JSON logging initialized", extra={"event": "logging_startup"})
