import hmac
import logging
from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models import ClientCase, ClientQuote
from app.routers.auth import get_current_admin
from app.schemas import ClientCaseCreate, ClientCaseOut, PasswordVerify
from app.email_service import send_case_created_email

router = APIRouter(prefix="/api/cases", tags=["cases"])
logger = logging.getLogger(__name__)


@router.get("", response_model=list[ClientCaseOut])
async def list_cases(db: AsyncSession = Depends(get_db), _: str = Depends(get_current_admin)):
    cases = (await db.execute(select(ClientCase).order_by(ClientCase.created_at.desc()))).scalars().all()
    result = []
    for c in cases:
        quote = (await db.execute(select(ClientQuote).where(ClientQuote.id == c.quote_id))).scalar_one_or_none()
        out = ClientCaseOut.model_validate(c)
        out.quote_number = quote.quote_number if quote else None
        result.append(out)
    return result


@router.post("", response_model=ClientCaseOut, status_code=201)
async def create_case(data: ClientCaseCreate, db: AsyncSession = Depends(get_db), _: str = Depends(get_current_admin)):
    quote = await db.get(ClientQuote, data.quote_id)
    if not quote:
        raise HTTPException(status_code=404, detail="找不到此報價單")

    # Check if a case already exists for this quote
    existing = (await db.execute(
        select(ClientCase).where(ClientCase.quote_id == data.quote_id)
    )).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="此報價單已成立案件")

    # Generate case number: CS-YYYYMMDD-NNN
    today = date.today()
    prefix = f"CS-{today.strftime('%Y%m%d')}-"
    count = (await db.execute(
        select(func.count()).where(ClientCase.case_number.like(f"{prefix}%"))
    )).scalar_one()
    case_number = f"{prefix}{count + 1:03d}"

    case = ClientCase(
        case_number=case_number,
        quote_id=quote.id,
        client_name=quote.client_name,
        client_email=quote.client_email,
    )
    db.add(case)
    await db.commit()
    await db.refresh(case)

    # Send email notification
    try:
        await send_case_created_email(
            to_email=quote.client_email,
            client_name=quote.client_name,
            case_number=case_number,
            quote_number=quote.quote_number,
        )
    except Exception as e:
        logger.error(f"案件成立通知信寄送失敗: {e}")

    out = ClientCaseOut.model_validate(case)
    out.quote_number = quote.quote_number
    return out


@router.post("/{case_id}/close", response_model=ClientCaseOut)
async def close_case(
    case_id: str,
    body: PasswordVerify,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_admin),
):
    if not hmac.compare_digest(body.password, settings.ADMIN_PASSWORD):
        raise HTTPException(status_code=403, detail="密碼錯誤")

    case = await db.get(ClientCase, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="找不到此案件")
    if case.status == "closed":
        raise HTTPException(status_code=400, detail="案件已結案")

    from datetime import datetime, timezone
    case.status = "closed"
    case.closed_at = datetime.now(timezone.utc).replace(tzinfo=None)
    await db.commit()
    await db.refresh(case)

    quote = (await db.execute(select(ClientQuote).where(ClientQuote.id == case.quote_id))).scalar_one_or_none()
    out = ClientCaseOut.model_validate(case)
    out.quote_number = quote.quote_number if quote else None
    return out
