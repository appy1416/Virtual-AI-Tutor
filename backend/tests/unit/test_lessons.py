import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.models.user import User
from app.db.models.course import Course
from app.db.models.lesson import Lesson, LessonCompletion
from app.core.security import create_access_token
from app.modules.lessons import crud as lesson_crud

@pytest.mark.asyncio
async def test_create_lesson_sequence_order(client: AsyncClient, db_session: AsyncSession):
    # Setup tutor and course
    tutor = User(email="tutor5@example.com", password_hash="hash", full_name="Tutor", role="tutor")
    db_session.add(tutor)
    await db_session.commit()
    await db_session.refresh(tutor)
    
    course = Course(tutor_id=tutor.id, title="Algorithm Course", description="Algo course desc", category="STEM", level="advanced", is_published=True)
    db_session.add(course)
    await db_session.commit()
    await db_session.refresh(course)
    
    tutor_token = create_access_token(data={"sub": tutor.id, "role": tutor.role})
    
    # Create lesson 1
    resp1 = await client.post(
        f"/api/v1/courses/{course.id}/lessons",
        headers={"Authorization": f"Bearer {tutor_token}"},
        json={
            "title": "Lesson 1: Intro",
            "description": "Introduction to algorithms.",
            "content": "# Markdown content here.",
            "learning_objectives": ["Understand algorithms"],
            "estimated_duration_minutes": 30,
            "difficulty_score": 3
        }
    )
    assert resp1.status_code == 201
    assert resp1.json()["data"]["sequence_order"] == 1
    
    # Create lesson 2
    resp2 = await client.post(
        f"/api/v1/courses/{course.id}/lessons",
        headers={"Authorization": f"Bearer {tutor_token}"},
        json={
            "title": "Lesson 2: Big O",
            "description": "Analyzing computational complexity.",
            "content": "# Markdown content here for Big O.",
            "learning_objectives": ["Understand Big O notation"],
            "estimated_duration_minutes": 45,
            "difficulty_score": 6
        }
    )
    assert resp2.status_code == 201
    assert resp2.json()["data"]["sequence_order"] == 2

@pytest.mark.asyncio
async def test_lesson_completion(client: AsyncClient, db_session: AsyncSession):
    # Setup student, course, lesson
    student = User(email="s2@example.com", password_hash="hash", full_name="Student", role="student")
    tutor = User(email="tutor6@example.com", password_hash="hash", full_name="Tutor", role="tutor")
    db_session.add_all([student, tutor])
    await db_session.commit()
    await db_session.refresh(student)
    await db_session.refresh(tutor)
    
    course = Course(tutor_id=tutor.id, title="Calculus Course", description="Calc course desc", category="STEM", level="intermediate", is_published=True)
    db_session.add(course)
    await db_session.commit()
    await db_session.refresh(course)
    
    lesson = Lesson(
        course_id=course.id,
        sequence_order=1,
        title="Derivatives",
        description="Intro to derivatives.",
        content="# Calc content",
        learning_objectives=[]
    )
    db_session.add(lesson)
    await db_session.commit()
    await db_session.refresh(lesson)
    
    student_token = create_access_token(data={"sub": student.id, "role": student.role})
    
    # Mark lesson complete
    resp = await client.post(
        f"/api/v1/lessons/{lesson.id}/complete",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    assert resp.status_code == 200
    assert resp.json()["success"] is True
    
    # Assert database log exists
    res = await db_session.execute(
        select(LessonCompletion).where(
            LessonCompletion.user_id == student.id,
            LessonCompletion.lesson_id == lesson.id
        )
    )
    assert res.scalars().first() is not None

@pytest.mark.asyncio
async def test_lesson_reordering(client: AsyncClient, db_session: AsyncSession):
    tutor = User(email="tutor7@example.com", password_hash="hash", full_name="Tutor", role="tutor")
    db_session.add(tutor)
    await db_session.commit()
    await db_session.refresh(tutor)
    
    course = Course(tutor_id=tutor.id, title="Reorder Course", description="Reorder course desc", category="STEM", level="advanced", is_published=True)
    db_session.add(course)
    await db_session.commit()
    await db_session.refresh(course)
    
    l1 = Lesson(course_id=course.id, sequence_order=1, title="L1", description="desc", content="content")
    l2 = Lesson(course_id=course.id, sequence_order=2, title="L2", description="desc", content="content")
    db_session.add_all([l1, l2])
    await db_session.commit()
    await db_session.refresh(l1)
    await db_session.refresh(l2)
    
    tutor_token = create_access_token(data={"sub": tutor.id, "role": tutor.role})
    
    # Reorder L2 to be first and L1 to be second
    resp = await client.put(
        f"/api/v1/lessons/{course.id}/reorder",
        headers={"Authorization": f"Bearer {tutor_token}"},
        json={
            "lesson_order_list": [l2.id, l1.id]
        }
    )
    assert resp.status_code == 200
    assert resp.json()["success"] is True
    
    # Refresh from DB and verify sequence orders
    res1 = await db_session.execute(select(Lesson).where(Lesson.id == l1.id))
    db_l1 = res1.scalars().first()
    res2 = await db_session.execute(select(Lesson).where(Lesson.id == l2.id))
    db_l2 = res2.scalars().first()
    
    assert db_l2.sequence_order == 1
    assert db_l1.sequence_order == 2
