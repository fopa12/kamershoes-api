# backend/main.py
import os
import sys

# 🛡️ PROTECTION VERCEL ABSOLUE : Surcharge mémoire immédiate avant tout chargement de modules locaux
DATABASE_CLOUD_URL = "postgresql+asyncpg://postgres.xpyuefuuxcquqzstityl:KamershoesCanada2026@://supabase.com"

os.environ["DATABASE_URL"] = DATABASE_CLOUD_URL

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Les routes métiers chargent désormais en toute sécurité avec la variable initialisée
from app.api.auth import router as auth_router
from app.api.products import router as products_router
from app.api.orders import router as orders_router
from app.api.payments import router as payments_router
from app.api.uploads import router as uploads_router

app = FastAPI(
    title="Atelier Cameroun-Canada E-commerce API",
    description="Back-end Serverless pour maroquinerie de luxe",
    version="2.0.0"
)

# 🔐 BOUCLIER DE SÉCURITÉ CORS POUR LA VITRINE REACT LOCALE
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(products_router)
app.include_router(orders_router)
app.include_router(payments_router)
app.include_router(uploads_router)

@app.get("/")
async def root():
    return {"status": "operational", "message": "Atelier Kamershoes Cloud Connect active !"}
