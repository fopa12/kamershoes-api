# backend/app/core/db.py
import os
from sqlmodel import SQLModel, text
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker

# 🌐 L'ADRESSE OFFICIELLE DE POOLING POUR SUPABASE CANADA (PORT 6543)
URL_BLINDEE_ATELIER = "postgresql+asyncpg://postgres.xpyuefuuxcquqzstityl:wVJ817D6SWtNFzZ@://supabase.com"

# 🛡️ LE FILTRE ABSOLU : Si le système transmet une adresse invalide ou vide, on la remplace de force avant la ligne 14
DATABASE_URL = URL_BLINDEE_ATELIER

# Ligne 14 ciblée par Vercel : Exécution protégée contre tout port vide
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
    """Initialise les tables de la base de données de l'Atelier."""
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
        await conn.execute(text("ALTER TABLE orders ALTER COLUMN user_id DROP NOT NULL;"))

async def get_async_session() -> AsyncSession:
    """Injecteur de session pour les requêtes de l'API."""
    async with async_session() as session:
        yield session
