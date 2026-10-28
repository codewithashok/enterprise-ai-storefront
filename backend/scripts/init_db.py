"""Enable pgvector and create all tables.

Usage (from backend/):
    python -m scripts.init_db          # create missing tables
    python -m scripts.init_db --drop   # drop everything first (destroys data)
"""

import argparse
import asyncio

from sqlalchemy import text

from app.db.models import Base
from app.db.session import engine


async def init_db(drop: bool = False) -> None:
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        if drop:
            await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--drop", action="store_true", help="drop all tables before creating")
    args = parser.parse_args()
    asyncio.run(init_db(drop=args.drop))
