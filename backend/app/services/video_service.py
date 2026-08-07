"""
Video processing service.

Fixes:
- Replace __import__ hacks with proper imports.
- Use datetime UTC alias, not pytz.
- Handle missing API keys gracefully.
- Secure subprocess calls with sanitized paths, prevent shell injection.
- Better error handling and type hints.
"""

from __future__ import annotations

import json
import subprocess
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import AppError
from app.models.media import VideoJob


class VideoService:
    def __init__(self, db: AsyncSession):
        self.db = db

    def _get_openai_client(self):
        api_key = settings.openai_api_key
        if not api_key:
            raise AppError(detail="OpenAI API key not configured")
        import openai

        return openai.AsyncOpenAI(api_key=api_key)

    async def summarize_video(self, video_path: str, language: str = "en") -> dict:
        transcript = await self._extract_transcript(video_path, language)
        client = self._get_openai_client()

        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": (
                        "Summarize the following video transcription. Provide:\n"
                        "1. Executive summary (2-3 sentences)\n"
                        "2. Key topics covered (bullet points)\n"
                        "3. Action items (if any)\n"
                        "4. Key quotes (if any)\n\n"
                        f"Transcript:\n{transcript[:100000]}"
                    ),
                }
            ],
            max_tokens=4000,
        )

        return {
            "transcript": transcript,
            "summary": response.choices[0].message.content if response.choices else "",
            "model": "gpt-4o",
        }

    async def _extract_transcript(self, video_path: str, language: str) -> str:
        client = self._get_openai_client()

        audio_path = None
        try:
            audio_path = await self._extract_audio(video_path)
            with open(audio_path, "rb") as audio_file:
                transcript = await client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language=language if language != "auto" else None,
                    response_format="text",
                )
            return transcript if isinstance(transcript, str) else getattr(transcript, "text", str(transcript))
        finally:
            if audio_path:
                try:
                    Path(audio_path).unlink(missing_ok=True)
                except Exception:
                    # Ignore cleanup errors for temp audio file
                    pass  # noqa: S110

    async def _extract_audio(self, video_path: str) -> str:
        """Extract audio from video, using moviepy if available else ffmpeg."""
        # Validate path exists
        vp = Path(video_path)
        if not vp.exists():
            raise AppError(detail=f"Video file not found: {video_path}")

        try:
            from moviepy import VideoFileClip

            clip = VideoFileClip(str(vp))
            audio_path = str(vp.with_suffix(".mp3"))
            clip.audio.write_audiofile(audio_path, logger=None)
            clip.close()
            return audio_path
        except ImportError:
            # Fallback to ffmpeg
            audio_path = str(vp.with_suffix(".mp3"))
            try:
                result = subprocess.run(
                    ["ffmpeg", "-i", str(vp), "-q:a", "0", "-map", "a", audio_path, "-y"],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if result.returncode != 0:
                    raise AppError(detail=f"ffmpeg failed: {result.stderr[:500]}")
                return audio_path
            except FileNotFoundError as exc:
                raise AppError(detail="ffmpeg not found. Install ffmpeg or moviepy.") from exc
        except Exception as e:
            raise AppError(detail=f"Failed to extract audio: {e}") from e

    async def generate_captions(self, video_path: str, language: str = "en") -> dict:
        transcript = await self._extract_transcript(video_path, language)
        client = self._get_openai_client()

        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": (
                        "Format this transcript as SRT subtitles. "
                        "Break into segments of 2-5 seconds each. "
                        f"Return only the SRT format, no explanation.\n\n{transcript[:100000]}"
                    ),
                }
            ],
            max_tokens=8000,
        )

        srt_content = response.choices[0].message.content if response.choices else ""

        return {
            "srt": srt_content,
            "transcript": transcript,
            "language": language,
        }

    async def analyze_scenes(self, video_path: str) -> dict:
        vp = Path(video_path)
        if not vp.exists():
            return {"duration_seconds": 0, "error": "File not found"}

        try:
            from moviepy import VideoFileClip

            clip = VideoFileClip(str(vp))
            duration = clip.duration
            fps = clip.fps
            width, height = clip.size
            clip.close()

            return {
                "duration_seconds": duration,
                "fps": fps,
                "resolution": f"{width}x{height}",
                "scene_count": max(1, int(duration / 10)),
            }
        except ImportError:
            try:
                result = subprocess.run(
                    [
                        "ffprobe",
                        "-v",
                        "quiet",
                        "-print_format",
                        "json",
                        "-show_format",
                        "-show_streams",
                        str(vp),
                    ],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                data = json.loads(result.stdout or "{}")
                stream = next(
                    (s for s in data.get("streams", []) if s.get("codec_type") == "video"),
                    {},
                )
                fmt = data.get("format", {})
                duration = float(fmt.get("duration", 0) or 0)

                return {
                    "duration_seconds": duration,
                    "fps": stream.get("avg_frame_rate", "0/0"),
                    "resolution": f"{stream.get('width', '?')}x{stream.get('height', '?')}",
                    "scene_count": max(1, int(duration / 10)),
                }
            except Exception:
                return {"duration_seconds": 0, "error": "Could not analyze video"}
        except Exception as e:
            return {"duration_seconds": 0, "error": str(e)}

    async def process_video_job(
        self,
        video_path: str,
        job_type: str,
        user_id: uuid.UUID,
        asset_id: uuid.UUID,
        organization_id: uuid.UUID | None = None,
    ) -> VideoJob:
        job = VideoJob(
            user_id=user_id,
            organization_id=organization_id,
            input_asset_id=asset_id,
            job_type=job_type,
            status="processing",
        )
        self.db.add(job)
        await self.db.flush()

        try:
            if job_type == "summary":
                result: dict[str, Any] = await self.summarize_video(video_path)
            elif job_type == "captions":
                result = await self.generate_captions(video_path)
            elif job_type == "analysis":
                result = await self.analyze_scenes(video_path)
            else:
                raise AppError(detail=f"Unknown job type: {job_type}")

            job.output = result
            job.status = "completed"
            job.progress = 100
            job.completed_at = datetime.now(UTC)
        except Exception as e:
            job.status = "failed"
            job.error = str(e)[:2000]

        await self.db.flush()
        return job


video_service = VideoService
