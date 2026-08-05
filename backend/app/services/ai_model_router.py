"""Enhanced AI model router supporting multimodal models."""


from app.core.config import settings


class AIModelRouter:
    """Routes AI requests to the optimal model based on capability, cost, and latency."""

    MODEL_CONFIGS = {
        "chat": {
            "primary": "gpt-4o",
            "fallback": "claude-3.5-sonnet",
            "cost_optimized": "gpt-4o-mini",
            "local": "ollama/llama3.1",
        },
        "vision": {
            "primary": "gpt-4o",
            "fallback": "claude-3.5-sonnet",
            "local": "ollama/llava",
        },
        "voice_stt": {
            "primary": "whisper-1",
            "fallback": "deepgram/nova-2",
            "local": "whisper.cpp",
        },
        "voice_tts": {
            "primary": "tts-1",
            "fallback": "elevenlabs/multi-lingual-v2",
            "local": "piper-tts",
        },
        "image_generation": {
            "primary": "dall-e-3",
            "fallback": "stability-ai/sdxl-turbo",
            "local": "comfyui",
        },
        "video_summary": {
            "primary": "gpt-4o",
            "fallback": "claude-3.5-sonnet",
        },
        "embeddings": {
            "primary": "text-embedding-3-large",
            "local": "sentence-transformers/all-MiniLM-L6-v2",
        },
        "code": {
            "primary": "claude-3.5-sonnet",
            "fallback": "gpt-4o",
            "local": "ollama/codellama",
        },
    }

    def __init__(
        self,
        strategy: str = "latency_first",
        cost_budget_monthly: float = 1000,
        latency_threshold_ms: int = 2000,
    ):
        self.strategy = strategy
        self.cost_budget_monthly = cost_budget_monthly
        self.latency_threshold_ms = latency_threshold_ms
        self._monthly_spend = 0.0

    def select_model(self, capability: str, prefer_local: bool = False) -> dict:
        config = self.MODEL_CONFIGS.get(capability, self.MODEL_CONFIGS["chat"])

        if prefer_local and "local" in config:
            return {"model": config["local"], "provider": "local", "tier": "local"}

        if self.strategy == "cost_first" and self._monthly_spend > self.cost_budget_monthly * 0.8:
            return {"model": config.get("cost_optimized", config["primary"]), "provider": "cloud", "tier": "cost"}

        if self.strategy == "quality_first":
            return {"model": config["primary"], "provider": "cloud", "tier": "primary"}

        return {"model": config["primary"], "provider": "cloud", "tier": "primary"}

    def get_available_models(self, capability: str) -> list[str]:
        config = self.MODEL_CONFIGS.get(capability, {})
        return [v for v in config.values() if v]

    def track_usage(self, model: str, tokens: int, cost: float):
        self._monthly_spend += cost

    @property
    def monthly_spend(self) -> float:
        return self._monthly_spend

    def get_voice_providers(self) -> dict:
        return {
            "stt": {
                "primary": settings.VOICE_STT_PROVIDER or "whisper",
                "available": self.get_available_models("voice_stt"),
            },
            "tts": {
                "primary": settings.VOICE_TTS_PROVIDER or "openai",
                "available": self.get_available_models("voice_tts"),
            },
        }


ai_model_router = AIModelRouter()
