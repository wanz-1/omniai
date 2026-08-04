import json
import logging
import uuid
from contextvars import ContextVar
from datetime import datetime, timezone
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
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "service": "omniai-api",
            "message": record.getMessage(),
        }
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
        if record.exc_info and record.exc_info[0]:
            entry["exception"] = self.formatException(record.exc_info)
        if hasattr(record, "extra_fields"):
            entry.update(record.extra_fields)
        return json.dumps(entry, default=str)


class JSONLogger(logging.Logger):
    def _log(
        self,
        level: int,
        msg: object,
        args: tuple[object, ...],
        exc_info: bool | tuple[type[BaseException], BaseException, Any] | None = None,
        extra: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        if extra:
            record = self.makeRecord(
                self.name, level, "", 0, msg, args, exc_info, extra=extra
            )
            record.extra_fields = extra
            self.handle(record)
        else:
            super()._log(level, msg, args, exc_info, **kwargs)


logging.setLoggerClass(JSONLogger)


def setup_logging() -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").handlers = [handler]
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("uvicorn.error").handlers = [handler]

    logging.info("JSON logging initialized", extra={"event": "logging_startup"})
