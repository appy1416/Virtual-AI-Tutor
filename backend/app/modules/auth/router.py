from fastapi import APIRouter, Depends, status, Request
from fastapi.security import OAuth2PasswordRequestForm

from app.core.database import get_db
from app.core.security import security_scheme, HTTPAuthorizationCredentials, verify_token
from app.modules.auth import service
from app.modules.auth.schemas import (
    RegisterRequest, 
    LoginRequest, 
    PasswordResetRequest, 
    PasswordResetConfirm
)
from app.utils.response import send_response
from app.utils.lms_helpers import log_activity

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, db = Depends(get_db)):
    """
    Registers a new student account.
    """
    user_data = await service.register_user(
        db=db, 
        email=body.email, 
        password=body.password, 
        full_name=body.full_name,
        role="student"
    )
    return send_response(
        status_code=status.HTTP_201_CREATED,
        success=True,
        data=user_data,
        message="User registered successfully."
    )

@router.post("/login")
async def login(body: LoginRequest, db = Depends(get_db)):
    """
    Authenticates a user using email and password, returning tokens.
    """
    access_token, refresh_token, user_data = await service.login_user(
        db=db, 
        email=body.email, 
        password=body.password
    )
    return send_response(
        status_code=status.HTTP_200_OK,
        success=True,
        data={
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": user_data
        },
        message="Logged in successfully."
    )

@router.post("/oauth-login")
async def oauth_login(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db = Depends(get_db)
):
    """
    Standard OAuth2 password flow login (for Swagger UI authorization compatibility).
    """
    access_token, refresh_token, user_data = await service.login_user(
        db=db, 
        email=form_data.username, 
        password=form_data.password
    )
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@router.post("/logout")
async def logout(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db = Depends(get_db)
):
    """
    Logs out the active user and revokes the bearer token.
    """
    token = credentials.credentials
    try:
        payload = verify_token(token, "access")
        user_id = payload.get("sub")
        if user_id:
            await log_activity(db, user_id, "logout", "User logged out")
    except Exception:
        pass
        
    await service.logout_user(token)
    return send_response(
        status_code=status.HTTP_200_OK,
        success=True,
        message="Logged out successfully."
    )

@router.post("/refresh")
async def refresh(request: Request, db = Depends(get_db)):
    """
    Retrieves a new access token using the supplied refresh_token.
    """
    refresh_token = None
    try:
        body = await request.json()
        if body:
            refresh_token = body.get("refresh_token")
    except Exception:
        pass
        
    if not refresh_token:
        # Fallback to Authorization header
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            refresh_token = auth_header.split(" ")[1]
            
    if not refresh_token:
        return send_response(
            status_code=status.HTTP_400_BAD_REQUEST,
            success=False,
            message="refresh_token is required in body or Authorization header."
        )
        
    try:
        new_token = await service.refresh_access_token(db=db, refresh_token=refresh_token)
        return send_response(
            status_code=status.HTTP_200_OK,
            success=True,
            data={"access_token": new_token, "token_type": "bearer"},
            message="Token refreshed successfully."
        )
    except Exception as e:
        return send_response(
            status_code=status.HTTP_400_BAD_REQUEST,
            success=False,
            message=str(e)
        )

@router.post("/forgot-password")
async def forgot_password(body: PasswordResetRequest, db = Depends(get_db)):
    """
    Initiates the password reset workflow by generating a token and writing to logs.
    """
    await service.initiate_password_reset(db=db, email=body.email)
    return send_response(
        status_code=status.HTTP_200_OK,
        success=True,
        message="If the email exists, a password reset link has been logged/sent."
    )

@router.post("/reset-password")
async def reset_password_route(body: PasswordResetConfirm, db = Depends(get_db)):
    """
    Completes the password reset process using the reset token.
    """
    await service.reset_password(db=db, token=body.token, new_password=body.new_password)
    return send_response(
        status_code=status.HTTP_200_OK,
        success=True,
        message="Password has been reset successfully."
    )
