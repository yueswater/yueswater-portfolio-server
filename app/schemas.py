from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from datetime import datetime


# --- Portfolio ---

class PortfolioCreate(BaseModel):
    name_zh: str
    name_en: str
    image: str
    description: str
    tags: list[str] = []

    @field_validator("tags")
    @classmethod
    def max_five_tags(cls, v: list[str]) -> list[str]:
        if len(v) > 5:
            raise ValueError("最多只能有 5 個標籤")
        return v


class PortfolioUpdate(BaseModel):
    name_zh: Optional[str] = None
    name_en: Optional[str] = None
    image: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[list[str]] = None

    @field_validator("tags")
    @classmethod
    def max_five_tags(cls, v: Optional[list[str]]) -> Optional[list[str]]:
        if v is not None and len(v) > 5:
            raise ValueError("最多只能有 5 個標籤")
        return v


class PortfolioOut(BaseModel):
    id: str
    name_zh: str
    name_en: str
    image: str
    description: str
    tags: list[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# --- Service ---

class ServiceCreate(BaseModel):
    name: str
    category: str
    thumbnail: str
    description: str
    price: Optional[float] = None


class ServiceUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    thumbnail: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None


class ServiceOut(BaseModel):
    id: str
    name: str
    category: str
    thumbnail: str
    description: str
    price: Optional[float]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# --- Client Quote ---

class ClientQuoteCreate(BaseModel):
    client_name: str
    client_email: EmailStr
    client_phone: str
    service_id: str
    requirement: str
    budget_min: float
    budget_max: Optional[float] = None
    expected_start: datetime
    expected_end: Optional[datetime] = None


class ClientQuoteOut(BaseModel):
    id: str
    quote_number: str
    client_name: str
    client_email: str
    client_phone: str
    service_id: str
    requirement: str
    budget_min: float
    budget_max: Optional[float]
    expected_start: datetime
    expected_end: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Tag ---

class TagCreate(BaseModel):
    name: str


class TagOut(BaseModel):
    id: str
    name: str
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Category ---

class CategoryCreate(BaseModel):
    name: str


class CategoryOut(BaseModel):
    id: str
    name: str
    created_at: datetime

    model_config = {"from_attributes": True}


# --- About ---

class AboutContentUpdate(BaseModel):
    content_zh: Optional[str] = None
    content_en: Optional[str] = None


class AboutContentOut(BaseModel):
    id: str
    content_zh: str
    content_en: str
    updated_at: datetime

    model_config = {"from_attributes": True}


# --- Chat ---

class ChatAuthRequest(BaseModel):
    quote_number: str
    email: EmailStr


class ChatAuthResponse(BaseModel):
    access_token: str
    room_id: str
    client_name: str
    quote_number: str


class ChatMessageCreate(BaseModel):
    content: Optional[str] = None
    message_type: str = "text"  # 'text', 'image', 'quote_offer'
    image_url: Optional[str] = None


class ChatMessageOut(BaseModel):
    id: str
    room_id: str
    sender_type: str
    message_type: str
    content: Optional[str]
    image_url: Optional[str]
    created_at: datetime
    offer: Optional["QuoteOfferOut"] = None

    model_config = {"from_attributes": True}


class QuoteOfferCreate(BaseModel):
    amount: float


class QuoteOfferOut(BaseModel):
    id: str
    message_id: str
    amount: float
    status: str
    reject_reason: Optional[str]
    responded_at: Optional[datetime]

    model_config = {"from_attributes": True}


class OfferResponseRequest(BaseModel):
    status: str  # 'accepted' or 'rejected'
    reject_reason: Optional[str] = None


class ChatRoomOut(BaseModel):
    id: str
    quote_id: str
    quote_number: str
    client_name: str
    client_email: str
    admin_last_read_at: Optional[datetime]
    client_last_read_at: Optional[datetime]
    created_at: datetime
    last_message: Optional[ChatMessageOut] = None
    unread_count: int = 0


# --- Password Verification ---

class PasswordVerify(BaseModel):
    password: str


# --- Client Case ---

class ClientCaseCreate(BaseModel):
    quote_id: str


class ClientCaseOut(BaseModel):
    id: str
    case_number: str
    quote_id: str
    client_name: str
    client_email: str
    status: str
    closed_at: Optional[datetime]
    created_at: datetime
    quote_number: Optional[str] = None

    model_config = {"from_attributes": True}
