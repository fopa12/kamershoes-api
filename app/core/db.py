# backend/app/core/db.py
# ⚙️ LOGIQUE DE CONNEXION POSTGRESQL OPTIMISÉE POUR L'ARCHITECTURE SERVERLESS VERCEL
import os
from contextlib import asynccontextmanager
from sqlmodel import SQLModel, text
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker

# 🌐 Lecture brute et sécurisée de la variable d'environnement Supabase Canada
DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL:
    DATABASE_URL = "postgresql://postgres.xpyuefuuxcquqzstityl:wVJ8%2F7D6SWtNFzZ@://supabase.com"

# Conversion automatique obligatoire vers le pilote asynchrone asyncpg
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

# 🚀 MOTEUR SERVERLESS : On retire pool_size et max_overflow pour éviter l'erreur 500 sur Vercel
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    future=True
)

# Fabrique de sessions asynchrones synchronisée avec vos routeurs FastAPI d'origine
async_session = sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

async_session_maker = async_session

async def init_db():
    """ Crée les tables en base de données et ajuste la contrainte de la table orders """
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
        await conn.execute(text("ALTER TABLE orders ALTER COLUMN user_id DROP NOT NULL;"))

async def get_async_session() -> AsyncSession:
    """ Injecteur de dépendance utilisé par votre fichier products.py (Depends) """
    async with async_session() as session:
        yield session
