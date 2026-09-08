# backend/main.py
# ⚙️ ARCHITECTURE DE ROUTAGE ENTRÈPRISE SERVERLESS POUR VERCEL CLOUD
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 🔓 Importations relatives directes pour contourner les conflits de dossiers parents
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

# 🔐 MIDDLEWARE CORS SÉCURISÉ POUR BRISER LA BARRIÈRE DE VOTRE COMPOSANT REACT
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Raccordement étanche de vos modules métiers fonctionnels
app.include_router(auth_router)
app.include_router(products_router)
app.include_router(orders_router)
app.include_router(payments_router)
app.include_router(uploads_router)

@app.get("/")
async def root():
    return {
        "status": "operational",
        "message": "API V2 de l'Atelier en ligne connectée à Supabase Canada !"
    }
