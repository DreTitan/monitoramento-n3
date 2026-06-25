"""
FastAPI Application Entry Point
"""
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import time

from app.api.subchamados import router as subchamados_router
from app.api.auth import router as auth_router
from app.api.users import router as users_router

# Rate limiter - 60 requisições por minuto por IP
limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])

app = FastAPI(
    title="Sistema de Monitoramento de Calibração",
    description="API para registro e acompanhamento de sub-chamados de calibração",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Adicionar rate limiter ao app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# Middleware para proteção adicional
@app.middleware("http")
async def security_headers(request: Request, call_next):
    """Adiciona headers de segurança"""
    response = await call_next(request)

    # Headers de segurança
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

    # HSTS para HTTPS (importante no Railway)
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

    return response


# CORS restrito - apenas origens permitidas
ALLOWED_ORIGINS = [
    "https://monitoramento-n3-production.up.railway.app",
    "https://monitoramento-n3.up.railway.app",
    "http://localhost:8000",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Requested-With"],
)

# Incluir rotas da API
app.include_router(subchamados_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "version": "2.0.0"}


# Servir o frontend estático
@app.get("/")
async def root():
    """Serve o frontend"""
    return FileResponse("app/frontend.html")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
