# backend/main.py
import os
import sys

# 🛡️ PROTECTION ULTIME VERCEL : URL de pooling officielle avec mot de passe encodé pour SQLAlchemy
URL_VALIDE = "postgresql+asyncpg://postgres.xpyuefuuxcquqzstityl:wVJ817D6SWtNFzZ@://supabase.com"

os.environ["DATABASE_URL"] = URL_VALIDE

# Hack mémoire : empêche n'importe quelle dépendance interne de recharger une variable d'environnement vide
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

# Importation sécurisée des routeurs après l'initialisation de l'URI mémoire
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

# 🔐 BOUCLIER CORS SECONDAIRE EN CAS DE BESOIN
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
