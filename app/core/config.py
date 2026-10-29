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

    # 🔑 Clé de signature des jetons de connexion (JWT) : DÉDIÉE, jamais la clé Stripe.
    # À générer avec : python -c "import secrets; print(secrets.token_hex(32))"
    SECRET_KEY: str = ""

    # 📧 Envoi d'e-mails (Gmail : utilisez un NOUVEAU mot de passe d'application)
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    ADMIN_EMAIL: str = ""  # adresse de repli pour les notifications

    # ☁️ Cloudinary (téléversement d'images)
    CLOUDINARY_CLOUD_NAME: str = ""
    CLOUDINARY_API_KEY: str = ""
    CLOUDINARY_API_SECRET: str = ""

    # Lit aussi un fichier .env local (jamais envoyé sur GitHub) et ignore les variables inconnues
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()