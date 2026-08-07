import base64
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.media import MediaAsset, OCRResult


class VisionService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def analyze_image(
        self, image_data: bytes | str, prompt: str = "Describe this image in detail.",
        mime_type: str = "image/png"
    ) -> dict:
        import openai
        client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

        if isinstance(image_data, bytes):
            image_b64 = base64.b64encode(image_data).decode("utf-8")
            data_uri = f"data:{mime_type};base64,{image_b64}"
        else:
            data_uri = image_data

        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": data_uri, "detail": "high"}},
                    ],
                }
            ],
            max_tokens=2000,
        )

        content = response.choices[0].message.content if response.choices else ""

        return {
            "description": content,
            "model": "gpt-4o",
            "tokens": response.usage.total_tokens if response.usage else 0,
        }

    async def extract_ocr(self, image_data: bytes, mime_type: str = "image/png") -> dict:
        import openai
        client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

        image_b64 = base64.b64encode(image_data).decode("utf-8")
        data_uri = f"data:{mime_type};base64,{image_b64}"

        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "content": (
                                "Extract all text from this image. Return ONLY the raw text "
                                "with no explanation. Preserve formatting, numbers, and structure. "
                                "If the image contains a table, format it as markdown."
                            ),
                        },
                        {"type": "image_url", "image_url": {"url": data_uri, "detail": "high"}},
                    ],
                }
            ],
            max_tokens=4000,
        )

        raw_text = response.choices[0].message.content if response.choices else ""

        structured = {}
        if any(kw in raw_text.lower() for kw in ["total", "$", "invoice", "receipt"]):
            structured = await self._parse_receipt_data(raw_text)

        return {
            "raw_text": raw_text,
            "structured_data": structured,
            "confidence": 0.95,
            "model": "gpt-4o",
            "tokens": response.usage.total_tokens if response.usage else 0,
        }

    async def _parse_receipt_data(self, text: str) -> dict:
        import openai
        client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"Extract structured data from this receipt/invoice text. "
                        f"Return JSON with: vendor, date, total, subtotal, tax, currency, "
                        f"items (array of {{description, quantity, unit_price, total}}), "
                        f"payment_method, receipt_number.\n\nText:\n{text}"
                    ),
                }
            ],
            response_format={"type": "json_object"},
        )

        import json
        try:
            return json.loads(response.choices[0].message.content)
        except (json.JSONDecodeError, AttributeError, IndexError):
            return {"raw": text}

    async def scan_document(self, image_data: bytes, mime_type: str = "image/png") -> dict:
        ocr_result = await self.extract_ocr(image_data, mime_type)

        import openai
        client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        image_b64 = base64.b64encode(image_data).decode("utf-8")
        data_uri = f"data:{mime_type};base64,{image_b64}"

        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "content": (
                                "Analyze this document image. Identify: document_type, "
                                "language, page_count (estimate), key_fields (dictionary of "
                                "important fields found). Return JSON."
                            ),
                        },
                        {"type": "image_url", "image_url": {"url": data_uri, "detail": "high"}},
                    ],
                }
            ],
            response_format={"type": "json_object"},
        )

        import json
        try:
            analysis = json.loads(response.choices[0].message.content)
        except (json.JSONDecodeError, AttributeError, IndexError):
            analysis = {"document_type": "unknown"}

        return {
            **ocr_result,
            "document_analysis": analysis,
        }

    async def create_asset_from_analysis(
        self, user_id: uuid.UUID, image_data: bytes,
        mime_type: str, analysis: dict, storage_key: str
    ) -> MediaAsset:
        asset = MediaAsset(
            user_id=user_id,
            asset_type="image",
            mime_type=mime_type,
            storage_key=storage_key,
            size_bytes=len(image_data),
            ocr_text=analysis.get("raw_text", "") if "raw_text" in analysis else None,
            ai_analysis=analysis,
        )
        self.db.add(asset)
        await self.db.flush()

        if "raw_text" in analysis and analysis.get("raw_text"):
            ocr = OCRResult(
                asset_id=asset.id,
                raw_text=analysis["raw_text"],
                structured_data=analysis.get("structured_data"),
                confidence=analysis.get("confidence"),
            )
            self.db.add(ocr)
            await self.db.flush()

        return asset


vision_service = VisionService
