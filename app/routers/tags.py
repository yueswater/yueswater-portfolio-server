from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models import Tag
from app.schemas import TagCreate, TagOut
from app.routers.auth import get_current_admin

router = APIRouter(prefix="/api/tags", tags=["tags"])


@router.get("", response_model=list[TagOut])
async def list_tags(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Tag).order_by(Tag.name))
    return result.scalars().all()


@router.post("", response_model=TagOut, status_code=201)
async def create_tag(data: TagCreate, db: AsyncSession = Depends(get_db), _: str = Depends(get_current_admin)):
    existing = await db.execute(select(Tag).where(Tag.name == data.name))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="標籤已存在")
    tag = Tag(name=data.name)
    db.add(tag)
    await db.commit()
    await db.refresh(tag)
    return tag


@router.delete("/{tag_id}", status_code=204)
async def delete_tag(tag_id: str, db: AsyncSession = Depends(get_db), _: str = Depends(get_current_admin)):
    tag = await db.get(Tag, tag_id)
    if not tag:
        raise HTTPException(status_code=404, detail="標籤不存在")
    await db.delete(tag)
    await db.commit()
