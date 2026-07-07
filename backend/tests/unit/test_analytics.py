import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone, timedelta

from app.db.models.user import User
from app.db.models.course import Course
from app.db.models.lesson import Lesson, LessonCompletion
from app.db.models.user_course import UserCourse
from app.db.models.analytics import AnalyticsEvent
from app.core.security import create_access_token
from app.tasks.analytics_tasks import log_page_view

@pytest.mark.asyncio
async def test_analytics_telemetry_and_dashboard(client: AsyncClient, db_session: AsyncSession):
    student = User(email="std_a@example.com", password_hash="hash", full_name="Student", role="student")
    tutor = User(email="tut_a@example.com", password_hash="hash", full_name="Tutor", role="tutor")
    db_session.add_all([student, tutor])
    await db_session.commit()
    await db_session.refresh(student)
    await db_session.refresh(tutor)

    student_token = create_access_token(data={"sub": student.id, "role": student.role})

    # Log two page views (one today, one yesterday)
    ev1 = AnalyticsEvent(student_id=student.id, event_type="page_view", metadata_json={"duration": 3600}, created_at=datetime.now(timezone.utc) - timedelta(days=1))
    ev2 = AnalyticsEvent(student_id=student.id, event_type="page_view", metadata_json={"duration": 1800}, created_at=datetime.now(timezone.utc))
    db_session.add_all([ev1, ev2])
    await db_session.commit()

    # 1. Fetch dashboard
    resp = await client.get(
        "/api/v1/analytics/dashboard",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    # 3600s + 1800s = 5400s = 1.5 hours
    assert data["total_study_hours"] == 1.5
    # Since active today and yesterday, streak is 2
    assert data["current_streak"] == 2

    # 2. Export CSV
    resp_exp = await client.get(
        "/api/v1/analytics/export",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    assert resp_exp.status_code == 200
    assert "text/csv" in resp_exp.headers["content-type"]
