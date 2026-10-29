# backend/app/api/products.py
import traceback
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import delete
from sqlalchemy.orm import selectinload  # ⚡ Charge les relations en asynchrone (évite MissingGreenlet)
from sqlmodel import select, or_
from sqlmodel.ext.asyncio.session import AsyncSession

from app.schemas.product import ProductCreate, ProductRead
from app.models.product import Product, ProductVariant, ProductCategory
from app.models.order import Order, OrderItem
from app.models.user import User
from app.core.db import get_async_session  # Sessions asynchrones Cloud
from app.api.deps import get_current_admin  # Dépendance de sécurité RBAC

router = APIRouter(prefix="/products", tags=["Products"])

# Mot de confirmation exigé pour la purge totale (à passer en paramètre : ?confirm=PURGE-TOUT)
PURGE_CONFIRMATION = "PURGE-TOUT"


# ==========================================================================
# 📝 SCHÉMAS DE MODIFICATION (tous les champs sont facultatifs : on n'envoie que ce qui change)
# ==========================================================================

class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    price_cad: Optional[float] = Field(None, gt=0)
    image_url: Optional[str] = Field(None, max_length=500)
    category: Optional[ProductCategory] = None  # "chaussures", "babouches" ou "sacs"
    is_active: Optional[bool] = None            # false = retiré de la vitrine


class VariantCreate(BaseModel):
    size: Optional[int] = Field(None, ge=0, le=100)   # pointure (vide pour un sac)
    color: Optional[str] = Field(None, max_length=50)
    stock: int = Field(0, ge=0, le=100000)


class VariantUpdate(BaseModel):
    size: Optional[int] = Field(None, ge=0, le=100)
    color: Optional[str] = Field(None, max_length=50)
    stock: Optional[int] = Field(None, ge=0, le=100000)


async def _load_product(session: AsyncSession, product_id: int) -> Optional[Product]:
    """Relit un produit avec ses variantes à jour (pour renvoyer l'état final à la vitrine)."""
    statement = (
        select(Product)
        .where(Product.id == product_id)
        .options(selectinload(Product.variants))
        .execution_options(populate_existing=True)
    )
    result = await session.execute(statement)
    return result.scalars().one_or_none()


def _service_unavailable(err: Exception) -> HTTPException:
    """
    Journalise l'erreur côté serveur (logs Vercel) et renvoie une réponse propre.
    On lève une HTTPException plutôt qu'une erreur brute : elle passe par le middleware CORS,
    donc le navigateur reçoit un vrai message au lieu d'une fausse erreur CORS.
    """
    print(f"💥 Erreur base de données : {err}\n{traceback.format_exc()}")
    return HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Service temporairement indisponible. Réessayez dans un instant.",
    )


# ==========================================================================
# 🛍️ LECTURE (publique)
# ==========================================================================

@router.get("/", response_model=List[ProductRead])
async def list_products(
    category: Optional[str] = None,
    search: Optional[str] = Query(None, max_length=100),  # 🔍 Recherche dynamique croisée
    limit: int = Query(200, ge=1, le=500),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_async_session),
):
    """Récupère les produits actifs avec leurs variantes."""
    try:
        statement = (
            select(Product)
            .where(Product.is_active.is_(True))
            .options(selectinload(Product.variants))
        )

        # 1. Filtre par catégorie ("all" = pas de filtre)
        if category and category not in ("all", "None"):
            try:
                category_filter = ProductCategory(category)
            except ValueError:
                return []  # catégorie inconnue : aucun produit (et non une erreur serveur)
            statement = statement.where(Product.category == category_filter)

        # 2. 🔍 Recherche insensible à la casse (les caractères % et _ saisis sont traités comme du texte)
        if search:
            escaped = search.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            pattern = f"%{escaped}%"
            statement = statement.where(
                or_(
                    Product.name.ilike(pattern, escape="\\"),
                    Product.description.ilike(pattern, escape="\\"),
                )
            )

        statement = statement.order_by(Product.id).offset(offset).limit(limit)
        results = await session.execute(statement)
        return results.scalars().all()

    except Exception as err:
        # ⚠️ On ne renvoie plus une liste vide : cela masquait les pannes de base de données
        # (la vitrine semblait simplement « vide »). Une 503 est visible et diagnostiquable.
        raise _service_unavailable(err)


@router.get("/{product_id}", response_model=ProductRead)
async def get_single_product_details(
    product_id: int,
    session: AsyncSession = Depends(get_async_session),
):
    try:
        # selectinload : sans lui, la lecture des variantes plante en mode asynchrone (MissingGreenlet)
        statement = (
            select(Product)
            .where(Product.id == product_id, Product.is_active.is_(True))
            .options(selectinload(Product.variants))
        )
        result = await session.execute(statement)
        product = result.scalars().one_or_none()
    except Exception as err:
        raise _service_unavailable(err)

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Cet article de maroquinerie de luxe n'est pas disponible.",
        )
    return product


