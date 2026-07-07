import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.user import User
from app.db.models.course import Course
from app.db.models.lesson import Lesson
from app.db.models.note import Note
from app.core.security import create_access_token

@pytest.mark.asyncio
async def test_notes_crud_and_search(client: AsyncClient, db_session: AsyncSession):
    student = User(email="std_n@example.com", password_hash="hash", full_name="Student", role="student")
    tutor = User(email="tut_n@example.com", password_hash="hash", full_name="Tutor", role="tutor")
    db_session.add_all([student, tutor])
    await db_session.commit()
    await db_session.refresh(student)
    await db_session.refresh(tutor)

    course = Course(tutor_id=tutor.id, title="Arts Course", description="description", category="ARTS", level="beginner", is_published=True)
    db_session.add(course)
    await db_session.commit()
    await db_session.refresh(course)

    lesson = Lesson(course_id=course.id, sequence_order=1, title="Intro to Art", description="Arts lesson", content="Content here")
    db_session.add(lesson)
    await db_session.commit()
    await db_session.refresh(lesson)

    student_token = create_access_token(data={"sub": student.id, "role": student.role})

    # 1. Create note
    resp = await client.post(
        f"/api/v1/lessons/{lesson.id}/notes",
        headers={"Authorization": f"Bearer {student_token}"},
        json={
            "lesson_id": lesson.id,
            "content": "This is a markdown content note covering primary colors."
        }
    )
    assert resp.status_code == 201
    assert resp.json()["data"]["word_count"] == 9
    note_id = resp.json()["data"]["id"]

    # 2. Update note tags
    resp_up = await client.put(
        f"/api/v1/notes/{note_id}",
        headers={"Authorization": f"Bearer {student_token}"},
        json={
            "tags": ["colors", "art"]
        }
    )
    assert resp_up.status_code == 200
    assert resp_up.json()["data"]["tags"] == ["colors", "art"]

    # 3. Search notes
    resp_sch = await client.get(
        f"/api/v1/users/me/notes/search?q=primary",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    assert resp_sch.status_code == 200
    assert len(resp_sch.json()["data"]) == 1

    # 4. Summarize note
    resp_sum = await client.post(
        f"/api/v1/notes/{note_id}/summarize",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    assert resp_sum.status_code == 200
    assert resp_sum.json()["data"]["ai_summary"] is not None
