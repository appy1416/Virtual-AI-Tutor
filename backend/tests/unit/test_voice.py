import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
import io

from app.db.models.user import User
from app.core.security import create_access_token

@pytest.mark.asyncio
async def test_voice_tutor_sessions(client: AsyncClient, db_session: AsyncSession):
    student = User(email="std_v@example.com", password_hash="hash", full_name="Student", role="student")
    db_session.add(student)
    await db_session.commit()
    await db_session.refresh(student)

    student_token = create_access_token(data={"sub": student.id, "role": student.role})

    # 1. Start session
    resp = await client.post(
        "/api/v1/voice/sessions",
        headers={"Authorization": f"Bearer {student_token}"},
        json={
            "tutor_type": "ai_voice",
            "lesson_id": None
        }
    )
    assert resp.status_code == 201
    session_id = resp.json()["data"]["id"]

    # 2. Upload audio (mp3 format)
    audio_data = io.BytesIO(b"dummy audio content")
    resp_up = await client.post(
        f"/api/v1/voice/sessions/{session_id}/upload",
        headers={"Authorization": f"Bearer {student_token}"},
        files={"file": ("test.mp3", audio_data, "audio/mpeg")}
    )
    assert resp_up.status_code == 200
    assert resp_up.json()["data"]["transcription"] is not None

    # 3. Retrieve transcript
    resp_tr = await client.get(
        f"/api/v1/voice/sessions/{session_id}/transcript",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    assert resp_tr.status_code == 200
    assert "Mock voice transcription" in resp_tr.json()["data"]["transcription"]

    # 4. Close session
    resp_cls = await client.post(
        f"/api/v1/voice/sessions/{session_id}/close",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    assert resp_cls.status_code == 200
    assert resp_cls.json()["data"]["ended_at"] is not None
