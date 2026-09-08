# backend/main.py
import os
import sys

# 🗺️ AJUSTEMENT WINDOWS/CLOUD : Aligne les chemins de fichiers pour Vercel
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Importations directes de vos modules fonctionnels d'origine
from app.api.products import router as products_router
from app.api.orders import router as orders_router
from app.api.payments import router as payments_router
from app.api.auth import router as auth_router
from app.api.uploads import router as uploads_router

app = FastAPI(
    title="kamershoes-Canada E-commerce API",
    description="Back-end Serverless pour maroquinerie de luxe",
    version="2.0.0"
)

# 🔐 BOUCLIER CORS TOTALEMENT OUVERT
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Raccordement de vos modules de vente
app.include_router(auth_router)
app.include_router(products_router)
app.include_router(orders_router)
app.include_router(payments_router)
app.include_router(uploads_router)

@app.get("/")
async def root():
    return {"status": "operational", "message": "Atelier Kamershoes Cloud Connect active !"}
