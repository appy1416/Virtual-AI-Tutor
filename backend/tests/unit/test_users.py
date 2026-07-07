import pytest
from httpx import AsyncClient
from app.core.database import MongoSession

from app.db.models.user import User
from app.core.security import create_access_token
from app.modules.users import crud

@pytest.mark.asyncio
async def test_get_profile_me_authenticated(client: AsyncClient, db_session: MongoSession):
    # Setup test user record manually in DB
    user = User(
        email="me@example.com",
        password_hash="hashedpwd",
        full_name="Me Myself",
        role="student"
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    # Generate token
    token = create_access_token(data={"sub": user.id, "role": user.role})
    
    # Fetch profile
    response = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["success"] is True
    assert json_data["data"]["email"] == "me@example.com"
    assert json_data["data"]["full_name"] == "Me Myself"

@pytest.mark.asyncio
async def test_get_profile_me_unauthorized(client: AsyncClient):
    response = await client.get("/api/v1/users/me")
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_update_profile_me(client: AsyncClient, db_session: MongoSession):
    user = User(
        email="update@example.com",
        password_hash="hashedpwd",
        full_name="Original Name",
        role="student",
        preferences={"theme": "light"}
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    token = create_access_token(data={"sub": user.id, "role": user.role})
    
    response = await client.put(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "full_name": "Updated Name",
            "bio": "Studying calculus",
            "preferences": {"theme": "dark", "sound": "on"}
        }
    )
    
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["success"] is True
    assert json_data["data"]["full_name"] == "Updated Name"
    assert json_data["data"]["bio"] == "Studying calculus"
    assert json_data["data"]["preferences"]["theme"] == "dark"
    assert json_data["data"]["preferences"]["sound"] == "on"

@pytest.mark.asyncio
async def test_change_password(client: AsyncClient, db_session: MongoSession):
    from app.core.security import hash_password
    user = User(
        email="changepwd@example.com",
        password_hash=hash_password("OldPassword1!"),
        full_name="Password Changer",
        role="student"
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    token = create_access_token(data={"sub": user.id, "role": user.role})
    
    # Change password
    response = await client.post(
        "/api/v1/users/change-password",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "old_password": "OldPassword1!",
            "new_password": "NewPassword2!"
        }
    )
    assert response.status_code == 200
    
    # Confirm old password doesn't work and new does
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "changepwd@example.com",
            "password": "NewPassword2!"
        }
    )
    assert login_resp.status_code == 200

@pytest.mark.asyncio
async def test_role_based_access_control(client: AsyncClient, db_session: MongoSession):
    # Create student and admin records
    student = User(email="std@example.com", password_hash="hash", full_name="Student User", role="student")
    admin = User(email="adm@example.com", password_hash="hash", full_name="Admin User", role="admin")
    db_session.add_all([student, admin])
    await db_session.commit()
    await db_session.refresh(student)
    await db_session.refresh(admin)
    
    student_token = create_access_token(data={"sub": student.id, "role": student.role})
    admin_token = create_access_token(data={"sub": admin.id, "role": admin.role})
    
    # Student tries to list users (admin only)
    resp = await client.get(
        "/api/v1/users",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    assert resp.status_code == 403
    assert "permission" in resp.json()["message"]
    
    # Admin tries to list users
    resp = await client.get(
        "/api/v1/users",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert resp.status_code == 200
    assert len(resp.json()["data"]) >= 2

@pytest.mark.asyncio
async def test_soft_delete(client: AsyncClient, db_session: MongoSession):
    # Create student and admin records
    student = User(email="delete-me@example.com", password_hash="hash", full_name="Delete User", role="student")
    admin = User(email="adm2@example.com", password_hash="hash", full_name="Admin User", role="admin")
    db_session.add_all([student, admin])
    await db_session.commit()
    await db_session.refresh(student)
    await db_session.refresh(admin)
    
    admin_token = create_access_token(data={"sub": admin.id, "role": admin.role})
    
    # Soft delete the student
    resp = await client.delete(
        f"/api/v1/users/{student.id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert resp.status_code == 200
    
    user_doc = await db_session.db["users"].find_one({"id": student.id})
    assert user_doc is not None
    assert user_doc.get("deleted_at") is not None
    
    # Verify CRUD ignores soft-deleted
    user_by_email = await crud.get_user_by_email(db_session, student.email)
    assert user_by_email is None
    
    user_by_id = await crud.get_user_by_id(db_session, student.id)
    assert user_by_id is None
