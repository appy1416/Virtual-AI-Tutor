import logging
from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from datetime import datetime, timezone

from app.core.cache import token_blacklist
from app.core.security import verify_token

logger = logging.getLogger("edutwin.middleware")

class AuthTokenBlacklistMiddleware(BaseHTTPMiddleware):
    """
    Middleware that intercepts all incoming API requests, checks for a Bearer JWT token,
    and returns a 401 error if the token has been blacklisted (e.g. logged out).
    """
    async def dispatch(self, request: Request, call_next):
        # Retrieve authorization header
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            
            # Check if token is blacklisted
            if token_blacklist.is_token_blacklisted(token):
                logger.warning("Rejected request utilizing blacklisted access token.")
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={
                        "success": False,
                        "status_code": status.HTTP_401_UNAUTHORIZED,
                        "data": None,
                        "message": "Token has been revoked or blacklisted. Please log in again.",
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
                )
                
        # Proceed with request execution
        response = await call_next(request)
        return response
