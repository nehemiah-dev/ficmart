from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from config import settings

db_url = (
    f"postgresql+asyncpg://{settings.pg_user}:"
    f"{settings.sqlalchemy_secret.get_secret_value()}"
    f"@localhost:5432/ficmart"
)
# db_url = settings.sqlalchemy_database_url
engine = create_async_engine(url=str(db_url))

AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
