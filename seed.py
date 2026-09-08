# backend/seed.py
import asyncio
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

# 🔒 Alignement de la mémoire pour éviter le crash de relation SQL
from app.models.user import User
from app.models.product import Product, ProductVariant
from app.models.order import Order, OrderItem

from app.core.db import engine

async def seed_luxury_catalog():
    print("🚀 Connexion au cluster PostgreSQL Supabase Canada...")
    
    async with AsyncSession(engine) as session:
        # Vérification si la base contient déjà les produits
        result = await session.exec(select(Product))
        existing_products = result.all()
        
        if len(existing_products) > 0:
            print("💡 Le catalogue Cloud contient déjà vos articles. Fin du seeding.")
            return

        print("📦 Injection des confections artisanales de maroquinerie (Sacs, Mocassins, Babouches)...")

        # 👜 ARTICLE 1 : Sac de Prestige
        bag = Product(
            name="Le Sac Cabas Horizon - Cuir Grainé Noir",
            description="Sac cabas intemporel confectionné à la main. Doublure en suède rouge signature, finitions métalliques en laiton poli.",
            price_cad=1250.00,
            image_url="https://unsplash.com",
            category="Sacs",
            is_active=True
        )
        session.add(bag)
        await session.flush()

        session.add(ProductVariant(product_id=bag.id, size=None, color="Noir Ébène", stock=15))
        session.add(ProductVariant(product_id=bag.id, size=None, color="Bordeaux Royal", stock=8))

        # 👞 ARTICLE 2 : Mocassins d'Atelier
        shoes = Product(
            name="Le Mocassin Oxford - Daim Marron Tabac",
            description="Mocassins de conduite traditionnels montés sur une semelle à picots en gomme naturelle.",
            price_cad=480.00,
            image_url="https://unsplash.com",
            category="Chaussures",
            is_active=True
        )
        session.add(shoes)
        await session.flush()

        session.add(ProductVariant(product_id=shoes.id, size=8, color="Marron Tabac", stock=20))
        session.add(ProductVariant(product_id=shoes.id, size=9, color="Marron Tabac", stock=25))

        # 🥿 ARTICLE 3 : Babouches Royales (Nouveauté)
        babouches = Product(
            name="La Babouche Impériale - Cuir Souple Ciselé",
            description="Babouches artisanales en cuir d'agneau ultra-souple. Cousues main avec des motifs traditionnels ciselés pour un confort absolu au quotidien.",
            price_cad=220.00,
            image_url="https://unsplash.com",
            category="Babouches",
            is_active=True
        )
        session.add(babouches)
        await session.flush()

        session.add(ProductVariant(product_id=babouches.id, size=39, color="Or Artisanal", stock=12))
        session.add(ProductVariant(product_id=babouches.id, size=41, color="Or Artisanal", stock=18))
        session.add(ProductVariant(product_id=babouches.id, size=43, color="Or Artisanal", stock=10))

        await session.commit()
        print("🎉 Catalogue de l'Atelier synchronisé avec succès ! 3 collections et 7 variantes en stock.")

if __name__ == "__main__":
    asyncio.run(seed_luxury_catalog())
