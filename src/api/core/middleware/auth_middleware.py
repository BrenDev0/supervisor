# middleware/auth_middleware.py
from fastapi import Request
from src.dependencies.container import Container
from src.api.core.middleware.middleware_service import MiddlewareService


async def auth_middleware(request: Request):
    middleware_service: MiddlewareService = Container.resolve("middleware_service")
    user = middleware_service.auth(request)

    request.state.user = user
    return user
    
        