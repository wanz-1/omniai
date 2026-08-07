import uuid

from sqlalchemy import Boolean, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import DeploymentStatus, WebsiteFramework, WebsiteStyling
from app.models.base import Base, TimestampMixin, UUIDMixin


class Website(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "websites"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    template_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    framework: Mapped[WebsiteFramework] = mapped_column(
        Enum(WebsiteFramework), default=WebsiteFramework.HTML_CSS, nullable=False
    )
    styling: Mapped[WebsiteStyling] = mapped_column(
        Enum(WebsiteStyling), default=WebsiteStyling.TAILWIND, nullable=False
    )
    pages: Mapped[dict | None] = mapped_column(JSONB, default=list, nullable=True)
    theme_config: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    generated_code_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    preview_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    published_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    deployment_status: Mapped[DeploymentStatus] = mapped_column(
        Enum(DeploymentStatus), default=DeploymentStatus.DRAFT, nullable=False
    )
    custom_domain: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    project_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id"), nullable=True, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )

    project = relationship("Project", back_populates="websites")
    deployments = relationship("WebsiteDeployment", back_populates="website", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"Website(id={self.id}, name={self.name})"


class WebsiteDeployment(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "website_deployments"

    website_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("websites.id"), nullable=False, index=True
    )
    platform: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)
    url: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    logs: Mapped[dict | None] = mapped_column(JSONB, default=list, nullable=True)

    website = relationship("Website", back_populates="deployments")
