# backend/app/models/order.py
from enum import Enum
from typing import List, Optional
from datetime import datetime
from sqlalchemy import Enum as SAEnum
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
    # Le statut est enregistré en texte simple dans la base ("PENDING", "PAID", "SHIPPED", "DELIVERED").
    # native_enum=False : pas de type ENUM PostgreSQL à maintenir (ajouter un statut ne demande
    # plus de migration compliquée). L'API continue d'afficher les libellés français.
    status: OrderStatus = Field(
        default=OrderStatus.PENDING,
        index=True,
        sa_type=SAEnum(OrderStatus, native_enum=False, length=50),
    )
    tracking_number: Optional[str] = Field(default=None)  # Numéro de suivi Postes Canada

    # ✅ FIX: datetime sans fuseau explicite pour éviter les erreurs PostgreSQL
    # "offset-naive vs offset-aware" avec la colonne timestamp.
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Order(OrderBase, table=True):
    __tablename__ = "orders"

    id: Optional[int] = Field(default=None, primary_key=True)

    # 🔌 Relations
    user: Optional["User"] = Relationship(back_populates="orders")
    items: List["OrderItem"] = Relationship(back_populates="order", sa_relationship_kwargs={"lazy": "selectin"})


class OrderItem(SQLModel, table=True):
    __tablename__ = "order_items"

    id: Optional[int] = Field(default=None, primary_key=True)
    order_id: int = Field(foreign_key="orders.id", index=True)
    product_id: int = Field(foreign_key="products.id")
    variant_id: int = Field(foreign_key="product_variants.id")
    quantity: int
    price_snap: float  # Capture du prix au moment de l'achat (anti-fluctuation)

    order: Order = Relationship(back_populates="items")