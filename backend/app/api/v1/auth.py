import uuid
from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.dependencies import get_db, get_current_user
from app.core.exceptions import AuthError, NotFoundError, ValidationError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_2fa_secret,
    get_2fa_otp_uri,
    hash_password,
    hash_token,
    verify_2fa_code,
    verify_password,
)
from app.models.user import User
from app.services.security_audit import SecurityAuditService
from app.schemas.auth import (
    LoginRequest,
    OAuthCallbackRequest,
    PasswordChangeRequest,
    RefreshTokenRequest,
    RegisterRequest,
    TokenResponse,
    TwoFactorLoginRequest,
    TwoFactorSetupResponse,
    TwoFactorVerifyRequest,
    UserResponse,
)

router = APIRouter()


def _client_context(request: Request) -> tuple[str, str]:
    ip = request.client.host if request.client else ""
    return ip, request.headers.get("user-agent", "")[:500]


async def _create_session(
    db: AsyncSession,
    user_id: uuid.UUID,
    refresh_token: str,
    ip: str,
    user_agent: str,
    device_name: str = "",
) -> None:
    """Persist a refresh-token session so tokens can be rotated and revoked."""
    from app.models.session import UserSession
    session = UserSession(
        user_id=user_id,
        token_hash=hash_token(refresh_token),
        refresh_token_hash=hash_token(refresh_token),
        ip_address=ip or None,
        user_agent=user_agent or None,
        device_name=device_name or None,
        is_active=True,
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days),
        last_activity_at=datetime.now(timezone.utc),
    )
    db.add(session)
    await db.flush()


def _issue_tokens(user_id: uuid.UUID, role) -> TokenResponse:
    access = create_access_token(subject=str(user_id), extra_claims={"role": role})
    refresh = create_refresh_token(subject=str(user_id))
    return TokenResponse(access_token=access, refresh_token=refresh)


async def _record_login_audit(
    db: AsyncSession,
    *,
    success: bool,
    user_id: str,
    ip: str,
    user_agent: str,
    detail: str = "",
    severity: str = "info",
    action: str = "user.login",
    extra: dict | None = None,
):
    audit = SecurityAuditService(db)
    await audit.log_event(
        event_type="login_attempt",
        action=action,
        user_id=user_id,
        severity=severity,
        ip_address=ip,
        user_agent=user_agent,
        resource_type="auth",
        result="success" if success else "failure",
        detail=detail,
        extra=extra,
    )


