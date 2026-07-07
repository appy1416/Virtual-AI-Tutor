from datetime import datetime, timezone
from fastapi import HTTPException, status
from fastapi.responses import JSONResponse

class EduTwinBaseException(Exception):
    """
    Base exception class for all custom EduTwin application exceptions.
    Provides standard attributes for unified error mapping.
    """
    def __init__(self, message: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.timestamp = datetime.now(timezone.utc).isoformat()

class InvalidCredentials(EduTwinBaseException):
    def __init__(self, message: str = "Invalid email or password."):
        super().__init__(message, status_code=status.HTTP_401_UNAUTHORIZED)

class UserNotFound(EduTwinBaseException):
    def __init__(self, message: str = "User profile not found."):
        super().__init__(message, status_code=status.HTTP_404_NOT_FOUND)

class UserAlreadyExists(EduTwinBaseException):
    def __init__(self, message: str = "A user account with this email already exists."):
        super().__init__(message, status_code=status.HTTP_400_BAD_REQUEST)

class TokenExpired(EduTwinBaseException):
    def __init__(self, message: str = "Authentication token has expired."):
        super().__init__(message, status_code=status.HTTP_401_UNAUTHORIZED)

class TokenInvalid(EduTwinBaseException):
    def __init__(self, message: str = "Authentication token is invalid or malformed."):
        super().__init__(message, status_code=status.HTTP_401_UNAUTHORIZED)

class RoleNotAllowed(EduTwinBaseException):
    def __init__(self, message: str = "You do not have permission to access this resource."):
        super().__init__(message, status_code=status.HTTP_403_FORBIDDEN)

def edutwin_exception_handler(request, exc: EduTwinBaseException):
    """
    Global FastAPI exception handler that catches custom EduTwin base exceptions
    and envelopes them in the standard response format.
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "status_code": exc.status_code,
            "data": None,
            "message": exc.message,
            "timestamp": exc.timestamp
        }
    )

def general_http_exception_handler(request, exc: HTTPException):
    """
    Exception handler for standard FastAPI/Starlette HTTPExceptions
    to match the output response envelope.
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "status_code": exc.status_code,
            "data": None,
            "message": exc.detail,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    )
