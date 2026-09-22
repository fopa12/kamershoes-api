# backend/main.py
import os
import sys

# 🛡️ FORÇAGE SYSTÉMIQUE : Injection absolue de la chaîne asynchrone avant TOUS les autres imports du projet
DATABASE_URL_PROD = "postgresql+asyncpg://postgres.xpyuefuuxcquqzstityl:KamershoesCanada2026@://supabase.com"
os.environ["DATABASE_URL"] = DATABASE_URL_PROD

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Les modules métiers s'importent maintenant en toute sécurité
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
