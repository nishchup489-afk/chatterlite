from typing import Literal 
from fastapi import APIRouter 
from pydantic import BaseModel 


from chatterlite.core.config import get_settings 


router = APIRouter(
    prefix="/health" , 
    tags=["health"]
)

class HealthResponse(BaseModel):
    status : Literal["healthy"]
    environment : str 
    application : str 
    version : str 



@router.get(
    "",
    response_model=HealthResponse , 
    summary="Check API status"
)
async def health_check() -> HealthResponse:
    settings = get_settings()

    return HealthResponse(
        status="healthy" , 
        environment=settings.app_env, 
        application=settings.app_name,
        version=settings.app_version
    )