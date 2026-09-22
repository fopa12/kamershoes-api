# backend/standalone_seed.py
# ⚙️ FULLY DECOUPLED INDEPENDENT PRODUCTION POPULATION ENGINE FOR ATELIER LUXURY
import os
import sys

# 🛡️ GHOST SHIELD: Wipe out any broken Windows environment variables before they cause a crash
if "DATABASE_URL" in os.environ:
    del os.environ["DATABASE_URL"]
os.environ.pop("DATABASE_URL", None)

from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()

class Product(Base):
    __tablename__ = "product"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    price_cad = Column(Float, nullable=False)
    image_url = Column(String, nullable=True)
    category = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)

class ProductVariant(Base):
    __tablename__ = "productvariant"
    id = Column(Integer, primary_key=True, index=True)
    size = Column(String, nullable=False)
    color = Column(String, nullable=False)
    stock = Column(Integer, default=0)
    product_id = Column(Integer, ForeignKey("product.id", ondelete="CASCADE"))

def fire_isolated_population():
    print("🚀 Initializing direct connection to Supabase Canada cluster...")
    
    # 🔐 ABSOLUTE INJECTION: Raw string literal prevents variable interception crashes
    engine = create_engine(
        "postgresql://postgres.xpyuefuuxcquqzstityl:KamershoesCanada2026@://supabase.com", 
        echo=False
    )
    
    SessionLocal = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
    
    session = SessionLocal()
    try:
        has_items = session.query(Product).first()
        if has_items:
            print("💡 Remote Supabase tables already populate asset rows. Seeding complete.")
            return

        print("📦 Populating premium workshop catalog grids...")
        
        # A) Loafers
        moccasin = Product(
            name="Mocassin L'Artisan Croco",
            description="Mocassin en cuir véritable motif crocodile, cousu main. Élégance et confort absolu.",
            price_cad=249.99,
            image_url="https://unsplash.com",
            category="chaussures",
            is_active=True
        )
        session.add(moccasin)
        session.flush()
        
        session.add_all([
            ProductVariant(size="42", color="Noir", stock=15, product_id=moccasin.id),
            ProductVariant(size="43", color="Brun", stock=10, product_id=moccasin.id)
        ])

        # B) Babouches
        babouche = Product(
            name="Babouche Royale",
            description="Babouche traditionnelle en cuir souple avec broderies artisanales haut de gamme.",
            price_cad=129.99,
            image_url="https://unsplash.com",
            category="babouches",
            is_active=True
        )
        session.add(babouche)
        session.flush()
        
        session.add_all([
            ProductVariant(size="41", color="Or", stock=8, product_id=babouche.id),
            ProductVariant(size="42", color="Noir", stock=12, product_id=babouche.id)
        ])

        # C) Luxury Bags
        bag = Product(
            name="Le Grand Sac Atelier",
            description="Sac à main d'exception en cuir pleine fleur, finitions métalliques dorées.",
            price_cad=450.00,
            image_url="https://unsplash.com",
            category="sacs",
            is_active=True
        )
        session.add(bag)
        session.flush()
        session.add(ProductVariant(size="Unique", color="Bordeaux", stock=5, product_id=bag.id))

        session.commit()
        print("🎉 Success! The isolated population script completed 100% to Supabase Canada!")

    except Exception as e:
        session.rollback()
        print(f"❌ Core processing error: {str(e)}")
    finally:
        session.close()

if __name__ == "__main__":
    fire_isolated_population()
