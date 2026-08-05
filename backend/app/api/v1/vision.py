import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.core.exceptions import NotFoundError
from app.models.media import MediaAsset
from app.models.user import User
from app.schemas.vision import (
    AnalyzeImageResponse,
    OCRResponse,
    MediaAssetResponse,
    ScanDocumentResponse,
)
from app.services.vision_service import VisionService

router = APIRouter()


@router.post("/analyze", response_model=AnalyzeImageResponse)
async def analyze_image(
    file: UploadFile = File(...),
    prompt: str = Form("Describe this image in detail."),
    current_user: Annotated[User, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    image_data = await file.read()
    svc = VisionService(db)
    result = await svc.analyze_image(image_data, prompt, file.content_type or "image/png")
    return result


@router.post("/ocr", response_model=OCRResponse)
async def extract_ocr(
    file: UploadFile = File(...),
    current_user: Annotated[User, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    image_data = await file.read()
    svc = VisionService(db)
    result = await svc.extract_ocr(image_data, file.content_type or "image/png")
    return result


@router.post("/scan", response_model=ScanDocumentResponse)
async def scan_document(
    file: UploadFile = File(...),
    current_user: Annotated[User, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    image_data = await file.read()
    svc = VisionService(db)
    result = await svc.scan_document(image_data, file.content_type or "image/png")
    return result


@router.get("/assets", response_model=list[MediaAssetResponse])
async def list_assets(
    asset_type: str | None = None,
    current_user: Annotated[User, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    query = select(MediaAsset).where(MediaAsset.user_id == current_user.id)
    if asset_type:
        query = query.where(MediaAsset.asset_type == asset_type)
    query = query.order_by(MediaAsset.created_at.desc())
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/assets/{asset_id}", response_model=MediaAssetResponse)
async def get_asset(
    asset_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    asset = await db.get(MediaAsset, asset_id)
    if not asset:
        raise NotFoundError("MediaAsset", str(asset_id))
    return asset


@router.delete("/assets/{asset_id}")
async def delete_asset(
    asset_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    asset = await db.get(MediaAsset, asset_id)
    if not asset:
        raise NotFoundError("MediaAsset", str(asset_id))
    await db.delete(asset)
    return {"message": "Asset deleted"}
