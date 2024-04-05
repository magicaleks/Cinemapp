import os
from typing import Any, Optional

import jwt
from fastapi import HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

JWT_SECRET = os.getenv("JWT_SECRET")

JWT_ALGORITHM = "HS256"


class JWTBearer(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        super(JWTBearer, self).__init__(auto_error=auto_error)

    async def __call__(self, request: Request) -> Optional[str]:
        creds: HTTPAuthorizationCredentials = await super(JWTBearer, self).__call__(
            request
        )

        if creds:
            if not creds.scheme == "Bearer":
                return HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Invalid authentication scheme.",
                )

            parsed_token = self.verify_jwt(creds.credentials)

            if not parsed_token:
                return HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Invalid authentication token.",
                )

            return parsed_token["sub"]

        else:
            return HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Authorization does not provided.",
            )

    def verify_jwt(self, token: str) -> Optional[dict[str, Any]]:
        try:
            decoded_token = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            return decoded_token
        except:
            return None


def signJWT(user_id: str) -> str:
    payload = {"sub": user_id}

    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    return token
