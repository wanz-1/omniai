"""Unit tests for the agent ToolExecutor tool implementations.

Covers the previously-placeholder document_read/document_write, email, and
crm tools, including workspace sandboxing and validation paths.
"""
import json
import uuid

import pytest

from app.models.agent import AgentTool
from app.services.agent_service import ToolExecutor


def _tool(tool_type: str, config: dict | None = None) -> AgentTool:
    return AgentTool(
        id=uuid.uuid4(),
        name=tool_type,
        tool_type=tool_type,
        description=f"{tool_type} tool",
        config=config or {},
        enabled=True,
        agent_id=uuid.uuid4(),
    )


async def test_document_write_then_read(tmp_path, monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "agent_workspace_dir", str(tmp_path))
    executor = ToolExecutor()

    written = await executor.execute(_tool("document_write"), {"path": "notes/plan.txt", "content": "hello world"})
    assert "Document written" in written

    read = await executor.execute(_tool("document_read"), {"path": "notes/plan.txt"})
    assert read == "hello world"


async def test_document_read_missing_returns_notice(tmp_path, monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "agent_workspace_dir", str(tmp_path))
    result = await ToolExecutor().execute(_tool("document_read"), {"path": "missing.txt"})
    assert "not found" in result


async def test_document_tools_block_path_traversal(tmp_path, monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "agent_workspace_dir", str(tmp_path))
    executor = ToolExecutor()

    read = await executor.execute(_tool("document_read"), {"path": "../secret.txt"})
    assert "Permission denied" in read

    written = await executor.execute(_tool("document_write"), {"path": "../../escape.txt", "content": "x"})
    assert "Permission denied" in written


async def test_email_queued_when_smtp_unconfigured(tmp_path, monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "smtp_host", None)
    result = await ToolExecutor().execute(
        _tool("email"),
        {"to": "user@example.com", "subject": "Hi", "body": "Body"},
    )
    assert "queued" in result and "user@example.com" in result


async def test_email_rejects_invalid_recipient(tmp_path, monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "smtp_host", None)
    result = await ToolExecutor().execute(_tool("email"), {"to": "not-an-email", "subject": "Hi"})
    assert "valid recipient" in result


async def test_crm_add_contact_requires_name_and_email(tmp_path, monkeypatch):
    result = await ToolExecutor().execute(_tool("crm"), {"action": "add_contact"})
    assert "required" in result


async def test_crm_unsupported_action(tmp_path, monkeypatch):
    result = await ToolExecutor().execute(_tool("crm"), {"action": "delete_all"})
    assert "unsupported" in result


async def test_crm_valid_action_returns_json(tmp_path, monkeypatch):
    result = await ToolExecutor().execute(
        _tool("crm"),
        {"action": "add_contact", "name": "Ada", "email": "ada@example.com"},
    )
    payload = json.loads(result)
    assert payload["status"] == "ok"
    assert payload["email"] == "ada@example.com"
