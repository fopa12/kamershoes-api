# backend/main.py
import os
import sys

# 🛡️ PROTECTION ULTIME VERCEL : Injection prioritaire de l'URL pour tuer le ValueError de SQLAlchemy
DATABASE_PRODUCTION_URL = "postgresql+asyncpg://postgres.xpyuefuuxcquqzstityl:KamershoesCanada2026@://supabase.com"

os.environ["DATABASE_URL"] = DATABASE_PRODUCTION_URL

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Les imports métiers s'exécutent maintenant après la configuration de la variable d'environnement
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

# 🔐 OUVERTURE DU BOUCLIER CORS POUR LA VITRINE REACT
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
