# backend/main.py
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth import router as auth_router
from app.api.products import router as products_router
from app.api.orders import router as orders_router
from app.api.payments import router as payments_router
from app.api.uploads import router as uploads_router

# 🔐 La configuration (DATABASE_URL, clés Stripe...) est lue automatiquement depuis les
# variables d'environnement Vercel par app/core/config.py et app/core/db.py.
# Aucune URL ni aucun secret ne doit être écrit dans ce fichier.

app = FastAPI(
    title="Atelier Cameroun-Canada E-commerce API",
    description="Back-end Serverless pour maroquinerie de luxe",
    version="2.0.0",
)

# 🌐 CORS : liste des sites autorisés à appeler l'API (vitrine React).
# Sur Vercel, ajoutez la variable ALLOWED_ORIGINS, par exemple :
#   https://votre-vitrine.vercel.app,https://www.votre-domaine.com
# Sans cette variable, tous les sites sont autorisés (pratique pour tester, à éviter en production).
_origins_env = os.getenv("ALLOWED_ORIGINS", "").strip()
if _origins_env:
    ALLOWED_ORIGINS = [o.strip() for o in _origins_env.split(",") if o.strip()]
    ALLOW_CREDENTIALS = True
else:
    ALLOWED_ORIGINS = ["*"]
    ALLOW_CREDENTIALS = False  # "*" et credentials ne sont pas compatibles

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=ALLOW_CREDENTIALS,
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