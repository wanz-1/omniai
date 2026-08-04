"""Document pipeline integration tests.

Covers the document lifecycle beyond the create/list basics in
``test_documents.py``: ownership enforcement, versioning (save/list/restore),
the AI text-processing pipeline (humanize/summarize/translate/grammar/analyze)
with the AI provider mocked, upload/export, and the security services that
guard document content (file scanning + PII redaction), which were previously
at 0% coverage.

Finding: ``python-magic`` is not installed in the test env, so
``FileSecurityService._detect_mime`` fails closed to ``application/octet-stream``
and every scan is rejected. Tests patch ``_detect_mime`` for deterministic
behavior; one env-guarded test documents the fail-closed fallback.
"""
import json
import uuid
from importlib.util import find_spec
from unittest.mock import AsyncMock, patch

import pytest

from app.core.dependencies import get_current_user
from app.models.document import Document, DocumentVersion
from app.models.user import User
from app.services.ai_service import ai_service

PASSWORD = "TestPassword123!"


async def _create_doc(client, title="Pipeline Doc", content="Original content for the document pipeline."):
    resp = await client.post(
        "/api/v1/documents",
        json={"title": title, "content": content},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


# ═══════════════════════════════════════════════════════════════════════════
# CRUD + OWNERSHIP
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
@pytest.mark.asyncio
async def test_document_crud_lifecycle(auth_client):
    client, _db, _user, _headers, _refresh = auth_client
    doc = await _create_doc(client)

    fetched = await client.get(f"/api/v1/documents/{doc['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["title"] == "Pipeline Doc"

    updated = await client.put(
        f"/api/v1/documents/{doc['id']}",
        json={"title": "Renamed", "content": "Updated body"},
    )
    assert updated.status_code == 200
    assert updated.json()["title"] == "Renamed"
    assert updated.json()["content"] == "Updated body"

    listed = await client.get("/api/v1/documents")
    assert listed.status_code == 200
    assert any(d["id"] == doc["id"] and d["title"] == "Renamed" for d in listed.json())

    deleted = await client.delete(f"/api/v1/documents/{doc['id']}")
    assert deleted.status_code == 200
    gone = await client.get(f"/api/v1/documents/{doc['id']}")
    assert gone.status_code == 404


@pytest.mark.integration
@pytest.mark.asyncio
async def test_document_ownership_enforced_across_users(stateful_client):
    import app.main as main_mod
    client, db = stateful_client

    first = User(email="owner@example.com", display_name="Owner", is_verified=True)
    second = User(email="intruder@example.com", display_name="Intruder", is_verified=True)
    db.add(first)
    db.add(second)

    main_mod.app.dependency_overrides[get_current_user] = lambda: first
    created = await client.post(
        "/api/v1/documents", json={"title": "Private", "content": "secret body"}
    )
    assert created.status_code == 200, created.text
    doc_id = created.json()["id"]

    main_mod.app.dependency_overrides[get_current_user] = lambda: second
    assert (await client.get(f"/api/v1/documents/{doc_id}")).status_code == 404
    assert (await client.put(
        f"/api/v1/documents/{doc_id}", json={"title": "Hijacked"}
    )).status_code == 404
    assert (await client.delete(f"/api/v1/documents/{doc_id}")).status_code == 404

    main_mod.app.dependency_overrides[get_current_user] = lambda: first
    assert (await client.get(f"/api/v1/documents/{doc_id}")).status_code == 200


# ═══════════════════════════════════════════════════════════════════════════
# VERSIONING  (save / list / restore)
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
@pytest.mark.asyncio
async def test_version_save_list_restore_roundtrip(auth_client):
    client, db, _user, _headers, _refresh = auth_client
    doc = await _create_doc(client, content="Draft v1")

    v1 = await client.post(
        f"/api/v1/documents/{doc['id']}/versions/save",
        json={"content": "Draft v1", "change_summary": "initial draft"},
    )
    assert v1.status_code == 200, v1.text
    assert v1.json()["version_number"] == 1

    await client.put(f"/api/v1/documents/{doc['id']}", json={"content": "Draft v2"})
    v2 = await client.post(
        f"/api/v1/documents/{doc['id']}/versions/save",
        json={"content": "Draft v2", "change_summary": "second pass"},
    )
    assert v2.json()["version_number"] == 2

    versions = (await client.get(f"/api/v1/documents/{doc['id']}/versions")).json()
    assert sorted(v["version_number"] for v in versions) == [1, 2]
    assert any(v["change_summary"] == "initial draft" for v in versions)

    restored = await client.post(
        f"/api/v1/documents/{doc['id']}/versions/{v1.json()['id']}/restore"
    )
    assert restored.status_code == 200, restored.text
    assert restored.json()["content"] == "Draft v1"

    stored = db.find(Document, id=uuid.UUID(doc["id"]))
    assert stored.content == "Draft v1"
    assert stored.humanized_content == "Draft v1"
    versions = (await client.get(f"/api/v1/documents/{doc['id']}/versions")).json()
    assert sorted(v["version_number"] for v in versions) == [1, 2, 3]
    assert any("Restored from version 1" in v["change_summary"] for v in versions)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_restore_version_from_another_document_returns_404(auth_client):
    client, _db, _user, _headers, _refresh = auth_client
    doc_a = await _create_doc(client, title="Doc A")
    doc_b = await _create_doc(client, title="Doc B")

    v_a = await client.post(
        f"/api/v1/documents/{doc_a['id']}/versions/save", json={"content": "A content"}
    )
    assert v_a.status_code == 200
    version_id = v_a.json()["id"]

    resp = await client.post(f"/api/v1/documents/{doc_b['id']}/versions/{version_id}/restore")
    assert resp.status_code == 404


# ═══════════════════════════════════════════════════════════════════════════
# AI TEXT PIPELINE  (humanize / summarize / translate / grammar / analyze)
# ═══════════════════════════════════════════════════════════════════════════

def _mock_ai(response_payload: dict):
    return patch.object(
        ai_service, "complete",
        new=AsyncMock(return_value={"content": response_payload, "tokens_used": 10}),
    )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_humanize_updates_document_and_creates_version(auth_client):
    client, db, _user, _headers, _refresh = auth_client
    doc = await _create_doc(client)

    with _mock_ai("This is the polished professional version of the text."):
        resp = await client.post(
            f"/api/v1/documents/{doc['id']}/humanize",
            json={"tone": "professional", "audience": "executives", "stream": False},
        )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["humanized_content"] == "This is the polished professional version of the text."
    assert data["streaming"] is False

    stored = db.find(Document, id=uuid.UUID(doc["id"]))
    assert stored.humanized_content == data["humanized_content"]
    assert stored.tone == "professional"
    assert stored.audience == "executives"
    assert stored.word_count == len(data["humanized_content"].split())

    versions = [v for v in db.objects_of(DocumentVersion) if v.document_id == uuid.UUID(doc["id"])]
    assert versions, "Humanize should record a version"
    assert versions[0].version_number == 1


@pytest.mark.integration
@pytest.mark.asyncio
async def test_humanize_unknown_document_returns_404(auth_client):
    client, _db, _user, _headers, _refresh = auth_client
    resp = await client.post(
        f"/api/v1/documents/{'00000000-0000-0000-0000-000000000000'}/humanize",
        json={"tone": "professional", "stream": False},
    )
    assert resp.status_code == 404


@pytest.mark.integration
@pytest.mark.asyncio
async def test_summarize_document(auth_client):
    client, _db, _user, _headers, _refresh = auth_client
    doc = await _create_doc(client)

    with _mock_ai("Key findings: the pipeline works end to end."):
        resp = await client.post(
            f"/api/v1/documents/{doc['id']}/summarize",
            json={"length": "short", "format": "bullets"},
        )
    assert resp.status_code == 200, resp.text
    assert resp.json()["summary"] == "Key findings: the pipeline works end to end."


@pytest.mark.integration
@pytest.mark.asyncio
async def test_translate_document(auth_client):
    client, _db, _user, _headers, _refresh = auth_client
    doc = await _create_doc(client)

    with _mock_ai("Ceci est la version traduite."):
        resp = await client.post(
            f"/api/v1/documents/{doc['id']}/translate",
            json={"target_language": "fr"},
        )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["translated_content"] == "Ceci est la version traduite."
    assert data["source_language"] == "en"
    assert data["target_language"] == "fr"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_grammar_check_parses_corrections(auth_client):
    client, _db, _user, _headers, _refresh = auth_client
    doc = await _create_doc(client, content="He go to the store yesterday.")

    corrections = [
        {"original": "He go", "suggestion": "He went", "type": "grammar",
         "position": {"start": 0, "end": 6}, "explanation": "Past tense",
         "severity": "error"},
    ]
    with _mock_ai(json.dumps(corrections)):
        resp = await client.post(f"/api/v1/documents/{doc['id']}/grammar")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert len(data["corrections"]) == 1
    assert data["corrections"][0]["original"] == "He go"
    assert data["corrections"][0]["suggestion"] == "He went"
    assert data["corrections"][0]["severity"] == "error"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_grammar_invalid_json_falls_back_to_info(auth_client):
    client, _db, _user, _headers, _refresh = auth_client
    doc = await _create_doc(client)

    with _mock_ai("this is definitely not json"):
        resp = await client.post(f"/api/v1/documents/{doc['id']}/grammar")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["corrections"]
    assert data["corrections"][0]["severity"] == "info"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_analyze_empty_document_returns_zero_scores(auth_client):
    client, _db, _user, _headers, _refresh = auth_client
    doc = await _create_doc(client, content="")

    with patch.object(ai_service, "complete", new=AsyncMock(side_effect=RuntimeError("no AI"))):
        resp = await client.post(f"/api/v1/documents/{doc['id']}/analyze")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["readability_score"] == 0
    assert data["reading_level"] == "unknown"


# ═══════════════════════════════════════════════════════════════════════════
# UPLOAD + EXPORT
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
@pytest.mark.asyncio
async def test_upload_txt_document(auth_client):
    client, _db, _user, _headers, _refresh = auth_client
    content = b"Uploaded plain text content.\nSecond line."

    resp = await client.post(
        "/api/v1/documents/upload",
        files={"file": ("notes.txt", content, "text/plain")},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["content"] == content.decode("utf-8")
    assert data["file_size"] == len(content)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_export_document_as_txt(auth_client):
    client, _db, _user, _headers, _refresh = auth_client
    doc = await _create_doc(client, content="Export me please.")

    resp = await client.post(
        f"/api/v1/documents/{doc['id']}/export", json={"format": "txt"}
    )
    assert resp.status_code == 200, resp.text
    assert resp.headers["content-type"].startswith("text/plain")
    assert resp.content.decode("utf-8") == "Export me please."


# ═══════════════════════════════════════════════════════════════════════════
# FILE SECURITY SERVICE
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
@pytest.mark.asyncio
async def test_scan_file_accepts_allowed_mime():
    from app.services.file_security import FileSecurityService
    svc = FileSecurityService()
    with patch.object(svc, "_detect_mime", return_value="text/plain"):
        result = await svc.scan_file("notes.txt", b"hello world")
    assert result.allowed is True
    assert result.detected_mime == "text/plain"
    assert result.reason == ""


@pytest.mark.integration
@pytest.mark.asyncio
async def test_scan_file_rejects_banned_extension():
    from app.services.file_security import FileSecurityService
    svc = FileSecurityService()
    result = await svc.scan_file("malware.exe", b"MZ...")
    assert result.allowed is False
    assert ".exe" in result.reason


@pytest.mark.integration
@pytest.mark.asyncio
async def test_scan_file_rejects_oversized():
    from app.services.file_security import FileSecurityService
    svc = FileSecurityService()
    with patch("app.services.file_security.MAX_FILE_SIZE_BYTES", 10):
        result = await svc.scan_file("big.txt", b"x" * 11)
    assert result.allowed is False
    assert "exceeds maximum size" in result.reason


@pytest.mark.integration
@pytest.mark.asyncio
async def test_scan_file_rejects_unallowed_mime():
    from app.services.file_security import FileSecurityService
    svc = FileSecurityService()
    with patch.object(svc, "_detect_mime", return_value="application/x-msdownload"):
        result = await svc.scan_file("tool.bin", b"data")
    assert result.allowed is False
    assert "not allowed" in result.reason


@pytest.mark.integration
@pytest.mark.asyncio
async def test_scan_file_sanitizes_control_characters():
    from app.services.file_security import FileSecurityService
    svc = FileSecurityService()
    with patch.object(svc, "_detect_mime", return_value="text/plain"):
        result = await svc.scan_file("clean.txt", b"ok\x00\x1fdata")
    assert result.allowed is True
    assert b"\x00" not in result.sanitized_data
    assert result.sanitized_data == b"okdata"


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.skipif(
    find_spec("magic") is not None,
    reason="python-magic installed: detection returns real MIME types",
)
async def test_scan_file_fails_closed_when_magic_unavailable():
    """Documents the fail-closed fallback when the MIME detector is missing."""
    from app.services.file_security import FileSecurityService
    svc = FileSecurityService()
    result = await svc.scan_file("notes.txt", b"plain text")
    assert result.allowed is False
    assert result.detected_mime == "application/octet-stream"


# ═══════════════════════════════════════════════════════════════════════════
# DATA PROTECTION SERVICE  (PII redaction / encryption)
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
@pytest.mark.asyncio
async def test_scan_detects_and_redacts_sensitive_data():
    from app.services.data_protection import DataProtectionService
    svc = DataProtectionService()
    text = (
        "Contact jane.doe@example.com or 555-123-4567. SSN 123-45-6789 "
        "and card 4111 1111 1111 1111."
    )
    result = svc.scan_for_sensitive_data(text)
    assert result.has_sensitive_data is True
    assert result.patterns_found.get("email") == 1
    assert result.patterns_found.get("ssn") == 1
    assert "[REDACTED_EMAIL]" in result.redacted_text
    assert "[REDACTED_SSN]" in result.redacted_text
    assert "jane.doe@example.com" not in result.redacted_text


@pytest.mark.integration
@pytest.mark.asyncio
async def test_validate_for_ai_redacts_and_returns_warnings():
    from app.services.data_protection import data_protection
    redacted, warnings = await data_protection.validate_for_ai(
        "Call 5551234567 now"
    )
    assert "5551234567" not in redacted
    assert warnings and "phone" in warnings[0]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_encrypt_decrypt_roundtrip():
    from app.services.data_protection import data_protection
    ciphertext = data_protection.encrypt("top-secret-content")
    assert ciphertext != "top-secret-content"
    assert data_protection.decrypt(ciphertext) == "top-secret-content"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_mask_helpers():
    from app.services.data_protection import data_protection
    assert data_protection.mask_email("jane.doe@example.com") == "j****e@example.com"
    assert data_protection.mask_phone("+1 (555) 123-4567").endswith("4567")
    assert "*" in data_protection.mask_phone("+1 (555) 123-4567")
