from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import AboutContent
from app.schemas import AboutContentUpdate, AboutContentOut
from app.routers.auth import get_current_admin

router = APIRouter(prefix="/api/about", tags=["about"])


async def _get_or_create(db: AsyncSession) -> AboutContent:
    result = await db.execute(select(AboutContent).limit(1))
    row = result.scalar_one_or_none()
    if row is None:
        row = AboutContent()
        db.add(row)
        await db.commit()
        await db.refresh(row)
    return row


@router.get("", response_model=AboutContentOut)
async def get_about(db: AsyncSession = Depends(get_db)):
    return await _get_or_create(db)


@router.put("", response_model=AboutContentOut)
async def update_about(
    payload: AboutContentUpdate,
    db: AsyncSession = Depends(get_db),
    _admin: str = Depends(get_current_admin),
):
    row = await _get_or_create(db)
    if payload.content_zh is not None:
        row.content_zh = payload.content_zh
    if payload.content_en is not None:
        row.content_en = payload.content_en
    await db.commit()
    await db.refresh(row)
    return row
