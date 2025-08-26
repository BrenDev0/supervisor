import os
import jwt
import time
from typing import Union, Dict, Any


class WebTokenService:
    def __init__(self):
        self.token_key = os.getenv("TOKEN_KEY")
        if not self.token_key:
            raise EnvironmentError("env variable TOKEN_KEY not set")

    def generate_token(self, payload: Dict[str, Union[str, int]], expiration: Union[str, int] = "15m") -> str:
        try:
            exp_seconds = self._parse_expiration(expiration)
            payload_with_exp = payload.copy()
            payload_with_exp["exp"] = int(time.time()) + exp_seconds

            return jwt.encode(payload_with_exp, self.token_key, algorithm="HS256")
        except Exception as e:
            print("Error generating token:", e)
            raise

    def decode_token(self, token: str) -> Union[Dict[str, Any], None]:
        return jwt.decode(token, self.token_key, algorithms=["HS256"])

    def _parse_expiration(self, exp: Union[str, int]) -> int:
        if isinstance(exp, int):
            return exp
        if isinstance(exp, str):
            unit = exp[-1]
            value = int(exp[:-1])
            if unit == "s":
                return value
            elif unit == "m":
                return value * 60
            elif unit == "h":
                return value * 3600
            elif unit == "d":
                return value * 86400
        raise ValueError("Invalid expiration format (e.g., '15m', '2h', 3600)")