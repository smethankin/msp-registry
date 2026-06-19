"""FastAPI приложение MSP Registry."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import Base, engine
from .routers import entity, search, stats, upload


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Создаём таблицы (для dev). В проде использовать alembic upgrade head.
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(
    title="MSP Registry API",
    version="1.0.0",
    description="API для работы с Реестром субъектов МСП ФНС России",
    lifespan=lifespan,
    max_form_memory_size=2 * 1024 * 1024,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(search.router, prefix="/api", tags=["search"])
app.include_router(entity.router, prefix="/api/entity", tags=["entity"])
app.include_router(upload.router, prefix="/api/admin", tags=["admin"])
app.include_router(stats.router, prefix="/api", tags=["stats"])


@app.get("/")
async def root():
    return {"name": "MSP Registry API", "version": "1.0.0", "docs": "/docs"}


@app.get("/health")
async def health():
    return {"status": "ok"}
