import asyncio
from sqlalchemy import select
from app.core.database import async_session
from app.models.user import User
from app.models.token import RefreshToken

async def check_data():
    async with async_session() as db:
        users_result = await db.execute(select(User))
        users = users_result.scalars().all()
        print(f"Users: {[u.email for u in users]}")
        
        tokens_result = await db.execute(select(RefreshToken))
        tokens = tokens_result.scalars().all()
        print(f"Refresh Tokens count: {len(tokens)}")

if __name__ == "__main__":
    asyncio.run(check_data())
