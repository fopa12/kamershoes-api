# backend/main.py
import os
import sys

# Aligne le système de fichiers pour que Vercel trouve le dossier "app"
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Importation directe des routeurs stables de l'Atelier
from app.api.products import router as products_router
from app.api.orders import router as orders_router
from app.api.payments import router as payments_router
from app.api.auth import router as auth_router
from app.api.uploads import router as uploads_router

app = FastAPI(
    title="Atelier Cameroun-Canada E-commerce API",
    description="Back-end Serverless pour maroquinerie de luxe",
    version="2.0.0"
)

# 🔐 MIDDLEWARE CORS TOTALEMENT OUVERT POUR BRISER LA BARRIÈRE DU NAVIGATEUR
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Raccordement propre des routeurs de l'Atelier
app.include_router(auth_router)
app.include_router(products_router)
app.include_router(orders_router)
app.include_router(payments_router)
app.include_router(uploads_router)

@app.get("/")
async def root():
    return {"status": "operational", "message": "Atelier Kamershoes Cloud Connect active !"}
