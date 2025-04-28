from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update

from backend.app.models.user import User
from backend.app.schemas.user import UserCreate, UserUpdate
from backend.app.core.security import get_password_hash
import uuid

async def get_user_by_id(db: AsyncSession, user_id: uuid.UUID) -> User | None:
    """Fetch a user by their UUID."""
    result = await db.execute(select(User).filter(User.id == user_id))
    return result.scalars().first()

async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    """Fetch a user by their email address."""
    result = await db.execute(select(User).filter(User.email == email))
    return result.scalars().first()

async def get_user_by_username(db: AsyncSession, username: str) -> User | None:
    """Fetch a user by their username."""
    result = await db.execute(select(User).filter(User.username == username))
    return result.scalars().first()

async def create_user(db: AsyncSession, user: UserCreate) -> User:
    """Create a new user in the database."""
    hashed_password = get_password_hash(user.password)
    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
        is_active=user.is_active,
        is_superuser=user.is_superuser
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user

# Placeholder for update user - more complex due to optional fields and password hashing
# async def update_user(db: AsyncSession, db_user: User, user_in: UserUpdate) -> User:
#     update_data = user_in.model_dump(exclude_unset=True)
#     if "password" in update_data and update_data["password"]:
#         hashed_password = get_password_hash(update_data["password"])
#         update_data["hashed_password"] = hashed_password
#         del update_data["password"]
#     else:
#         # Ensure password/hashed_password is not accidentally nulled if not provided
#         update_data.pop("password", None)
#         update_data.pop("hashed_password", None)

#     # Update the user fields
#     for field, value in update_data.items():
#         setattr(db_user, field, value)

#     db.add(db_user)
#     await db.commit()
#     await db.refresh(db_user)
#     return db_user

# Placeholder for delete user
# async def delete_user(db: AsyncSession, user_id: uuid.UUID) -> User | None:
#     user = await get_user_by_id(db, user_id)
#     if user:
#         await db.delete(user)
#         await db.commit()
#     return user 