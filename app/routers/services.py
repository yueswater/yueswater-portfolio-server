from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models import Service
from app.schemas import ServiceCreate, ServiceUpdate, ServiceOut
from app.services.storage import upload_image
from app.routers.auth import get_current_admin

router = APIRouter(prefix="/api/services", tags=["services"])

MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5 MB
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png"}


@router.get("", response_model=list[ServiceOut])
async def list_services(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Service).order_by(Service.created_at.desc()))
    return result.scalars().all()


@router.get("/{service_id}", response_model=ServiceOut)
async def get_service(service_id: str, db: AsyncSession = Depends(get_db)):
    service = await db.get(Service, service_id)
    if not service:
        raise HTTPException(status_code=404, detail="服務不存在")
    return service


@router.post("", response_model=ServiceOut, status_code=201)
async def create_service(data: ServiceCreate, db: AsyncSession = Depends(get_db), _: str = Depends(get_current_admin)):
    service = Service(**data.model_dump())
    db.add(service)
    await db.commit()
    await db.refresh(service)
    return service


@router.put("/{service_id}", response_model=ServiceOut)
async def update_service(service_id: str, data: ServiceUpdate, db: AsyncSession = Depends(get_db), _: str = Depends(get_current_admin)):
    service = await db.get(Service, service_id)
    if not service:
        raise HTTPException(status_code=404, detail="服務不存在")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(service, key, value)
    await db.commit()
    await db.refresh(service)
    return service


@router.delete("/{service_id}", status_code=204)
async def delete_service(service_id: str, db: AsyncSession = Depends(get_db), _: str = Depends(get_current_admin)):
    service = await db.get(Service, service_id)
    if not service:
        raise HTTPException(status_code=404, detail="服務不存在")
    await db.delete(service)
    await db.commit()


@router.post("/upload-image")
async def upload_service_image(file: UploadFile = File(...), _: str = Depends(get_current_admin)):
    ext = (file.filename or "img.png").rsplit(".", 1)[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="僅支援 JPG / PNG 格式")

    content = await file.read()
    if len(content) > MAX_IMAGE_SIZE:
        raise HTTPException(status_code=400, detail="圖片大小不得超過 5 MB")

    content_type = file.content_type or "image/png"
    url = await upload_image(content, file.filename or "img.png", content_type)
    return {"url": url}
