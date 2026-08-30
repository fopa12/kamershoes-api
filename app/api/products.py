# backend/app/api/products.py
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import select, or_
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import selectinload  # ⚡ Solution Pro : indispensable pour charger les relations en asynchrone
from app.schemas.product import ProductCreate, ProductRead
from app.models.product import Product, ProductVariant
from app.models.order import Order, OrderItem # ⚡ AJOUT DES MODÈLES POUR LE NETTOYAGE COMPTABLE DE LA PURGE
from app.models.user import User
from app.core.db import get_async_session  # Sessions asynchrones
from app.api.deps import get_current_admin  # Dépendance de sécurité RBAC

router = APIRouter(prefix="/products", tags=["Products"])

@router.get("/", response_model=List[ProductRead])
async def list_products(
    category: Optional[str] = None,  
    search: Optional[str] = None,    # 🔍 Moteur de recherche dynamique croisée
    session: AsyncSession = Depends(get_async_session)
):
    """
    Récupère tous les produits actifs de manière asynchrone. 
    Permet de filtrer par catégorie et par mot-clé (nom/description) depuis la barre de recherche React.
    Bypasse le filtre si category est réglé sur "all" ou None.
    """
    # ⚡ Chargement non-bloquant des variantes relationnelles (évite le crash MissingGreenlet)
    statement = select(Product).where(Product.is_active == True).options(selectinload(Product.variants))
    
    # 1. Filtrage intelligent par catégorie (si "all", on ignore le filtre pour tout extraire)
    if category and category != "all" and category != "None":
        statement = statement.where(Product.category == category)
        
    # 2. 🔍 MOTEUR DE RECHERCHE DYNAMIQUE (ilike ignore les majuscules/minuscules)
    if search:
        search_filter = f"%{search}%"
        statement = statement.where(
            or_(
                Product.name.ilike(search_filter),
                Product.description.ilike(search_filter)
            )
        )
        
    # Exécution asynchrone non-bloquante via l'API native .exec() de SQLModel
    results = await session.exec(statement)
    return results.all()

@router.post("/", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
async def create_product(
    product_in: ProductCreate, 
    session: AsyncSession = Depends(get_async_session),
    admin: User = Depends(get_current_admin)  # 🔐 Sécurisé : bloque les requêtes non-admin
):
    """
    Crée un nouvel article (chaussure, babouche ou sac) de manière asynchrone.
    Seul l'artisan administrateur authentifié par JWT peut exécuter cette action.
    """
    # 1. Création asynchrone de l'entité produit parente
    db_product = Product(
        name=product_in.name,
        description=product_in.description,
        price_cad=product_in.price_cad,
        image_url=product_in.image_url,
        category=product_in.category,
        is_active=product_in.is_active
    )
    session.add(db_product)
    await session.commit()
    await session.refresh(db_product)
    
    # 2. Création et liaison asynchrone des variantes (tailles ou couleurs)
    for variant in product_in.variants:
        db_variant = ProductVariant(
            size=variant.size,
            color=variant.color,
            stock=variant.stock,
            product_id=db_product.id
        )
        session.add(db_variant)
    
    await session.commit()
    
    # ⚡ Ajustement Pro : On récupère l'objet complet mis à jour avec ses relations pour la réponse JSON
    statement = select(Product).where(Product.id == db_product.id).options(selectinload(Product.variants))
    refresh_result = await session.exec(statement)
    return refresh_result.one()
# backend/app/api/products.py (Suite et fin du routeur de l'inventaire)

@router.delete("/{product_id}", status_code=status.HTTP_200_OK)
async def delete_single_product(
    product_id: int,
    session: AsyncSession = Depends(get_async_session),
    admin: User = Depends(get_current_admin)  # 🔐 Sécurisé par jeton JWT Administrateur
):
    """
    🗑️ SUPPRESSION INDIVIDUELLE ABSOLUE : Purge un article, ses déclinaisons 
    et supprime automatiquement les lignes d'achats clients associées pour casser le verrou SQL.
    """
    # A) Extraction de toutes les déclinaisons de variantes liées au produit parent
    variant_statement = select(ProductVariant).where(ProductVariant.product_id == product_id)
    variant_results = await session.exec(variant_statement)
    all_variants = variant_results.all()
    
    # B) Liquidation préalable ciblée des reçus d'achats enfants (order_items) pour détruire la contrainte de clé étrangère
    for var in all_variants:
        order_item_statement = select(OrderItem).where(OrderItem.variant_id == var.id)
        order_item_results = await session.exec(order_item_statement)
        linked_items = order_item_results.all()
        
        for item in linked_items:
            await session.delete(item)
            
        # Maintenant que les jointures financières de l'article sont libérées, on supprime la variante enfant
        await session.delete(var)
        
    await session.flush() # Synchronisation intermédiaire pour libérer l'intégrité référentielle de PostgreSQL

    # C) Destruction définitive du produit parent de la vitrine
    product_statement = select(Product).where(Product.id == product_id)
    product_result = await session.exec(product_statement)
    db_product = product_result.one_or_none()
    
    if not db_product:
        raise HTTPException(status_code=404, detail="Cette confection n'existe pas ou a déjà été supprimée.")
        
    await session.delete(db_product)
    await session.commit() # Validation SQL définitive de la suppression unifiée
    return {"success": True, "detail": f"Le modèle #{product_id} et l'historique associé ont été purgés avec succès."}


@router.delete("/purge/all-history", status_code=status.HTTP_200_OK)
async def purge_entire_warehouse_history(
    session: AsyncSession = Depends(get_async_session),
    admin: User = Depends(get_current_admin)  # 🔐 Sécurisé par jeton JWT Administrateur
):
    """
    💥 COMMANDE FLUSH CASCADE : Remet l'intégralité de la base de données PostgreSQL à zéro.
    Purger séquentiellement dans l'ordre strict des clés étrangères pour empêcher tout plantage.
    """
    # Étape 1 : Nettoyer l'historique des lignes enfants de factures (order_items)
    all_order_items = await session.exec(select(OrderItem))
    for item in all_order_items.all():
        await session.delete(item)
    await session.flush()

    # Étape 2 : Nettoyer l'historique des commandes parentes (orders)
    all_orders = await session.exec(select(Order))
    for ord_row in all_orders.all():
        await session.delete(ord_row)
    await session.flush()

    # Étape 3 : Nettoyer toutes les déclinaisons de variantes de souliers (product_variants)
    all_variants = await session.exec(select(ProductVariant))
    for var in all_variants.all():
        await session.delete(var)
    await session.flush()

    # Étape 4 : Nettoyer l'ensemble des collections de produits (products)
    all_products = await session.exec(select(Product))
    for prod in all_products.all():
        await session.delete(prod)
        
    await session.commit() # Validation unifiée de la purge en cascade absolue
    return {"success": True, "detail": "💥 L'intégralité de la plateforme, des ventes et de l'inventaire a été remise à zéro."}
