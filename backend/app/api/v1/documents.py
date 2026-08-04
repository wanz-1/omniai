import json
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.core.exceptions import NotFoundError
from app.models.document import Document, DocumentVersion
from app.models.user import User
from app.schemas.document import (
    DocumentCreateRequest,
    DocumentResponse,
    DocumentUpdateRequest,
    DocumentVersionResponse,
    ExportRequest,
    GrammarResponse,
    HumanizeRequest,
    HumanizeResponse,
    SummarizeRequest,
    SummarizeResponse,
    TranslateRequest,
    TranslateResponse,
)

router = APIRouter()


@router.get("", response_model=list[DocumentResponse])
async def list_documents(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    project_id: uuid.UUID | None = None,
):
    query = select(Document).where(Document.user_id == current_user.id)
    if project_id:
        query = query.where(Document.project_id == project_id)
    query = query.order_by(Document.updated_at.desc())
    result = await db.execute(query)
    return result.scalars().all()


@router.post("", response_model=DocumentResponse)
async def create_document(
    body: DocumentCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    doc = Document(
        title=body.title,
        content=body.content,
        content_type=body.content_type,
        project_id=body.project_id,
        user_id=current_user.id,
    )
    db.add(doc)
    await db.flush()
    return doc


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    project_id: uuid.UUID | None = None,
):
    from app.services.file_service import FileService
    content = await file.read()
    text, doc_type = await FileService.parse_file(file.filename or "untitled", content)

    doc = Document(
        title=file.filename or "Untitled",
        content=text,
        content_type=doc_type,
        project_id=project_id,
        user_id=current_user.id,
        file_size=len(content),
    )
    db.add(doc)
    await db.flush()
    return doc


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    doc = await db.get(Document, document_id)
    if not doc or doc.user_id != current_user.id:
        raise NotFoundError("Document", str(document_id))
    return doc


@router.put("/{document_id}", response_model=DocumentResponse)
async def update_document(
    document_id: uuid.UUID,
    body: DocumentUpdateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    doc = await db.get(Document, document_id)
    if not doc or doc.user_id != current_user.id:
        raise NotFoundError("Document", str(document_id))

    if body.title is not None:
        doc.title = body.title
    if body.content is not None:
        doc.content = body.content
    await db.flush()
    return doc


@router.delete("/{document_id}")
async def delete_document(
    document_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    doc = await db.get(Document, document_id)
    if not doc or doc.user_id != current_user.id:
        raise NotFoundError("Document", str(document_id))
    await db.delete(doc)
    await db.flush()
    return {"message": "Document deleted"}


@router.post("/{document_id}/humanize", response_model=HumanizeResponse)
async def humanize_document(
    document_id: uuid.UUID,
    body: HumanizeRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    from app.services.document_service import DocumentService
    service = DocumentService(db)
    result = await service.humanize(document_id, current_user.id, body)
    return result


@router.post("/{document_id}/humanize/stream")
async def humanize_document_stream(
    document_id: uuid.UUID,
    body: HumanizeRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    from app.services.document_service import DocumentService
    service = DocumentService(db)
    body.stream = True

    async def event_generator():
        async for event in service.humanize_stream(document_id, current_user.id, body):
            yield f"data: {event}\n\n"
        yield "data: {\"type\": \"done\"}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/{document_id}/analyze")
async def analyze_document(
    document_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    doc = await db.get(Document, document_id)
    if not doc or doc.user_id != current_user.id:
        raise NotFoundError("Document", str(document_id))

    from app.services.document_service import DocumentService
    service = DocumentService(db)
    content = doc.humanized_content or doc.content or ""
    analysis = await service._analyze_text(content)
    return analysis


@router.post("/{document_id}/summarize", response_model=SummarizeResponse)
async def summarize_document(
    document_id: uuid.UUID,
    body: SummarizeRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    from app.services.document_service import DocumentService
    service = DocumentService(db)
    result = await service.summarize(document_id, current_user.id, body)
    return result


@router.post("/{document_id}/translate", response_model=TranslateResponse)
async def translate_document(
    document_id: uuid.UUID,
    body: TranslateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    from app.services.document_service import DocumentService
    service = DocumentService(db)
    result = await service.translate(document_id, current_user.id, body)
    return result


@router.post("/{document_id}/grammar", response_model=GrammarResponse)
async def check_grammar(
    document_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    from app.services.document_service import DocumentService
    service = DocumentService(db)
    result = await service.check_grammar(document_id, current_user.id)
    return result


@router.get("/{document_id}/versions", response_model=list[DocumentVersionResponse])
async def get_versions(
    document_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    from app.services.document_service import DocumentService
    service = DocumentService(db)
    versions = await service.get_versions(document_id, current_user.id)
    return versions


@router.post("/{document_id}/versions/save", response_model=DocumentVersionResponse)
async def save_version(
    document_id: uuid.UUID,
    body: dict,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    from app.services.document_service import DocumentService
    service = DocumentService(db)
    version = await service.save_version(
        document_id, current_user.id,
        body.get("content", ""),
        body.get("change_summary", ""),
    )
    return version


@router.post("/{document_id}/versions/{version_id}/restore", response_model=DocumentResponse)
async def restore_version(
    document_id: uuid.UUID,
    version_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    from app.services.document_service import DocumentService
    service = DocumentService(db)
    doc = await service.restore_version(document_id, current_user.id, version_id)
    return doc


@router.post("/{document_id}/export")
async def export_document(
    document_id: uuid.UUID,
    body: ExportRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    from app.services.file_service import FileService
    doc = await db.get(Document, document_id)
    if not doc or doc.user_id != current_user.id:
        raise NotFoundError("Document", str(document_id))
    content = doc.humanized_content or doc.content or ""
    file_bytes, media_type = await FileService.export_file(content, body.format)
    from fastapi.responses import Response
    return Response(
        content=file_bytes,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{doc.title}.{body.format}"'},
    )
