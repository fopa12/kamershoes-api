# backend/seed_clean.py
# ⚙️ 100% INDEPENDENT PRODUCTION ENGINE - BYPASSES ALL PROJECT INITIALIZATION BLOCKS
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker

# 🌐 SECURE PRODUCTION ENDPOINT LINK HARCODED WITHOUT APP CONFIGURATION INTERFERENCE
DATABASE_URL = "postgresql://postgres.xpyuefuuxcquqzstityl:KamershoesCanada2026@://supabase.com"

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

def run_isolated_seed():
    print("🚀 Connecting cleanly to Supabase Canada cluster...")
    engine = create_engine(DATABASE_URL, echo=False)
    SessionLocal = sessionmaker(bind=engine)
    
    # Map tables directly on Supabase Cloud without touching SQLModel background tasks
    Base.metadata.create_all(engine)
    
    session = SessionLocal()
    try:
        if session.query(Product).first():
            print("💡 The Supabase database already contains items. Seeding bypassed safely.")
            return
        
        print("📦 Populating premium showroom catalog grids...")
        
        # A) Loafers Collection
        m = Product(
            name="Mocassin L'Artisan Croco", 
            description="Cuir veritable motif crocodile, cousu main. Elegance et confort absolu.", 
            price_cad=249.99, 
            image_url="https://unsplash.com", 
            category="chaussures", 
            is_active=True
        )
        session.add(m)
        session.flush()
        session.add_all([ProductVariant(size="42", color="Noir", stock=15, product_id=m.id)])
        
        # B) Babouches Collection
        b = Product(
            name="Babouche Royale", 
            description="Babouche traditionnelle en cuir souple avec broderies artisanales haut de gamme.", 
            price_cad=129.99, 
            image_url="https://unsplash.com", 
            category="babouches", 
            is_active=True
        )
        session.add(b)
        session.flush()
        session.add_all([ProductVariant(size="42", color="Noir", stock=12, product_id=b.id)])
        
        # C) Luxury Bags Collection
        s = Product(
            name="Le Grand Sac Atelier", 
            description="Sac a main d exception en cuir pleine fleur, finitions metalliques dorees.", 
            price_cad=450.00, 
            image_url="https://unsplash.com", 
            category="sacs", 
            is_active=True
        )
        session.add(s)
        session.flush()
        session.add_all([ProductVariant(size="Unique", color="Bordeaux", stock=5, product_id=s.id)])
        
        session.commit()
        print("🎉 SUCCESS TOTAL : Le catalogue a ete injecte a 100% sur Supabase Canada !")

    except Exception as e:
        session.rollback()
        print(f"❌ Error during seeding: {str(e)}")
    finally:
        session.close()

if __name__ == "__main__":
    run_isolated_seed()
