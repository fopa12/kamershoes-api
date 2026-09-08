# backend/app/app/core/db.py
# ⚙️ MOTEUR DE SESSION ASYNCHRONE SUPABASE CANADA IMMUNISÉ POUR VERCEL CLOUD
import os
from contextlib import asynccontextmanager
from sqlmodel import SQLModel, text
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker

# 🌐 LECTURE DIRECTE DE LA VARIABLE SYSTÈME (Bypasse les crashs de validation pydantic settings)
DATABASE_URL = os.environ.get("DATABASE_URL")

# Sécurité si Vercel met quelques millisecondes à charger la variable d'environnement
if not DATABASE_URL:
    DATABASE_URL = "postgresql://postgres.xpyuefuuxcquqzstityl:wVJ8%2F7D6SWtNFzZ@://supabase.com"

# Conversion automatique obligatoire pour le pilote asynchrone asyncpg exigé par le Cloud
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

# Création du moteur asynchrone avec un pool de connexions optimisé pour l'Atelier
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    future=True,
    pool_size=20,
    max_overflow=10
)

# Harmonisation des sessions pour tous vos routeurs FastAPI d'origine
async_session = sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

# Alias de sécurité pour conserver la compatibilité avec vos scripts locaux (seed.py)
async_session_maker = async_session

async def init_db():
    """ Crée les tables en base de données et ajuste la contrainte de la table orders """
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
        await conn.execute(text("ALTER TABLE orders ALTER COLUMN user_id DROP NOT NULL;"))
        print("🔓 [PostgreSQL] Contrainte synchronisée : orders.user_id est NULLABLE.")

async def get_async_session() -> AsyncSession:
    """ Injecteur de dépendance utilisé par votre fichier products.py (Depends) """
    async with async_session() as session:
        yield session
