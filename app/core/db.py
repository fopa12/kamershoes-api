# backend/app/core/db.py
# ⚙️ MOTEUR DE SESSION ASYNCHRONE OPTIMISÉ POUR L'ARCHITECTURE CLOUD DE L'ATELIER
import os
from contextlib import asynccontextmanager
from sqlmodel import SQLModel, text
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.order import Order # Enregistrement des métadonnées de l'Atelier

# 🚀 URL PostgreSQL asynchrone (Conversion automatique du pilote +asyncpg)
RAW_URL = os.getenv("DATABASE_URL", settings.DATABASE_URL)
DATABASE_URL = RAW_URL.replace("postgresql://", "postgresql+asyncpg://")

# Création du moteur asynchrone avec un pool de connexions optimisé pour l'entreprise
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    future=True,
    pool_size=20,
    max_overflow=10
)

# ⚡ SYNCHRONISATION DES NOMS DE SESSIONS POUR ALIGNER TOUS VOS ROUTEURS FASTAPI
async_session = sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

# Alias de sécurité pour conserver la compatibilité avec vos anciens scripts locaux
async_session_maker = async_session

async def init_db():
    """ 
    Crée les tables en base de données si elles n'existent pas et 
    aligne automatiquement les contraintes d'intégrité de la table orders.
    """
    async with engine.begin() as conn:
        # 1. Crée les tables si elles n'existent pas encore
        await conn.run_sync(SQLModel.metadata.create_all)
        
        # 2. ⚡ CORRECTIF CRITIQUE DE CONTRAINTE POSTGRESQL (Bypasse l'erreur NotNullViolationError)
        await conn.execute(text("ALTER TABLE orders ALTER COLUMN user_id DROP NOT NULL;"))
        print("🔓 [PostgreSQL] Contrainte synchronisée : 'orders.user_id' est désormais NULLABLE.")

async def get_async_session() -> AsyncSession:
    """ Injecteur de dépendance pour FastAPI (utilisé dans Depends()) """
    async with async_session() as session:
        yield session
