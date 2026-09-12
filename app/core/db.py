# backend/app/core/db.py
import os
from sqlmodel import SQLModel, text
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# 🌐 Fallback order: 1. System environment -> 2. settings.py fallback configuration
DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL or DATABASE_URL.strip() == "":
    DATABASE_URL = settings.DATABASE_URL

# ⚡ Transform connection prefix safely for asynchronous asyncpg drivers
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

# Asynchronous serverless cloud engine deployment configuration
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    future=True
)

async_session = sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

async_session_maker = async_session

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
        await conn.execute(text("ALTER TABLE orders ALTER COLUMN user_id DROP NOT NULL;"))

async def get_async_session() -> AsyncSession:
    async with async_session() as session:
        yield session
