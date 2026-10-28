from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from openai import AsyncOpenAI
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1 import auth
from app.core.config import settings
from app.db.session import engine, get_db


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Startup: fail fast if Postgres is unreachable, then build shared clients once
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))
    app.state.openai = AsyncOpenAI(api_key=settings.OPENAI_API_KEY.get_secret_value())

    yield

    # Shutdown: release sockets before the event loop closes
    await app.state.openai.close()
    await engine.dispose()


app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1")


@app.get("/api/health", tags=["system"])
async def health(db: Annotated[AsyncSession, Depends(get_db)]) -> dict[str, str]:
    try:
        await db.execute(text("SELECT 1"))
    except Exception as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "database unreachable") from exc
    return {"status": "ok", "database": "ok", "environment": settings.ENVIRONMENT}
