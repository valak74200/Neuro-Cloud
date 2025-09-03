from app.infrastructure.db.postgres import Base
from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column


class MemoryModel(Base):
    """SQLAlchemy model for persisting domain Memory entities.

    This model intentionally keeps a minimal schema aligned with the domain:
    - id: stable UUID string provided by the domain
    - user_id: owner of the memory (indexed)
    - content: free text content
    - source: string literal reflecting MemorySource
    Extra technical columns (created_at) are allowed for auditing.
    """

    __tablename__ = "memories"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[str] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
