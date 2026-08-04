import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.agent_service import ToolExecutor


@pytest.mark.asyncio
class TestToolExecutor:
    @pytest.fixture
    def executor(self):
        return ToolExecutor()

    async def test_web_search_uses_ai_fallback(self, executor):
        with patch("app.services.agent_service.ai_service.complete", new_callable=AsyncMock) as mock_complete:
            mock_complete.return_value = {"content": "Search result"}
            result = await executor._web_search("test query")
            assert result is not None

    async def test_web_scrape_invalid_url(self, executor):
        result = await executor._web_scrape("not-a-url")
        assert "Invalid URL" in result

    async def test_web_scrape_valid_url(self, executor):
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = AsyncMock()
            mock_response.text = "<html><body>Hello World</body></html>"
            mock_response.is_success = True
            mock_context = AsyncMock()
            mock_context.__aenter__ = AsyncMock(return_value=mock_context)
            mock_context.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            mock_client.return_value = mock_context

            result = await executor._web_scrape("https://example.com")
            assert "Hello World" in result

    async def test_execute_code_python(self, executor):
        code = "result = 1 + 2"
        result = await executor._execute_code(code, "python")
        assert "3" in result

    async def test_execute_code_python_error(self, executor):
        code = "raise ValueError('test error')"
        result = await executor._execute_code(code, "python")
        assert "Error" in result

    async def test_execute_code_unsupported_language(self, executor):
        result = await executor._execute_code("code", "java")
        assert "not supported" in result

    async def test_file_system_no_path(self, executor):
        result = await executor._file_system("read", "")
        assert "No path" in result

    async def test_api_call_no_url(self, executor):
        result = await executor._api_call("", "GET", {}, {})
        assert "No URL" in result

    async def test_api_call_success(self, executor):
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.text = '{"status": "ok"}'
            mock_response.is_success = True
            mock_client_instance = AsyncMock()
            mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client.return_value = mock_client_instance
            mock_client_instance.request = AsyncMock(return_value=mock_response)

            result = await executor._api_call("https://api.example.com", "GET", {}, {})
            assert "200" in result

    async def test_unknown_tool_type(self, executor):
        mock_tool = MagicMock()
        mock_tool.tool_type = "nonexistent_tool"
        mock_tool.config = {}
        result = await executor.execute(mock_tool, {})
        assert "Unknown tool" in result

    async def test_tool_error_handling(self, executor):
        mock_tool = MagicMock()
        mock_tool.tool_type = "web_search"
        mock_tool.config = {}

        with patch.object(executor, "_web_search", side_effect=Exception("connection error")):
            result = await executor.execute(mock_tool, {"query": "test"})
            assert "Tool error" in result
            assert "connection error" in result
