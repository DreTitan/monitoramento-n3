"""
FastAPI Application Entry Point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from app.api.subchamados import router as subchamados_router
from app.api.auth import router as auth_router
from app.api.users import router as users_router

app = FastAPI(
    title="Sistema de Monitoramento de Calibração",
    description="API para registro e acompanhamento de sub-chamados de calibração",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configurar CORS restrito
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://monitoramento-n3-production.up.railway.app",
        "http://localhost:8000",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
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
