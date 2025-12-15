from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.endpoints import clients

app = FastAPI(
    title="RetailCRM Integration API",
    description="Прокси-сервис для взаимодействия с RetailCRM API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(clients.router, prefix="/api/v1")

@app.get("/")
async def root():
    return {
        "message": "RetailCRM Integration API",
        "docs": "/docs",
        "version": "1.0.0"
    }

@app.get("/ping")
async def health_check():
    return {"status": "pong"}