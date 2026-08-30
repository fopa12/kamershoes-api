from enum import Enum
from typing import List, Optional
from sqlmodel import Field, Relationship, SQLModel

# 🏷️ Énumération stricte des catégories de votre atelier pour le marché canadien
class ProductCategory(str, Enum):
    SHOES = "chaussures"
    SLIPPERS = "babouches"
    BAGS = "sacs"

class ProductBase(SQLModel):
    name: str = Field(index=True, max_length=100)
    description: str = Field(max_length=1000)
    price_cad: float = Field(default=0.0)  # Prix affiché au Canada
    image_url: str
    category: ProductCategory = Field(default=ProductCategory.SHOES, index=True)  # 🎒 Tri automatique des articles
    is_active: bool = Field(default=True)

class Product(ProductBase, table=True):
    __tablename__ = "products"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Relation un-à-plusieurs : un produit a plusieurs déclinaisons (tailles/couleurs)
    variants: List["ProductVariant"] = Relationship(back_populates="product")

class ProductVariantBase(SQLModel):
    size: Optional[int] = Field(default=None, index=True)  # Optionnel (ex: Pointure pour chaussures/babouches, None pour sacs)
    color: Optional[str] = Field(default=None, max_length=50)  # Optionnel (ex: Noir, Marron, Kaki pour vos sacs de cuir)
    stock: int = Field(default=0)  # Quantité physique disponible au Canada
    product_id: int = Field(foreign_key="products.id")

class ProductVariant(ProductVariantBase, table=True):
    __tablename__ = "product_variants"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Relation inverse vers le produit parent
    product: Product = Relationship(back_populates="variants")
