from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
from app.config import settings
from app.routers import portfolios, services, quotes, auth, tags, categories, about, chat, cases


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(title="Anthony Portfolio API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.CORS_ORIGINS.split(",")],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(tags.router)
app.include_router(categories.router)
app.include_router(about.router)
app.include_router(portfolios.router)
app.include_router(services.router)
app.include_router(quotes.router)
app.include_router(chat.router)
app.include_router(cases.router)


@app.get("/api/health")
async def health():
    return {"status": "ok"}
