"""

This is just an example of using the authentication system to protect POST endpoint, with POST /company as the example.

"""

from fastapi import APIRouter, Depends
from typing import Annotated
from pydantic import BaseModel, Field

from schemas import User
from authentication.dependency import get_current_active_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

# This is just an example pydantic model so it is not put in schemas
class Company(BaseModel):
    name: str = Field(..., example="Acme Corporation")
    industry: str = Field(..., example="Technology")
    size: int = Field(..., gt=0, example=250)  # must be positive


@router.post("/company")
async def create_company(
    company: Company,
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    # return data without saving/modifying any state
    return {
        "message": f"Company data received from {current_user.username}.",
        "company": company.dict()
    }

