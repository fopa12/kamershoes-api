# backend/main.py
# ⚙️ LOGIQUE DE RECHERCHE DYNAMIQUE DES MODULES POUR L'ARCHITECTURE VERCEL
import os
import sys

# 🗺️ Guidage de sécurité : Force Python à inclure le dossier backend dans ses calculs de routes
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import products, orders, payments, auth, uploads  # Routeurs d'entreprise

app = FastAPI(
    title="Atelier Cameroun-Canada E-commerce API",
    description="Back-end Serverless, fiscalisé et sécurisé pour maroquinerie de luxe",
    version="2.0.0"
)

# 🔐 BOUCLIER CORS TOTALEMENT OUVERT POUR COMMUNIQUER AVEC REACT
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🔌 INCLUSION DES ROUTEURS DE NOTRE ENTREPRISE
app.include_router(auth.router)       # Comptes clients
app.include_router(products.router)   # Catalogue (Chaussures, Babouches, Sacs)
app.include_router(orders.router)     # Moteur fiscal canadien
app.include_router(payments.router)   # Terminal Stripe & Factures E-mails
app.include_router(uploads.router)    # Gestion des images Cloud

@app.get("/")
async def root():
    return {"message": "API V2 de l'Atelier sur Vercel entièrement opérationnelle et connectée à Supabase Canada !"}
