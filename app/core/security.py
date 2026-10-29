from datetime import datetime, timedelta, timezone
import jwt
from passlib.context import CryptContext
from app.core.config import settings

# Configuration du hachage de mot de passe avec BCrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 🔐 Clé de signature des jetons de connexion : une clé DÉDIÉE (variable d'environnement SECRET_KEY),
# distincte de la clé Stripe. Quiconque connaît cette clé peut fabriquer un faux jeton administrateur.
SECRET_KEY = (settings.SECRET_KEY or "").strip()
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # Le jeton reste valide 24 heures

# 🛑 Arrêt immédiat si la clé est absente ou faible : mieux vaut une API qui refuse de démarrer
# (avec un message clair dans les logs) qu'une API dont les jetons peuvent être falsifiés.
if len(SECRET_KEY) < 32:
    raise RuntimeError(
        "SECRET_KEY est absente ou trop courte (32 caractères minimum). Générez-en une avec : "
        "python -c \"import secrets; print(secrets.token_hex(32))\" "
        "puis ajoutez-la aux variables d'environnement (Vercel et fichier .env)."
    )
if "kamershoes" in SECRET_KEY.lower():
    raise RuntimeError(
        "SECRET_KEY ressemble à l'ancienne clé lisible, qui a été exposée publiquement. "
        "Générez-en une nouvelle avec : python -c \"import secrets; print(secrets.token_hex(32))\""
    )
if settings.STRIPE_SECRET_KEY and SECRET_KEY == settings.STRIPE_SECRET_KEY:
    raise RuntimeError("SECRET_KEY ne doit jamais être identique à la clé secrète Stripe.")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict) -> str:
    """Génère un jeton JWT sécurisé contenant l'identifiant du client"""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt