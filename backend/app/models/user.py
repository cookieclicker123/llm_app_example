import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, func, UUID as SQLAlchemyUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base_class import Base
# Type checking block for forward reference
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from backend.app.models.session import ConversationSession

class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(SQLAlchemyUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    username: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationship to ConversationSession
    sessions: Mapped[list["ConversationSession"]] = relationship(back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', username='{self.username}')>" 