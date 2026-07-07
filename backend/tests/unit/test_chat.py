import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.testclient import TestClient

from app.db.models.user import User
from app.core.security import create_access_token
from app.main import app

@pytest.mark.asyncio
async def test_chat_dialogue_flow_and_websockets(client: AsyncClient, db_session: AsyncSession):
    student = User(email="std_c@example.com", password_hash="hash", full_name="Student", role="student")
    db_session.add(student)
    await db_session.commit()
    await db_session.refresh(student)

    student_token = create_access_token(data={"sub": student.id, "role": student.role})

    # 1. Start Chat Session
    resp = await client.post(
        "/api/v1/chat/start",
        headers={"Authorization": f"Bearer {student_token}"},
        json={
            "lesson_id": None,
            "course_id": None
        }
    )
    assert resp.status_code == 201
    session_id = resp.json()["data"]["id"]

    # 2. Send Message
    resp_msg = await client.post(
        f"/api/v1/chat/{session_id}/message",
        headers={"Authorization": f"Bearer {student_token}"},
        json={
            "message": "What is the capital of France?"
        }
    )
    assert resp_msg.status_code == 200
    data = resp_msg.json()["data"]
    assert data["user_message"]["content"] == "What is the capital of France?"
    assert "法国" in data["ai_response"]["content"] or "France" in data["ai_response"]["content"]

    # 3. Search Chat History
    resp_sch = await client.get(
        "/api/v1/chat/search?q=capital",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    assert resp_sch.status_code == 200
    assert len(resp_sch.json()["data"]) == 1

    # 4. Close Session
    resp_cls = await client.post(
        f"/api/v1/chat/{session_id}/close",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    assert resp_cls.status_code == 200
    assert resp_cls.json()["data"]["ended_at"] is not None

    # 5. WebSocket Test (Using TestClient synchronous interface since it supports WebSocket checks natively)
    sync_client = TestClient(app)
    with sync_client.websocket_connect(f"/api/v1/ws/chat/{session_id}") as websocket:
        websocket.send_text("Hello Live Companion")
        reply = websocket.receive_text()
        assert "WebSocket Echo response to:" in reply
