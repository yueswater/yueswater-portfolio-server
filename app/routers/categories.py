from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models import Category
from app.schemas import CategoryCreate, CategoryOut
from app.routers.auth import get_current_admin

router = APIRouter(prefix="/api/categories", tags=["categories"])


@router.get("", response_model=list[CategoryOut])
async def list_categories(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Category).order_by(Category.name))
    return result.scalars().all()


@router.post("", response_model=CategoryOut, status_code=201)
async def create_category(data: CategoryCreate, db: AsyncSession = Depends(get_db), _: str = Depends(get_current_admin)):
    existing = await db.execute(select(Category).where(Category.name == data.name))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="分類已存在")
    category = Category(name=data.name)
    db.add(category)
    await db.commit()
    await db.refresh(category)
    return category


@router.delete("/{category_id}", status_code=204)
async def delete_category(category_id: str, db: AsyncSession = Depends(get_db), _: str = Depends(get_current_admin)):
    category = await db.get(Category, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="分類不存在")
    await db.delete(category)
    await db.commit()
