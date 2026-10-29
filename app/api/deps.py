# backend/app/api/deps.py
from typing import Optional

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.security import SECRET_KEY, ALGORITHM
from app.models.user import User, UserRole
from app.core.db import get_async_session  # Session asynchrone

# auto_error=False : l'absence de jeton n'est plus une erreur automatique en anglais ;
# chaque dépendance ci-dessous décide elle-même quoi faire (refuser ou continuer en invité).
# Le bouton « Authorize » de /docs continue de fonctionner.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login", auto_error=False)


def _credentials_exception() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Session expirée ou invalide. Veuillez vous reconnecter.",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def _user_from_token(token: str, session: AsyncSession) -> Optional[User]:
    """
    Renvoie l'utilisateur ACTIF correspondant au jeton,
    ou None si le jeton est invalide, expiré, ou si le compte n'existe plus / est désactivé.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload.get("sub"))
    except (jwt.PyJWTError, TypeError, ValueError):
        return None

    try:
        user = await session.get(User, user_id)
    except Exception as err:
        # On lève une HTTPException (qui garde les en-têtes CORS) plutôt qu'une erreur 500 brute
        print(f"💥 Erreur base de données (deps) : {err}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service temporairement indisponible. Réessayez dans un instant.",
        )

    if user is None or not user.is_active:
        return None
    return user


async def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_async_session),
) -> User:
    """Utilisateur connecté OBLIGATOIRE : refuse la requête sans jeton valide."""
    if not token:
        raise _credentials_exception()
    user = await _user_from_token(token, session)
    if user is None:
        raise _credentials_exception()
    return user


async def get_optional_user(
    token: Optional[str] = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_async_session),
) -> Optional[User]:
    """
    Utilisateur connecté FACULTATIF (caisse, commandes sans compte).
    Sans jeton, ou avec un jeton périmé, la requête continue en tant qu'invité.
    """
    if not token:
        return None
    return await _user_from_token(token, session)


async def get_current_admin(current_user: User = Depends(get_current_user)) -> User:
    """Bloque la requête si l'utilisateur connecté n'est pas l'administrateur de l'atelier"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Action refusée. Seul l'artisan administrateur peut modifier le catalogue.",
        )
    return current_user