# backend/app/core/db.py
# ⚙️ MOTEUR DE SESSION ASYNCHRONE OPTIMISÉ POUR VERCEL (serverless) + SUPABASE POOLER (port 6543)
from uuid import uuid4
from typing import AsyncGenerator

from sqlmodel import SQLModel, text
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from app.core.config import settings

# 📚 Enregistre TOUTES les tables dans SQLModel.metadata (sinon create_all les ignore)
from app.models import order, product, user  # noqa: F401


def _build_database_url(raw_url: str):
    """
    Nettoie et valide DATABASE_URL (lue par settings depuis les variables d'environnement
    Vercel, ou depuis le fichier .env en local). Ne l'affiche jamais : elle contient le mot de passe.
    """
    raw_url = (raw_url or "").strip().strip('"').strip("'")

    if not raw_url:
        raise RuntimeError(
            "DATABASE_URL est vide : ajoutez-la dans les variables d'environnement Vercel "
            "(ou dans le fichier .env en local)."
        )

    # Conversion automatique du pilote (sans toucher une URL qui contient déjà +asyncpg)
    if raw_url.startswith("postgres://"):
        raw_url = raw_url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif raw_url.startswith("postgresql://"):
        raw_url = raw_url.replace("postgresql://", "postgresql+asyncpg://", 1)

    try:
        url = make_url(raw_url)
    except Exception:
        # "from None" : évite d'afficher dans les logs une erreur contenant l'URL
        raise RuntimeError(
            "DATABASE_URL est invalide. Format attendu : "
            "postgresql+asyncpg://USER:MOT_DE_PASSE@HOTE:6543/postgres "
            "(caractères spéciaux du mot de passe à encoder en URL)."
        ) from None

    if not url.host or not url.port or not url.database:
        raise RuntimeError(
            "DATABASE_URL est incomplète : l'hôte, le port ou le nom de la base est manquant "
            "(exemple : ...@aws-0-ca-central-1.pooler.supabase.com:6543/postgres)."
        )

    # Retire les options libpq que asyncpg ne comprend pas (copiées parfois depuis Supabase)
    return url.difference_update_query(["sslmode", "pgbouncer", "supa"])


DATABASE_URL = _build_database_url(settings.DATABASE_URL)

# Moteur asynchrone adapté au mode "Transaction pooler" de Supabase :
# - NullPool : pas de pool côté application (le pooler Supabase s'en charge, et
#   chaque instance serverless Vercel est éphémère). Attention : pool_size et
#   max_overflow sont INCOMPATIBLES avec NullPool.
# - statement_cache_size = 0 : désactive les prepared statements (non supportés
#   en mode transaction, sinon erreur "prepared statement ... does not exist").
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
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
    aligne la contrainte d'intégrité de la table orders.

    ⚠️ À lancer à la main (ou en local), pas à chaque démarrage sur Vercel :
    chaque démarrage à froid exécuterait ces commandes inutilement.
    """
    async with engine.begin() as conn:
        # 1. Crée les tables manquantes
        await conn.run_sync(SQLModel.metadata.create_all)

        # 2. ⚡ CORRECTIF DE CONTRAINTE POSTGRESQL (évite NotNullViolationError)
        #    IF EXISTS : pas d'erreur si la table n'existe pas encore.
        await conn.execute(text("ALTER TABLE IF EXISTS orders ALTER COLUMN user_id DROP NOT NULL;"))
        print("🔓 [PostgreSQL] Contrainte synchronisée : 'orders.user_id' est désormais NULLABLE.")


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """ Injecteur de dépendance pour FastAPI (utilisé dans Depends()) """
    async with async_session() as session:
        yield session