import uuid
from datetime import datetime, timezone

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import AuthError
from app.core.security import create_access_token, create_refresh_token, hash_password
from app.models.user import OAuthAccount, User
from app.schemas.auth import TokenResponse


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def handle_oauth_callback(
        self, provider: str, code: str, redirect_uri: str
    ) -> TokenResponse:
        token_url, userinfo_url, client_id, client_secret = self._get_oauth_config(provider)

        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                token_url,
                data={
                    "code": code,
                    "redirect_uri": redirect_uri,
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "grant_type": "authorization_code",
                },
                headers={"Accept": "application/json"},
            )
            if token_response.status_code != 200:
                raise AuthError(f"OAuth token exchange failed for {provider}")

            token_data = token_response.json()
            access_token = token_data.get("access_token")

            user_response = await client.get(
                userinfo_url,
                headers={"Authorization": f"Bearer {access_token}"},
            )
            if user_response.status_code != 200:
                raise AuthError(f"Failed to fetch user info from {provider}")

            user_data = user_response.json()

        email, name, provider_id = self._extract_user_info(provider, user_data)
        if not email:
            raise AuthError(f"Could not retrieve email from {provider}")

        result = await self.db.execute(
            select(OAuthAccount).where(
                OAuthAccount.provider == provider,
                OAuthAccount.provider_user_id == provider_id,
            )
        )
        account = result.scalar_one_or_none()

        if account:
            account.access_token = access_token
            user = await self.db.get(User, account.user_id)
        else:
            existing_user = await self.db.execute(select(User).where(User.email == email))
            user = existing_user.scalar_one_or_none()

            if not user:
                user = User(
                    email=email,
                    display_name=name or email.split("@")[0],
                    is_verified=True,
                )
                self.db.add(user)
                await self.db.flush()

            account = OAuthAccount(
                user_id=user.id,
                provider=provider,
                provider_user_id=provider_id,
                access_token=access_token,
            )
            self.db.add(account)
            await self.db.flush()

        user.last_login_at = datetime.now(timezone.utc)
        await self.db.flush()

        jwt_access = create_access_token(subject=str(user.id), extra_claims={"role": user.role})
        jwt_refresh = create_refresh_token(subject=str(user.id))

        return TokenResponse(access_token=jwt_access, refresh_token=jwt_refresh)

    def _get_oauth_config(self, provider: str) -> tuple:
        configs = {
            "google": (
                "https://oauth2.googleapis.com/token",
                "https://www.googleapis.com/oauth2/v2/userinfo",
                settings.oauth_google_client_id,
                settings.oauth_google_client_secret,
            ),
            "github": (
                "https://github.com/login/oauth/access_token",
                "https://api.github.com/user",
                settings.oauth_github_client_id,
                settings.oauth_github_client_secret,
            ),
        }
        config = configs.get(provider)
        if not config:
            raise AuthError(f"Unsupported OAuth provider: {provider}")
        if not config[2] or not config[3]:
            raise AuthError(f"OAuth {provider} not configured")
        return config

    def _extract_user_info(self, provider: str, data: dict) -> tuple:
        if provider == "google":
            return data.get("email"), data.get("name"), data.get("id")
        elif provider == "github":
            return data.get("email"), data.get("name"), str(data.get("id"))
        return None, None, None
