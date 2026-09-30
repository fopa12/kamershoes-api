# backend/app/core/config.py
import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # 🔐 Clé secrète de test Stripe officielle nettoyée
    STRIPE_SECRET_KEY: str = "sk_test_51U6vZARjpaxWnLPeNAzR4WiJ06nxhCnC2w92I4WW0hzFyh4wOKoRXZtKrZSPrTz75bazxRbhM1nwXu1F5wpZHDiT00Qzsuy7Vh"
    
    STRIPE_WEBHOOK_SECRET: str = "whsec_votre_cle_ici"
    
    # 🌐 CONFIGURATION FINALE SÉCURISÉE POUR LE CLUSTER SUPABASE CANADA (PORT 6543)
    # L'adresse de pooling asynchrone est injectée en dur pour couper court à tout crash sur Vercel
    DATABASE_URL: str = "postgresql+asyncpg://postgres.xpyuefuuxcquqzstityl:wVJ817D6SWtNFzZ@://supabase.com"

settings = Settings()
