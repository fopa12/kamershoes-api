import bcrypt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserRead, Token
from app.core.security import create_access_token
from app.core.db import get_async_session

router = APIRouter(prefix="/auth", tags=["Authentication"])

def verify_password_native(plain_password: str, hashed_password: str) -> bool:
    """Safely verifies a login password against its stored database hash."""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def hash_password_native(password: str) -> str:
    """Generates a secure salt and hashes the user password natively."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(user_in: UserCreate, session: AsyncSession = Depends(get_async_session)):
    """
    Inscription asynchrone d'un nouveau client canadien ou international.
    """
    # 🔍 Vérification asynchrone si l'email existe déjà dans PostgreSQL
    statement = select(User).where(User.email == user_in.email)
    result = await session.exec(statement)
    existing_user = result.first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Cet email est déjà enregistré."
        )
        
    # 🛠️ Création sécurisée de l'entité avec mot de passe haché en natif
    db_user = User(
        email=user_in.email,
        full_name=user_in.full_name,
        hashed_password=hash_password_native(user_in.password),
        role=UserRole.CLIENT,  # Attribution automatique du rôle client de base
        is_active=True
    )
    
    session.add(db_user)
    await session.commit()
    await session.refresh(db_user)
    return db_user


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    session: AsyncSession = Depends(get_async_session)
):
    """
    Connexion asynchrone du client et génération du jeton de session JWT.
    """
    # 🔍 Recherche de l'utilisateur par e-mail
    statement = select(User).where(User.email == form_data.username)
    result = await session.exec(statement)
    user = result.first()
    
    # ❌ Validation sécurisée de sécurité par hachage natif
    if not user or not verify_password_native(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Ce compte utilisateur a été désactivé."
        )
        
    # 👑 Génération du token JWT lié à l'ID utilisateur
    access_token = create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}
