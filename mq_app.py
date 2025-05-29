from fastapi import FastAPI
from routes.mq_routes import mq_router

mq_app = FastAPI(
    title="MQ API",
    description="Management Quality (MQ) endpoints and documentation.",
    version="1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)
mq_app.include_router(mq_router)
