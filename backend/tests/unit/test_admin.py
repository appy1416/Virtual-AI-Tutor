import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.user import User
from app.core.security import create_access_token

@pytest.mark.asyncio
async def test_admin_control_panel(client: AsyncClient, db_session: AsyncSession):
    admin = User(email="adm@example.com", password_hash="hash", full_name="Admin", role="admin")
    student = User(email="std_adm@example.com", password_hash="hash", full_name="Student", role="student")
    db_session.add_all([admin, student])
    await db_session.commit()
    await db_session.refresh(admin)
    await db_session.refresh(student)

    admin_token = create_access_token(data={"sub": admin.id, "role": admin.role})
    student_token = create_access_token(data={"sub": student.id, "role": student.role})

    # 1. Student access blocked (403)
    resp_blk = await client.get(
        "/api/v1/admin/users",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    assert resp_blk.status_code == 403

    # 2. Admin lists users (200)
    resp_list = await client.get(
        "/api/v1/admin/users",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert resp_list.status_code == 200
    assert resp_list.json()["data"]["total_count"] >= 2

    # 3. Change user role
    resp_role = await client.put(
        f"/api/v1/admin/users/{student.id}/role",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"role": "tutor"}
    )
    assert resp_role.status_code == 200
    assert resp_role.json()["data"]["role"] == "tutor"

    # 4. Deactivate user
    resp_deact = await client.post(
        f"/api/v1/admin/users/{student.id}/deactivate",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert resp_deact.status_code == 200

    # Verify user deactivated
    await db_session.refresh(student)
    assert student.deleted_at is not None
