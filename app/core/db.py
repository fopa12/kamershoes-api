# backend/app/core/db.py
from contextlib import asynccontextmanager
from sqlmodel import SQLModel, text
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.order import Order # Ensure your Order model is imported to register metadata

# 🚀 URL PostgreSQL asynchrone (pilote +asyncpg)
DATABASE_URL = settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

# Création du moteur asynchrone avec un pool de connexions optimisé pour l'entreprise
engine = create_async_engine(
    DATABASE_URL,
    echo=False,          # Mettre à True en développement pour voir les requêtes SQL brutes
    future=True,
    pool_size=20,        # Nombre de connexions persistantes simultanées
    max_overflow=10      # Connexions temporaires supplémentaires en cas de pic de trafic
)

# Générateur de sessions asynchrones
async_session_maker = sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

async def init_db():
    """ 
    Crée les tables en base de données si elles n'existent pas et 
    aligne automatiquement les contraintes d'intégrité de la table orders.
    """
    async with engine.begin() as conn:
        # 1. Crée les tables si elles n'existent pas encore
        await conn.run_sync(SQLModel.metadata.create_all)
        
        # 2. ⚡ CORRECTIF CRITIQUE DE CONTRAINTE POSTGRESQL (Bypasse l'erreur NotNullViolationError)
        # Force la colonne user_id à accepter les valeurs NULL pour les achats tests et invités.
        await conn.execute(text("ALTER TABLE orders ALTER COLUMN user_id DROP NOT NULL;"))
        print("🔓 [PostgreSQL] Contrainte synchronisée : 'orders.user_id' est désormais NULLABLE.")

async def get_async_session() -> AsyncSession:
    """ Injecteur de dépendance pour FastAPI (utilisé dans Depends()) """
    async with async_session_maker() as session:
        yield session
