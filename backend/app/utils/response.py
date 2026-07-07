from datetime import datetime, timezone
from typing import Any, Optional
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

def send_response(
    status_code: int, 
    success: bool, 
    data: Any = None, 
    message: str = ""
) -> JSONResponse:
    """
    Standardized API response wrapper matching Phase 2 specifications.
    Utilizes fastapi's jsonable_encoder to safely serialize complex types
    such as datetimes, Pydantic objects, and nested dict structures.
    """
    content = {
        "success": success,
        "status_code": status_code,
        "data": jsonable_encoder(data),
        "message": message,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    return JSONResponse(status_code=status_code, content=content)
