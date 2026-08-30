from enum import Enum
from typing import List, Optional, TYPE_CHECKING
from sqlmodel import Field, Relationship, SQLModel

# Éviter les importations circulaires pendant la validation des schémas
if TYPE_CHECKING:
    from app.models.order import Order

# 🔐 Énumération des rôles pour sécuriser l'accès à l'administration de l'atelier
class UserRole(str, Enum):
    ADMIN = "admin"      # Vous (l'artisan créateur)
    CLIENT = "client"    # Les acheteurs canadiens et internationaux

class UserBase(SQLModel):
    email: str = Field(unique=True, index=True)
    full_name: str
    role: UserRole = Field(default=UserRole.CLIENT, index=True)  # 🛡️ Attribution automatique du rôle client
    is_active: bool = Field(default=True)

class User(UserBase, table=True):
    __tablename__ = "users"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    hashed_password: str
    
    # 📦 Réactivation de la relation de niveau entreprise avec les commandes passées pour le suivi des colis
    orders: List["Order"] = Relationship(back_populates="user")
