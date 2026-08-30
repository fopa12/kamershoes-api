# backend/create_admin.py
import asyncio
import sys
import bcrypt  # 🛡️ Utilisation directe de la bibliothèque officielle native
from sqlmodel import select
from app.core.db import async_session_maker, init_db
from app.models.user import User, UserRole

def hash_password_native(password: str) -> str:
    """Hache proprement un mot de passe en utilisant bcrypt natif sans passlib"""
    password_bytes = password.encode('utf-8')
    # Génération du grain de sel (salt) et hachage
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')

async def create_admin_account():
    # S'assurer que les tables PostgreSQL existent
    await init_db()
    
    async with async_session_maker() as session:
        # 1. Vos identifiants administratifs officiels
        admin_email = "fopsimella@gmail.com"  
        admin_password = "123456789"  
        
        # 2. Vérifier si l'admin existe déjà pour éviter les doublons
        statement = select(User).where(User.email == admin_email)
        result = await session.exec(statement)
        existing_admin = result.first()
        
        if existing_admin:
            print(f"ℹ️ Le compte administrateur ({admin_email}) existe déjà.")
            return

        print("🔐 Création du compte administrateur avec Bcrypt natif...")
        
        # 3. Création de l'entité
        admin_user = User(
            email=admin_email,
            full_name="Artisan Créateur",
            hashed_password=hash_password_native(admin_password),  # ✨ Utilisation du hachage sécurisé natif
            role=UserRole.ADMIN,
            is_active=True
        )
        
        session.add(admin_user)
        await session.commit()
        
        print("🎉 ==========================================")
        print("🎉 COMPTE ADMINISTRATEUR CRÉÉ AVEC SUCCÈS !")
        print(f"📧 Email : {admin_email}")
        print(f"🔑 Rôle  : {admin_user.role}")
        print("🎉 ==========================================")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(create_admin_account())
