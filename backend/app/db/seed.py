import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

from app.core.security import hash_password
from app.db.models.user import User
from app.db.models.course import Course
from app.db.models.lesson import Lesson
from app.db.models.quiz import Quiz

logger = logging.getLogger("edutwin.seed")

async def seed_data(db: AsyncSession) -> None:
    # Check if we already have users
    stmt = select(func.count(User.id))
    res = await db.execute(stmt)
    user_count = res.scalar() or 0
    if user_count > 0:
        logger.info("Database already seeded. Skipping initial database seeding.")
        return

    logger.info("Starting database seeding...")

    # 1. Create Users
    admin = User(
        email="admin@edutwin.ai",
        password_hash=hash_password("password"),
        full_name="Admin User",
        role="admin"
    )
    student = User(
        email="student@edutwin.ai",
        password_hash=hash_password("password"),
        full_name="Student User",
        role="student"
    )
    db.add_all([admin, student])
    await db.flush()  # Generate IDs

    # 2. Create Courses
    c1 = Course(
        tutor_id=admin.id,
        title="Calculus Foundations",
        description="Master limits, derivatives, integrals and their applications in science and engineering.",
        category="STEM",
        level="intermediate",
        is_published=True
    )
    c2 = Course(
        tutor_id=admin.id,
        title="Modern World History",
        description="Understand key global events from the industrial revolution to modern geopolitics.",
        category="Humanity",
        level="beginner",
        is_published=True
    )
    db.add_all([c1, c2])
    await db.flush()

    # 3. Create Lessons
    l1 = Lesson(
        course_id=c1.id,
        sequence_order=1,
        title="Introduction to Limits",
        description="Understand the fundamental concept of limits and how they form the basis of calculus.",
        content="""# Introduction to Limits

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
        learning_objectives=["Understand limit definitions", "Analyze limits graphically and algebraically", "Solve limit problems involving indeterminates"],
        estimated_duration_minutes=30,
        difficulty_score=3
    )

    l2 = Lesson(
        course_id=c1.id,
        sequence_order=2,
        title="The Derivative Concept",
        description="Learn the derivative as an instantaneous rate of change and the slope of a tangent line.",
        content="""# The Derivative Concept

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
        learning_objectives=["Define derivative as a limit", "Use the Power Rule", "Calculate tangent line slopes"],
        estimated_duration_minutes=45,
        difficulty_score=5
    )

    l3 = Lesson(
        course_id=c2.id,
        sequence_order=1,
        title="The Industrial Revolution",
        description="Explore the shift from agrarian economies to industrialized manufacturing hubs.",
        content="""# The Industrial Revolution

The Industrial Revolution marks a major turning point in human history, transitioning societies from agrarian economies to manufacturing powerhouses.

## Key Factors of Industrialization

1. **The Steam Engine**: James Watt's refinement of the steam engine allowed factories to be built anywhere, not just near rivers.
2. **Coal and Iron**: Crucial natural resources that fueled steam power and built machine frames.
3. **Urbanization**: Workers migrated from rural farms to cities to work in textile mills and manufacturing plants.

### Societal Impacts:
- Growth of the middle class
- Standard of living changes
- Early labor unions and reforms""",
        learning_objectives=["Identify primary drivers of industrialization", "Analyze social changes", "Explain geographic shifts in manufacturing"],
        estimated_duration_minutes=35,
        difficulty_score=2
    )
    db.add_all([l1, l2, l3])
    await db.flush()

    # 4. Create Quizzes
    q1 = Quiz(
        lesson_id=l1.id,
        question_text="What is the limit of f(x) = (x^2 - 4) / (x - 2) as x approaches 2?",
        quiz_type="mcq",
        options=[
            {"option_text": "2", "is_correct": False},
            {"option_text": "4", "is_correct": True},
            {"option_text": "undefined", "is_correct": False},
            {"option_text": "0", "is_correct": False}
        ],
        difficulty_level=3,
        max_attempts=3
    )

    q2 = Quiz(
        lesson_id=l2.id,
        question_text="What is the derivative of f(x) = 3x^3 + 5x?",
        quiz_type="mcq",
        options=[
            {"option_text": "9x^2 + 5", "is_correct": True},
            {"option_text": "3x^2 + 5", "is_correct": False},
            {"option_text": "9x^3 + 5x", "is_correct": False},
            {"option_text": "x^3 + 5", "is_correct": False}
        ],
        difficulty_level=4,
        max_attempts=3
    )

    q3 = Quiz(
        lesson_id=l3.id,
        question_text="Who refined the steam engine, greatly accelerating the Industrial Revolution?",
        quiz_type="mcq",
        options=[
            {"option_text": "Thomas Edison", "is_correct": False},
            {"option_text": "Eli Whitney", "is_correct": False},
            {"option_text": "James Watt", "is_correct": True},
            {"option_text": "Henry Ford", "is_correct": False}
        ],
        difficulty_level=2,
        max_attempts=3
    )
    db.add_all([q1, q2, q3])
    await db.commit()
    logger.info("Database seeding successfully completed!")
