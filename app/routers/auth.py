import hmac
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
import jwt

from app.config import settings

router = APIRouter(prefix="/api/auth", tags=["auth"])
security = HTTPBearer()


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


def create_token(username: str) -> str:
    payload = {
        "sub": username,
        "exp": datetime.now(timezone.utc) + timedelta(hours=24),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")


def get_current_admin(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    try:
        payload = jwt.decode(credentials.credentials, settings.JWT_SECRET, algorithms=["HS256"])
        return payload["sub"]
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token 已過期")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="無效的 Token")


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest):
    username_match = hmac.compare_digest(data.username, settings.ADMIN_USERNAME)
    password_match = hmac.compare_digest(data.password, settings.ADMIN_PASSWORD)
    if not (username_match and password_match):
        raise HTTPException(status_code=401, detail="帳號或密碼錯誤")
    token = create_token(data.username)
    return TokenResponse(access_token=token)


@router.get("/me")
async def me(admin: str = Depends(get_current_admin)):
    return {"username": admin}
