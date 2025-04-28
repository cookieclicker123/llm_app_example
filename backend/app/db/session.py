from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import sessionmaker
from backend.app.core.config import settings

# Create the async engine using the DATABASE_URL from settings
# pool_pre_ping=True helps prevent connection errors after long idle periods
async_engine = create_async_engine(
    settings.DATABASE_URL.unicode_string(), # Ensure it's a string
    pool_pre_ping=True,
    echo=settings.DB_ECHO_LOG, # Set to True in dev for SQL logging
)

# Create an async session factory
# expire_on_commit=False prevents attributes from expiring after commit,
# useful if objects are accessed outside the session context sometimes.
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Dependency to get an async database session
async def get_db_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close() 