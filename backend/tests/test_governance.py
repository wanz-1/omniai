import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.ai_governance.hallucination_detector import HallucinationDetector
from app.services.ai_governance.quality_scoring import QualityScoringService as QualityScorer


@pytest.mark.asyncio
class TestHallucinationDetector:
    @pytest.fixture
    def detector(self):
        return HallucinationDetector()

    async def test_analyze_no_claims(self, detector):
        result = await detector.analyze("Hello, how are you?")
        assert result["hallucination_count"] == 0
        assert result["total_claims"] == 0

    async def test_analyze_with_date_claim_no_source(self, detector):
        result = await detector.analyze(
            "The company was founded in 2023. It has 1 million users.",
            source_text="",
        )
        assert result["total_claims"] >= 1
        assert result["hallucination_count"] >= 1  # No source to verify

    async def test_analyze_with_source_support(self, detector):
        result = await detector.analyze(
            "The company was founded in 2023.",
            source_text="The company was founded in 2023 and has grown rapidly.",
        )
        assert result["total_claims"] >= 1
        # Has source context match so not a hallucination
        assert result["hallucination_count"] == 0

    async def test_analyze_with_citation(self, detector):
        result = await detector.analyze(
            "Studies show that AI improves productivity by 40% [1].",
            source_text="",
        )
        assert result["total_claims"] >= 1
        # Has citation so not a hallucination
        assert result["hallucination_count"] == 0

    async def test_extract_claims(self, detector):
        claims = detector._extract_claims(
            "In 2024, the company grew. It has 500 employees. "
            "The CEO said 'We are growing fast'. Nothing here. Hello."
        )
        assert len(claims) >= 3

    async def test_llm_verification(self, detector):
        with patch("app.services.ai_governance.hallucination_detector.ai_service") as mock_ai:
            mock_ai.complete = AsyncMock(return_value={
                "content": '{"hallucinations": [], "verification_summary": "All claims supported"}'
            })
            result = await detector._llm_verify(
                "The sky is blue.",
                "The sky appears blue due to Rayleigh scattering.",
            )
            assert "hallucinations" in result
            assert "verification_summary" in result


class TestQualityScorer:
    @pytest.fixture
    def scorer(self):
        return QualityScorer()

    def test_compute_overall_score_perfect(self, scorer):
        scores = scorer.compute_overall_score(
            accuracy=100.0, safety=100.0, citation=100.0,
            latency_ms=100, tokens_used=50,
        )
        assert scores["overall"] >= 90.0
        assert scores["accuracy"] == 100.0
        assert scores["safety"] == 100.0

    def test_compute_overall_score_poor(self, scorer):
        scores = scorer.compute_overall_score(
            accuracy=0.0, safety=0.0, citation=0.0,
            latency_ms=10000, tokens_used=50000,
        )
        assert scores["overall"] < 30.0

    def test_latency_score_tiers(self, scorer):
        assert scorer._compute_latency_score(100) == 100.0
        assert scorer._compute_latency_score(750) == 90.0
        assert scorer._compute_latency_score(1500) == 75.0
        assert scorer._compute_latency_score(3500) == 50.0
        assert scorer._compute_latency_score(10000) == 25.0

    def test_cost_score_tiers(self, scorer):
        assert scorer._compute_cost_score(50) == 100.0
        assert scorer._compute_cost_score(300) == 90.0
        assert scorer._compute_cost_score(1000) == 70.0
        assert scorer._compute_cost_score(5000) == 40.0
        assert scorer._compute_cost_score(50000) == 10.0

    @pytest.mark.asyncio
    async def test_generate_quality_report_empty(self, scorer):
        mock_db = AsyncMock()
        mock_execute = AsyncMock()
        mock_result = MagicMock()
        mock_result.one = MagicMock(return_value=(None, None))
        mock_result.scalar = MagicMock(return_value=0)
        mock_execute.return_value = mock_result
        mock_db.execute = mock_execute
        scorer.set_session(mock_db)

        report = await scorer.generate_quality_report("gpt-4o")
        assert report["model"] == "gpt-4o"
        assert report["total_evaluations"] == 0
        assert report["pass_rate"] == 0.0
