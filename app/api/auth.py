# backend/app/api/auth.py
from typing import Optional

import bcrypt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserRead, Token
from app.core.security import create_access_token
from app.core.db import get_async_session

router = APIRouter(prefix="/auth", tags=["Authentication"])

MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_BYTES = 72  # limite imposée par bcrypt


def hash_password_native(password: str) -> str:
    """Génère un sel sécurisé et hache le mot de passe avec bcrypt natif."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password_native(plain_password: str, hashed_password: str) -> bool:
    """Vérifie un mot de passe. Un hachage illisible ou invalide donne « faux » au lieu d'une erreur 500."""
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except (ValueError, TypeError):
        return False


# Faux hachage utilisé quand l'e-mail n'existe pas : le temps de réponse reste le même,
# donc un attaquant ne peut pas deviner quelles adresses ont un compte.
_dummy_hash: Optional[str] = None


def _get_dummy_hash() -> str:
    global _dummy_hash
    if _dummy_hash is None:
        _dummy_hash = hash_password_native("mot-de-passe-factice-jamais-utilise")
    return _dummy_hash


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def _service_unavailable(err: Exception) -> HTTPException:
    """Journalise l'erreur côté serveur et renvoie une réponse propre (qui garde les en-têtes CORS)."""
    print(f"💥 Erreur base de données (auth) : {err}")
    return HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Service temporairement indisponible. Réessayez dans un instant.",
    )


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(user_in: UserCreate, session: AsyncSession = Depends(get_async_session)):
    """Inscription asynchrone d'un nouveau client canadien ou international."""
    email = _normalize_email(user_in.email)

    if len(user_in.password) < MIN_PASSWORD_LENGTH:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Le mot de passe doit contenir au moins {MIN_PASSWORD_LENGTH} caractères.",
        )
    if len(user_in.password.encode("utf-8")) > MAX_PASSWORD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le mot de passe est trop long (72 octets maximum).",
        )

    try:
        # 🔍 Vérification de l'e-mail sans tenir compte des majuscules
        result = await session.exec(select(User).where(func.lower(User.email) == email))
        if result.first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cet email est déjà enregistré.",
            )

        # 🛠️ Le rôle est TOUJOURS « client » : une inscription publique ne peut jamais créer un administrateur
        db_user = User(
            email=email,
            full_name=user_in.full_name.strip(),
            hashed_password=hash_password_native(user_in.password),
            role=UserRole.CLIENT,
            is_active=True,
        )
        session.add(db_user)
        await session.commit()
        await session.refresh(db_user)
        return db_user

    except HTTPException:
        raise
    except IntegrityError:
        # Deux inscriptions simultanées avec la même adresse
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cet email est déjà enregistré.",
        )
    except Exception as err:
        await session.rollback()
        raise _service_unavailable(err)


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_async_session),
):
    """Connexion asynchrone et génération du jeton de session JWT."""
    email = _normalize_email(form_data.username)

    try:
        result = await session.exec(select(User).where(func.lower(User.email) == email))
        user = result.first()
    except Exception as err:
        raise _service_unavailable(err)

    # Le hachage est toujours calculé (vrai ou factice) pour que la durée de réponse ne trahisse rien
    password_ok = verify_password_native(
        form_data.password,
        user.hashed_password if user else _get_dummy_hash(),
    )

    if not user or not password_ok:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ce compte utilisateur a été désactivé.",
        )

    # 👑 Jeton JWT lié à l'identifiant de l'utilisateur
    access_token = create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}