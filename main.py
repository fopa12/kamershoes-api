# backend/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Atelier Cameroun-Canada E-commerce API",
    description="Back-end Serverless pour maroquinerie de luxe",
    version="2.0.0"
)

# 🔐 BOUCLIER CORS TOTALEMENT OUVERT POUR BRISER LA BARRIÈRE DE REACT
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🛡️ CHARGEMENT SÉCURISÉ DES ROUTEURS POUR CAPTURER L'ERREUR 500
try:
    from app.api.auth import router as auth_router
    from app.api.products import router as products_router
    from app.api.orders import router as orders_router
    from app.api.payments import router as payments_router
    from app.api.uploads import router as uploads_router

    app.include_router(auth_router)
    app.include_router(products_router)
    app.include_router(orders_router)
    app.include_router(payments_router)
    app.include_router(uploads_router)
    
    global_error = None
except Exception as e:
    import traceback
    global_error = f"💥 Crash au chargement du module: {str(e)}\n{traceback.format_exc()}"
    print(global_error)

@app.get("/")
async def root():
    if global_error:
        return {"status": "error", "details": global_error}
    return {"status": "operational", "message": "Atelier Kamershoes Cloud Connect active !"}

@app.get("/products/")
async def backup_products():
    if global_error:
        return {"status": "error", "error_message": "Le serveur est bloqué par une importation", "details": global_error}
    return []
