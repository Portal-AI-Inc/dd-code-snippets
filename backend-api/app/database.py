from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Optional, assert_type

from sqlalchemy import create_engine
from app.config import settings
from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import sessionmaker
from app.models.base_model import BaseModel, ModelType


class DatabaseSessionManager:
    def __init__(self, host: str, engine_kwargs: dict[str, Any] = {}):
        self._engine = create_async_engine(host, **engine_kwargs)
        self._sessionmaker = async_sessionmaker(autocommit=False, bind=self._engine, expire_on_commit=False)
        self._sync_engine = create_engine(host, **engine_kwargs)
        self._sync_sessionmaker = sessionmaker(self._sync_engine)

    async def close(self):
        if self._engine is None:
            raise Exception("DatabaseSessionManager is not initialized")
        await self._engine.dispose()

        self._engine = None
        self._sessionmaker = None

    @asynccontextmanager
    async def connect(self) -> AsyncIterator[AsyncConnection]:
        if self._engine is None:
            raise Exception("DatabaseSessionManager is not initialized")

        async with self._engine.begin() as connection:
            try:
                yield connection
            except Exception:
                await connection.rollback()
                raise

    @asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        if self._sessionmaker is None:
            raise Exception("DatabaseSessionManager is not initialized")

        session = self._sessionmaker()
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

    def sync_session(self):
        return self._sync_sessionmaker()

    @asynccontextmanager
    async def provide_or_create_session(self, db_session: Optional[AsyncSession] = None) -> AsyncIterator[AsyncSession]:
        if db_session is None:
            async with self.session() as new_session:
                yield new_session
        else:
            assert_type(db_session, AsyncSession)
            yield db_session


sessionmanager = DatabaseSessionManager(settings.DATABASE_URL, {"echo": settings.ECHO_SQL})


async def get_db_session():
    async with sessionmanager.session() as session:
        yield session


async def try_commit(db_session: AsyncSession):
    try:
        await db_session.commit()
    except Exception as e:
        await db_session.rollback()
        raise e


async def db_commit(db_session: AsyncSession, item: BaseModel):
    db_session.add(item)
    await try_commit(db_session)


async def db_commit_and_refresh(db_session: AsyncSession, item: ModelType) -> ModelType:
    await db_commit(db_session, item)
    await db_session.refresh(item)
    return item
