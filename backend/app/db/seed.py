import logging
import uuid
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.core.security import hash_password

logger = logging.getLogger("edutwin.seed")

async def seed_data(db: AsyncIOMotorDatabase) -> None:
    # Check if we already have users
    user_count = await db["users"].count_documents({"deleted_at": None})
    if user_count > 0:
        logger.info("Database already seeded. Skipping initial database seeding.")
        return

    logger.info("Starting database seeding...")

    # 1. Generate IDs
    admin_id = str(uuid.uuid4())
    student_id = str(uuid.uuid4())
    c1_id = str(uuid.uuid4())
    c2_id = str(uuid.uuid4())
    l1_id = str(uuid.uuid4())
    l2_id = str(uuid.uuid4())
    l3_id = str(uuid.uuid4())
    
    now = datetime.now(timezone.utc)

    # 2. Users
    admin_user = {
        "id": admin_id,
        "email": "admin@edutwin.ai",
        "password_hash": hash_password("password"),
        "full_name": "Admin User",
        "role": "admin",
        "profile_picture_url": None,
        "bio": "System Administrator",
        "preferences": {},
        "points": 0,
        "badges": [],
        "streak_days": 0,
        "last_activity_date": None,
        "created_at": now,
        "updated_at": now,
        "deleted_at": None
    }
    
    student_user = {
        "id": student_id,
        "email": "student@edutwin.ai",
        "password_hash": hash_password("password"),
        "full_name": "Student User",
        "role": "student",
        "profile_picture_url": None,
        "bio": "Active Learner",
        "preferences": {},
        "points": 0,
        "badges": [],
        "streak_days": 0,
        "last_activity_date": None,
        "created_at": now,
        "updated_at": now,
        "deleted_at": None
    }
    
    await db["users"].insert_many([admin_user, student_user])

    # 3. Courses
    c1 = {
        "id": c1_id,
        "tutor_id": admin_id,
        "title": "Calculus Foundations",
        "description": "Master limits, derivatives, integrals and their applications in science and engineering.",
        "category": "STEM",
        "level": "intermediate",
        "thumbnail_url": None,
        "max_students": None,
        "is_published": True,
        "created_at": now,
        "updated_at": now,
        "deleted_at": None
    }
    
    c2 = {
        "id": c2_id,
        "tutor_id": admin_id,
        "title": "Modern World History",
        "description": "Understand key global events from the industrial revolution to modern geopolitics.",
        "category": "Humanity",
        "level": "beginner",
        "thumbnail_url": None,
        "max_students": None,
        "is_published": True,
        "created_at": now,
        "updated_at": now,
        "deleted_at": None
    }
    
    await db["courses"].insert_many([c1, c2])

    # 4. Lessons
    l1 = {
        "id": l1_id,
        "course_id": c1_id,
        "sequence_order": 1,
        "title": "Introduction to Limits",
        "description": "Understand the fundamental concept of limits and how they form the basis of calculus.",
        "content": """# Introduction to Limits

Limits are the fundamental building blocks of calculus. They allow us to study the behavior of functions as they approach specific points, even if the function is undefined at that point.

## What is a Limit?

Mathematically, we write:
$$\\lim_{x \\to c} f(x) = L$$

This means that as $x$ gets arbitrarily close to $c$, the function value $f(x)$ gets close to $L$.

### Example:
Consider the function $f(x) = \\frac{x^2 - 1}{x - 1}$. 
At $x = 1$, the function is undefined (division by zero). However, we can simplify the function for $x \\neq 1$:
$$f(x) = \\frac{(x-1)(x+1)}{x-1} = x + 1$$

Therefore, as $x$ approaches $1$, $f(x)$ approaches $1 + 1 = 2$.
Thus, $\\lim_{x \\to 1} f(x) = 2$.""",
        "learning_objectives": ["Understand limit definitions", "Analyze limits graphically and algebraically", "Solve limit problems involving indeterminates"],
        "estimated_duration_minutes": 30,
        "difficulty_score": 3,
        "created_at": now,
        "updated_at": now,
        "deleted_at": None
    }

    l2 = {
        "id": l2_id,
        "course_id": c1_id,
        "sequence_order": 2,
        "title": "The Derivative Concept",
        "description": "Learn the derivative as an instantaneous rate of change and the slope of a tangent line.",
        "content": """# The Derivative Concept

The derivative is one of the most powerful tools in mathematics, representing the rate at which a function is changing at any given point.

## The Slope of a Curve

For a straight line, the slope is constant: $m = \\frac{\\Delta y}{\\Delta x}$.
For a curve, the slope changes continuously. The derivative represents the slope of the *tangent line* to the curve at a specific point.

### Definition of Derivative:
$$f'(x) = \\lim_{h \\to 0} \\frac{f(x+h) - f(x)}{h}$$

This is known as the limit of the difference quotient.

### Common Rules:
1. **Power Rule**: $\\frac{d}{dx}[x^n] = n x^{n-1}$
2. **Constant Rule**: $\\frac{d}{dx}[c] = 0$
3. **Sum Rule**: $(f + g)' = f' + g'$""",
        "learning_objectives": ["Define derivative as a limit", "Use the Power Rule", "Calculate tangent line slopes"],
        "estimated_duration_minutes": 45,
        "difficulty_score": 5,
        "created_at": now,
        "updated_at": now,
        "deleted_at": None
    }

    l3 = {
        "id": l3_id,
        "course_id": c2_id,
        "sequence_order": 1,
        "title": "The Industrial Revolution",
        "description": "Explore the shift from agrarian economies to industrialized manufacturing hubs.",
        "content": """# The Industrial Revolution

The Industrial Revolution marks a major turning point in human history, transitioning societies from agrarian economies to manufacturing powerhouses.

## Key Factors of Industrialization

1. **The Steam Engine**: James Watt's refinement of the steam engine allowed factories to be built anywhere, not just near rivers.
2. **Coal and Iron**: Crucial natural resources that fueled steam power and built machine frames.
3. **Urbanization**: Workers migrated from rural farms to cities to work in textile mills and manufacturing plants.

### Societal Impacts:
- Growth of the middle class
- Standard of living changes
- Early labor unions and reforms""",
        "learning_objectives": ["Identify primary drivers of industrialization", "Analyze social changes", "Explain geographic shifts in manufacturing"],
        "estimated_duration_minutes": 35,
        "difficulty_score": 2,
        "created_at": now,
        "updated_at": now,
        "deleted_at": None
    }
    
    await db["lessons"].insert_many([l1, l2, l3])

    # 5. Quizzes
    q1 = {
        "id": str(uuid.uuid4()),
        "lesson_id": l1_id,
        "question_text": "What is the limit of f(x) = (x^2 - 4) / (x - 2) as x approaches 2?",
        "quiz_type": "mcq",
        "options": [
            {"option_text": "2", "is_correct": False},
            {"option_text": "4", "is_correct": True},
            {"option_text": "undefined", "is_correct": False},
            {"option_text": "0", "is_correct": False}
        ],
        "difficulty_level": 3,
        "max_attempts": 3,
        "created_at": now,
        "updated_at": now,
        "deleted_at": None
    }

    q2 = {
        "id": str(uuid.uuid4()),
        "lesson_id": l2_id,
        "question_text": "What is the derivative of f(x) = 3x^3 + 5x?",
        "quiz_type": "mcq",
        "options": [
            {"option_text": "9x^2 + 5", "is_correct": True},
            {"option_text": "3x^2 + 5", "is_correct": False},
            {"option_text": "9x^3 + 5x", "is_correct": False},
            {"option_text": "x^3 + 5", "is_correct": False}
        ],
        "difficulty_level": 4,
        "max_attempts": 3,
        "created_at": now,
        "updated_at": now,
        "deleted_at": None
    }

    q3 = {
        "id": str(uuid.uuid4()),
        "lesson_id": l3_id,
        "question_text": "Who refined the steam engine, greatly accelerating the Industrial Revolution?",
        "quiz_type": "mcq",
        "options": [
            {"option_text": "Thomas Edison", "is_correct": False},
            {"option_text": "Eli Whitney", "is_correct": False},
            {"option_text": "James Watt", "is_correct": True},
            {"option_text": "Henry Ford", "is_correct": False}
        ],
        "difficulty_level": 2,
        "max_attempts": 3,
        "created_at": now,
        "updated_at": now,
        "deleted_at": None
    }
    
    await db["quizzes"].insert_many([q1, q2, q3])
    logger.info("Database seeding successfully completed!")
