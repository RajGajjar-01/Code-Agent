import asyncio
from sqlalchemy import text
from app.core.database import engine

async def check_db():
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            print("DB connected successfully")
            
            # Check for token tables
            result = await conn.execute(text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'"))
            tables = [row[0] for row in result.fetchall()]
            print(f"Tables: {tables}")
            
    except Exception as e:
        print(f"Error checking DB: {e}")
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check_db())
