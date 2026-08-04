import uuid
import os
import tempfile
from pathlib import Path
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import AppError
from app.models.media import VideoJob


class VideoService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def summarize_video(self, video_path: str, language: str = "en") -> dict:
        transcript = await self._extract_transcript(video_path, language)

        import openai
        client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"Summarize the following video transcription. Provide:\n"
                        f"1. Executive summary (2-3 sentences)\n"
                        f"2. Key topics covered (bullet points)\n"
                        f"3. Action items (if any)\n"
                        f"4. Key quotes (if any)\n\n"
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
        import openai
        client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

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
            return transcript if isinstance(transcript, str) else transcript.text
        finally:
            if audio_path:
                Path(audio_path).unlink(missing_ok=True)

    async def _extract_audio(self, video_path: str) -> str:
        try:
            from moviepy import VideoFileClip
        except ImportError:
            try:
                import subprocess
                audio_path = video_path.rsplit(".", 1)[0] + ".mp3"
                result = subprocess.run(
                    ["ffmpeg", "-i", video_path, "-q:a", "0", "-map", "a", audio_path, "-y"],
                    capture_output=True, text=True
                )
                if result.returncode != 0:
                    raise AppError(detail=f"ffmpeg failed: {result.stderr}")
                return audio_path
            except FileNotFoundError:
                raise AppError(detail="ffmpeg not found. Install ffmpeg or moviepy.")

        clip = VideoFileClip(video_path)
        audio_path = video_path.rsplit(".", 1)[0] + ".mp3"
        clip.audio.write_audiofile(audio_path, logger=None)
        clip.close()
        return audio_path

    async def generate_captions(self, video_path: str, language: str = "en") -> dict:
        transcript = await self._extract_transcript(video_path, language)

        import openai
        client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

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
        try:
            from moviepy import VideoFileClip
            clip = VideoFileClip(video_path)
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
            import subprocess
            try:
                result = subprocess.run(
                    ["ffprobe", "-v", "quiet", "-print_format", "json",
                     "-show_format", "-show_streams", video_path],
                    capture_output=True, text=True
                )
                import json
                data = json.loads(result.stdout)
                stream = next((s for s in data.get("streams", []) if s["codec_type"] == "video"), {})
                fmt = data.get("format", {})
                duration = float(fmt.get("duration", 0))

                return {
                    "duration_seconds": duration,
                    "fps": stream.get("avg_frame_rate", "0/0"),
                    "resolution": f"{stream.get('width', '?')}x{stream.get('height', '?')}",
                    "scene_count": max(1, int(duration / 10)),
                }
            except Exception:
                return {"duration_seconds": 0, "error": "Could not analyze video"}

    async def process_video_job(
        self, video_path: str, job_type: str, user_id: uuid.UUID,
        asset_id: uuid.UUID, organization_id: uuid.UUID | None = None
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
                result = await self.summarize_video(video_path)
            elif job_type == "captions":
                result = await self.generate_captions(video_path)
            elif job_type == "analysis":
                result = await self.analyze_scenes(video_path)
            else:
                raise AppError(detail=f"Unknown job type: {job_type}")

            job.output = result
            job.status = "completed"
            job.progress = 100
            job.completed_at = __import__("datetime").datetime.now(__import__("pytz").UTC)
        except Exception as e:
            job.status = "failed"
            job.error = str(e)

        await self.db.flush()
        return job


video_service = VideoService
