# backend/app/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # 🔐 Tous les secrets sont lus depuis les variables d'environnement
    # (Vercel : Project > Settings > Environment Variables, ou fichier .env en local).
    # Les noms ci-dessous doivent correspondre EXACTEMENT aux noms des variables.
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""

    # 🌐 URL Supabase (Transaction pooler, port 6543), au format :
    # postgresql+asyncpg://USER:MOT_DE_PASSE@HOTE:6543/postgres
    DATABASE_URL: str = ""

    # Lit aussi un fichier .env local (jamais envoyé sur GitHub) et ignore les variables inconnues
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()