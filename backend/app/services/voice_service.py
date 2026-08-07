import tempfile
import uuid
from collections.abc import AsyncGenerator
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import AppError
from app.models.media import VoiceMessage, VoiceSession


class VoiceService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_session(
        self, user_id: uuid.UUID, organization_id: uuid.UUID | None = None,
        agent_id: uuid.UUID | None = None, language: str = "en"
    ) -> VoiceSession:
        session = VoiceSession(
            user_id=user_id,
            organization_id=organization_id,
            agent_id=agent_id,
            language=language,
        )
        self.db.add(session)
        await self.db.flush()
        return session

    async def end_session(self, session_id: uuid.UUID) -> VoiceSession:
        session = await self.db.get(VoiceSession, session_id)
        if not session:
            raise AppError(detail="Voice session not found")
        session.status = "ended"
        await self.db.flush()
        return session

    async def transcribe_audio(
        self, audio_data: bytes, mime_type: str = "audio/webm",
        language: str | None = None
    ) -> dict:
        provider = settings.VOICE_STT_PROVIDER or "whisper"
        if provider == "deepgram":
            return await self._transcribe_deepgram(audio_data, mime_type, language)
        return await self._transcribe_whisper(audio_data, mime_type, language)

    async def _transcribe_whisper(
        self, audio_data: bytes, mime_type: str, language: str | None
    ) -> dict:
        import openai
        client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

        suffix = ".webm"
        if "wav" in mime_type:
            suffix = ".wav"
        elif "mp3" in mime_type or "mpeg" in mime_type:
            suffix = ".mp3"
        elif "ogg" in mime_type:
            suffix = ".ogg"

        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(audio_data)
            tmp_path = tmp.name

        try:
            with open(tmp_path, "rb") as audio_file:
                kwargs = {"model": "whisper-1", "file": audio_file, "response_format": "verbose_json"}
                if language:
                    kwargs["language"] = language
                transcript = await client.audio.transcriptions.create(**kwargs)

            return {
                "text": transcript.text,
                "confidence": getattr(transcript, "confidence", None),
                "language": getattr(transcript, "language", language or "en"),
                "duration_ms": int(getattr(transcript, "duration", 0) * 1000) if hasattr(transcript, "duration") else None,
                "segments": [s.dict() for s in transcript.segments] if hasattr(transcript, "segments") else [],
                "provider": "whisper",
            }
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    async def _transcribe_deepgram(
        self, audio_data: bytes, mime_type: str, language: str | None
    ) -> dict:
        try:
            from deepgram import DeepgramClient, PrerecordedOptions
            client = DeepgramClient(settings.DEEPGRAM_API_KEY)

            payload = {"buffer": audio_data, "mimetype": mime_type}
            options = PrerecordedOptions(model="nova-2", smart_format=True, language=language or "en")
            response = await client.listen.asyncrest.v("1").transcribe(payload, options)

            channel = response.results.channels[0] if response.results.channels else None
            alternatives = channel.alternatives[0] if channel and channel.alternatives else None

            return {
                "text": alternatives.transcript if alternatives else "",
                "confidence": alternatives.confidence if alternatives else None,
                "language": language or "en",
                "duration_ms": int(response.results.metadata.duration * 1000) if response.results.metadata else None,
                "words": [w.dict() for w in alternatives.words] if alternatives and alternatives.words else [],
                "provider": "deepgram",
            }
        except ImportError:
            return {"text": "", "error": "Deepgram SDK not installed", "provider": "deepgram"}

    async def synthesize_speech(
        self, text: str, voice: str = "alloy", language: str = "en"
    ) -> bytes:
        provider = settings.VOICE_TTS_PROVIDER or "openai"
        if provider == "elevenlabs":
            return await self._synthesize_elevenlabs(text, voice, language)
        return await self._synthesize_openai(text, voice)

    async def _synthesize_openai(self, text: str, voice: str) -> bytes:
        import openai
        client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

        response = await client.audio.speech.create(
            model="tts-1",
            voice=voice,
            input=text,
            response_format="mp3",
        )
        return response.content

    async def _synthesize_elevenlabs(self, text: str, voice: str, language: str) -> bytes:
        try:
            from elevenlabs import generate
            audio = generate(text=text, voice=voice, model="eleven_multilingual_v2", language=language)
            if isinstance(audio, bytes):
                return audio
            if isinstance(audio, AsyncGenerator):
                chunks = []
                async for chunk in audio:
                    chunks.append(chunk)
                return b"".join(chunks)
            return b""
        except ImportError:
            return b""

    async def process_voice_message(
        self, session_id: uuid.UUID, audio_data: bytes,
        mime_type: str = "audio/webm", language: str | None = None
    ) -> VoiceMessage:
        transcript = await self.transcribe_audio(audio_data, mime_type, language)
        text = transcript.get("text", "")

        session = await self.db.get(VoiceSession, session_id)
        if session:
            existing = session.transcription or []
            existing.append({"role": "user", "text": text, "confidence": transcript.get("confidence")})
            session.transcription = existing

        message = VoiceMessage(
            session_id=session_id,
            role="user",
            text=text,
            confidence=transcript.get("confidence"),
            language=transcript.get("language"),
            meta_data={"transcript": transcript},
        )
        self.db.add(message)
        await self.db.flush()
        return message

    async def generate_voice_response(
        self, session_id: uuid.UUID, agent_response: str, voice: str = "alloy"
    ) -> VoiceMessage:
        audio_bytes = await self.synthesize_speech(agent_response, voice=voice)

        from app.services.storage_service import StorageService
        storage = StorageService()
        audio_url = await storage.save_audio(audio_bytes, f"voice_resp_{uuid.uuid4()}.mp3")

        message = VoiceMessage(
            session_id=session_id,
            role="assistant",
            text=agent_response,
            audio_url=audio_url,
        )
        self.db.add(message)
        await self.db.flush()
        return message

    async def get_session_messages(self, session_id: uuid.UUID) -> list[VoiceMessage]:
        result = await self.db.execute(
            select(VoiceMessage).where(VoiceMessage.session_id == session_id)
            .order_by(VoiceMessage.created_at.asc())
        )
        return result.scalars().all()


voice_service = VoiceService
