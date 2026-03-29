from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from .models import Base
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./trend_intel.db")

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
