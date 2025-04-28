import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete

from backend.app.models.session import ConversationSession
from backend.app.schemas.session import SessionCreate, SessionUpdate

async def create_session(
    db: AsyncSession, *, session_in: SessionCreate, user_id: uuid.UUID
) -> ConversationSession:
    """Create a new conversation session metadata entry."""
    db_session = ConversationSession(
        **session_in.model_dump(),
        user_id=user_id,
        # created_at and last_accessed_at have server defaults
    )
    db.add(db_session)
    await db.commit()
    await db.refresh(db_session)
    return db_session

async def get_session_by_session_uuid(
    db: AsyncSession, *, session_uuid: uuid.UUID
) -> ConversationSession | None:
    """Get session metadata by the session UUID (used in Redis key)."""
    result = await db.execute(
        select(ConversationSession).filter(ConversationSession.session_uuid == session_uuid)
    )
    return result.scalars().first()

async def get_sessions_by_user(
    db: AsyncSession, *, user_id: uuid.UUID, skip: int = 0, limit: int = 100
) -> list[ConversationSession]:
    """Get a list of session metadata entries for a specific user."""
    result = await db.execute(
        select(ConversationSession)
        .filter(ConversationSession.user_id == user_id)
        .order_by(ConversationSession.last_accessed_at.desc()) # Show most recent first
        .offset(skip)
        .limit(limit)
    )
    return list(result.scalars().all())

async def update_session(
    db: AsyncSession, *, db_session: ConversationSession, session_in: SessionUpdate
) -> ConversationSession:
    """Update session metadata (e.g., title)."""
    update_data = session_in.model_dump(exclude_unset=True)
    # last_accessed_at is updated automatically by onupdate=func.now()
    # update_data["last_accessed_at"] = datetime.now(timezone.utc)
    
    for field, value in update_data.items():
        setattr(db_session, field, value)
        
    db.add(db_session)
    await db.commit()
    await db.refresh(db_session)
    return db_session

# Note: update_session_last_accessed might not be strictly necessary if only updating title,
# as the model's onupdate handles last_accessed_at. If other actions should trigger 
# an update without changing data, a dedicated function or manual update could be used.
# async def touch_session(db: AsyncSession, *, db_session: ConversationSession) -> ConversationSession:
#     """Explicitly update last_accessed_at without changing other data."""
#     db_session.last_accessed_at = datetime.now(timezone.utc)
#     db.add(db_session)
#     await db.commit()
#     await db.refresh(db_session)
#     return db_session

async def delete_session(db: AsyncSession, *, db_session: ConversationSession) -> ConversationSession:
    """Delete session metadata."""
    # The relationship cascade should handle related data if configured
    await db.delete(db_session)
    await db.commit()
    return db_session # Return the deleted object (transient state) 