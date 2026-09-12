# backend/purge.py
import asyncio
import os
import sys
from sqlmodel import text
from sqlmodel.ext.asyncio.session import AsyncSession

# 🌐 PATH CONFIGURATION: Forces Windows to resolve internal modules seamlessly
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from app.core.db import engine

async def try_truncate(table_string: str) -> bool:
    """Runs a truncation query inside a clean transaction block to prevent transaction abort chains."""
    async with AsyncSession(engine) as session:
        try:
            await session.execute(text(f"TRUNCATE TABLE {table_string} CASCADE;"))
            await session.commit()
            print(f"💥 Success! Cleaned tables using pattern: {table_string}")
            return True
        except Exception as e:
            await session.rollback()
            print(f"⚠️ Pattern skipped ({table_string}): {str(e).splitlines()[0]}")
            return False

async def clear_supabase_tables():
    print("🚀 Connecting to Supabase Canada cluster for security tables wipeout...")
    
    # Pattern 1: Case-Sensitive Class PascalCase Notation (Standard SQLModel mapping rules)
    if await try_truncate('"OrderItem", "Order", "ProductVariant", "Product"'):
        print("🎉 Database clean up successful!")
        return
        
    # Pattern 2: Lowercase Standard Naming rules
    if await try_truncate('"orderitem", "orders", "productvariant", "product"'):
        return

    # Pattern 3: Standard Underscore Plural Notation
    if await try_truncate('"order_items", "orders", "product_variants", "products"'):
        return

    print("❌ All preset database truncation patterns skipped.")

if __name__ == "__main__":
    asyncio.run(clear_supabase_tables())
