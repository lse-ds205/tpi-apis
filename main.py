import uvicorn
from fastapi import FastAPI

from v1.app import app

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", log_level="info")