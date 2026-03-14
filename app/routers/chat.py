import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, UploadFile, File, Query

logger = logging.getLogger(__name__)
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models import ClientQuote, ChatRoom, ChatMessage, QuoteOffer
from app.routers.auth import get_current_admin
from app.schemas import (
    ChatAuthRequest, ChatAuthResponse,
    ChatMessageOut, QuoteOfferCreate, QuoteOfferOut,
    OfferResponseRequest, ChatRoomOut,
)
from app.services.storage import upload_image

router = APIRouter(prefix="/api/chat", tags=["chat"])

CHAT_IMAGE_BUCKET = "chat-images"
MAX_IMAGE_SIZE = 5 * 1024 * 1024
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png"}


# ── WebSocket Connection Manager ──

class ConnectionManager:
    def __init__(self):
        self.rooms: dict[str, list[tuple[WebSocket, str]]] = {}  # room_id -> [(ws, sender_type)]

    async def connect(self, ws: WebSocket, room_id: str, sender_type: str):
        self.rooms.setdefault(room_id, []).append((ws, sender_type))

    def disconnect(self, ws: WebSocket, room_id: str):
        conns = self.rooms.get(room_id, [])
        self.rooms[room_id] = [(w, t) for w, t in conns if w is not ws]

    async def broadcast(self, room_id: str, data: dict, exclude: WebSocket | None = None):
        for ws, _ in self.rooms.get(room_id, []):
            if ws is not exclude:
                try:
                    await ws.send_json(data)
                except Exception:
                    pass

    async def send_to_type(self, room_id: str, sender_type: str, data: dict):
        for ws, t in self.rooms.get(room_id, []):
            if t == sender_type:
                try:
                    await ws.send_json(data)
                except Exception:
                    pass


manager = ConnectionManager()


# ── Helpers ──

def create_chat_token(room_id: str, quote_id: str, client_name: str, client_email: str) -> str:
    payload = {
        "room_id": room_id,
        "quote_id": quote_id,
        "client_name": client_name,
        "client_email": client_email,
        "type": "chat_client",
        "exp": datetime.now(timezone.utc) + timedelta(hours=24),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")


def decode_chat_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
        if payload.get("type") != "chat_client":
            raise ValueError()
        return payload
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, ValueError):
        raise HTTPException(status_code=401, detail="無效或過期的聊天 Token")


def _msg_to_dict(msg: ChatMessage, offer: QuoteOffer | None = None) -> dict:
    d = {
        "id": msg.id,
        "room_id": msg.room_id,
        "sender_type": msg.sender_type,
        "message_type": msg.message_type,
        "content": msg.content,
        "image_url": msg.image_url,
        "created_at": msg.created_at.isoformat(),
    }
    if offer:
        d["offer"] = {
            "id": offer.id,
            "message_id": offer.message_id,
            "amount": offer.amount,
            "status": offer.status,
            "reject_reason": offer.reject_reason,
            "responded_at": offer.responded_at.isoformat() if offer.responded_at else None,
        }
    return d


# ── Customer Auth ──

@router.post("/auth", response_model=ChatAuthResponse)
async def chat_auth(data: ChatAuthRequest, db: AsyncSession = Depends(get_db)):
    quote = (await db.execute(
        select(ClientQuote).where(
            ClientQuote.quote_number == data.quote_number,
            ClientQuote.client_email == data.email,
        )
    )).scalar_one_or_none()
    if not quote:
        raise HTTPException(status_code=401, detail="訂單編號或信箱不正確")

    # Get or create room
    room = (await db.execute(
        select(ChatRoom).where(ChatRoom.quote_id == quote.id)
    )).scalar_one_or_none()
    if not room:
        room = ChatRoom(quote_id=quote.id)
        db.add(room)
        await db.commit()
        await db.refresh(room)

    token = create_chat_token(room.id, quote.id, quote.client_name, quote.client_email)
    return ChatAuthResponse(
        access_token=token,
        room_id=room.id,
        client_name=quote.client_name,
        quote_number=quote.quote_number,
    )


