from collections.abc import AsyncIterator
from contextlib import asynccontextmanager 

from fastapi import FastAPI 
from fastapi.middleware.cors import CORSMiddleware 

from chatterlite.core.config import get_settings
from chatterlite.api.router import api_router

from chatterlite.core.database import close_database


@asynccontextmanager
async def lifespan(_:FastAPI) -> AsyncIterator[None]:

    #startup
    yield 
    #shutdown 
    await close_database()


def create_application() -> FastAPI:
    settings = get_settings()

    application =  FastAPI(
        title=settings.app_name , 
        version=settings.app_version ,
        debug=settings.debug ,
        lifespan=lifespan ,
        docs_url="/docs" , 
        redoc_url= "/redocs" , 
        openapi_url= "/openapi.json"
    )


    application.add_middleware(
        CORSMiddleware , 
        allow_origins = settings.cors_origin , 
        allow_credentials = True , 
        allow_methods = ["*"] , 
        allow_headers = ["*"]
    )


    application.include_router(
        api_router , 
        prefix=settings.api_v1_prefix
    )

    return application



app = create_application()