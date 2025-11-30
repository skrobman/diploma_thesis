from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.config.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    connect_args={
            "ssl": "require"
    },
    pool_pre_ping=True
)

AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False
)

# Функция для FastAPI Depends
async def get_db():
    db = AsyncSessionLocal()
    try:
        yield db
    finally:
        await db.close()