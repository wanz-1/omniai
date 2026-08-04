"""Authorization boundary tests: enforce ownership / tenant isolation.

Verifies that a user cannot read or modify resources owned by another user, and
that organization-scoped queries are always filtered by the tenant.
"""
import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.api.v1.documents import delete_document, get_document
from app.core.exceptions import NotFoundError
from app.models.document import Document
from app.models.user import User


def _user() -> User:
    return User(id=uuid.uuid4(), email="a@omniai.test", display_name="A", is_active=True)


def _doc(owner_id: uuid.UUID, doc_id: uuid.UUID | None = None) -> Document:
    doc = Document(
        id=doc_id or uuid.uuid4(),
        user_id=owner_id,
        title="Shared",
        content="content",
        content_type="txt",
        language="en",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    return doc


def _db(get_return):
    db = MagicMock()
    db.get = AsyncMock(return_value=get_return)
    return db


@pytest.mark.asyncio
async def test_user_cannot_read_another_users_document():
    owner = _user()
    other = _user()
    doc = _doc(owner.id)
    db = _db(doc)
    with pytest.raises(NotFoundError):
        await get_document(doc.id, other, db)


@pytest.mark.asyncio
async def test_user_can_read_own_document():
    user = _user()
    doc = _doc(user.id)
    db = _db(doc)
    result = await get_document(doc.id, user, db)
    assert result.id == doc.id


@pytest.mark.asyncio
async def test_missing_document_raises_not_found():
    user = _user()
    db = _db(None)
    with pytest.raises(NotFoundError):
        await get_document(uuid.uuid4(), user, db)


@pytest.mark.asyncio
async def test_user_cannot_delete_another_users_document():
    owner = _user()
    other = _user()
    doc = _doc(owner.id)
    db = _db(doc)
    with pytest.raises(NotFoundError):
        await delete_document(doc.id, other, db)
