# backend/main.py
import os
import sys

# 🛡️ GLOBAL INFRASTRUCTURE ALIGNMENT
URL_VALIDE = "postgresql+asyncpg://postgres.xpyuefuuxcquqzstityl:wVJ817D6SWtNFzZ@://supabase.com"
SUPABASE_URL = "https://xpyuefuuxcquqzstityl.supabase.co"

os.environ["DATABASE_URL"] = URL_VALIDE
os.environ["SUPABASE_URL"] = SUPABASE_URL

# System Hook: Prevents runtime packages from falling back to empty context variables
class SafeEnviron(dict):
    def get(self, key, default=None):
        if key == "DATABASE_URL":
            return URL_VALIDE
        if key == "SUPABASE_URL":
            return SUPABASE_URL
        return super().get(key, default)
    def __getitem__(self, key):
        if key == "DATABASE_URL":
            return URL_VALIDE
        if key == "SUPABASE_URL":
            return SUPABASE_URL
        return super().__getitem__(key)

os.environ = SafeEnviron(os.environ)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Relative business pathway routing modules
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

# 🔐 CROSS-ORIGIN ACCESS HEADERS RE-CONFIGURED
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
    return {
        "status": "operational", 
        "message": "Atelier Kamershoes Cloud Connect active !",
        "endpoint": SUPABASE_URL
    }
