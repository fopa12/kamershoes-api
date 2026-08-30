from typing import List
from app.models.product import ProductBase, ProductVariantBase

# Schéma pour voir les variantes imbriquées dans un produit (Output)
class ProductVariantRead(ProductVariantBase):
    id: int

class ProductRead(ProductBase):
    id: int
    variants: List[ProductVariantRead] = []

# Schéma pour la création d'un produit complet depuis le panneau d'administration (Input)
class VariantCreateInline(ProductVariantBase):
    # On omet product_id ici car il sera hérité lors de la création du parent
    product_id: None = None 

class ProductCreate(ProductBase):
    variants: List[VariantCreateInline] = []
