import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.user import User
from app.db.models.course import Course
from app.db.models.lesson import Lesson
from app.db.models.quiz import Quiz
from app.db.models.analytics import StudentPerformance
from app.core.security import create_access_token
from app.modules.recommendations import service as rec_service

@pytest.mark.asyncio
async def test_personalized_recommendations(client: AsyncClient, db_session: AsyncSession):
    student = User(email="std_r@example.com", password_hash="hash", full_name="Student", role="student")
    tutor = User(email="tut_r@example.com", password_hash="hash", full_name="Tutor", role="tutor")
    db_session.add_all([student, tutor])
    await db_session.commit()
    await db_session.refresh(student)
    await db_session.refresh(tutor)

    course = Course(tutor_id=tutor.id, title="Calculus Foundations", description="description", category="STEM", level="intermediate", is_published=True)
    db_session.add(course)
    await db_session.commit()
    await db_session.refresh(course)

    lesson = Lesson(course_id=course.id, sequence_order=1, title="Calculus 1", description="Calculus lesson", content="Content here")
    db_session.add(lesson)
    await db_session.commit()
    await db_session.refresh(lesson)

    quiz = Quiz(lesson_id=lesson.id, question_text="Quiz Q", quiz_type="mcq")
    db_session.add(quiz)
    await db_session.commit()
    await db_session.refresh(quiz)

    # Log weakness in Calculus 1 (score = 50)
    perf = StudentPerformance(
        student_id=student.id,
        lesson_id=lesson.id,
        quiz_id=quiz.id,
        score=50,
        accuracy=50,
        time_spent_seconds=30
    )
    db_session.add(perf)
    await db_session.commit()

    student_token = create_access_token(data={"sub": student.id, "role": student.role})

    # 1. Fetch recommendations on the fly
    resp = await client.get(
        "/api/v1/recommendations",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data["items"]) > 0
    rec_id = data["items"][0]["id"]

    # 2. Mark recommendation clicked
    resp_clk = await client.post(
        f"/api/v1/recommendations/{rec_id}/feedback",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    assert resp_clk.status_code == 200
    assert resp_clk.json()["data"]["clicked"] is True
