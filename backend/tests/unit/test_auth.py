import pytest
from httpx import AsyncClient
from app.core.database import MongoSession

from app.db.models.user import User
from app.core.security import verify_password

@pytest.mark.asyncio
async def test_register_user_success(client: AsyncClient, db_session: MongoSession):
    # Register student
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "student@example.com",
            "password": "SecurePassword123!",
            "full_name": "Test Student"
        }
    )
    
    assert response.status_code == 201
    json_data = response.json()
    assert json_data["success"] is True
    assert json_data["data"]["email"] == "student@example.com"
    assert json_data["data"]["role"] == "student"
    
    # Confirm DB entry
    doc = await db_session.db["users"].find_one({"email": "student@example.com"})
    user = User(**doc) if doc else None
    assert user is not None
    assert user.full_name == "Test Student"
    assert verify_password("SecurePassword123!", user.password_hash)

@pytest.mark.asyncio
async def test_register_user_duplicate_email(client: AsyncClient):
    # Register first
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "dup@example.com",
            "password": "SecurePassword123!",
            "full_name": "Original Name"
        }
    )
    
    # Register duplicate
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "dup@example.com",
            "password": "SecurePassword123!",
            "full_name": "Duplicate Name"
        }
    )
    
    assert response.status_code == 400
    assert response.json()["success"] is False
    assert "already exists" in response.json()["message"]

@pytest.mark.asyncio
async def test_register_user_invalid_inputs(client: AsyncClient):
    # Invalid email domain blacklist
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "bad@mailinator.com",
            "password": "SecurePassword123!",
            "full_name": "Blocked Domain"
        }
    )
    assert response.status_code == 400
    assert "Disposable" in response.json()["message"]

    # Weak password
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "weak@example.com",
            "password": "123",
            "full_name": "Weak Pwd"
        }
    )
    assert response.status_code == 400
    assert "at least 8" in response.json()["message"]

@pytest.mark.asyncio
async def test_login_user_success(client: AsyncClient):
    # Register first
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "login@example.com",
            "password": "SecurePassword123!",
            "full_name": "Login Tester"
        }
    )
    
    # Attempt login
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "login@example.com",
            "password": "SecurePassword123!"
        }
    )
    
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["success"] is True
    assert "access_token" in json_data["data"]
    assert "refresh_token" in json_data["data"]
    assert json_data["data"]["user"]["email"] == "login@example.com"

@pytest.mark.asyncio
async def test_login_user_invalid_credentials(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "nonexistent@example.com",
            "password": "WrongPassword1!"
        }
    )
    assert response.status_code == 401
    assert response.json()["success"] is False

@pytest.mark.asyncio
async def test_token_refresh(client: AsyncClient):
    # Register and login
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "refresh@example.com",
            "password": "SecurePassword123!",
            "full_name": "Refresh Tester"
        }
    )
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "refresh@example.com",
            "password": "SecurePassword123!"
        }
    )
    refresh_token = login_resp.json()["data"]["refresh_token"]
    
    # Request refresh
    response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()["data"]

@pytest.mark.asyncio
async def test_password_reset_flow(client: AsyncClient, db_session: MongoSession):
    # Register user
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "reset@example.com",
            "password": "OldPassword1!",
            "full_name": "Reset Student"
        }
    )
    
    # Initiate forgot password
    resp = await client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "reset@example.com"}
    )
    assert resp.status_code == 200
    
    # Extract token manually from the database session to simulate finding it in emails/logs
    doc = await db_session.db["users"].find_one({"email": "reset@example.com"})
    user = User(**doc) if doc else None
    
    # We generate a reset token using security utils for the user
    from app.core.security import create_access_token
    from datetime import timedelta
    reset_token = create_access_token(
        data={"sub": user.id, "email": user.email, "type": "reset"},
        expires_delta=timedelta(minutes=15)
    )
    
    # Trigger password reset
    reset_resp = await client.post(
        "/api/v1/auth/reset-password",
        json={
            "token": reset_token,
            "new_password": "NewSecurePassword1!"
        }
    )
    assert reset_resp.status_code == 200
    assert reset_resp.json()["success"] is True
    
    # Attempt login with new password
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "reset@example.com",
            "password": "NewSecurePassword1!"
        }
    )
    assert login_resp.status_code == 200
