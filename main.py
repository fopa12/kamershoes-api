# backend/main.py
import os
import sys

# 🛡️ LE MAÎTRE VERROU : Définition de l'adresse de pooling officielle Supabase Canada
URL_PARFAITE = "postgresql+asyncpg://postgres.xpyuefuuxcquqzstityl:wVJ817D6SWtNFzZ@://supabase.com"

# On injecte l'URL de force dans l'environnement global de Vercel
os.environ["DATABASE_URL"] = URL_PARFAITE

# Hack système global : si une configuration cachée tente de lire os.getenv, on la force à lire l'URL parfaite
class ForceEnviron(dict):
    def get(self, key, default=None):
        if key == "DATABASE_URL":
            return URL_PARFAITE
        return super().get(key, default)
    def __getitem__(self, key):
        if key == "DATABASE_URL":
            return URL_PARFAITE
        return super().__getitem__(key)

os.environ = ForceEnviron(os.environ)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Les modules s'importent maintenant de manière sécurisée après le forçage d'environnement
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

# 🔐 INTERCEPTION DES REQUÊTES DE LA VITRINE REACT
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
