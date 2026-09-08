# backend/main.py
# ⚙️ LOGIQUE D'ALLUMAGE SANS SERVEUR (SERVERLESS) OPTIMISÉE POUR VERCEL CLOUD
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import products, orders, payments, auth, uploads  # 🌄 Routeurs d'entreprise

# 🔓 On retire l'événement lifespan qui faisait crasher Vercel au démarrage (Erreur 500)
app = FastAPI(
    title="Atelier Cameroun-Canada E-commerce API",
    description="Back-end Serverless, fiscalisé et sécurisé pour maroquinerie de luxe",
    version="2.0.0"
)

# 🔐 MIDDLEWARE CORS TOTALEMENT OUVERT POUR LE FRONTEND REACT LOCAL ET EN LIGNE
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],  # Autorise GET, POST, OPTIONS, etc.
    allow_headers=["*"],  # Autorise tous les jetons d'authentification JWT
)

# 🔌 INCLUSION DES ROUTEURS DE NOTRE ENTREPRISE
app.include_router(auth.router)       # 🔑 Comptes clients
app.include_router(products.router)   # 🛠️ Catalogue (Chaussures, Babouches, Sacs)
app.include_router(orders.router)     # 📊 Moteur fiscal canadien
app.include_router(payments.router)   # 💸 Terminal Stripe & Factures E-mails
app.include_router(uploads.router)    # 🌄 Gestion des images Cloud

@app.get("/")
async def root():
    return {"message": "API V2 de l'Atelier sur Vercel entièrement opérationnelle et connectée à Supabase Canada !"}
