# backend/main.py
import os
import sys

# 🛡️ LE VERROU ABSOLU : Écrase et fige la variable dans tout le moteur Python de Vercel
URL_VALIDE = "postgresql+asyncpg://postgres.xpyuefuuxcquqzstityl:KamershoesCanada2026@://supabase.com"

os.environ["DATABASE_URL"] = URL_VALIDE

# Hack système : si un module tiers essaie d'analyser une variable d'environnement vide, on le court-circuite
class SafeEnviron(dict):
    def get(self, key, default=None):
        if key == "DATABASE_URL":
            return URL_VALIDE
        return super().get(key, default)
    def __getitem__(self, key):
        if key == "DATABASE_URL":
            return URL_VALIDE
        return super().__getitem__(key)

os.environ = SafeEnviron(os.environ)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Les modules de l'Atelier peuvent maintenant charger en toute sécurité, le ValueError est impossible
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

# 🔐 OUVERTURE DU CORS POUR LA VITRINE REACT
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
