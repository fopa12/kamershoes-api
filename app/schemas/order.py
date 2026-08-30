from pydantic import BaseModel, Field
from typing import List

class CartItem(BaseModel):
    product_id: int
    variant_id: int  # La taille spécifique choisie
    quantity: int = Field(gt=0, description="La quantité doit être supérieure à 0")

class TaxEstimationRequest(BaseModel):
    items: List[CartItem]
    province_code: str = Field(min_length=2, max_length=2, description="Ex: ON, QC, AB")