# ==========================================================================
# 🔐 ADMINISTRATION
# ==========================================================================

@router.post("/", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
async def create_product(
    product_in: ProductCreate,
    session: AsyncSession = Depends(get_async_session),
    admin: User = Depends(get_current_admin),  # 🔐 Bloque les requêtes non-admin
):
    """Crée un article et ses variantes en une seule transaction."""
    if product_in.price_cad <= 0:
        raise HTTPException(status_code=400, detail="Le prix doit être supérieur à zéro.")

    variants_in = product_in.variants or []
    for variant in variants_in:
        if variant.stock < 0:
            raise HTTPException(status_code=400, detail="Le stock ne peut pas être négatif.")

    try:
        db_product = Product(
            name=product_in.name,
            description=product_in.description,
            price_cad=product_in.price_cad,
            image_url=product_in.image_url,
            category=product_in.category,
            is_active=product_in.is_active,
        )
        session.add(db_product)
        await session.flush()  # obtient l'id du produit sans valider la transaction
        new_id = db_product.id

        for variant in variants_in:
            session.add(
                ProductVariant(
                    size=variant.size,
                    color=variant.color,
                    stock=variant.stock,
                    product_id=new_id,
                )
            )

        await session.commit()  # produit + variantes validés ensemble (tout ou rien)

        statement = (
            select(Product)
            .where(Product.id == new_id)
            .options(selectinload(Product.variants))
            .execution_options(populate_existing=True)
        )
        result = await session.execute(statement)
        return result.scalars().one()

    except HTTPException:
        raise
    except Exception as err:
        await session.rollback()
        raise _service_unavailable(err)


@router.get("/admin/all", response_model=List[ProductRead])
async def list_all_products_for_admin(
    session: AsyncSession = Depends(get_async_session),
    admin: User = Depends(get_current_admin),
):
    """Liste TOUS les produits (y compris désactivés ou archivés) pour le tableau de bord."""
    try:
        statement = select(Product).options(selectinload(Product.variants)).order_by(Product.id)
        results = await session.execute(statement)
        return results.scalars().all()
    except Exception as err:
        raise _service_unavailable(err)


@router.patch("/{product_id}", response_model=ProductRead)
async def update_product(
    product_id: int,
    changes: ProductUpdate,
    session: AsyncSession = Depends(get_async_session),
    admin: User = Depends(get_current_admin),
):
    """Modifie un produit : prix, photo, description, catégorie, visibilité. Seuls les champs envoyés changent."""
    data = changes.model_dump(exclude_unset=True)
    if not data:
        raise HTTPException(status_code=400, detail="Aucune modification fournie.")

    for field_name, value in data.items():
        if value is None:
            raise HTTPException(status_code=400, detail=f"Le champ « {field_name} » ne peut pas être vide.")

    image_url = data.get("image_url")
    if image_url and not image_url.startswith("https://"):
        raise HTTPException(status_code=400, detail="L'adresse de l'image doit commencer par https://")

    try:
        db_product = await session.get(Product, product_id)
        if not db_product:
            raise HTTPException(status_code=404, detail="Cette confection n'existe pas.")

        for field_name, value in data.items():
            setattr(db_product, field_name, value)
        session.add(db_product)
        await session.commit()

        return await _load_product(session, product_id)

    except HTTPException:
        raise
    except Exception as err:
        await session.rollback()
        raise _service_unavailable(err)


@router.post("/{product_id}/variants", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
async def add_variant(
    product_id: int,
    variant_in: VariantCreate,
    session: AsyncSession = Depends(get_async_session),
    admin: User = Depends(get_current_admin),
):
    """Ajoute une déclinaison (pointure, couleur, stock) à un produit existant."""
    try:
        db_product = await session.get(Product, product_id)
        if not db_product:
            raise HTTPException(status_code=404, detail="Cette confection n'existe pas.")

        duplicate = await session.execute(
            select(ProductVariant.id)
            .where(
                ProductVariant.product_id == product_id,
                ProductVariant.size == variant_in.size,
                ProductVariant.color == variant_in.color,
            )
            .limit(1)
        )
        if duplicate.first() is not None:
            raise HTTPException(
                status_code=409,
                detail="Cette déclinaison existe déjà : modifiez son stock au lieu d'en créer une seconde.",
            )

        session.add(
            ProductVariant(
                product_id=product_id,
                size=variant_in.size,
                color=variant_in.color,
                stock=variant_in.stock,
            )
        )
        await session.commit()

        return await _load_product(session, product_id)

    except HTTPException:
        raise
    except Exception as err:
        await session.rollback()
        raise _service_unavailable(err)


@router.patch("/variants/{variant_id}", response_model=ProductRead)
async def update_variant(
    variant_id: int,
    changes: VariantUpdate,
    session: AsyncSession = Depends(get_async_session),
    admin: User = Depends(get_current_admin),
):
    """Modifie une déclinaison (surtout le stock). Renvoie le produit complet à jour."""
    data = changes.model_dump(exclude_unset=True)
    if not data:
        raise HTTPException(status_code=400, detail="Aucune modification fournie.")
    if "stock" in data and data["stock"] is None:
        raise HTTPException(status_code=400, detail="Le stock ne peut pas être vide.")

    try:
        variant = await session.get(ProductVariant, variant_id)
        if not variant:
            raise HTTPException(status_code=404, detail="Cette déclinaison n'existe pas.")

        parent_id = variant.product_id
        for field_name, value in data.items():
            setattr(variant, field_name, value)
        session.add(variant)
        await session.commit()

        return await _load_product(session, parent_id)

    except HTTPException:
        raise
    except Exception as err:
        await session.rollback()
        raise _service_unavailable(err)


@router.delete("/variants/{variant_id}", status_code=status.HTTP_200_OK)
async def delete_variant(
    variant_id: int,
    session: AsyncSession = Depends(get_async_session),
    admin: User = Depends(get_current_admin),
):
    """Supprime une déclinaison jamais vendue. Une déclinaison déjà vendue doit passer à stock 0."""
    try:
        variant = await session.get(ProductVariant, variant_id)
        if not variant:
            raise HTTPException(status_code=404, detail="Cette déclinaison n'existe pas.")

        sold = await session.execute(
            select(OrderItem.id).where(OrderItem.variant_id == variant_id).limit(1)
        )
        if sold.first() is not None:
            raise HTTPException(
                status_code=409,
                detail="Cette déclinaison a déjà été vendue : mettez son stock à 0 plutôt que de la supprimer.",
            )

        await session.delete(variant)
        await session.commit()
        return {"success": True, "detail": f"La déclinaison #{variant_id} a été supprimée."}

    except HTTPException:
        raise
    except Exception as err:
        await session.rollback()
        raise _service_unavailable(err)


# ⚠️ Déclarée avant la suppression unitaire pour éviter toute ambiguïté de routage
@router.delete("/purge/all-history", status_code=status.HTTP_200_OK)
async def purge_entire_warehouse_history(
    confirm: Optional[str] = Query(None, description=f"Doit valoir {PURGE_CONFIRMATION}"),
    session: AsyncSession = Depends(get_async_session),
    admin: User = Depends(get_current_admin),
):
    """
    💥 REMISE À ZÉRO TOTALE : commandes, lignes de commande, variantes et produits.
    Irréversible. Exige ?confirm=PURGE-TOUT pour éviter tout appel accidentel.
    """
    if confirm != PURGE_CONFIRMATION:
        raise HTTPException(
            status_code=400,
            detail=f"Confirmation requise : ajoutez le paramètre ?confirm={PURGE_CONFIRMATION}",
        )

    print(f"🚨 PURGE TOTALE demandée par l'administrateur id={admin.id}")
    try:
        # Suppressions groupées, dans l'ordre des clés étrangères (enfants d'abord)
        await session.execute(delete(OrderItem))
        await session.execute(delete(Order))
        await session.execute(delete(ProductVariant))
        await session.execute(delete(Product))
        await session.commit()  # tout ou rien
    except Exception as err:
        await session.rollback()
        raise _service_unavailable(err)

    return {
        "success": True,
        "detail": "💥 L'intégralité de la plateforme, des ventes et de l'inventaire a été remise à zéro.",
    }


@router.delete("/{product_id}", status_code=status.HTTP_200_OK)
async def delete_single_product(
    product_id: int,
    session: AsyncSession = Depends(get_async_session),
    admin: User = Depends(get_current_admin),
):
    """
    🗑️ Retire un article de la vitrine.
    - Jamais vendu : suppression définitive (produit + variantes).
    - Déjà vendu : archivage (is_active = False). L'historique des ventes et les
      factures des clients restent intacts.
    """
    try:
        db_product = await session.get(Product, product_id)
        if not db_product:
            raise HTTPException(
                status_code=404,
                detail="Cette confection n'existe pas ou a déjà été supprimée.",
            )

        sold = await session.execute(
            select(OrderItem.id).where(OrderItem.product_id == product_id).limit(1)
        )
        has_sales = sold.first() is not None

        if has_sales:
            db_product.is_active = False
            session.add(db_product)
            await session.commit()
            return {
                "success": True,
                "archived": True,
                "detail": f"Le modèle #{product_id} a déjà été vendu : il est retiré de la vitrine "
                          f"mais conservé dans l'historique des ventes.",
            }

        variants = await session.execute(
            select(ProductVariant).where(ProductVariant.product_id == product_id)
        )
        for variant in variants.scalars().all():
            await session.delete(variant)
        await session.flush()  # libère les variantes avant de supprimer le parent

        await session.delete(db_product)
        await session.commit()
        return {"success": True, "archived": False, "detail": f"Le modèle #{product_id} a été supprimé définitivement."}

    except HTTPException:
        raise
    except Exception as err:
        await session.rollback()
        raise _service_unavailable(err)