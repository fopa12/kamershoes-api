# backend/app/core/db.py
# ⚙️ MOTEUR DE SESSION ASYNCHRONE OPTIMISÉ POUR VERCEL (serverless) + SUPABASE POOLER (port 6543)
import os
from uuid import uuid4
from typing import AsyncGenerator

from sqlmodel import SQLModel, text
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from app.core.config import settings
from app.models.order import Order  # Enregistrement des métadonnées de l'Atelier

# 🚀 URL PostgreSQL asynchrone
# La variable d'environnement Vercel est prioritaire sur la valeur de config.py
RAW_URL = os.getenv("DATABASE_URL") or settings.DATABASE_URL

if not RAW_URL:
    raise RuntimeError("DATABASE_URL est vide : ajoutez-la dans les variables d'environnement Vercel.")

# Conversion automatique du pilote (sans toucher une URL qui contient déjà +asyncpg)
DATABASE_URL = RAW_URL
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
elif DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

# Moteur asynchrone adapté au mode "Transaction pooler" de Supabase :
# - NullPool : pas de pool côté application (le pooler Supabase s'en charge, et
#   chaque instance serverless Vercel est éphémère). Attention : pool_size et
#   max_overflow sont INCOMPATIBLES avec NullPool, donc retirés.
# - statement_cache_size = 0 : désactive les prepared statements (non supportés
#   en mode transaction, sinon erreur "prepared statement ... does not exist").
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    future=True,
    poolclass=NullPool,
    connect_args={
        "statement_cache_size": 0,
        "prepared_statement_cache_size": 0,
        "prepared_statement_name_func": lambda: f"__asyncpg_{uuid4()}__",
    },
)

# ⚡ SYNCHRONISATION DES NOMS DE SESSIONS POUR ALIGNER TOUS VOS ROUTEURS FASTAPI
async_session = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
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

        # 2. ⚡ CORRECTIF DE CONTRAINTE POSTGRESQL (évite NotNullViolationError)
        await conn.execute(text("ALTER TABLE orders ALTER COLUMN user_id DROP NOT NULL;"))
        print("🔓 [PostgreSQL] Contrainte synchronisée : 'orders.user_id' est désormais NULLABLE.")


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """ Injecteur de dépendance pour FastAPI (utilisé dans Depends()) """
    async with async_session() as session:
        yield session