import os
import jwt
from typing import Dict
from fastapi import Request, HTTPException
from src.api.core.services.http_service import HttpService
from src.api.core.database.session import get_db_session
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

        
    
    def auth(self, request: Request):
        token_payload = self.get_token_payload(request)
        user = self.authorize_user(token_payload)

        return user
    
    def verify(self, request: Request):
        token_payload = self.get_token_payload(request)

        verification_code = token_payload.get("verification_code")

        if verification_code is None:
            raise HTTPException(status_code=403, detail="Unauthorized")
        
        return verification_code


        
    
    def authorize_user(self, token_payload: Dict):
        try:  
            user_id = token_payload.get("user_id")

            if user_id is None:
                raise HTTPException(status_code=401, detail="Invlalid token")
            
            db = next(get_db_session())
            
            user = self.http_service.request_validation_service.verify_resource(
                service_key="users_service",
                params={"db": db, "where_col": "user_id", "identifier": user_id},
                not_found_message="Unauthorized",
                status_code=403
            )

            if user is None:
                raise HTTPException(status_code=403, detail="Unauthorized")
            
            return user
    
        except ValueError as e:
            raise HTTPException(status_code=401, detail=str(e))


    

        