@router.post("/register", response_model=TokenResponse)
async def register(
    body: RegisterRequest,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    existing = await db.execute(select(User).where(User.email == body.email))
    if existing.scalar_one_or_none():
        raise ValidationError("Email already registered")

    user = User(
        email=body.email,
        password_hash=hash_password(body.password),
        display_name=body.display_name,
    )
    db.add(user)
    await db.flush()

    tokens = _issue_tokens(user.id, user.role)
    ip, ua = _client_context(request)
    await _create_session(db, user.id, tokens.refresh_token, ip, ua)
    return tokens


@router.post("/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    ip, ua = _client_context(request)
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()

    if not user or not user.password_hash:
        await _record_login_audit(db, success=False, user_id="", ip=ip, user_agent=ua, detail="Unknown account or missing password hash")
        raise AuthError("Invalid email or password")

    now = datetime.now(timezone.utc)

    if user.locked_until and user.locked_until > now:
        await _record_login_audit(
            db, success=False, user_id=str(user.id), ip=ip, user_agent=ua,
            severity="high", action="user.login_locked",
            detail=f"Login blocked: account locked until {user.locked_until.isoformat()}",
        )
        raise AuthError("Account is temporarily locked due to too many failed attempts. Try again later.")

    if user.locked_until and user.locked_until <= now:
        user.failed_attempts = 0
        user.locked_until = None

    if not verify_password(body.password, user.password_hash):
        user.failed_attempts = (user.failed_attempts or 0) + 1
        user.last_failed_login = now
        if user.failed_attempts >= settings.account_lockout_threshold:
            user.locked_until = now + timedelta(minutes=settings.account_lockout_minutes)
            await _record_login_audit(
                db, success=False, user_id=str(user.id), ip=ip, user_agent=ua,
                severity="high", action="user.lockout",
                detail=f"Account locked for {settings.account_lockout_minutes} minutes after {user.failed_attempts} failed attempts",
            )
            await db.flush()
            raise AuthError("Account is temporarily locked due to too many failed attempts. Try again later.")
        await _record_login_audit(
            db, success=False, user_id=str(user.id), ip=ip, user_agent=ua,
            detail=f"Invalid password (failed attempt {user.failed_attempts}/{settings.account_lockout_threshold})",
        )
        await db.flush()
        raise AuthError("Invalid email or password")

    if not user.is_active:
        raise AuthError("Account is deactivated")

    user.failed_attempts = 0
    user.locked_until = None
    user.last_login_at = now
    user.last_ip = ip
    await db.flush()

    if user.two_factor_enabled:
        await _record_login_audit(db, success=True, user_id=str(user.id), ip=ip, user_agent=ua, detail="Password verified; 2FA required")
        return TokenResponse(access_token="", refresh_token="")

    tokens = _issue_tokens(user.id, user.role)
    await _create_session(db, user.id, tokens.refresh_token, ip, ua)
    await _record_login_audit(db, success=True, user_id=str(user.id), ip=ip, user_agent=ua, detail="Login successful")
    return tokens


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    body: RefreshTokenRequest,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    ip, ua = _client_context(request)
    payload = decode_token(body.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise AuthError("Invalid refresh token")

    user_id = payload.get("sub")
    jti = payload.get("jti", "")
    if not user_id:
        raise AuthError("Invalid refresh token")

    from app.models.session import UserSession
    token_hash = hash_token(body.refresh_token)
    result = await db.execute(
        select(UserSession).where(
            UserSession.token_hash == token_hash,
            UserSession.user_id == uuid.UUID(user_id),
        )
    )
    session = result.scalar_one_or_none()

    if not session:
        audit = SecurityAuditService(db)
        await audit.log_event(
            event_type="token_reuse", action="user.refresh_rejected", user_id=user_id,
            severity="high", ip_address=ip, user_agent=ua, resource_type="auth",
            result="failure", detail="Refresh token reuse or revocation detected",
            extra={"jti": jti},
        )
        raise AuthError("Invalid refresh token")

    now = datetime.now(timezone.utc)

    if not session.is_active or (session.expires_at and session.expires_at < now):
        session.is_active = False
        await db.flush()
        raise AuthError("Refresh token expired or revoked")

    user = await db.get(User, uuid.UUID(user_id))
    if not user or not user.is_active:
        raise AuthError("User not found or deactivated")

    session.is_active = False
    session.last_activity_at = now
    await db.flush()

    tokens = _issue_tokens(user.id, user.role)
    await _create_session(db, user.id, tokens.refresh_token, ip, ua)

    audit = SecurityAuditService(db)
    await audit.log_event(
        event_type="token_rotation", action="user.refresh", user_id=user_id,
        severity="info", ip_address=ip, user_agent=ua, resource_type="auth",
        result="success", detail="Refresh token rotated", extra={"old_jti": jti},
    )
    return tokens


@router.post("/oauth/{provider}", response_model=TokenResponse)
async def oauth_callback(provider: str, body: OAuthCallbackRequest, db: Annotated[AsyncSession, Depends(get_db)]):
    from app.services.auth_service import AuthService
    service = AuthService(db)
    return await service.handle_oauth_callback(provider, body.code, body.redirect_uri)


@router.post("/2fa/setup", response_model=TwoFactorSetupResponse)
async def setup_2fa(
    current_user: Annotated[User, Depends(get_current_user)],
):
    secret = generate_2fa_secret()
    otp_uri = get_2fa_otp_uri(secret, current_user.email)
    return TwoFactorSetupResponse(secret=secret, qr_code_url=otp_uri)


@router.post("/2fa/login", response_model=TokenResponse)
async def two_factor_login(
    body: TwoFactorLoginRequest,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    user_id = decode_token(body.temp_token)
    if not user_id:
        raise AuthError("Invalid or expired temporary token")
    if not user_id.get("sub"):
        raise AuthError("Invalid token payload")

    user = await db.get(User, uuid.UUID(user_id["sub"]))
    if not user or not user.is_active:
        raise AuthError("User not found or deactivated")
    if not user.two_factor_secret:
        raise AuthError("2FA not configured")
    if not verify_2fa_code(user.two_factor_secret, body.code):
        raise AuthError("Invalid 2FA code")

    user.last_login_at = datetime.now(timezone.utc)
    user.failed_attempts = 0
    user.locked_until = None
    await db.flush()

    tokens = _issue_tokens(user.id, user.role)
    ip, ua = _client_context(request)
    await _create_session(db, user.id, tokens.refresh_token, ip, ua)
    return tokens


@router.get("/sessions")
async def list_sessions(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    from app.models.session import UserSession
    result = await db.execute(
        select(UserSession).where(
            UserSession.user_id == current_user.id,
            UserSession.is_active == True,
        ).order_by(UserSession.last_activity_at.desc())
    )
    return result.scalars().all()


@router.post("/sessions/{session_id}/revoke")
async def revoke_session(
    session_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    from app.models.session import UserSession
    session = await db.get(UserSession, session_id)
    if not session or session.user_id != current_user.id:
        raise NotFoundError("Session", str(session_id))
    session.is_active = False
    await db.flush()
    return {"message": "Session revoked"}


@router.post("/2fa/verify")
async def verify_2fa(
    body: TwoFactorVerifyRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    if not verify_2fa_code(body.temp_token, body.code):
        raise AuthError("Invalid 2FA code. Make sure the code from your authenticator app matches.")

    user = await db.get(User, current_user.id)
    user.two_factor_enabled = True
    user.two_factor_secret = body.temp_token
    await db.flush()
    return {"message": "2FA enabled successfully"}


@router.post("/logout")
async def logout(
    body: RefreshTokenRequest,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    from app.models.session import UserSession
    token_hash = hash_token(body.refresh_token)
    result = await db.execute(select(UserSession).where(UserSession.token_hash == token_hash))
    session = result.scalar_one_or_none()

    if session:
        session.is_active = False
        session.last_activity_at = datetime.now(timezone.utc)
        await db.flush()
        ip, ua = _client_context(request)
        audit = SecurityAuditService(db)
        await audit.log_event(
            event_type="logout", action="user.logout", user_id=str(session.user_id),
            severity="info", ip_address=ip, user_agent=ua, resource_type="auth",
            result="success", detail="Logged out (current device)",
        )

    return {"message": "Logged out successfully"}


@router.post("/logout-all")
async def logout_all(
    current_user: Annotated[User, Depends(get_current_user)],
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    from app.models.session import UserSession
    result = await db.execute(
        select(UserSession).where(
            UserSession.user_id == current_user.id,
            UserSession.is_active == True,
        )
    )
    sessions = result.scalars().all()
    for session in sessions:
        session.is_active = False
        session.last_activity_at = datetime.now(timezone.utc)
    await db.flush()

    ip, ua = _client_context(request)
    audit = SecurityAuditService(db)
    await audit.log_event(
        event_type="logout_all", action="user.logout_all", user_id=str(current_user.id),
        severity="high", ip_address=ip, user_agent=ua, resource_type="auth",
        result="success", detail=f"Revoked {len(sessions)} session(s) across all devices",
    )
    return {"message": f"Revoked {len(sessions)} session(s)"}


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: Annotated[User, Depends(get_current_user)]):
    return current_user


@router.put("/me/password")
async def change_password(
    body: PasswordChangeRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    if not current_user.password_hash or not verify_password(body.current_password, current_user.password_hash):
        raise AuthError("Current password is incorrect")

    user = await db.get(User, current_user.id)
    user.password_hash = hash_password(body.new_password)
    await db.flush()
    return {"message": "Password changed successfully"}
