import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.user import User
from app.db.models.course import Course
from app.db.models.lesson import Lesson
from app.db.models.quiz import Quiz
from app.core.security import create_access_token

@pytest.mark.asyncio
async def test_quiz_lifecycle_and_grading(client: AsyncClient, db_session: AsyncSession):
    # Setup users
    student = User(email="std_q@example.com", password_hash="hash", full_name="Student", role="student")
    tutor = User(email="tut_q@example.com", password_hash="hash", full_name="Tutor", role="tutor")
    db_session.add_all([student, tutor])
    await db_session.commit()
    await db_session.refresh(student)
    await db_session.refresh(tutor)

    course = Course(tutor_id=tutor.id, title="Math Course", description="description", category="STEM", level="intermediate", is_published=True)
    db_session.add(course)
    await db_session.commit()
    await db_session.refresh(course)

    lesson = Lesson(course_id=course.id, sequence_order=1, title="Calculus", description="Calculus lesson", content="Content here")
    db_session.add(lesson)
    await db_session.commit()
    await db_session.refresh(lesson)

    student_token = create_access_token(data={"sub": student.id, "role": student.role})
    tutor_token = create_access_token(data={"sub": tutor.id, "role": tutor.role})

    # 1. Create Quiz (Tutor only)
    resp = await client.post(
        f"/api/v1/lessons/{lesson.id}/quizzes",
        headers={"Authorization": f"Bearer {tutor_token}"},
        json={
            "lesson_id": lesson.id,
            "question_text": "What is 2+2?",
            "quiz_type": "mcq",
            "options": [
                {"option_text": "3", "is_correct": False},
                {"option_text": "4", "is_correct": True}
            ],
            "difficulty_level": 2,
            "max_attempts": 2
        }
    )
    assert resp.status_code == 201
    quiz_id = resp.json()["data"]["id"]

    # 2. Get Quiz as student (Assert correctness flag is stripped)
    resp_get = await client.get(
        f"/api/v1/quizzes/{quiz_id}",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    assert resp_get.status_code == 200
    options = resp_get.json()["data"]["options"]
    assert "is_correct" not in options[0]

    # 3. Submit correct answer
    resp_sub = await client.post(
        f"/api/v1/quizzes/{quiz_id}/submit",
        headers={"Authorization": f"Bearer {student_token}"},
        json={
            "user_answer": "4",
            "time_spent_seconds": 15
        }
    )
    assert resp_sub.status_code == 200
    assert resp_sub.json()["data"]["is_correct"] is True
    assert resp_sub.json()["data"]["score"] == 100

    # 4. Submit incorrect answer
    resp_sub2 = await client.post(
        f"/api/v1/quizzes/{quiz_id}/submit",
        headers={"Authorization": f"Bearer {student_token}"},
        json={
            "user_answer": "3",
            "time_spent_seconds": 10
        }
    )
    assert resp_sub2.status_code == 200
    assert resp_sub2.json()["data"]["is_correct"] is False
    assert resp_sub2.json()["data"]["score"] == 0

    # 5. Submit 3rd time (max_attempts = 2, so should fail)
    resp_fail = await client.post(
        f"/api/v1/quizzes/{quiz_id}/submit",
        headers={"Authorization": f"Bearer {student_token}"},
        json={
            "user_answer": "4",
            "time_spent_seconds": 12
        }
    )
    assert resp_fail.status_code == 400
