from fastapi import APIRouter 



from chatterlite.api.routes.health import router as backend_health_router 



api_router = APIRouter()


api_router.include_router(backend_health_router)