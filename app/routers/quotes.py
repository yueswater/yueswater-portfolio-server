import hmac
import logging
from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models import ClientQuote, Service
from app.schemas import ClientQuoteCreate, ClientQuoteOut, PasswordVerify
from app.email_service import send_quote_confirmation, send_quote_admin_notification
from app.routers.auth import get_current_admin
from sqlalchemy import select, func

router = APIRouter(prefix="/api/quotes", tags=["quotes"])
logger = logging.getLogger(__name__)


@router.get("", response_model=list[ClientQuoteOut])
async def list_quotes(db: AsyncSession = Depends(get_db), _: str = Depends(get_current_admin)):
    result = await db.execute(select(ClientQuote).order_by(ClientQuote.created_at.desc()))
    return result.scalars().all()


@router.post("/{quote_id}/delete", status_code=204)
async def delete_quote(quote_id: str, body: PasswordVerify, db: AsyncSession = Depends(get_db), _: str = Depends(get_current_admin)):
    if not hmac.compare_digest(body.password, settings.ADMIN_PASSWORD):
        raise HTTPException(status_code=403, detail="密碼錯誤")
    quote = await db.get(ClientQuote, quote_id)
    if not quote:
        raise HTTPException(status_code=404, detail="報價不存在")
    await db.delete(quote)
    await db.commit()


@router.post("", response_model=ClientQuoteOut, status_code=201)
async def create_quote(data: ClientQuoteCreate, db: AsyncSession = Depends(get_db)):
    service = await db.get(Service, data.service_id)
    if not service:
        raise HTTPException(status_code=400, detail="所選服務不存在")

    # Generate quote number: QT-YYYYMMDD-NNN
    today = date.today()
    prefix = f"QT-{today.strftime('%Y%m%d')}-"
    result = await db.execute(
        select(func.count()).where(ClientQuote.quote_number.like(f"{prefix}%"))
    )
    seq = result.scalar_one() + 1
    quote_number = f"{prefix}{seq:03d}"

    quote = ClientQuote(quote_number=quote_number, **data.model_dump())
    db.add(quote)
    await db.commit()
    await db.refresh(quote)

    # Send confirmation email (non-blocking failure: log but don't fail the request)
    try:
        await send_quote_confirmation(
            to_email=data.client_email,
            client_name=data.client_name,
            service_name=service.name,
            budget_min=data.budget_min,
            budget_max=data.budget_max,
                expected_start=data.expected_start,
                expected_end=data.expected_end,
            quote_number=quote.quote_number,
        )
    except Exception as e:
        logger.error(f"寄送確認信失敗: {e}")

    # Notify admin
    try:
        await send_quote_admin_notification(
            client_name=data.client_name,
            client_email=data.client_email,
            client_phone=data.client_phone,
            service_name=service.name,
            budget_min=data.budget_min,
            budget_max=data.budget_max,
                expected_start=data.expected_start,
                expected_end=data.expected_end,
            quote_number=quote.quote_number,
            description=data.requirement,
        )
    except Exception as e:
        logger.error(f"寄送管理員通知失敗: {e}")

    return quote
