from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


def build_engine(database_url: str) -> AsyncEngine:
    if not database_url.startswith("postgresql+asyncpg://"):
        raise ValueError("only async PostgreSQL URLs are supported")
    return create_async_engine(database_url, pool_pre_ping=True)

