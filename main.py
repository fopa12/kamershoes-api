# backend/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Importation directe et étanche de vos routeurs de base de l'Atelier
from app.api.auth import router as auth_router
from app.api.products import router as products_router
from app.api.orders import router as orders_router
from app.api.payments import router as payments_router
from app.api.uploads import router as uploads_router

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

# raccordement des briques logiques de l'Atelier
app.include_router(auth_router)
app.include_router(products_router)
app.include_router(orders_router)
app.include_router(payments_router)
app.include_router(uploads_router)

@app.get("/")
async def root():
    return {
        "status": "operational",
        "message": "API V2 de l'Atelier sur Vercel entièrement opérationnelle et connectée à Supabase Canada !"
    }
