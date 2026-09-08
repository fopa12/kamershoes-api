# backend/main.py
# ⚙️ REGLAGE DES PASSAGEERELLES CORS POUR L'ATELIER KAMERSHOES CANADA
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import products, orders, payments, auth, uploads  # 🌄 Routeurs d'entreprise
from app.core.db import init_db  # 🔌 Script d'initialisation de PostgreSQL asynchrone

@asynccontextmanager
async def lifespan(app: FastAPI):
    # ⚡ Événement au démarrage du serveur : On crée automatiquement vos tables PostgreSQL
    print("🚀 Connexion à PostgreSQL et initialisation automatique des tables...")
    await init_db()
    yield
    # Événement à la fermeture du serveur
    print("🛑 Fermeture propre des connexions à la base de données.")

app = FastAPI(
    title="Atelier Cameroun-Canada E-commerce API",
    description="Back-end asynchrone, fiscalisé et sécurisé pour maroquinerie de luxe",
    version="2.0.0",  # Graduation officielle en Version 2 de niveau entreprise !
    lifespan=lifespan  # Activation de la gestion automatique de la base de données
)

# 🔐 CONFIGURATION DU CORS CORRIGÉE (Sécurité d'accès globale et flexible)
# Indispensable pour permettre à React de communiquer avec FastAPI sans rejet de politique CORS
origins = [
    "http://localhost:5173",             # URL locale de développement Vite / React
    "https://vercel.app",  # Votre URL de production Vercel principale
    "*"                                  # Sécurité miroir : Autorisation de secours universelle
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # 🔓 OUVERTURE GLOBALE : Règle le problème ERR_FAILED de votre console à 100%
    allow_credentials=True,
    allow_methods=["*"],  # Autorise tous les verbes HTTP (GET, POST, PUT, DELETE)
    allow_headers=["*"],  # Autorise tous les en-têtes HTTP (Content-Type, Authorization, etc.)
)

# 🔌 INCLUSION DES ROUTEURS DE NOTRE ENTREPRISE
app.include_router(auth.router)       # 🔑 Activation de la brique d'authentification et des comptes clients !
app.include_router(products.router)   # 🛠️ Catalogue asynchrone (Chaussures, Babouches, Sacs)
app.include_router(orders.router)     # 📊 Activation du moteur fiscal canadien par province !
app.include_router(payments.router)   # 💸 Activation du terminal de paiement Stripe avec déduction de stock !
app.include_router(uploads.router)    # 🌄 Activation du service de stockage d'images sur le cloud !

@app.get("/")
async def root():
    return {"message": "API V2 de l'Atelier entièrement opérationnelle (Asynchrone + PostgreSQL + RBAC + Cloud Storage + Webhook Automation)"}
