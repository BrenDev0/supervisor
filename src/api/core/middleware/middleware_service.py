import os
import jwt
from typing import Dict
from fastapi import Request, HTTPException
from src.api.core.services.http_service import HttpService
from fastapi.security import HTTPBearer



security = HTTPBearer()
class MiddlewareService:
    def __init__(self, http_service: HttpService):
        self.TOKEN_KEY = os.getenv("TOKEN_KEY")
        self.http_service = http_service

    def get_token_payload(self, request: Request):
        auth_header = request.headers.get("Authorization")

        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Unautrhorized, Missing required auth headers")
        
        token = auth_header.split(" ")[1]

        try:
            payload = self.http_service.webtoken_service.decode_token(token=token)

            return payload
        except jwt.ExpiredSignatureError:
            print("token expired")
            raise HTTPException(status_code=403, detail="Expired Token")
        
        except jwt.InvalidTokenError:
            print("token invalid")
            raise HTTPException(status_code=401, detail="Invlalid token")
        
        except ValueError as e:
            raise HTTPException(status_code=401, detail=str(e))

        
    
    def auth(self, req: Request):
        token_payload = self.get_token_payload(req)
        user_id = token_payload.get("user_-id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Unathorarized")
        
        return user_id

   


    


    

        
