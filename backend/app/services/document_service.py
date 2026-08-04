import json
import uuid
from typing import AsyncGenerator

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.document import Document, DocumentVersion
from app.services.prompt_guard import build_user_prompt, wrap_untrusted
from app.schemas.document import (
    GrammarCorrection,
    GrammarResponse,
    HumanizeRequest,
    HumanizeResponse,
    SummarizeRequest,
    SummarizeResponse,
    TranslateRequest,
    TranslateResponse,
)
from app.services.ai_service import ai_service

HUMANIZE_PROMPTS = {
    "academic": (
        "You are an expert academic editor. Rewrite the following text to meet rigorous academic standards. "
        "Use formal scholarly language, precise terminology, and maintain objective tone. "
        "Improve sentence structure for clarity while preserving the original meaning and citations. "
        "Keep the writing at a graduate/postgraduate reading level."
    ),
    "professional": (
        "You are a professional business writer. Rewrite the following text with a polished, "
        "professional tone suitable for corporate communication. Use clear, confident language. "
        "Improve readability while maintaining a formal but approachable style."
    ),
    "business": (
        "You are a business communication expert. Rewrite the following text for a business audience. "
        "Be direct, actionable, and results-oriented. Use industry-appropriate terminology. "
        "Keep sentences concise and impactful."
    ),
    "casual": (
        "You are a conversational writing expert. Rewrite the following text in a friendly, "
        "conversational tone as if speaking to a friend. Use natural language, contractions, "
        "and varied sentence length. Keep it engaging and easy to read."
    ),
    "creative": (
        "You are a creative writing editor. Rewrite the following text with vivid, engaging language. "
        "Use literary devices, varied sentence structure, and evocative vocabulary. "
        "Make the writing compelling and memorable while preserving the core message."
    ),
    "ngo": (
        "You are an NGO communications specialist. Rewrite the following text for a non-profit "
        "and advocacy context. Use compelling, empathetic language that drives action. "
        "Balance emotional appeal with factual credibility. Make it accessible to donors, "
        "partners, and communities."
    ),
    "technical": (
        "You are a technical documentation expert. Rewrite the following text with precision and clarity. "
        "Use correct technical terminology, maintain consistent notation, and structure information "
        "logically. Prioritize accuracy and unambiguous communication."
    ),
}

READABILITY_PROMPT = """Analyze the following text and provide a JSON analysis with:
- "readability_score": Flesch reading ease score (0-100)
- "reading_level": "elementary"|"middle_school"|"high_school"|"college"|"graduate"
- "sentence_complexity": average words per sentence (number)
- "word_diversity": unique word ratio (0-1)
- "paragraph_structure": average sentences per paragraph (number)
- "ai_probability": estimated probability this text was AI-generated (0-100)
- "ai_patterns": list of detected patterns (e.g., "overly uniform sentence length", "repetitive transitions", "lacks personal voice")
- "improvement_suggestions": list of specific suggestions for improvement
- "grammar_issues": count of potential grammar issues found
- "vocabulary_score": estimated vocabulary sophistication (0-100)

Only return valid JSON. No markdown, no explanations.

Text:
"""

GRAMMAR_PROMPT = """You are a grammar expert. Review the following text and identify all grammar, spelling, punctuation, and style issues.
Return a JSON array of corrections. Each correction must have:
- "original": the exact text as written
- "suggestion": the corrected version
- "type": "grammar"|"spelling"|"punctuation"|"style"|"clarity"
- "position": {"start": int, "end": int} character positions in the original text
- "explanation": brief explanation of why this change improves the text
- "severity": "error"|"warning"|"suggestion"

Only return valid JSON array. No markdown.

Text:
"""

TRANSLATION_SYSTEM_PROMPT = """You are a professional translator. Translate the following text accurately while:
1. Preserving the original meaning and nuance
2. Adapting idioms and cultural references appropriately
3. Maintaining the original tone (formal/informal)
4. Keeping formatting (paragraphs, lists) intact
5. Using natural phrasing in the target language

Return ONLY the translated text, no explanations."""


