import uvicorn
from fastapi import FastAPI

from app.app import app

main_app = FastAPI()
main_app.mount("/v1", app)  # your app routes will now be /v1/{your-route-here}

if __name__ == "__main__":
    uvicorn.run(main_app, host="127.0.0.1", log_level="info")