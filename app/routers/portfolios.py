from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models import Portfolio
from app.schemas import PortfolioCreate, PortfolioUpdate, PortfolioOut
from app.services.storage import upload_image
from app.routers.auth import get_current_admin

router = APIRouter(prefix="/api/portfolios", tags=["portfolios"])


@router.get("", response_model=list[PortfolioOut])
async def list_portfolios(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Portfolio).order_by(Portfolio.created_at.desc()))
    return result.scalars().all()


@router.get("/{portfolio_id}", response_model=PortfolioOut)
async def get_portfolio(portfolio_id: str, db: AsyncSession = Depends(get_db)):
    portfolio = await db.get(Portfolio, portfolio_id)
    if not portfolio:
        raise HTTPException(status_code=404, detail="作品集不存在")
    return portfolio


@router.post("", response_model=PortfolioOut, status_code=201)
async def create_portfolio(data: PortfolioCreate, db: AsyncSession = Depends(get_db), _: str = Depends(get_current_admin)):
    portfolio = Portfolio(**data.model_dump())
    db.add(portfolio)
    await db.commit()
    await db.refresh(portfolio)
    return portfolio


@router.put("/{portfolio_id}", response_model=PortfolioOut)
async def update_portfolio(portfolio_id: str, data: PortfolioUpdate, db: AsyncSession = Depends(get_db), _: str = Depends(get_current_admin)):
    portfolio = await db.get(Portfolio, portfolio_id)
    if not portfolio:
        raise HTTPException(status_code=404, detail="作品集不存在")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(portfolio, key, value)
    await db.commit()
    await db.refresh(portfolio)
    return portfolio


@router.delete("/{portfolio_id}", status_code=204)
async def delete_portfolio(portfolio_id: str, db: AsyncSession = Depends(get_db), _: str = Depends(get_current_admin)):
    portfolio = await db.get(Portfolio, portfolio_id)
    if not portfolio:
        raise HTTPException(status_code=404, detail="作品集不存在")
    await db.delete(portfolio)
    await db.commit()


MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5 MB
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png"}


@router.post("/upload-image")
async def upload_portfolio_image(file: UploadFile = File(...), _: str = Depends(get_current_admin)):
    ext = (file.filename or "img.png").rsplit(".", 1)[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="僅支援 JPG / PNG 格式")

    content = await file.read()
    if len(content) > MAX_IMAGE_SIZE:
        raise HTTPException(status_code=400, detail="圖片大小不得超過 5 MB")

    content_type = file.content_type or "image/png"
    url = await upload_image(content, file.filename or "img.png", content_type)
    return {"url": url}