# ── Chat Rooms (admin only) ──

@router.get("/rooms", response_model=list[ChatRoomOut])
async def list_rooms(db: AsyncSession = Depends(get_db), _: str = Depends(get_current_admin)):
    rooms = (await db.execute(select(ChatRoom).order_by(ChatRoom.created_at.desc()))).scalars().all()
    result = []
    for room in rooms:
        quote = (await db.execute(select(ClientQuote).where(ClientQuote.id == room.quote_id))).scalar_one_or_none()
        if not quote:
            continue

        # Last message
        last_msg = (await db.execute(
            select(ChatMessage).where(ChatMessage.room_id == room.id).order_by(ChatMessage.created_at.desc()).limit(1)
        )).scalar_one_or_none()

        # Unread count (messages after admin_last_read_at)
        unread_q = select(func.count(ChatMessage.id)).where(ChatMessage.room_id == room.id)
        if room.admin_last_read_at:
            unread_q = unread_q.where(ChatMessage.created_at > room.admin_last_read_at)
        unread = (await db.execute(unread_q)).scalar() or 0

        last_msg_out = None
        if last_msg:
            offer = None
            if last_msg.message_type == "quote_offer":
                offer = (await db.execute(
                    select(QuoteOffer).where(QuoteOffer.message_id == last_msg.id)
                )).scalar_one_or_none()
            last_msg_out = ChatMessageOut(
                id=last_msg.id, room_id=last_msg.room_id, sender_type=last_msg.sender_type,
                message_type=last_msg.message_type, content=last_msg.content,
                image_url=last_msg.image_url, created_at=last_msg.created_at,
                offer=QuoteOfferOut(**{
                    "id": offer.id, "message_id": offer.message_id, "amount": offer.amount,
                    "status": offer.status, "reject_reason": offer.reject_reason,
                    "responded_at": offer.responded_at,
                }) if offer else None,
            )

        result.append(ChatRoomOut(
            id=room.id, quote_id=room.quote_id, quote_number=quote.quote_number,
            client_name=quote.client_name, client_email=quote.client_email,
            admin_last_read_at=room.admin_last_read_at, client_last_read_at=room.client_last_read_at,
            created_at=room.created_at, last_message=last_msg_out, unread_count=unread,
        ))
    return result


# ── Messages ──

@router.get("/rooms/{room_id}/messages", response_model=list[ChatMessageOut])
async def get_messages(
    room_id: str,
    before: Optional[str] = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    token: str = Query(...),
):
    _verify_room_access(token, room_id)

    q = select(ChatMessage).where(ChatMessage.room_id == room_id)
    if before:
        q = q.where(ChatMessage.created_at < datetime.fromisoformat(before))
    q = q.order_by(ChatMessage.created_at.desc()).limit(limit)
    messages = (await db.execute(q)).scalars().all()

    result = []
    for msg in reversed(messages):
        offer = None
        if msg.message_type == "quote_offer":
            offer_row = (await db.execute(
                select(QuoteOffer).where(QuoteOffer.message_id == msg.id)
            )).scalar_one_or_none()
            if offer_row:
                offer = QuoteOfferOut(
                    id=offer_row.id, message_id=offer_row.message_id, amount=offer_row.amount,
                    status=offer_row.status, reject_reason=offer_row.reject_reason,
                    responded_at=offer_row.responded_at,
                )
        result.append(ChatMessageOut(
            id=msg.id, room_id=msg.room_id, sender_type=msg.sender_type,
            message_type=msg.message_type, content=msg.content,
            image_url=msg.image_url, created_at=msg.created_at, offer=offer,
        ))
    return result


