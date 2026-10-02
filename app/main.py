"""FastAPI factory: logging, DB init, routers."""
from __future__ import annotations
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.config import get_settings
from app.database import init_db
from app.routers import webhook, simulate


def _logging() -> None:
    s = get_settings()
    logging.basicConfig(level=getattr(logging, s.LOG_LEVEL.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


def create_app() -> FastAPI:
    _logging()
    s = get_settings()
    app = FastAPI(title=s.APP_NAME, lifespan=lifespan)
    app.include_router(webhook.router)
    app.include_router(simulate.router)
    return app


app = create_app()
