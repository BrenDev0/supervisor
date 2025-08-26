import bcrypt
import hashlib
from fastapi import HTTPException

class HashingService:
    @staticmethod
    def hash_for_search( data: str) -> str:
        email_bytes = data.lower().encode('utf-8')  
        hashed_data = hashlib.sha256(email_bytes).hexdigest()
        return hashed_data

    @staticmethod
    def hash_password(password: str) -> str:
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')

    @staticmethod
    def compare_password(password: str, hashed_password: str) -> bool:
        if not bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8')):
            raise HTTPException(status_code=400, detail="Incorrect password")
        return True