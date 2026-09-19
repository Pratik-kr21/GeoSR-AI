import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from app.config import settings
from app.database import Base
from app.models import *

async def reset_db():
    print("Connecting to database to reset tables...")
    engine = create_async_engine(settings.DATABASE_URI, echo=True)
    async with engine.begin() as conn:
        print("Dropping all tables...")
        await conn.run_sync(Base.metadata.drop_all)
        print("Creating all tables...")
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()
    print("Database reset successfully.")

if __name__ == "__main__":
    asyncio.run(reset_db())
