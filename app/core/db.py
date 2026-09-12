# backend/app/core/db.py
import os
from sqlmodel import SQLModel, text
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker

# 🌐 SECURE TARGET LINK ASSIGNMENT: Resolves empty environment variable issues instantly
DATABASE_URL = os.environ.get("DATABASE_URL")

# If Vercel environment variables are empty or loading slow, inject fallback directly
if not DATABASE_URL or DATABASE_URL.strip() == "":
    DATABASE_URL = "postgresql://postgres.xpyuefuuxcquqzstityl:wVJ8%2F7D6SWtNFzZ@://supabase.com"

# 🚀 Force standard connection string format conversion into asyncpg format
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

# Initialize the persistent serverless engine with absolute fallback parameters
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    future=True
)

async_session = sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

async_session_maker = async_session

async def init_db():
    """Initializes schema blueprints and sets the critical nullable constraint on users."""
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
        await conn.execute(text("ALTER TABLE orders ALTER COLUMN user_id DROP NOT NULL;"))

async def get_async_session() -> AsyncSession:
    """Dependency injection gateway utilized by products and orders router models."""
    async with async_session() as session:
        yield session
