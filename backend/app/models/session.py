import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, func, ForeignKey, UUID as SQLAlchemyUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base_class import Base
from backend.app.models.user import User # Import User for relationship

class ConversationSession(Base):
    __tablename__ = "conversation_sessions"

    id: Mapped[uuid.UUID] = mapped_column(SQLAlchemyUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # session_uuid will likely match the key used in Redis for chat history
    session_uuid: Mapped[uuid.UUID] = mapped_column(SQLAlchemyUUID(as_uuid=True), unique=True, index=True, nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True) # Optional title

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    last_accessed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationship to User
    user: Mapped["User"] = relationship(back_populates="sessions")

    def __repr__(self):
        return f"<ConversationSession(id={self.id}, session_uuid={self.session_uuid}, user_id={self.user_id})>" 