class DocumentService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def humanize(
        self, document_id: uuid.UUID, user_id: uuid.UUID, body: HumanizeRequest
    ) -> HumanizeResponse:
        doc = await self.db.get(Document, document_id)
        if not doc or doc.user_id != user_id:
            raise NotFoundError("Document", str(document_id))

        content = doc.content or ""
        tone_instruction = HUMANIZE_PROMPTS.get(body.tone, HUMANIZE_PROMPTS["professional"])
        audience = body.audience or "general"

        prompt = build_user_prompt(
            f"""{tone_instruction}

Audience: {audience}
Preserve original meaning: {'Yes - keep all facts, data, and citations intact' if body.preserve_meaning else 'Focus on improving while keeping core message'}

Rewritten version (return only the rewritten text, no explanations):""",
            content,
        )

        doc.tone = body.tone
        doc.audience = audience

        if body.stream:
            return HumanizeResponse(
                humanized_content="",
                readability_score=0,
                original_ai_score=0,
                humanized_ai_score=0,
                word_count=0,
                streaming=True,
            )

        response = await ai_service.complete(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            provider=body.ai_provider if hasattr(body, 'ai_provider') else None,
        )

        humanized = response["content"].strip()

        analysis = await self._analyze_text(humanized)
        original_analysis = await self._analyze_text(content)

        doc.humanized_content = humanized
        doc.readability_score = analysis.get("readability_score", 75.0)
        doc.original_ai_score = original_analysis.get("ai_probability", 50.0)
        doc.humanized_ai_score = analysis.get("ai_probability", 15.0)
        doc.word_count = len(humanized.split())

        version = DocumentVersion(
            document_id=doc.id,
            version_number=await self._next_version_number(doc.id),
            content=humanized,
            change_summary=f"Humanized with {body.tone} tone for {audience} audience",
        )
        self.db.add(version)

        changes = await self._compute_changes(content, humanized)

        await self.db.flush()

        return HumanizeResponse(
            humanized_content=humanized,
            readability_score=analysis.get("readability_score", 75.0),
            original_ai_score=original_analysis.get("ai_probability", 50.0),
            humanized_ai_score=analysis.get("ai_probability", 15.0),
            word_count=len(humanized.split()),
            changes_summary=json.dumps(changes),
            reading_level=analysis.get("reading_level", "college"),
            sentence_complexity=analysis.get("sentence_complexity", 0),
            word_diversity=analysis.get("word_diversity", 0),
            ai_patterns=analysis.get("ai_patterns", []),
            improvements=analysis.get("improvement_suggestions", []),
        )

    async def humanize_stream(
        self, document_id: uuid.UUID, user_id: uuid.UUID, body: HumanizeRequest
    ) -> AsyncGenerator[str, None]:
        doc = await self.db.get(Document, document_id)
        if not doc or doc.user_id != user_id:
            raise NotFoundError("Document", str(document_id))

        content = doc.content or ""
        tone_instruction = HUMANIZE_PROMPTS.get(body.tone, HUMANIZE_PROMPTS["professional"])
        audience = body.audience or "general"

        prompt = f"""{tone_instruction}

Audience: {audience}
Preserve original meaning: {'Yes' if body.preserve_meaning else 'Keep core message'}

Original text:
{content}

Rewritten version:"""

        yield json.dumps({"type": "status", "status": "analyzing", "message": "Analyzing document structure..."})
        yield json.dumps({"type": "progress", "progress": 0.2})

        yield json.dumps({"type": "status", "status": "improving", "message": "Improving language and style..."})
        yield json.dumps({"type": "progress", "progress": 0.4})

        async for token in ai_service.complete_stream(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        ):
            yield json.dumps({"type": "token", "content": token})

        yield json.dumps({"type": "status", "status": "finalizing", "message": "Finalizing quality review..."})
        yield json.dumps({"type": "progress", "progress": 0.9})

        full_text = doc.humanized_content or content

        if not doc.humanized_content:
            doc.humanized_content = full_text
            doc.tone = body.tone

            analysis = await self._analyze_text(full_text)
            doc.readability_score = analysis.get("readability_score", 75.0)
            doc.humanized_ai_score = analysis.get("ai_probability", 15.0)
            doc.word_count = len(full_text.split())

            version = DocumentVersion(
                document_id=doc.id,
                version_number=await self._next_version_number(doc.id),
                content=full_text,
                change_summary=f"Humanized with {body.tone} tone",
            )
            self.db.add(version)
            await self.db.flush()

        yield json.dumps({"type": "complete", "status": "complete"})

    async def _analyze_text(self, text: str) -> dict:
        if not text.strip():
            return {
                "readability_score": 0,
                "reading_level": "unknown",
                "sentence_complexity": 0,
                "word_diversity": 0,
                "paragraph_structure": 0,
                "ai_probability": 0,
                "ai_patterns": [],
                "improvement_suggestions": [],
                "grammar_issues": 0,
                "vocabulary_score": 0,
            }

        words = text.split()
        sentences = [s.strip() for s in text.replace("!", ".").replace("?", ".").split(".") if s.strip()]
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

        word_count = len(words)
        sentence_count = max(len(sentences), 1)
        paragraph_count = max(len(paragraphs), 1)

        unique_words = len(set(w.lower().strip(".,!?;:\"'()[]{}") for w in words))
        avg_sentence_length = word_count / sentence_count
        avg_paragraph_length = sentence_count / paragraph_count

        syllable_count = sum(
            max(1, sum(1 for c in w.lower() if c in "aeiou") - w.lower().count("e"))
            for w in words[:100]
        )
        syllable_count = max(syllable_count, 1)

        readability = 206.835 - 1.015 * avg_sentence_length - 84.6 * (syllable_count / max(len(words[:100]), 1))
        readability = max(0, min(100, readability))

        if readability >= 90:
            level = "elementary"
        elif readability >= 60:
            level = "middle_school"
        elif readability >= 50:
            level = "high_school"
        elif readability >= 30:
            level = "college"
        else:
            level = "graduate"

        word_diversity = unique_words / max(word_count, 1)

        try:
            response = await ai_service.complete(
                messages=[{"role": "user", "content": build_user_prompt(READABILITY_PROMPT, text, 3000)}],
                temperature=0.3,
                model="gpt-4o-mini",
                max_tokens=1000,
            )
            ai_analysis = json.loads(response["content"])
            ai_analysis["readability_score"] = readability
            ai_analysis["reading_level"] = level
            return ai_analysis
        except Exception:
            return {
                "readability_score": readability,
                "reading_level": level,
                "sentence_complexity": round(avg_sentence_length, 1),
                "word_diversity": round(word_diversity, 2),
                "paragraph_structure": round(avg_paragraph_length, 1),
                "ai_probability": 50.0,
                "ai_patterns": ["Unable to complete AI pattern analysis"],
                "improvement_suggestions": ["Consider varying sentence length for better flow"],
                "grammar_issues": 0,
                "vocabulary_score": 50.0,
            }

    async def _compute_changes(self, original: str, humanized: str) -> dict:
        return {
            "original_word_count": len(original.split()),
            "humanized_word_count": len(humanized.split()),
            "change_percentage": round(
                abs(len(original.split()) - len(humanized.split()))
                / max(len(original.split()), 1) * 100, 1
            ),
        }

    async def _next_version_number(self, document_id: uuid.UUID) -> int:
        result = await self.db.execute(
            select(DocumentVersion.version_number)
            .where(DocumentVersion.document_id == document_id)
            .order_by(DocumentVersion.version_number.desc())
            .limit(1)
        )
        last = result.scalar()
        return (last or 0) + 1

    async def summarize(
        self, document_id: uuid.UUID, user_id: uuid.UUID, body: SummarizeRequest
    ) -> SummarizeResponse:
        doc = await self.db.get(Document, document_id)
        if not doc or doc.user_id != user_id:
            raise NotFoundError("Document", str(document_id))

        length_map = {"short": "2-3 sentences", "medium": "1 paragraph", "long": "2-3 paragraphs"}
        format_map = {"paragraphs": "paragraphs", "bullets": "bullet points"}

        prompt = build_user_prompt(
            f"""Summarize the following text in {length_map.get(body.length, '1 paragraph')} using {format_map.get(body.format, 'paragraphs')}.
Focus on key points, main arguments, and critical data. Preserve important names, dates, and numbers.""",
            doc.content,
        )

        response = await ai_service.complete(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=1500,
        )

        return SummarizeResponse(summary=response["content"])

    async def translate(
        self, document_id: uuid.UUID, user_id: uuid.UUID, body: TranslateRequest
    ) -> TranslateResponse:
        doc = await self.db.get(Document, document_id)
        if not doc or doc.user_id != user_id:
            raise NotFoundError("Document", str(document_id))

        content = doc.humanized_content or doc.content or ""

        prompt = build_user_prompt(
            f"""{TRANSLATION_SYSTEM_PROMPT}

Translate to: {body.target_language}

Translation:""",
            content,
        )

        response = await ai_service.complete(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=4096,
        )

        return TranslateResponse(
            translated_content=response["content"],
            source_language=doc.language,
            target_language=body.target_language,
        )

    async def check_grammar(self, document_id: uuid.UUID, user_id: uuid.UUID) -> GrammarResponse:
        doc = await self.db.get(Document, document_id)
        if not doc or doc.user_id != user_id:
            raise NotFoundError("Document", str(document_id))

        content = doc.humanized_content or doc.content or ""

        prompt = build_user_prompt(GRAMMAR_PROMPT, content, 5000)

        response = await ai_service.complete(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            model="gpt-4o-mini",
            max_tokens=3000,
        )

        try:
            corrections_data = json.loads(response["content"])
            corrections = [
                GrammarCorrection(**c) for c in corrections_data
            ]
        except (json.JSONDecodeError, Exception):
            corrections = [
                GrammarCorrection(
                    original="",
                    suggestion="Grammar analysis unavailable",
                    type="info",
                    position={"start": 0, "end": 0},
                    explanation="Could not parse grammar results",
                    severity="info",
                )
            ]

        return GrammarResponse(corrections=corrections)

    async def save_version(
        self, document_id: uuid.UUID, user_id: uuid.UUID, content: str, change_summary: str = ""
    ) -> DocumentVersion:
        doc = await self.db.get(Document, document_id)
        if not doc or doc.user_id != user_id:
            raise NotFoundError("Document", str(document_id))

        version = DocumentVersion(
            document_id=doc.id,
            version_number=await self._next_version_number(doc.id),
            content=content,
            change_summary=change_summary or f"Manual save v{await self._next_version_number(doc.id)}",
        )
        self.db.add(version)
        doc.content = content
        await self.db.flush()
        return version

    async def get_versions(self, document_id: uuid.UUID, user_id: uuid.UUID) -> list[DocumentVersion]:
        doc = await self.db.get(Document, document_id)
        if not doc or doc.user_id != user_id:
            raise NotFoundError("Document", str(document_id))

        result = await self.db.execute(
            select(DocumentVersion)
            .where(DocumentVersion.document_id == document_id)
            .order_by(DocumentVersion.created_at.desc())
        )
        return result.scalars().all()

    async def restore_version(
        self, document_id: uuid.UUID, user_id: uuid.UUID, version_id: uuid.UUID
    ) -> Document:
        doc = await self.db.get(Document, document_id)
        if not doc or doc.user_id != user_id:
            raise NotFoundError("Document", str(document_id))

        version = await self.db.get(DocumentVersion, version_id)
        if not version or version.document_id != document_id:
            raise NotFoundError("Version", str(version_id))

        new_version = DocumentVersion(
            document_id=doc.id,
            version_number=await self._next_version_number(doc.id),
            content=version.content,
            change_summary=f"Restored from version {version.version_number}",
        )
        self.db.add(new_version)

        doc.content = version.content
        doc.humanized_content = version.content
        await self.db.flush()
        return doc
