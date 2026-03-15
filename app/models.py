import uuid
from datetime import datetime, timezone, timedelta
from sqlalchemy import String, Text, Float, DateTime, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


def _now_utc() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Portfolio(Base):
    __tablename__ = "portfolios"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name_zh: Mapped[str] = mapped_column(String(200))
    name_en: Mapped[str] = mapped_column(String(200))
    image: Mapped[str] = mapped_column(String(500))
    description: Mapped[str] = mapped_column(Text)
    tags: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now_utc)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now_utc, onupdate=_now_utc)


class Service(Base):
    __tablename__ = "services"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(200))
    category: Mapped[str] = mapped_column(String(100))
    thumbnail: Mapped[str] = mapped_column(String(500))
    description: Mapped[str] = mapped_column(Text)  # Markdown supported
    price: Mapped[float | None] = mapped_column(Float, nullable=True)  # None = 議價
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now_utc)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now_utc, onupdate=_now_utc)


class ClientQuote(Base):
    __tablename__ = "client_quotes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    quote_number: Mapped[str] = mapped_column(String(20), unique=True)
    client_name: Mapped[str] = mapped_column(String(200))
    client_email: Mapped[str] = mapped_column(String(200))
    client_phone: Mapped[str] = mapped_column(String(50))
    service_id: Mapped[str] = mapped_column(String(36))
    requirement: Mapped[str] = mapped_column(Text)  # Markdown supported
    budget_min: Mapped[float] = mapped_column(Float)
    budget_max: Mapped[float | None] = mapped_column(Float, nullable=True)
    expected_start: Mapped[datetime] = mapped_column(DateTime)
    expected_end: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now_utc)


class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(100), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now_utc)


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(100), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now_utc)


class AboutContent(Base):
    __tablename__ = "about_content"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    content_zh: Mapped[str] = mapped_column(Text, default="")
    content_en: Mapped[str] = mapped_column(Text, default="")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now_utc, onupdate=_now_utc)


class ChatRoom(Base):
    __tablename__ = "chat_rooms"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    quote_id: Mapped[str] = mapped_column(String(36), ForeignKey("client_quotes.id"), unique=True)
    admin_last_read_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    client_last_read_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now_utc)


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    room_id: Mapped[str] = mapped_column(String(36), ForeignKey("chat_rooms.id"))
    sender_type: Mapped[str] = mapped_column(String(10))  # 'admin' or 'client'
    message_type: Mapped[str] = mapped_column(String(20))  # 'text', 'image', 'quote_offer'
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now_utc)


class QuoteOffer(Base):
    __tablename__ = "quote_offers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    message_id: Mapped[str] = mapped_column(String(36), ForeignKey("chat_messages.id"), unique=True)
    amount: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(20), default="pending")  # 'pending', 'accepted', 'rejected'
    reject_reason: Mapped[str | None] = mapped_column(String(100), nullable=True)
    responded_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class ClientCase(Base):
    __tablename__ = "client_cases"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    case_number: Mapped[str] = mapped_column(String(20), unique=True)
    quote_id: Mapped[str] = mapped_column(String(36), ForeignKey("client_quotes.id"))
    client_name: Mapped[str] = mapped_column(String(200))
    client_email: Mapped[str] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(20), default="active")  # 'active', 'closed'
    closed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now_utc)
