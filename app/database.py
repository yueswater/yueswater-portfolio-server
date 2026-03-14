from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text
from app.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with async_session() as session:
        yield session


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Add quote_number column if missing (no Alembic)
        await conn.execute(text(
            "ALTER TABLE client_quotes ADD COLUMN IF NOT EXISTS quote_number VARCHAR(20) UNIQUE"
        ))
        # Backfill existing rows that have NULL quote_number
        await conn.execute(text(
            "UPDATE client_quotes SET quote_number = 'QT-00000000-' || LPAD(sub.rn::text, 3, '0') "
            "FROM (SELECT id, ROW_NUMBER() OVER (ORDER BY created_at) AS rn FROM client_quotes WHERE quote_number IS NULL) sub "
            "WHERE client_quotes.id = sub.id"
        ))
        # Create chat-images bucket if not exists (Supabase Storage)
        import httpx
        from app.config import settings
        try:
            async with httpx.AsyncClient() as client:
                await client.post(
                    f"{settings.SUPABASE_URL}/storage/v1/bucket",
                    json={"id": "chat-images", "name": "chat-images", "public": True},
                    headers={"Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}"},
                )
        except Exception:
            pass  # bucket may already exist
