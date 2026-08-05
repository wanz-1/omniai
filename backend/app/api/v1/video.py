import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.core.exceptions import NotFoundError
from app.models.media import VideoJob, MediaAsset
from app.models.user import User
from app.schemas.video import VideoJobResponse, VideoJobCreateResponse
from app.services.video_service import VideoService

router = APIRouter()


@router.post("/process", response_model=VideoJobCreateResponse)
async def process_video(
    file: UploadFile = File(...),
    job_type: str = Form("summary"),
    current_user: Annotated[User, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    video_data = await file.read()
    import tempfile
    import os
    suffix = os.path.splitext(file.filename or "video.mp4")[1] or ".mp4"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(video_data)
        tmp_path = tmp.name

    from app.services.storage_service import StorageService
    storage = StorageService()
    storage_key = f"videos/{uuid.uuid4()}{suffix}"
    await storage.save_file(storage_key, video_data)

    asset = MediaAsset(
        user_id=current_user.id,
        asset_type="video",
        mime_type=file.content_type or "video/mp4",
        storage_key=storage_key,
        size_bytes=len(video_data),
    )
    db.add(asset)
    await db.flush()

    svc = VideoService(db)
    job = await svc.process_video_job(
        video_path=tmp_path,
        job_type=job_type,
        user_id=current_user.id,
        asset_id=asset.id,
        organization_id=None,
    )

    import os as _os
    _os.unlink(tmp_path)

    return VideoJobCreateResponse(
        job_id=job.id,
        asset_id=asset.id,
        status=job.status,
        job_type=job.job_type,
        output=job.output,
    )


@router.get("/jobs", response_model=list[VideoJobResponse])
async def list_jobs(
    current_user: Annotated[User, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    result = await db.execute(
        select(VideoJob).where(VideoJob.user_id == current_user.id)
        .order_by(VideoJob.created_at.desc())
    )
    return result.scalars().all()


@router.get("/jobs/{job_id}", response_model=VideoJobResponse)
async def get_job(
    job_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    job = await db.get(VideoJob, job_id)
    if not job:
        raise NotFoundError("VideoJob", str(job_id))
    return job
