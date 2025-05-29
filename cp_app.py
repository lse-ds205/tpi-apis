from fastapi import FastAPI
from routes.cp_routes import cp_router

cp_app = FastAPI(
    title="CP API",
    description="Carbon Performance (CP) endpoints and documentation.",
    version="1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)
cp_app.include_router(cp_router)
