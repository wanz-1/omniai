import json
import logging
import re
from typing import Any

from app.services.ai_service import ai_service

logger = logging.getLogger("omniai.governance.hallucination")


class ClaimExtractor:
    DATE_PATTERN = re.compile(r"(?:in|by|since|during|as of)\s+(20\d{2}|19\d{2})", re.IGNORECASE)
    NUMBER_PATTERN = re.compile(
        r"\b(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*(?:%|million|billion|thousand|users|customers|dollars|usd|employees|workers)(?:\b|[^A-Za-z0-9_])",
        re.IGNORECASE,
    )
    FACT_PATTERN = re.compile(r"(?:is|are|was|were|has|have|had|will|shall|must|should)\s+(?:the|a|an|not\s+)", re.IGNORECASE)
    QUOTE_PATTERN = re.compile(r"""[\"']([^\"']+)[\"']""")
    REFERENCE_PATTERN = re.compile(r"\[(\d+|[a-zA-Z])\]")
    SOURCE_PATTERN = re.compile(r"(?:according to|source|reference|based on|per|as per)", re.IGNORECASE)
    SPECIFIC_PATTERN = re.compile(r"\b(?:exactly|specifically|precisely|always|never|everyone|no one|all|none)\b", re.IGNORECASE)


class HallucinationDetector:
    def __init__(self) -> None:
        self.extractor = ClaimExtractor()

    async def analyze(
        self,
        text: str,
        source_text: str = "",
        model: str = "",
        use_llm_verification: bool = True,
    ) -> dict[str, Any]:
        claims = self._extract_claims(text)
        hallucinations: list[dict[str, Any]] = []
        total_confidence = 100.0

        for claim in claims:
            result = self._check_claim_heuristic(claim, text, source_text)
            if result["is_hallucination"]:
                hallucinations.append(result)
                total_confidence -= result.get("confidence_deduction", 10)

        if use_llm_verification and (source_text or len(claims) > 0):
            try:
                llm_result = await self._llm_verify(text, source_text)
                for h in llm_result.get("hallucinations", []):
                    if h not in hallucinations:
                        hallucinations.append(h)
                        total_confidence -= 15
            except Exception as e:
                logger.warning("LLM verification failed", extra={"error": str(e)})

        return {
            "hallucination_count": len(hallucinations),
            "hallucinations": hallucinations[:10],
            "total_claims": len(claims),
            "overall_confidence": max(0, round(total_confidence, 1)),
            "hallucination_rate": round(len(hallucinations) / max(len(claims), 1) * 100, 2),
        }

    def _extract_claims(self, text: str) -> list[str]:
        claims: list[str] = []
        sentences = re.split(r"[.!?]+", text)
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 10:
                continue
            if (self.extractor.DATE_PATTERN.search(sentence) or
                self.extractor.NUMBER_PATTERN.search(sentence) or
                self.extractor.FACT_PATTERN.search(sentence) or
                self.extractor.QUOTE_PATTERN.search(sentence) or
                self.extractor.SPECIFIC_PATTERN.search(sentence)):
                claims.append(sentence)
        return claims[:20]

    def _check_claim_heuristic(self, claim: str, full_text: str, source_text: str) -> dict[str, Any]:
        has_citation = bool(self.extractor.REFERENCE_PATTERN.search(claim))
        has_source = bool(self.extractor.SOURCE_PATTERN.search(claim))
        has_source_context = bool(source_text and any(
            word in source_text.lower() for word in claim.lower().split()[:5]
        ))

        is_hallucination = False
        severity = "low"
        confidence_deduction = 10
        category = "unsupported_claim"
        evidence_source = ""

        if not has_citation and not has_source:
            if source_text and not has_source_context:
                is_hallucination = True
                severity = "medium"
                confidence_deduction = 25
                category = "missing_citation"
            elif not source_text:
                is_hallucination = True
                severity = "medium"
                confidence_deduction = 25
                category = "unverifiable_claim"
        elif has_source_context:
            evidence_source = "source_text"
        elif has_citation:
            evidence_source = "inline_citation"

        return {
            "claim": claim[:500],
            "is_hallucination": is_hallucination,
            "severity": severity,
            "confidence_deduction": confidence_deduction,
            "category": category,
            "evidence_found": has_citation or has_source or has_source_context,
            "evidence_source": evidence_source,
            "confidence": max(0, 100 - confidence_deduction) if is_hallucination else 95,
        }

    async def _llm_verify(self, text: str, source_text: str) -> dict[str, Any]:
        source_section = f"\n\nReference Source:\n{source_text[:4000]}" if source_text else ""
        prompt = f"""Analyze the following AI-generated text for factual hallucinations and unsupported claims.

AI Text:
{text[:4000]}{source_section}

Identify any claims that:
1. Are not supported by the provided reference source (if given)
2. Contain specific numbers, dates, or statistics that cannot be verified
3. Make definitive statements without evidence
4. Contradict known facts

Return ONLY valid JSON:
{{"hallucinations": [{{"claim": "exact text", "reason": "why it may be hallucinated", "severity": "low|medium|high"}}], "verification_summary": "brief overall assessment"}}"""

        response = await ai_service.complete(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            model="gpt-4o-mini",
        )
        content = response.get("content", "{}")
        content = content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1] if "\n" in content else content
            content = content.rsplit("```", 1)[0] if "```" in content else content
        try:
            result = json.loads(content)
            for h in result.get("hallucinations", []):
                h["is_hallucination"] = True
                h["detection_method"] = "llm"
                h["confidence_deduction"] = {"low": 10, "medium": 20, "high": 35}.get(h.get("severity", "medium"), 15)
            return result
        except (json.JSONDecodeError, Exception):
            return {"hallucinations": [], "verification_summary": "LLM verification failed"}

    async def check_claim_support(self, claim: str, source_text: str) -> dict[str, Any]:
        return self._check_claim_heuristic(claim, source_text, source_text)


hallucination_detector = HallucinationDetector()
