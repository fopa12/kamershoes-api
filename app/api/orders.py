# backend/app/api/orders.py
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from app.models.order import Order
from app.schemas.order import TaxEstimationRequest
from app.core.taxes import calculate_order_taxes
from app.models.product import Product
from app.core.db import get_async_session
from typing import List

router = APIRouter(prefix="/orders", tags=["Orders"])

@router.get("/history", response_model=List[Order])
async def get_orders_history(session: AsyncSession = Depends(get_async_session)):
    """
    Récupère toutes les commandes enregistrées dans PostgreSQL pour l'historique d'audit.
    """
    try:
        statement = select(Order).order_by(Order.created_at.desc())
        result = await session.execute(statement)
        orders = result.scalars().all()
        return orders
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur historique : {str(e)}")


@router.post("/estimate-tax")
async def estimate_order_tax(payload: TaxEstimationRequest, session: AsyncSession = Depends(get_async_session)):
    """
    Calcule dynamiquement les taxes provinciales canadiennes (TPS, TVQ, TVP, TVH) 
    pour l'affichage en direct de la facture dans le panier d'achat.
    """
    try:
        subtotal = 0.0
        for item in payload.items:
            product = await session.get(Product, item.product_id)
            if not product or not product.is_active:
                raise HTTPException(status_code=404, detail=f"Produit ID {item.product_id} introuvable")
            subtotal += product.price_cad * item.quantity
            
        tax_summary = calculate_order_taxes(subtotal, payload.province_code)
        return tax_summary
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
