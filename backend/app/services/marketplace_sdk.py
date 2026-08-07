from app.services.ai_service import ai_service

SDK_TEMPLATES = {
    "python": """
# OmniAI Python SDK
import httpx
from typing import Any, Optional

class OmniAIClient:
    def __init__(self, api_key: str, base_url: str = "https://api.omniai.app/v1"):
        self.api_key = api_key
        self.base_url = base_url
        self._client = httpx.AsyncClient(headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"})

    async def agents(self) -> "AgentsAPI": return AgentsAPI(self)
    async def marketplace(self) -> "MarketplaceAPI": return MarketplaceAPI(self)
    async def workflows(self) -> "WorkflowsAPI": return WorkflowsAPI(self)
    async def chat(self) -> "ChatAPI": return ChatAPI(self)
    async def code_studio(self) -> "CodeStudioAPI": return CodeStudioAPI(self)

    async def close(self): await self._client.aclose()

class APIBase:
    def __init__(self, client: OmniAIClient): self._client = client
    async def _get(self, path: str, **kwargs): return (await self._client._client.get(f"{self._client.base_url}{path}", params=kwargs)).json()
    async def _post(self, path: str, data: dict = None): return (await self._client._client.post(f"{self._client.base_url}{path}", json=data or {})).json()

class AgentsAPI(APIBase):
    async def list(self): return await self._get("/agents")
    async def create(self, name: str, role: str, **kwargs): return await self._post("/agents", {"name": name, "role": role, **kwargs})
    async def chat(self, agent_id: str, message: str): return await self._post(f"/agents/{agent_id}/chat", {"message": message})

class MarketplaceAPI(APIBase):
    async def browse(self, category: str = None): return await self._get("/marketplace-extended/products", category=category)
    async def publish(self, data: dict): return await self._post("/marketplace-extended/products", data)
    async def purchase(self, product_id: str): return await self._post(f"/marketplace-extended/products/{product_id}/purchase")

class WorkflowsAPI(APIBase):
    async def list(self): return await self._get("/business/workflows")
    async def create(self, data: dict): return await self._post("/business/workflows", data)
    async def execute(self, workflow_id: str): return await self._post(f"/business/workflows/{workflow_id}/execute")

class ChatAPI(APIBase):
    async def send(self, message: str, session_id: str = None): return await self._post("/chat/send", {"message": message, "session_id": session_id})

class CodeStudioAPI(APIBase):
    async def projects(self): return await self._get("/code-studio/projects")
    async def generate(self, data: dict): return await self._post("/code-studio/generate", data)
""",
    "javascript": """
// OmniAI JavaScript SDK
class OmniAIClient {
  constructor(apiKey, baseUrl = 'https://api.omniai.app/v1') {
    this.apiKey = apiKey;
    this.baseUrl = baseUrl;
  }

  async request(path, options = {}) {
    const res = await fetch(`${this.baseUrl}${path}`, {
      headers: { 'Authorization': `Bearer ${this.apiKey}`, 'Content-Type': 'application/json', ...options.headers },
      ...options,
    });
    return res.json();
  }

  agents = { list: () => this.request('/agents'), create: (data) => this.request('/agents', { method: 'POST', body: JSON.stringify(data) }) };
  marketplace = { browse: (cat) => this.request(`/marketplace-extended/products${cat ? '?category='+cat : ''}`), publish: (data) => this.request('/marketplace-extended/products', { method: 'POST', body: JSON.stringify(data) }) };
  chat = { send: (msg, sid) => this.request('/chat/send', { method: 'POST', body: JSON.stringify({ message: msg, session_id: sid }) }) };
  codeStudio = { projects: () => this.request('/code-studio/projects'), generate: (data) => this.request('/code-studio/generate', { method: 'POST', body: JSON.stringify(data) }) };
}
""",
}


class MarketplaceSDKService:
    async def generate_sdk(self, language: str = "python", features: list[str] | None = None) -> dict:
        template = SDK_TEMPLATES.get(language, SDK_TEMPLATES["python"])
        if features and len(features) < 5:
            return {"language": language, "code": template, "features": features or ["agents", "marketplace", "chat"]}

        messages = [
            {"role": "system", "content": f"Generate a comprehensive {language} SDK for the OmniAI platform with all API modules."},
            {"role": "user", "content": f"Generate {language} SDK covering: {', '.join(features or ['agents', 'marketplace', 'workflows', 'chat', 'code_studio', 'business'])}. Include full type hints, error handling, and examples."},
        ]
        result = await ai_service.complete(messages, model="gpt-4o", temperature=0.3)
        return {"language": language, "code": result.get("content", template), "features": features or []}

    async def get_sdk_template(self, language: str = "python") -> dict:
        code = SDK_TEMPLATES.get(language, SDK_TEMPLATES["python"])
        return {"language": language, "code": code}
