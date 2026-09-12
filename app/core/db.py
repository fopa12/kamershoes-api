# backend/app/core/db.py
import os
from sqlmodel import SQLModel, text
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker

# 🌐 LECTURE ET INJECTION SÉCURISÉE EN CAS DE VARIABLE VIDE
DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()

# Si Vercel ou Windows ne trouve pas la variable, on force le lien Supabase Canada en dur
if not DATABASE_URL:
    DATABASE_URL = "postgresql://postgres.xpyuefuuxcquqzstityl:wVJ8%2F7D6SWtNFzZ@://supabase.com"

# 🚀 Conversion automatique et obligatoire pour le pilote asynchrone exigé par le Cloud
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

# Création du moteur de base de données sans option de pool bloquante pour Vercel
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
