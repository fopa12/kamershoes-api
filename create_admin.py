# backend/create_admin.py
"""
Crée (ou met à jour) le compte administrateur de l'Atelier.

Usage, depuis le dossier backend, venv activé :
    python create_admin.py

L'adresse e-mail et le mot de passe sont saisis dans le terminal : rien n'est écrit dans le code.
Si le compte existe déjà, son mot de passe est remplacé et son rôle est remis à « admin ».
La base utilisée est celle de DATABASE_URL (fichier .env local).
"""
import asyncio
import getpass

import bcrypt
from sqlmodel import select

from app.core.db import async_session, engine
from app.models.user import User, UserRole

MIN_PASSWORD_LENGTH = 12


def hash_password_native(password: str) -> str:
    """Hachage bcrypt natif (compatible avec la vérification de connexion)."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def ask_credentials():
    """Demande les identifiants dans le terminal (le mot de passe n'est pas affiché)."""
    email = input("Adresse e-mail de l'administrateur : ").strip().lower()
    if "@" not in email or " " in email:
        raise SystemExit("❌ Adresse e-mail invalide.")

    password = getpass.getpass(f"Mot de passe ({MIN_PASSWORD_LENGTH} caractères minimum) : ")
    confirmation = getpass.getpass("Confirmez le mot de passe : ")

    if password != confirmation:
        raise SystemExit("❌ Les deux mots de passe ne correspondent pas.")
    if len(password) < MIN_PASSWORD_LENGTH:
        raise SystemExit(f"❌ Mot de passe trop court ({MIN_PASSWORD_LENGTH} caractères minimum).")
    if len(password.encode("utf-8")) > 72:
        raise SystemExit("❌ Mot de passe trop long (72 octets maximum pour bcrypt).")

    full_name = input("Nom complet [Administrateur de l'Atelier] : ").strip()
    return email, password, full_name or "Administrateur de l'Atelier"


async def save_admin(email: str, password: str, full_name: str) -> None:
    try:
        async with async_session() as session:
            result = await session.execute(select(User).where(User.email == email))
            user = result.scalars().one_or_none()

            if user:
                user.hashed_password = hash_password_native(password)
                user.role = UserRole.ADMIN
                user.is_active = True
                action = "mis à jour"
            else:
                user = User(
                    email=email,
                    full_name=full_name,
                    hashed_password=hash_password_native(password),
                    role=UserRole.ADMIN,
                    is_active=True,
                )
                action = "créé"

            session.add(user)
            await session.commit()

        print(f"✅ Compte administrateur {action}.")
        print(f"📧 Email : {email}")
        print("🔑 Rôle  : admin")
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(save_admin(*ask_credentials()))