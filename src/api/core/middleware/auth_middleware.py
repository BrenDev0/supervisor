# middleware/auth_middleware.py
from fastapi import Request
from src.dependencies.container import Container
from src.api.core.middleware.middleware_service import MiddlewareService


async def auth_middleware(req: Request):
    middleware_service: MiddlewareService = Container.resolve("middleware_service")
    user, company = middleware_service.auth(req)

    req.state.user = user
    req.state.company = company
    return user
    
        