import uuid
from datetime import datetime
from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import OrganizationPlan, Role
from app.models.base import Base, TimestampMixin, UUIDMixin


class Organization(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    logo_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    plan: Mapped[OrganizationPlan] = mapped_column(Enum(OrganizationPlan), default=OrganizationPlan.FREE, nullable=False)
    settings: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    members = relationship("OrganizationMember", back_populates="organization", cascade="all, delete-orphan")
    subscription = relationship("Subscription", back_populates="organization", uselist=False, cascade="all, delete-orphan")
    digital_twins = relationship("DigitalTwin", back_populates="organization", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"Organization(id={self.id}, name={self.name}, plan={self.plan})"


class OrganizationMember(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "organization_members"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    role: Mapped[Role] = mapped_column(Enum(Role), default=Role.MEMBER, nullable=False)

    organization = relationship("Organization", back_populates="members")
    user = relationship("User", back_populates="organizations")

    __table_args__ = (
        UniqueConstraint("organization_id", "user_id", name="uq_org_member"),
    )

    def __repr__(self) -> str:
        return f"OrganizationMember(org={self.organization_id}, user={self.user_id}, role={self.role})"
