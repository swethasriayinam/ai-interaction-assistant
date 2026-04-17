# database.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

# Ensure this is a physical file path
SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///./crm.db"

engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL, 
    echo=True, # Set to True to see the actual SQL in your terminal
    connect_args={"check_same_thread": False}
)

AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

Base = declarative_base()

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()