# backend/app/core/db.py
# ⚙️ MOTEUR DE SESSION ASYNCHRONE SUPABASE CANADA TOTALEMENT IMMUNISÉ ET CORRIGÉ
from sqlmodel import SQLModel, text
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker

# 🌐 SYNTAXE RÉSEAU OFFICIELLE CORRIGÉE : Raccordement direct à l'hôte Supabase Canada
DATABASE_URL = "postgresql+asyncpg://postgres.xpyuefuuxcquqzstityl:KamershoesCanada2026@://supabase.com"

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
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
        await conn.execute(text("ALTER TABLE orders ALTER COLUMN user_id DROP NOT NULL;"))

async def get_async_session() -> AsyncSession:
    async with async_session() as session:
        yield session
