import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.user import User
from app.core.security import create_access_token

@pytest.mark.asyncio
async def test_learning_twin_profiling(client: AsyncClient, db_session: AsyncSession):
    student = User(email="std_lt@example.com", password_hash="hash", full_name="Student", role="student")
    db_session.add(student)
    await db_session.commit()
    await db_session.refresh(student)

    student_token = create_access_token(data={"sub": student.id, "role": student.role})

    # 1. Fetch profile (tests self-healing auto creation)
    resp = await client.get(
        "/api/v1/learning-twin",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["learning_style"] == "mixed"

    # 2. Update profile
    resp_up = await client.put(
        "/api/v1/learning-twin",
        headers={"Authorization": f"Bearer {student_token}"},
        json={
            "learning_style": "visual",
            "learning_pace": "fast"
        }
    )
    assert resp_up.status_code == 200
    assert resp_up.json()["data"]["learning_style"] == "visual"
    assert resp_up.json()["data"]["learning_pace"] == "fast"

    # 3. Fetch insights and roadmaps
    resp_ins = await client.get(
        "/api/v1/learning-twin/insights",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    assert resp_ins.status_code == 200
    assert len(resp_ins.json()["data"]["insights"]) > 0

    resp_rd = await client.get(
        "/api/v1/learning-twin/roadmap",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    assert resp_rd.status_code == 200
    assert len(resp_rd.json()["data"]) > 0
