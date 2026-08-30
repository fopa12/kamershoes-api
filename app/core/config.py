# backend/app/core/config.py
import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # 🔐 Clé secrète de test Stripe officielle nettoyée (Bypasse le cache système)
    STRIPE_SECRET_KEY: str = "sk_test_51U6vZARjpaxWnLPeNAzR4WiJ06nxhCnC2w92I4WW0hzFyh4wOKoRXZtKrZSPrTz75bazxRbhM1nwXu1F5wpZHDiT00Qzsuy7Vh"
    
    STRIPE_WEBHOOK_SECRET: str = "whsec_votre_cle_ici"
    
    # 🔌 Configuration de la passerelle locale PostgreSQL sous Windows
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "postgresql://postgres:123456789@127.0.0.1:5432/atelier_db"
    )

settings = Settings()
