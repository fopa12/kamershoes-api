# backend/app/core/db.py
import os
from sqlmodel import SQLModel, text
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker

# 🌐 LIAISON DIRECTE IMMUNISÉE CONTRE L'ERREUR DE PORT VIDE
URL_VALIDE_CLOUD = "postgresql+asyncpg://postgres.xpyuefuuxcquqzstityl:wVJ817D6SWtNFzZ@://supabase.com"

# Ligne 11 ciblée par Vercel : Forçage asynchrone explicite
engine = create_async_engine(
    str(URL_VALIDE_CLOUD), 
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
    """Builds missing database tables and matches relational tracking parameters."""
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
        await conn.execute(text("ALTER TABLE orders ALTER COLUMN user_id DROP NOT NULL;"))

async def get_async_session() -> AsyncSession:
    """Dependency injector wrapping live sessions for transactional middleware."""
    async with async_session() as session:
        yield session
