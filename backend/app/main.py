import logging
from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import os

# Initialize logging config first
from app import logging_config
logging_config.setup_logging()
from app.core.config import settings
from app.core.exceptions import (
    EduTwinBaseException,
    edutwin_exception_handler,
    general_http_exception_handler
)
from app.middleware.auth import AuthTokenBlacklistMiddleware
from app.modules.auth.router import router as auth_router
from app.modules.users.router import router as user_router
from app.modules.courses.router import router as courses_router
from app.modules.lessons.router import router as lessons_router
from app.modules.quizzes.router import router as quizzes_router
from app.modules.notes.router import router as notes_router
from app.modules.chat.router import router as chat_router
from app.modules.analytics.router import router as analytics_router
from app.modules.recommendations.router import router as recommendations_router
from app.modules.voice.router import router as voice_router
from app.modules.learning_twin.router import router as learning_twin_router
from app.modules.admin.router import router as admin_router
from app.modules.health.router import router as health_router
from app.modules.assignments.router import router as assignments_router
from app.modules.lms_notes.router import router as lms_notes_router
from app.modules.notifications.router import router as notifications_router
from app.modules.activity_logs.router import router as activity_logs_router

logger = logging.getLogger("edutwin.main")

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Intelligent Personalized Learning Companion Backend Services",
    version="1.0.0",
    debug=settings.DEBUG
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_origin_regex=r"^(https?://(localhost|127\.0\.0\.1|10\.\d+\.\d+\.\d+|192\.168\.\d+\.\d+|172\.(1[6-9]|2\d|3[0-1])\.\d+\.\d+)(:\d+)?)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Revoked Token Verification Middleware
app.add_middleware(AuthTokenBlacklistMiddleware)

# Static files mapping (for profile avatars)
static_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
os.makedirs(static_path, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_path), name="static")

# Static files mapping for shared study notes and assignments uploads
uploads_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads")
os.makedirs(uploads_path, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=uploads_path), name="uploads")

# Custom Exceptions Handlers Registration
app.add_exception_handler(EduTwinBaseException, edutwin_exception_handler)
app.add_exception_handler(HTTPException, general_http_exception_handler)

# General Exception Handler (Unhandled system errors)
@app.exception_handler(Exception)
async def unhandled_exception_handler(request, exc: Exception):
    logger.error("Unhandled server exception on %s: %s", request.url.path, exc, exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "data": None,
            "message": "Internal Server Error. Please contact systems administrator.",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    )

# Register routers
app.include_router(auth_router, prefix="/api/v1")
app.include_router(user_router, prefix="/api/v1")
app.include_router(courses_router, prefix="/api/v1")
app.include_router(lessons_router, prefix="/api/v1")
app.include_router(quizzes_router, prefix="/api/v1")
app.include_router(notes_router, prefix="/api/v1")
app.include_router(chat_router, prefix="/api/v1")
app.include_router(analytics_router, prefix="/api/v1")
app.include_router(recommendations_router, prefix="/api/v1")
app.include_router(voice_router, prefix="/api/v1")
app.include_router(learning_twin_router, prefix="/api/v1")
app.include_router(admin_router, prefix="/api/v1")
app.include_router(health_router, prefix="/api/v1/health")
app.include_router(assignments_router, prefix="/api/v1")
app.include_router(lms_notes_router, prefix="/api/v1")
app.include_router(notifications_router, prefix="/api/v1")
app.include_router(activity_logs_router, prefix="/api/v1")

@app.on_event("startup")
async def startup_event():
    logger.info("Verifying MongoDB connection...")
    from app.core.database import verify_mongodb_connection, mongo_db
    from app.db.seed import seed_data
    
    # 1. Connect and verify
    await verify_mongodb_connection()
    
    # 2. Run seed
    await seed_data(mongo_db)


@app.get("/health")
async def health_check():
    """
    Service health verification endpoint.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat()
    } # reload model settings
