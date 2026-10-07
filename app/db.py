from collections.abc import Iterator
from pathlib import Path

from fastapi import Request
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

IN_MEMORY_URLS = {"sqlite://", "sqlite:///memory"}

def make_engine(url: str) -> Engine:
    """Create an engine, with the extra settings SQLite needs."""
    if not url.startswith("sqlite"):
        return create_engine(url)

    kwargs: dict = {"connect_args": {"check_same_thread": False}}
    if url in IN_MEMORY_URLS:
        kwargs["poolclass"] = StaticPool
    else:
        Path(url.removeprefix("sqlite:///")).parent.mkdir(parents=True, exist_ok=True)
    return create_engine(url, **kwargs)

def get_session(request: Request) -> Iterator[Session]:
    """Yield one database session per request."""
    with request.app.state.session_factory() as session:
        yield session