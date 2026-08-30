import io  # 💡 Indispensable pour encapsuler les octets binaires sous forme de flux de fichier
import cloudinary
import cloudinary.uploader
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from app.models.user import User
from app.api.deps import get_current_admin

router = APIRouter(prefix="/uploads", tags=["Uploads (Images)"])

# 🌄 CONFIGURATION RÉELLE ET LIÉE À VOTRE COMPTE DE PRODUCTION CLOUDINARY
cloudinary.config(
    cloud_name="y8zmwf3m",
    api_key="696728626311919",
    api_secret="FHwpIr4HpBC0iRU2yoyaI72SKRE"
)

@router.post("/image", response_model=dict)
async def upload_product_image(
    file: UploadFile = File(...), 
    admin: User = Depends(get_current_admin)  # 🔐 Seul l'admin authentifié par JWT peut uploader
):
    """ 
    Envoie de manière fluide et asynchrone une photo de vos créations (chaussures, babouches, sacs)
    sur Cloudinary et retourne l'URL sécurisée HTTPS à enregistrer dans PostgreSQL.
    """
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Le fichier doit être une image.")
        
    try:
        # 1. Lecture asynchrone non-bloquante du flux envoyé par React
        contents = await file.read()
        
        # 2. ⚡ Correctif Windows/Cloudinary : Conversion des octets bruts en flux de fichier lisible en mémoire
        file_stream = io.BytesIO(contents)
        
        # 3. Extraction propre du nom de fichier original (sans l'extension) pour un affichage net sur le cloud
        filename_clean = file.filename.split('.')[0] if file.filename else "article"
        
        # 4. Envoi sécurisé au serveur de stockage Cloudinary
        upload_result = cloudinary.uploader.upload(
            file_stream, 
            folder="atelier_canada",
            public_id=filename_clean
        )
        
        # 5. Renvoi de l'URL sécurisée convertie en JSON au Dashboard React
        return {"image_url": upload_result.get("secure_url")}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur d'envoi Cloud : {str(e)}")