def _verify_room_access(token: str, room_id: str):
    """Verify token grants access to the specified room (admin or matching client)."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        raise HTTPException(status_code=401, detail="無效的 Token")
    # Admin tokens have 'sub', chat tokens have 'type'
    if "sub" in payload:
        return  # admin has access to all rooms
    if payload.get("type") == "chat_client" and payload.get("room_id") == room_id:
        return
    raise HTTPException(status_code=403, detail="無權訪問此聊天室")


# ── Image Upload ──

@router.post("/rooms/{room_id}/upload-image")
async def upload_chat_image(
    room_id: str,
    file: UploadFile = File(...),
    token: str = Query(...),
):
    _verify_room_access(token, room_id)
    ext = (file.filename or "img.png").rsplit(".", 1)[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="僅支援 JPG / PNG 格式")

    content = await file.read()
    if len(content) > MAX_IMAGE_SIZE:
        raise HTTPException(status_code=400, detail="圖片大小不得超過 5 MB")

    content_type = file.content_type or "image/png"
    filename = f"{room_id}/{uuid.uuid4().hex}.{ext}"

    import httpx
    url = f"{settings.SUPABASE_URL}/storage/v1/object/{CHAT_IMAGE_BUCKET}/{filename}"
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, content=content, headers={
            "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
            "Content-Type": content_type,
        })
        resp.raise_for_status()

    public_url = f"{settings.SUPABASE_URL}/storage/v1/object/public/{CHAT_IMAGE_BUCKET}/{filename}"
    return {"url": public_url}


# ── Quote Offers (admin send) ──

@router.post("/rooms/{room_id}/offer", response_model=ChatMessageOut)
async def send_offer(
    room_id: str,
    data: QuoteOfferCreate,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_admin),
):
    msg = ChatMessage(
        room_id=room_id,
        sender_type="admin",
        message_type="quote_offer",
        content=f"報價 NT$ {data.amount:,.0f}",
    )
    db.add(msg)
    await db.flush()

    offer = QuoteOffer(message_id=msg.id, amount=data.amount)
    db.add(offer)
    await db.commit()
    await db.refresh(msg)
    await db.refresh(offer)

    msg_data = _msg_to_dict(msg, offer)
    await manager.broadcast(room_id, {"type": "message", **msg_data})

    return ChatMessageOut(
        id=msg.id, room_id=msg.room_id, sender_type=msg.sender_type,
        message_type=msg.message_type, content=msg.content,
        image_url=msg.image_url, created_at=msg.created_at,
        offer=QuoteOfferOut(
            id=offer.id, message_id=offer.message_id, amount=offer.amount,
            status=offer.status, reject_reason=offer.reject_reason,
            responded_at=offer.responded_at,
        ),
    )


# ── Quote Offer Response (client) ──

@router.post("/offers/{offer_id}/respond", response_model=QuoteOfferOut)
async def respond_offer(
    offer_id: str,
    data: OfferResponseRequest,
    token: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    if data.status not in ("accepted", "rejected"):
        raise HTTPException(status_code=400, detail="狀態必須為 accepted 或 rejected")
    if data.status == "rejected" and data.reject_reason and len(data.reject_reason) > 100:
        raise HTTPException(status_code=400, detail="拒絕原因不得超過 100 字")

    offer = (await db.execute(select(QuoteOffer).where(QuoteOffer.id == offer_id))).scalar_one_or_none()
    if not offer:
        raise HTTPException(status_code=404, detail="找不到此報價")
    if offer.status != "pending":
        raise HTTPException(status_code=400, detail="此報價已回覆")

    # Verify client access
    msg = (await db.execute(select(ChatMessage).where(ChatMessage.id == offer.message_id))).scalar_one()
    payload = decode_chat_token(token)
    if payload.get("room_id") != msg.room_id:
        raise HTTPException(status_code=403, detail="無權操作此報價")

    offer.status = data.status
    offer.reject_reason = data.reject_reason if data.status == "rejected" else None
    offer.responded_at = datetime.now(timezone.utc).replace(tzinfo=None)
    await db.commit()
    await db.refresh(offer)

    await manager.broadcast(msg.room_id, {
        "type": "offer_updated",
        "offer": {
            "id": offer.id, "message_id": offer.message_id, "amount": offer.amount,
            "status": offer.status, "reject_reason": offer.reject_reason,
            "responded_at": offer.responded_at.isoformat() if offer.responded_at else None,
        },
    })

    return QuoteOfferOut(
        id=offer.id, message_id=offer.message_id, amount=offer.amount,
        status=offer.status, reject_reason=offer.reject_reason,
        responded_at=offer.responded_at,
    )


# ── Mark Read ──

@router.post("/rooms/{room_id}/read")
async def mark_read(room_id: str, token: str = Query(...), db: AsyncSession = Depends(get_db)):
    payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
    room = (await db.execute(select(ChatRoom).where(ChatRoom.id == room_id))).scalar_one_or_none()
    if not room:
        raise HTTPException(status_code=404, detail="找不到聊天室")

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    if "sub" in payload:
        room.admin_last_read_at = now
        reader_type = "admin"
    elif payload.get("type") == "chat_client" and payload.get("room_id") == room_id:
        room.client_last_read_at = now
        reader_type = "client"
    else:
        raise HTTPException(status_code=403, detail="無權操作")

    await db.commit()
    await manager.broadcast(room_id, {"type": "read", "reader_type": reader_type, "timestamp": now.isoformat()})
    return {"ok": True}


# ── WebSocket ──

@router.websocket("/ws/{room_id}")
async def websocket_chat(ws: WebSocket, room_id: str, token: str = Query(...)):
    await ws.accept()

    # Verify token (after accept so we can send error messages)
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        await ws.send_json({"type": "error", "code": "auth_failed", "detail": "Token 無效或已過期"})
        await ws.close(code=4001)
        return

    if "sub" in payload:
        sender_type = "admin"
    elif payload.get("type") == "chat_client" and payload.get("room_id") == room_id:
        sender_type = "client"
    else:
        await ws.send_json({"type": "error", "code": "auth_failed", "detail": "無權訪問此聊天室"})
        await ws.close(code=4003)
        return

    await manager.connect(ws, room_id, sender_type)
    try:
        while True:
            data = await ws.receive_json()
            msg_type = data.get("type")

            if msg_type == "typing":
                await manager.broadcast(room_id, {"type": "typing", "sender_type": sender_type}, exclude=ws)

            elif msg_type == "message":
                async with get_db_session() as db:
                    msg = ChatMessage(
                        room_id=room_id,
                        sender_type=sender_type,
                        message_type=data.get("message_type", "text"),
                        content=data.get("content"),
                        image_url=data.get("image_url"),
                    )
                    db.add(msg)
                    await db.commit()
                    await db.refresh(msg)
                    await manager.broadcast(room_id, {"type": "message", **_msg_to_dict(msg)})

            elif msg_type == "read":
                async with get_db_session() as db:
                    room = (await db.execute(select(ChatRoom).where(ChatRoom.id == room_id))).scalar_one_or_none()
                    if room:
                        now = datetime.now(timezone.utc).replace(tzinfo=None)
                        if sender_type == "admin":
                            room.admin_last_read_at = now
                        else:
                            room.client_last_read_at = now
                        await db.commit()
                        await manager.broadcast(room_id, {
                            "type": "read", "reader_type": sender_type, "timestamp": now.isoformat(),
                        })

    except WebSocketDisconnect:
        manager.disconnect(ws, room_id)
    except Exception:
        logger.exception("WebSocket handler error in room %s", room_id)
        manager.disconnect(ws, room_id)


# Helper to get a fresh DB session for WebSocket handlers
from contextlib import asynccontextmanager
from app.database import async_session

@asynccontextmanager
async def get_db_session():
    async with async_session() as session:
        yield session
