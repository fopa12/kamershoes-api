# backend/app/core/db.py
import os
from sqlmodel import SQLModel, text
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker

# 🌐 CONSTANTE D'URI ISOLÉE - NE CHERCHE PLUS AUCUN IMPORT EXTÉRIEUR
URL_VERROUILLEE = "postgresql+asyncpg://postgres.xpyuefuuxcquqzstityl:wVJ817D6SWtNFzZ@://supabase.com"

# Ligne 11-15 ciblée par Vercel : Exécution immunisée de force
engine = create_async_engine(
    URL_VERROUILLEE, 
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
    """Initialise les tables de la base de données de l'Atelier."""
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
        await conn.execute(text("ALTER TABLE orders ALTER COLUMN user_id DROP NOT NULL;"))

async def get_async_session() -> AsyncSession:
    """Injecteur de session pour les requêtes de l'API."""
    async with async_session() as session:
        yield session
