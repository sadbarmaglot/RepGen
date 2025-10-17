from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from settings import SQL_USER, SQL_PASSWORD, SQL_DB, SQL_HOST, SQL_PORT

from api.models.entities import User, Project, Object, Plan, Mark

# Async PostgreSQL URL
DATABASE_URL = f"postgresql+asyncpg://{SQL_USER}:{SQL_PASSWORD}@{SQL_HOST}:{SQL_PORT}/{SQL_DB}"

# Создаем async engine
engine = create_async_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Проверяем соединения перед использованием
    pool_recycle=300,  # Пересоздаем соединения каждые 5 минут
    pool_size=20,  # Увеличиваем размер пула соединений
    max_overflow=40,  # Увеличиваем максимальное количество дополнительных соединений
    pool_timeout=60,  # Увеличиваем таймаут ожидания соединения
)

# Создаем async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_db():
    """Dependency для получения async сессии базы данных"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
