# ascor_app.py
from fastapi import FastAPI
from routes.ascor_routes import router as ascor_router

ascor_app = FastAPI(
    title="ASCOR API",
    description="ASCOR endpoints and documentation.",
    version="1.0",
    docs_url="/docs",              # at /ascor/docs
    redoc_url=None,                # disable ReDoc if you like
    openapi_url="/openapi.json",   # at /ascor/openapi.json
)
ascor_app.include_router(ascor_router, prefix="/v1")
