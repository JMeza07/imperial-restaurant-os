from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.logging import configure_logging, logger
from app.core.middleware import (
    RequestTimingMiddleware,
    SecurityHeadersMiddleware,
)
from app.core.rate_limit import limiter


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    logger.info("Iniciando Imperial Restaurant OS API...")
    yield
    logger.info("Deteniendo Imperial Restaurant OS API...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="Imperial Restaurant OS - Backend Integral de Grado Empresarial",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestTimingMiddleware)
app.add_middleware(SlowAPIMiddleware)

app.include_router(api_router, prefix="/api/v1")


@app.get("/", include_in_schema=False)
async def root():
    return {
        "message": "Imperial Restaurant OS API",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health", tags=["system"])
async def health():
    return {
        "status": "ok",
        "service": settings.PROJECT_NAME,
        "environment": settings.ENVIRONMENT,
    }
