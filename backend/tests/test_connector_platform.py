import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.connector_platform.authentication_service import (
    AuthenticationService, encrypt_value, decrypt_value, _get_fernet,
)


class TestEncryption:
    def test_encrypt_decrypt_roundtrip(self):
        original = "test-secret-value-123"
        encrypted = encrypt_value(original)
        assert encrypted != original
        decrypted = decrypt_value(encrypted)
        assert decrypted == original

    def test_encrypt_different_outputs(self):
        v1 = encrypt_value("same-value")
        v2 = encrypt_value("same-value")
        # Fernet always produces different output (includes IV)
        assert v1 != v2


@pytest.mark.asyncio
class TestAuthenticationService:
    @pytest.fixture
    def service(self):
        db = AsyncMock()
        return AuthenticationService(db)

    async def test_authenticate_api_key(self, service):
        mock_integ = MagicMock()
        mock_integ.id = "integration-1"
        mock_integ.organization_id = "org-1"
        mock_integ.status = "disconnected"
        mock_integ.config = {}

        mock_execute = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mock_integ)
        mock_execute.return_value = mock_result
        service.db.execute = mock_execute

        result = await service.authenticate(
            "integration-1",
            {"auth_type": "api_key", "api_key": "sk-test-123"},
        )
        assert result["status"] == "connected"
        assert result["auth_type"] == "api_key"
        service.db.add.assert_called()
        service.db.commit.assert_called()

    async def test_authenticate_encrypts_sensitive_fields(self, service):
        mock_integ = MagicMock()
        mock_integ.id = "integration-1"
        mock_integ.organization_id = "org-1"
        mock_integ.status = "disconnected"

        mock_execute = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mock_integ)
        mock_execute.return_value = mock_result
        service.db.execute = mock_execute

        await service.authenticate(
            "integration-1",
            {"auth_type": "api_key", "api_key": "sk-test-123", "client_secret": "secret-456", "name": "test"},
        )

        call_args = service.db.add.call_args_list[0][0][0]
        encrypted = call_args.encrypted_data
        assert encrypted["api_key"] != "sk-test-123"
        assert encrypted["client_secret"] != "secret-456"
        assert encrypted["name"] == "test"  # Non-sensitive is stored as-is

    async def test_get_active_token_no_credentials(self, service):
        mock_execute = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        mock_execute.return_value = mock_result
        service.db.execute = mock_execute

        token = await service.get_active_token("integration-1")
        assert token is None

    async def test_get_active_token_with_valid_token(self, service):
        mock_cred = MagicMock()
        mock_cred.encrypted_data = {"access_token": encrypt_value("valid-token-123")}
        mock_cred.expires_at = None

        mock_execute = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mock_cred)
        mock_execute.return_value = mock_result
        service.db.execute = mock_execute

        token = await service.get_active_token("integration-1")
        assert token == "valid-token-123"

    async def test_create_api_key(self, service):
        mock_org_id = "org-1"
        service.db.commit = AsyncMock()
        service.db.refresh = AsyncMock()

        key = await service.create_api_key(mock_org_id, "Test Key", ["read"], "user-1")
        assert key.name == "Test Key"
        assert key.key_prefix == key.key_prefix
        assert key.key_hash is not None
        assert key.scopes == ["read"]
        assert key.status == "active"

    async def test_revoke_api_key(self, service):
        mock_key = MagicMock()
        mock_key.status = "active"

        mock_execute = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mock_key)
        mock_execute.return_value = mock_result
        service.db.execute = mock_execute
        service.db.commit = AsyncMock()

        result = await service.revoke_api_key("key-1")
        assert result is True
        assert mock_key.status == "revoked"

    async def test_revoke_api_key_not_found(self, service):
        mock_execute = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        mock_execute.return_value = mock_result
        service.db.execute = mock_execute

        result = await service.revoke_api_key("nonexistent")
        assert result is False


class TestOAuthProviders:
    def test_get_oauth_config_known(self):
        from app.services.connector_platform.authentication_service import get_oauth_config
        config = get_oauth_config("google_drive")
        assert config is not None
        assert "authorize_url" in config
        assert "https://accounts.google.com" in config["authorize_url"]
        assert "scopes" in config

    def test_get_oauth_config_unknown(self):
        from app.services.connector_platform.authentication_service import get_oauth_config
        config = get_oauth_config("nonexistent_service")
        assert config is None
