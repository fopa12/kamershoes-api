# backend/app/models/order.py
from enum import Enum
from typing import List, Optional
from datetime import datetime
from sqlmodel import Field, Relationship, SQLModel

class OrderStatus(str, Enum):
    PENDING = "En attente de paiement"
    PAID = "Payé - En préparation à l'Atelier"
    SHIPPED = "Expédié - En cours de livraison"
    DELIVERED = "Livré"

class OrderBase(SQLModel):
    user_id: Optional[int] = Field(default=None, foreign_key="users.id", index=True, nullable=True)
    total_amount: float
    tax_amount: float
    province_code: str
    shipping_address: str
    status: OrderStatus = Field(default=OrderStatus.PENDING, index=True)
    tracking_number: Optional[str] = Field(default=None) # Numéro de suivi Postes Canada
    
    # ✅ FIX: Using datetime.utcnow or datetime.now without explicit timezone contexts 
    # to eliminate offset-naive vs offset-aware PostgreSQL DataError mismatches.
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Order(OrderBase, table=True):
    __tablename__ = "orders"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # 🔌 Enterprise Relations Mapping Hooks
    user: Optional["User"] = Relationship(back_populates="orders")
    items: List["OrderItem"] = Relationship(back_populates="order", sa_relationship_kwargs={"lazy": "selectin"})

class OrderItem(SQLModel, table=True):
    __tablename__ = "order_items"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    order_id: int = Field(foreign_key="orders.id", index=True)
    product_id: int = Field(foreign_key="products.id")
    variant_id: int = Field(foreign_key="product_variants.id")
    quantity: int
    price_snap: float # Capture du prix au moment de l'achat (anti-fluctuation)
    
    order: Order = Relationship(back_populates="items")
