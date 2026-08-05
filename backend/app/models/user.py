import uuid
from datetime import datetime
from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import Role
from app.models.base import Base, TimestampMixin, UUIDMixin


class User(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    role: Mapped[Role] = mapped_column(Enum(Role), default=Role.USER, nullable=False)

    two_factor_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    two_factor_secret: Mapped[str | None] = mapped_column(String(64), nullable=True)

    preferences: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)

    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_ip: Mapped[str | None] = mapped_column(String(45), nullable=True)

    failed_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_failed_login: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    credits_balance: Mapped[int] = mapped_column(default=0, nullable=False)

    oauth_accounts = relationship("OAuthAccount", back_populates="user", cascade="all, delete-orphan")
    organizations = relationship("OrganizationMember", back_populates="user", cascade="all, delete-orphan")
    projects = relationship("Project", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")

    @property
    def organization_id(self) -> uuid.UUID | None:
        """Tenant organization id, resolved from the real membership model.

        Users belong to organizations through ``OrganizationMember`` (no direct
        ``organization_id`` column exists). Expose the first membership's
        organization id under the ``organization_id`` name so API layers can keep
        using ``current_user.organization_id or current_user.id`` for tenant
        scoping. Returns ``None`` when the user has no membership or the
        relationship is not loaded, letting callers fall back to the user id.
        """
        try:
            memberships = self.organizations
        except Exception:
            return None
        if not memberships:
            return None
        try:
            first = memberships[0] if isinstance(memberships, (list, tuple)) else next(iter(memberships))
        except (TypeError, IndexError, StopIteration):
            return None
        return getattr(first, "organization_id", None)

    def __repr__(self) -> str:
        return f"User(id={self.id}, email={self.email}, role={self.role})"


class OAuthAccount(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "oauth_accounts"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    provider_user_id: Mapped[str] = mapped_column(String(255), nullable=False)
    access_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    refresh_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="oauth_accounts")

    def __repr__(self) -> str:
        return f"OAuthAccount(provider={self.provider}, user_id={self.user_id})"
