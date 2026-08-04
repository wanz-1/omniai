import uuid
from sqlalchemy import Enum, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.constants import CreditTransactionType
from app.models.base import Base, TimestampMixin, UUIDMixin


class CreditTransaction(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "credit_transactions"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    organization_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True, index=True
    )
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    balance_after: Mapped[int] = mapped_column(Integer, nullable=False)
    type: Mapped[CreditTransactionType] = mapped_column(
        Enum(CreditTransactionType), nullable=False
    )
    description: Mapped[str | None] = mapped_column(String(300), nullable=True)
    meta_data: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)

    def __repr__(self) -> str:
        return f"CreditTransaction(id={self.id}, amount={self.amount}, type={self.type})"
