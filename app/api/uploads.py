# backend/app/api/uploads.py
import asyncio
import io
from uuid import uuid4

import cloudinary
import cloudinary.uploader
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException

from app.core.config import settings
from app.models.user import User
from app.api.deps import get_current_admin

router = APIRouter(prefix="/uploads", tags=["Uploads (Images)"])

# 🌄 Configuration Cloudinary lue depuis les variables d'environnement (jamais écrite dans le code)
cloudinary.config(
    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET,
    secure=True,
)

# Types acceptés (le SVG est exclu : il peut contenir du code actif)
ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}

# Vercel limite le corps d'une requête à environ 4,5 Mo : on reste en dessous
MAX_BYTES = 4 * 1024 * 1024


def _looks_like_image(data: bytes) -> bool:
    """Vérifie les premiers octets : le type MIME envoyé par le client peut être falsifié."""
    return (
        data.startswith(b"\xff\xd8\xff")              # JPEG
        or data.startswith(b"\x89PNG\r\n\x1a\n")      # PNG
        or data[:6] in (b"GIF87a", b"GIF89a")         # GIF
        or (data[:4] == b"RIFF" and data[8:12] == b"WEBP")  # WebP
    )


@router.post("/image", response_model=dict)
async def upload_product_image(
    file: UploadFile = File(...),
    admin: User = Depends(get_current_admin),  # 🔐 Seul l'admin authentifié par JWT peut téléverser
):
    """
    Envoie une photo de vos créations (chaussures, babouches, sacs) sur Cloudinary
    et retourne l'URL sécurisée HTTPS à enregistrer dans PostgreSQL.
    """
    if not (
        settings.CLOUDINARY_CLOUD_NAME
        and settings.CLOUDINARY_API_KEY
        and settings.CLOUDINARY_API_SECRET
    ):
        raise HTTPException(status_code=503, detail="Le service d'images n'est pas configuré.")

    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Format non pris en charge. Utilisez une image JPEG, PNG, WebP ou GIF.",
        )

    # Lecture limitée : on ne charge jamais plus que MAX_BYTES + 1 octet en mémoire
    contents = await file.read(MAX_BYTES + 1)
    if len(contents) > MAX_BYTES:
        raise HTTPException(status_code=413, detail="Image trop lourde (4 Mo maximum).")
    if not _looks_like_image(contents):
        raise HTTPException(status_code=400, detail="Le fichier n'est pas une image valide.")

    try:
        # Appel bloquant exécuté hors de la boucle asynchrone.
        # public_id aléatoire : deux photos portant le même nom ne s'écrasent plus.
        upload_result = await asyncio.to_thread(
            cloudinary.uploader.upload,
            io.BytesIO(contents),
            folder="atelier_canada",
            public_id=uuid4().hex,
            resource_type="image",
        )
    except Exception as err:
        print(f"⚠️ [CLOUDINARY ERROR] {err}")
        raise HTTPException(status_code=502, detail="L'envoi de l'image a échoué. Réessayez.")

    image_url = upload_result.get("secure_url")
    if not image_url:
        raise HTTPException(status_code=502, detail="L'envoi de l'image a échoué. Réessayez.")

    return {"image_url": image_url}