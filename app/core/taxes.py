from typing import Dict, TypedDict

class TaxRate(TypedDict):
    province_name: str
    tps: float  # Taxe Fédérale
    tvp: float  # Taxe Provinciale
    tvh: float  # Taxe Harmonisée (si applicable)
    total_rate: float

# Base de données immuable des taux de taxation canadiens
CANADIAN_TAX_RATES: Dict[str, TaxRate] = {
    "ON": {"province_name": "Ontario", "tps": 0.0, "tvp": 0.0, "tvh": 0.13, "total_rate": 0.13},
    "QC": {"province_name": "Québec", "tps": 0.05, "tvp": 0.09975, "tvh": 0.0, "total_rate": 0.14975},
    "AB": {"province_name": "Alberta", "tps": 0.05, "tvp": 0.0, "tvh": 0.0, "total_rate": 0.05},
    "BC": {"province_name": "Colombie-Britannique", "tps": 0.05, "tvp": 0.07, "tvh": 0.0, "total_rate": 0.12},
    "MB": {"province_name": "Manitoba", "tps": 0.05, "tvp": 0.07, "tvh": 0.0, "total_rate": 0.12},
    "NB": {"province_name": "Nouveau-Brunswick", "tps": 0.0, "tvp": 0.0, "tvh": 0.15, "total_rate": 0.15},
    "NL": {"province_name": "Terre-Neuve-et-Labrador", "tps": 0.0, "tvp": 0.0, "tvh": 0.15, "total_rate": 0.15},
    "NS": {"province_name": "Nouvelle-Écosse", "tps": 0.0, "tvp": 0.0, "tvh": 0.15, "total_rate": 0.15},
    "PE": {"province_name": "Île-du-Prince-Édouard", "tps": 0.0, "tvp": 0.0, "tvh": 0.15, "total_rate": 0.15},
    "SK": {"province_name": "Saskatchewan", "tps": 0.05, "tvp": 0.06, "tvh": 0.0, "total_rate": 0.11},
    "YT": {"province_name": "Yukon", "tps": 0.05, "tvp": 0.0, "tvh": 0.0, "total_rate": 0.05},
    "NT": {"province_name": "Territoires du Nord-Ouest", "tps": 0.05, "tvp": 0.0, "tvh": 0.0, "total_rate": 0.05},
    "NU": {"province_name": "Nunavut", "tps": 0.05, "tvp": 0.0, "tvh": 0.0, "total_rate": 0.05},
}

def calculate_order_taxes(items_subtotal: float, province_code: str) -> dict:
    """
    Calcule le montant exact des taxes sur la base du code de la province (ex: 'ON', 'QC').
    """
    code = province_code.upper().strip()
    if code not in CANADIAN_TAX_RATES:
        raise ValueError(f"Code de province canadien invalide : {province_code}")
        
    tax_info = CANADIAN_TAX_RATES[code]
    
    # Calculs précis des montants
    tps_amount = round(items_subtotal * tax_info["tps"], 2)
    tvp_amount = round(items_subtotal * tax_info["tvp"], 2)
    tvh_amount = round(items_subtotal * tax_info["tvh"], 2)
    total_tax = round(items_subtotal * tax_info["total_rate"], 2)
    
    return {
        "province": tax_info["province_name"],
        "subtotal": items_subtotal,
        "tps_amount": tps_amount,
        "tvp_amount": tvp_amount,
        "tvh_amount": tvh_amount,
        "total_tax_amount": total_tax,
        "total_with_tax": round(items_subtotal + total_tax, 2)
    }
