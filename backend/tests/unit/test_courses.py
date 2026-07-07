import pytest
from httpx import AsyncClient
from app.core.database import MongoSession

from app.db.models.user import User
from app.db.models.course import Course
from app.db.models.user_course import UserCourse
from app.core.security import create_access_token


@pytest.mark.asyncio
async def test_create_course_permissions(client: AsyncClient, db_session: MongoSession):
    # Create a tutor, a student, and an admin
    tutor = User(email="tutor@example.com", password_hash="hash", full_name="Tutor One", role="tutor")
    student = User(email="std1@example.com", password_hash="hash", full_name="Student One", role="student")
    db_session.add_all([tutor, student])
    await db_session.commit()
    await db_session.refresh(tutor)
    await db_session.refresh(student)
    
    tutor_token = create_access_token(data={"sub": tutor.id, "role": tutor.role})
    student_token = create_access_token(data={"sub": student.id, "role": student.role})
    
    # 1. Tutor creates course - Success (201)
    resp = await client.post(
        "/api/v1/courses",
        headers={"Authorization": f"Bearer {tutor_token}"},
        json={
            "title": "Quantum Computation",
            "description": "An introduction to quantum gates and algorithms.",
            "category": "STEM",
            "level": "intermediate"
        }
    )
    assert resp.status_code == 201
    assert resp.json()["success"] is True
    assert resp.json()["data"]["title"] == "Quantum Computation"
    assert resp.json()["data"]["tutor_id"] == tutor.id
    
    # 2. Student attempts course creation - Blocked (403)
    resp2 = await client.post(
        "/api/v1/courses",
        headers={"Authorization": f"Bearer {student_token}"},
        json={
            "title": "Unauthorized Course",
            "description": "Should fail.",
            "category": "STEM",
            "level": "beginner"
        }
    )
    assert resp2.status_code == 403

@pytest.mark.asyncio
async def test_course_enrollment_flow(client: AsyncClient, db_session: MongoSession):
    # Setup tutor, student, course
    tutor = User(email="t1@example.com", password_hash="hash", full_name="Tutor", role="tutor")
    student = User(email="s1@example.com", password_hash="hash", full_name="Student", role="student")
    db_session.add_all([tutor, student])
    await db_session.commit()
    await db_session.refresh(tutor)
    await db_session.refresh(student)
    
    course = Course(
        tutor_id=tutor.id,
        title="Physics 101",
        description="Introductory physics.",
        category="STEM",
        level="beginner",
        is_published=True
    )
    db_session.add(course)
    await db_session.commit()
    await db_session.refresh(course)
    
    student_token = create_access_token(data={"sub": student.id, "role": student.role})
    tutor_token = create_access_token(data={"sub": tutor.id, "role": tutor.role})
    
    # 1. Student enrolls - Success (200)
    resp = await client.post(
        f"/api/v1/courses/{course.id}/enroll",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    assert resp.status_code == 200
    assert resp.json()["success"] is True
    
    # Verify enrollment entry
    enroll_doc = await db_session.db["user_courses"].find_one({"user_id": student.id, "course_id": course.id})
    assert enroll_doc is not None
    
    # 2. Duplicate enrollment - Failure (400)
    resp_dup = await client.post(
        f"/api/v1/courses/{course.id}/enroll",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    assert resp_dup.status_code == 400
    
    # 3. Tutor attempts to enroll - Blocked (403)
    resp_tutor = await client.post(
        f"/api/v1/courses/{course.id}/enroll",
        headers={"Authorization": f"Bearer {tutor_token}"}
    )
    assert resp_tutor.status_code == 403

@pytest.mark.asyncio
async def test_get_courses_pagination_and_filtering(client: AsyncClient, db_session: MongoSession):
    tutor = User(email="tutor3@example.com", password_hash="hash", full_name="Tutor", role="tutor")
    db_session.add(tutor)
    await db_session.commit()
    await db_session.refresh(tutor)
    
    # Create 3 published courses and 1 unpublished course
    c1 = Course(tutor_id=tutor.id, title="STEM Beg", description="STEM Beg Desc", category="STEM", level="beginner", is_published=True)
    c2 = Course(tutor_id=tutor.id, title="STEM Int", description="STEM Int Desc", category="STEM", level="intermediate", is_published=True)
    c3 = Course(tutor_id=tutor.id, title="Arts Beg", description="Arts Beg Desc", category="ARTS", level="beginner", is_published=True)
    c4 = Course(tutor_id=tutor.id, title="Unpublished STEM", description="Unpub Desc", category="STEM", level="beginner", is_published=False)
    
    db_session.add_all([c1, c2, c3, c4])
    await db_session.commit()
    
    # 1. Fetch default list - should return 3 published courses
    resp = await client.get("/api/v1/courses")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data["items"]) == 3
    assert data["total_count"] == 3
    
    # 2. Filter by category=STEM - returns 2
    resp_filter = await client.get("/api/v1/courses?category=STEM")
    assert len(resp_filter.json()["data"]["items"]) == 2
    
    # 3. Filter by level=beginner - returns 2
    resp_lvl = await client.get("/api/v1/courses?level=beginner")
    assert len(resp_lvl.json()["data"]["items"]) == 2
    
    # 4. Paginate limit=2
    resp_pag = await client.get("/api/v1/courses?limit=2")
    assert len(resp_pag.json()["data"]["items"]) == 2
    assert resp_pag.json()["data"]["page_count"] == 2

@pytest.mark.asyncio
async def test_course_soft_delete(client: AsyncClient, db_session: MongoSession):
    tutor = User(email="tutor4@example.com", password_hash="hash", full_name="Tutor", role="tutor")
    db_session.add(tutor)
    await db_session.commit()
    await db_session.refresh(tutor)
    
    course = Course(tutor_id=tutor.id, title="Delete Course", description="Delete Desc", category="STEM", level="beginner", is_published=True)
    db_session.add(course)
    await db_session.commit()
    await db_session.refresh(course)
    
    tutor_token = create_access_token(data={"sub": tutor.id, "role": tutor.role})
    
    # 1. Soft delete
    resp = await client.delete(
        f"/api/v1/courses/{course.id}",
        headers={"Authorization": f"Bearer {tutor_token}"}
    )
    assert resp.status_code == 200
    
    # 2. Assert not returned in list queries
    list_resp = await client.get("/api/v1/courses")
    assert not any(c["id"] == course.id for c in list_resp.json()["data"]["items"])
    
    db_course_doc = await db_session.db["courses"].find_one({"id": course.id})
    assert db_course_doc is not None
    assert db_course_doc.get("deleted_at") is not None
