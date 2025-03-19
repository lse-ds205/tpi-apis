"""
This module initializes the FastAPI application and includes the route modules for the TPI API.
It integrates endpoints for Company, Management Quality (MQ), and Carbon Performance (CP) assessments,
and provides a basic home endpoint for a welcome message.
"""

from fastapi import FastAPI
from routes.company_routes import router as company_router  # Import the company router
from routes.mq_routes import mq_router  # Import MQ router
from routes.cp_routes import cp_router  # Import CP router 

# Initialize FastAPI app
app = FastAPI()

# Include routers to add endpoints from different modules into the main app.
# This integrates the Company, MQ, and CP endpoints into one unified API.
app.include_router(company_router)
app.include_router(mq_router) 
app.include_router(cp_router) 

@app.get("/")
def home():
    """
    Home endpoint that returns a basic welcome message.

    Returns:
        dict: A dictionary containing the welcome message.
    """
    return {"message": "Welcome to the TPI API!"}
