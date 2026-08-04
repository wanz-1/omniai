import hashlib
import hmac
import json
import logging
import secrets
import time
import uuid
from base64 import urlsafe_b64decode, urlsafe_b64encode
from datetime import datetime, timezone, timedelta
from typing import Any

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.v5_connector_platform import (
    ConnectorIntegration, ConnectorCredential, ConnectorApiKey, ConnectorLog,
)

logger = logging.getLogger("omniai.connector.auth")

_fernet_cache: Fernet | None = None


def _get_fernet() -> Fernet:
    global _fernet_cache
    if _fernet_cache is not None:
        return _fernet_cache
    key_material = settings.jwt_secret or "omniai-default-encryption-key-change-in-production!"
    if len(key_material) < 32:
        key_material = key_material * (32 // len(key_material) + 1)
    digest = hashlib.sha256(key_material.encode()).digest()
    key = urlsafe_b64encode(digest)
    _fernet_cache = Fernet(key)
    return _fernet_cache


def encrypt_value(plaintext: str) -> str:
    f = _get_fernet()
    return f.encrypt(plaintext.encode()).decode()


def decrypt_value(ciphertext: str) -> str:
    f = _get_fernet()
    return f.decrypt(ciphertext.encode()).decode()


OAUTH_PROVIDERS: dict[str, dict[str, Any]] = {
    "google_drive": {
        "authorize_url": "https://accounts.google.com/o/oauth2/v2/auth",
        "token_url": "https://oauth2.googleapis.com/token",
        "scopes": ["https://www.googleapis.com/auth/drive.readonly"],
        "client_id_setting": "oauth_google_client_id",
        "client_secret_setting": "oauth_google_client_secret",
    },
    "gmail": {
        "authorize_url": "https://accounts.google.com/o/oauth2/v2/auth",
        "token_url": "https://oauth2.googleapis.com/token",
        "scopes": ["https://www.googleapis.com/auth/gmail.readonly", "https://www.googleapis.com/auth/gmail.send"],
        "client_id_setting": "oauth_google_client_id",
        "client_secret_setting": "oauth_google_client_secret",
    },
    "github": {
        "authorize_url": "https://github.com/login/oauth/authorize",
        "token_url": "https://github.com/login/oauth/access_token",
        "scopes": ["repo", "read:user", "admin:repo_hook"],
        "client_id_setting": "oauth_github_client_id",
        "client_secret_setting": "oauth_github_client_secret",
    },
    "microsoft_365": {
        "authorize_url": "https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
        "token_url": "https://login.microsoftonline.com/common/oauth2/v2.0/token",
        "scopes": ["Files.Read.All", "Sites.Read.All", "User.Read"],
        "client_id_setting": "oauth_microsoft_client_id",
        "client_secret_setting": "oauth_microsoft_client_secret",
    },
    "slack": {
        "authorize_url": "https://slack.com/oauth/v2/authorize",
        "token_url": "https://slack.com/api/oauth.v2.access",
        "scopes": ["channels:history", "channels:read", "chat:write", "users:read"],
        "client_id": "",
        "client_secret": "",
    },
    "notion": {
        "authorize_url": "https://api.notion.com/v1/oauth/authorize",
        "token_url": "https://api.notion.com/v1/oauth/token",
        "scopes": [],
        "client_id": "",
        "client_secret": "",
    },
    "dropbox": {
        "authorize_url": "https://www.dropbox.com/oauth2/authorize",
        "token_url": "https://api.dropboxapi.com/oauth2/token",
        "scopes": ["files.metadata.read", "files.content.read"],
        "client_id": "",
        "client_secret": "",
    },
    "stripe": {
        "authorize_url": "https://connect.stripe.com/oauth/authorize",
        "token_url": "https://connect.stripe.com/oauth/token",
        "scopes": ["read_write"],
        "client_id": "",
        "client_secret": "",
    },
    "telegram": {
        "authorize_url": "",
        "token_url": "",
        "scopes": [],
        "bot_token_setting": "",
    },
    "discord": {
        "authorize_url": "https://discord.com/api/oauth2/authorize",
        "token_url": "https://discord.com/api/oauth2/token",
        "scopes": ["bot", "messages.read", "guilds.join"],
        "client_id": "",
        "client_secret": "",
    },
    "whatsapp_business": {
        "authorize_url": "",
        "token_url": "",
        "scopes": [],
        "api_key_setting": "",
    },
}


def get_oauth_config(provider_name: str) -> dict[str, Any] | None:
    config = OAUTH_PROVIDERS.get(provider_name)
    if not config:
        return None
    resolved = dict(config)
    client_id_setting = config.get("client_id_setting", "")
    client_secret_setting = config.get("client_secret_setting", "")
    if client_id_setting:
        resolved["client_id"] = getattr(settings, client_id_setting, None) or ""
        resolved["client_secret"] = getattr(settings, client_secret_setting, None) or ""
    return resolved


class AuthenticationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_authorization_url(self, integration_id: uuid.UUID, redirect_uri: str) -> dict:
        rows = await self.db.execute(select(ConnectorIntegration).where(ConnectorIntegration.id == integration_id))
        integ = rows.scalar_one_or_none()
        if not integ:
            return {"error": "Integration not found"}

        rows = await self.db.execute(
            select(__import__("app.models.v5_connector_platform", fromlist=["ConnectorDefinition"]).ConnectorDefinition)
            .where(__import__("app.models.v5_connector_platform", fromlist=["ConnectorDefinition"]).ConnectorDefinition.id == integ.connector_id)
        )
        definition = rows.scalar_one_or_none()
        if not definition:
            return {"error": "Connector definition not found"}

        oauth_config = get_oauth_config(definition.connector_type)
        if not oauth_config or not oauth_config.get("authorize_url"):
            return {"error": f"OAuth not supported for {definition.connector_type}"}

        state = secrets.token_hex(32)
        integ.config = dict(integ.config or {})
        integ.config["oauth_state"] = state
        integ.config["oauth_redirect_uri"] = redirect_uri
        await self.db.commit()

        params = {
            "client_id": oauth_config.get("client_id", ""),
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": " ".join(oauth_config.get("scopes", [])),
            "state": state,
            "access_type": "offline",
            "prompt": "consent",
        }
        import urllib.parse
        auth_url = oauth_config["authorize_url"] + "?" + urllib.parse.urlencode(params)
        return {"authorization_url": auth_url, "state": state}

    async def handle_oauth_callback(self, integration_id: uuid.UUID, code: str, state: str) -> dict:
        rows = await self.db.execute(select(ConnectorIntegration).where(ConnectorIntegration.id == integration_id))
        integ = rows.scalar_one_or_none()
        if not integ:
            return {"error": "Integration not found"}

        saved_state = (integ.config or {}).get("oauth_state", "")
        if saved_state and saved_state != state:
            return {"error": "State mismatch. Possible CSRF attack."}

        rows = await self.db.execute(
            select(__import__("app.models.v5_connector_platform", fromlist=["ConnectorDefinition"]).ConnectorDefinition)
            .where(__import__("app.models.v5_connector_platform", fromlist=["ConnectorDefinition"]).ConnectorDefinition.id == integ.connector_id)
        )
        definition = rows.scalar_one_or_none()
        if not definition:
            return {"error": "Connector definition not found"}

        oauth_config = get_oauth_config(definition.connector_type)
        if not oauth_config:
            return {"error": f"OAuth not supported for {definition.connector_type}"}

        redirect_uri = (integ.config or {}).get("oauth_redirect_uri", "")
        import httpx
        try:
            token_data = {
                "client_id": oauth_config.get("client_id", ""),
                "client_secret": oauth_config.get("client_secret", ""),
                "code": code,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            }
            async with httpx.AsyncClient(timeout=30.0) as client:
                token_response = await client.post(oauth_config["token_url"], data=token_data)
                token_response.raise_for_status()
                tokens = token_response.json()
        except Exception as e:
            logger.error("OAuth token exchange failed", extra={"event": "oauth_failed", "error": str(e)})
            return {"error": f"Token exchange failed: {str(e)}"}

        access_token = tokens.get("access_token", "")
        refresh_token = tokens.get("refresh_token", "")
        expires_in = tokens.get("expires_in", 3600)
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=int(expires_in))

        cred = ConnectorCredential(
            integration_id=integration_id,
            credential_type="oauth2",
            encrypted_data={
                "access_token": encrypt_value(access_token) if access_token else "",
                "refresh_token": encrypt_value(refresh_token) if refresh_token else "",
                "token_type": tokens.get("token_type", "Bearer"),
                "scope": tokens.get("scope", ""),
            },
            expires_at=expires_at,
        )
        self.db.add(cred)
        integ.status = "connected"
        integ.last_sync_at = datetime.now(timezone.utc)
        config = dict(integ.config or {})
        config.pop("oauth_state", None)
        config.pop("oauth_redirect_uri", None)
        integ.config = config
        log = ConnectorLog(
            integration_id=integ.id, organization_id=integ.organization_id,
            level="info", action="oauth_callback",
            message=f"OAuth completed for {definition.name}",
        )
        self.db.add(log)
        await self.db.commit()
        await self.db.refresh(cred)
        return {"status": "connected", "credential_id": str(cred.id)}

    async def refresh_access_token(self, credential_id: uuid.UUID) -> dict:
        rows = await self.db.execute(select(ConnectorCredential).where(ConnectorCredential.id == credential_id))
        cred = rows.scalar_one_or_none()
        if not cred:
            return {"error": "Credential not found"}

        encrypted = cred.encrypted_data or {}
        encrypted_refresh = encrypted.get("refresh_token", "")
        if not encrypted_refresh:
            return {"error": "No refresh token available"}

        try:
            refresh_token = decrypt_value(encrypted_refresh)
        except Exception:
            return {"error": "Failed to decrypt refresh token"}

        rows = await self.db.execute(select(ConnectorIntegration).where(ConnectorIntegration.id == cred.integration_id))
        integ = rows.scalar_one_or_none()
        if not integ:
            return {"error": "Integration not found"}

        rows = await self.db.execute(
            select(__import__("app.models.v5_connector_platform", fromlist=["ConnectorDefinition"]).ConnectorDefinition)
            .where(__import__("app.models.v5_connector_platform", fromlist=["ConnectorDefinition"]).ConnectorDefinition.id == integ.connector_id)
        )
        definition = rows.scalar_one_or_none()
        if not definition:
            return {"error": "Connector definition not found"}

        oauth_config = get_oauth_config(definition.connector_type)
        if not oauth_config:
            return {"error": "OAuth config not found"}

        import httpx
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(oauth_config["token_url"], data={
                    "client_id": oauth_config.get("client_id", ""),
                    "client_secret": oauth_config.get("client_secret", ""),
                    "refresh_token": refresh_token,
                    "grant_type": "refresh_token",
                })
                response.raise_for_status()
                tokens = response.json()
        except Exception as e:
            logger.error("Token refresh failed", extra={"event": "token_refresh_failed", "error": str(e)})
            cred.is_expired = True
            await self.db.commit()
            return {"error": f"Token refresh failed: {str(e)}"}

        new_access = tokens.get("access_token", "")
        new_refresh = tokens.get("refresh_token", refresh_token)
        expires_in = tokens.get("expires_in", 3600)
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=int(expires_in))

        cred.encrypted_data = {
            "access_token": encrypt_value(new_access) if new_access else encrypted.get("access_token", ""),
            "refresh_token": encrypt_value(new_refresh) if new_refresh else encrypted.get("refresh_token", ""),
            "token_type": tokens.get("token_type", "Bearer"),
            "scope": tokens.get("scope", ""),
        }
        cred.expires_at = expires_at
        cred.is_expired = False
        cred.rotated_at = datetime.now(timezone.utc)
        await self.db.commit()
        return {"status": "refreshed", "credential_id": str(credential_id)}

    async def get_active_token(self, integration_id: uuid.UUID) -> str | None:
        rows = await self.db.execute(
            select(ConnectorCredential)
            .where(ConnectorCredential.integration_id == integration_id)
            .order_by(ConnectorCredential.created_at.desc())
            .limit(1)
        )
        cred = rows.scalar_one_or_none()
        if not cred:
            return None

        encrypted = cred.encrypted_data or {}
        if cred.expires_at and cred.expires_at < datetime.now(timezone.utc) and encrypted.get("refresh_token"):
            result = await self.refresh_access_token(cred.id)
            if "error" in result:
                return None
            rows = await self.db.execute(
                select(ConnectorCredential).where(ConnectorCredential.id == cred.id)
            )
            cred = rows.scalar_one_or_none()
            if not cred:
                return None
            encrypted = cred.encrypted_data or {}

        encrypted_token = encrypted.get("access_token", "")
        if not encrypted_token:
            return None
        try:
            return decrypt_value(encrypted_token)
        except Exception:
            return None

    async def authenticate(self, integration_id: uuid.UUID, auth_data: dict) -> dict:
        rows = await self.db.execute(select(ConnectorIntegration).where(ConnectorIntegration.id == integration_id))
        integ = rows.scalar_one_or_none()
        if not integ:
            return {"error": "Integration not found"}
        auth_type = auth_data.get("auth_type", "api_key")

        sensitive_fields = ["api_key", "password", "client_secret", "token"]
        encrypted_data = {}
        for k, v in auth_data.items():
            if k == "auth_type":
                continue
            if k in sensitive_fields or "key" in k.lower() or "secret" in k.lower() or "token" in k.lower():
                encrypted_data[k] = encrypt_value(str(v))
            else:
                encrypted_data[k] = v

        cred = ConnectorCredential(
            integration_id=integration_id,
            credential_type=auth_type,
            encrypted_data=encrypted_data,
        )
        self.db.add(cred)
        integ.status = "connected"
        integ.last_sync_at = datetime.now(timezone.utc)
        log = ConnectorLog(
            integration_id=integ.id, organization_id=integ.organization_id,
            level="info", action="authenticate", message=f"Authenticated via {auth_type}",
        )
        self.db.add(log)
        await self.db.commit()
        await self.db.refresh(cred)
        return {"status": "connected", "credential_id": str(cred.id), "auth_type": auth_type}

    async def rotate_credentials(self, credential_id: uuid.UUID) -> dict:
        rows = await self.db.execute(select(ConnectorCredential).where(ConnectorCredential.id == credential_id))
        cred = rows.scalar_one_or_none()
        if not cred:
            return {"error": "Credential not found"}
        cred.rotated_at = datetime.now(timezone.utc)
        cred.is_expired = False
        await self.db.commit()
        integ_rows = await self.db.execute(select(ConnectorIntegration).where(ConnectorIntegration.id == cred.integration_id))
        integ = integ_rows.scalar_one_or_none()
        if integ:
            log = ConnectorLog(
                integration_id=integ.id, organization_id=integ.organization_id,
                level="info", action="rotate_credentials", message="Credentials rotated",
            )
            self.db.add(log)
            await self.db.commit()
        return {"status": "rotated", "credential_id": str(credential_id)}

    async def create_api_key(self, org_id: uuid.UUID, name: str, scopes: list | None, created_by: uuid.UUID) -> ConnectorApiKey:
        raw_key = f"omni_{secrets.token_hex(24)}"
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        key_prefix = raw_key[:10]
        api_key = ConnectorApiKey(
            organization_id=org_id, name=name,
            key_hash=key_hash, key_prefix=key_prefix,
            scopes=scopes or ["read"], status="active",
            created_by=created_by,
        )
        self.db.add(api_key)
        await self.db.commit()
        await self.db.refresh(api_key)
        return api_key

    async def list_api_keys(self, org_id: uuid.UUID) -> list[ConnectorApiKey]:
        rows = await self.db.execute(
            select(ConnectorApiKey).where(ConnectorApiKey.organization_id == org_id).order_by(ConnectorApiKey.created_at.desc())
        )
        return list(rows.scalars().all())

    async def revoke_api_key(self, key_id: uuid.UUID) -> bool:
        rows = await self.db.execute(select(ConnectorApiKey).where(ConnectorApiKey.id == key_id))
        key = rows.scalar_one_or_none()
        if not key:
            return False
        key.status = "revoked"
        await self.db.commit()
        return True
