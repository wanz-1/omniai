import asyncio
import contextlib


def session_cm():
    from app.main import async_session_factory

    return contextlib.asynccontextmanager(lambda: async_session_factory())


def run(coro):
    return asyncio.run(coro)
