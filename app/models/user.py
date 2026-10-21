from enum import Enum
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import Enum as SAEnum
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
    # 🛡️ Attribution automatique du rôle client.
    # Le rôle est enregistré en texte simple ("admin" / "client") : native_enum=False évite
    # un type ENUM PostgreSQL, et values_callable stocke la valeur lisible plutôt que le nom Python.
    role: UserRole = Field(
        default=UserRole.CLIENT,
        index=True,
        sa_type=SAEnum(
            UserRole,
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
            native_enum=False,
            length=20,
        ),
    )
    is_active: bool = Field(default=True)


class User(UserBase, table=True):
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    hashed_password: str

    # 📦 Relation avec les commandes passées pour le suivi des colis
    orders: List["Order"] = Relationship(back_populates="user")