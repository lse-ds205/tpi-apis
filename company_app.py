from fastapi import FastAPI
from routes.company_routes import router as company_router

company_app = FastAPI(
    title="Company API",
    description="Company endpoints and documentation.",
    version="1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)
company_app.include_router(company_router)
