import uuid
from datetime import datetime
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class AIOrganizationOS(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "ai_organization_os"

    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)
    config: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    metrics: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    departments = relationship("AIDepartment", back_populates="organization_os", cascade="all, delete-orphan")
    workflows = relationship("AutonomousWorkflow", back_populates="organization_os", cascade="all, delete-orphan")

    def __repr__(self):
        return f"AIOrganizationOS(id={self.id}, name={self.name})"


class AIDepartment(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "ai_departments"

    organization_os_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("ai_organization_os.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    department_type: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    capabilities: Mapped[list | None] = mapped_column(JSONB, default=list, nullable=True)
    agents: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    metrics: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    organization_os = relationship("AIOrganizationOS", back_populates="departments")

    def __repr__(self):
        return f"AIDepartment(id={self.id}, name={self.name})"


class AutonomousWorkflow(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "autonomous_workflows"

    organization_os_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("ai_organization_os.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    workflow_type: Mapped[str] = mapped_column(String(50), nullable=False)
    trigger: Mapped[str | None] = mapped_column(String(100), nullable=True)
    steps: Mapped[list | None] = mapped_column(JSONB, default=list, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)
    is_automatic: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_executed: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    execution_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    config: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    metrics: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)

    organization_os = relationship("AIOrganizationOS", back_populates="workflows")

    def __repr__(self):
        return f"AutonomousWorkflow(id={self.id}, name={self.name})"


class DepartmentAgent(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "department_agents"

    department_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("ai_departments.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    agent_type: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    capabilities: Mapped[list | None] = mapped_column(JSONB, default=list, nullable=True)
    system_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    config: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    performance: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)

    def __repr__(self):
        return f"DepartmentAgent(id={self.id}, name={self.name})"
