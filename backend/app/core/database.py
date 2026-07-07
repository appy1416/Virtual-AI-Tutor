import os
import logging
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from sqlalchemy.inspection import inspect
from app.core.config import settings

logger = logging.getLogger("edutwin.database")

# Detect test mode to run isolated SQL
is_testing = os.getenv("TESTING") == "True"
is_mongo = settings.DATABASE_URL.startswith("mongodb") and not is_testing

mongo_client = None
mongo_db = None

if is_mongo:
    # Use SQLite as the local cache/mirror for SQLAlchemy compatibility
    db_url = "sqlite+aiosqlite:///edutwin_mongo_cache.db"
    
    # Remove existing cache file on startup to avoid stale/out-of-sync cache
    cache_path = "edutwin_mongo_cache.db"
    if os.path.exists(cache_path):
        try:
            os.remove(cache_path)
        except Exception as e:
            logger.warning(f"Could not remove SQLite cache file: {e}")
            
    connect_args = {"check_same_thread": False}
    
    # Initialize motor client for MongoDB
    from motor.motor_asyncio import AsyncIOMotorClient  # type: ignore
    import urllib.parse
    
    # Parse and URL encode credentials dynamically if password has @
    mongo_url = settings.DATABASE_URL
    if "://" in mongo_url:
        scheme, rest = mongo_url.split("://", 1)
        if "@" in rest:
            auth, host = rest.rsplit("@", 1)
            if ":" in auth:
                user, password = auth.split(":", 1)
                # Decode first to prevent double encoding
                decoded_user = urllib.parse.unquote(user)
                decoded_password = urllib.parse.unquote(password)
                mongo_url = f"{scheme}://{urllib.parse.quote_plus(decoded_user)}:{urllib.parse.quote_plus(decoded_password)}@{host}"
                
    logger.info("Initializing MongoDB client...")
    mongo_client = AsyncIOMotorClient(mongo_url)
    mongo_db = mongo_client.get_default_database("edutwin_db")
elif settings.DATABASE_URL.startswith("mongodb"):
    # If settings.DATABASE_URL is MongoDB but is_testing is True, fall back to in-memory SQLite for testing
    db_url = "sqlite+aiosqlite:///:memory:"
    connect_args = {"check_same_thread": False}
else:
    db_url = settings.DATABASE_URL
    is_sqlite = db_url.startswith("sqlite")
    connect_args = {"check_same_thread": False} if is_sqlite else {}

# Create Engine
engine = create_async_engine(
    db_url,
    echo=settings.DEBUG and not db_url.startswith("sqlite"),
    connect_args=connect_args,
    pool_pre_ping=True if not db_url.startswith("sqlite") else False
)

# Create Session factory
AsyncSessionLocalRaw = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

class MongoSyncSession:
    """
    Session wrapper that intercepts flush and commit commands to capture and accumulate 
    additions, modifications, and deletions, and synchronizes them to MongoDB on commit.
    """
    def __init__(self, session: AsyncSession):
        self._session = session
        self._pending_new = set()
        self._pending_dirty = set()
        self._pending_deleted = set()  # set of (table_name, pk_val)
        
    def __getattr__(self, name):
        return getattr(self._session, name)
        
    async def __aenter__(self):
        await self._session.__aenter__()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._session.__aexit__(exc_type, exc_val, exc_tb)
        
    def _capture_changes(self):
        if not is_mongo or mongo_db is None:
            return
            
        for obj in self._session.new:
            if hasattr(obj, "__tablename__"):
                self._pending_new.add(obj)
                
        for obj in self._session.dirty:
            if hasattr(obj, "__tablename__"):
                if obj not in self._pending_new:
                    self._pending_dirty.add(obj)
                    
        for obj in self._session.deleted:
            if hasattr(obj, "__tablename__"):
                self._pending_new.discard(obj)
                self._pending_dirty.discard(obj)
                self._pending_deleted.add((obj.__tablename__, self._get_pk_val(obj)))
                
    async def flush(self, objects=None):
        self._capture_changes()
        await self._session.flush(objects)
        
    async def commit(self):
        self._capture_changes()
        
        # 1. Flush SQLite session to generate all keys, defaults, and timestamps
        await self._session.flush()
        
        # 2. Extract final states of new/dirty objects now that keys are populated
        new_data = []
        for obj in self._pending_new:
            new_data.append((obj.__tablename__, self._get_pk_val(obj), self._model_to_dict(obj)))
            
        dirty_data = []
        for obj in self._pending_dirty:
            dirty_data.append((obj.__tablename__, self._get_pk_val(obj), self._model_to_dict(obj)))
            
        deleted_data = list(self._pending_deleted)
        
        # 3. Commit SQLite transaction
        await self._session.commit()
        
        # 4. Synchronize all collected records to MongoDB Atlas
        if is_mongo and mongo_db is not None:
            logger.info(f"Syncing changes to MongoDB: {len(new_data)} new, {len(dirty_data)} dirty, {len(deleted_data)} deleted.")
            await self._sync_to_mongo(new_data, dirty_data, deleted_data)
            
        # 5. Clear session tracking collections
        self._pending_new.clear()
        self._pending_dirty.clear()
        self._pending_deleted.clear()
        
    async def rollback(self):
        await self._session.rollback()
        # Reset accumulations on rollback
        self._pending_new.clear()
        self._pending_dirty.clear()
        self._pending_deleted.clear()
        
    def _get_pk_val(self, obj):
        try:
            inspector = inspect(obj.__class__)
            pk_cols = [c.name for c in inspector.primary_key]
            if len(pk_cols) == 1:
                return getattr(obj, pk_cols[0])
            else:
                vals = [str(getattr(obj, col)) for col in pk_cols]
                return "_".join(vals)
        except Exception:
            return getattr(obj, "id", None)
            
    def _model_to_dict(self, obj):
        return {col.name: getattr(obj, col.name) for col in obj.__table__.columns}
        
    async def _sync_to_mongo(self, new_data, dirty_data, deleted_data):
        # Insert/replace new records
        for table_name, pk_val, doc in new_data:
            if pk_val is None:
                continue
            coll = mongo_db[table_name]
            doc["_id"] = pk_val
            logger.info(f"MongoDB Sync: UPSERT {table_name} with _id={pk_val}")
            await coll.replace_one({"_id": pk_val}, doc, upsert=True)
            
        # Update modified records
        for table_name, pk_val, doc in dirty_data:
            if pk_val is None:
                continue
            coll = mongo_db[table_name]
            doc["_id"] = pk_val
            logger.info(f"MongoDB Sync: UPDATE {table_name} with _id={pk_val}")
            await coll.replace_one({"_id": pk_val}, doc, upsert=True)
            
        # Delete removed records
        for table_name, pk_val in deleted_data:
            if pk_val is None:
                continue
            coll = mongo_db[table_name]
            logger.info(f"MongoDB Sync: DELETE {table_name} with _id={pk_val}")
            await coll.delete_one({"_id": pk_val})

def AsyncSessionLocal(**kwargs):
    session = AsyncSessionLocalRaw(**kwargs)
    if is_mongo:
        return MongoSyncSession(session)
    return session

Base = declarative_base()

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency yielding an async database session.
    Ensures rollback on error and proper close operations.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

async def load_from_mongodb_to_sqlite(session: AsyncSession):
    """
    Fetch all existing documents from MongoDB and load them into the SQLite cache.
    """
    if not is_mongo or mongo_db is None:
        return
        
    logger.info("Syncing existing data from MongoDB to local cache...")
    
    # Import all models dynamically to load their definitions
    from app.db.models.user import User
    from app.db.models.course import Course
    from app.db.models.lesson import Lesson, LessonCompletion
    from app.db.models.quiz import Quiz, QuizAnswer
    from app.db.models.note import Note
    from app.db.models.chat import ChatHistory
    from app.db.models.analytics import AnalyticsEvent, StudentPerformance
    from app.db.models.recommendation import Recommendation
    from app.db.models.learning_twin import LearningTwin
    from app.db.models.voice import VoiceSession
    from app.db.models.user_course import UserCourse
    from app.db.models.notification import Notification
    from app.db.models.activity_log import ActivityLog
    from app.db.models.assignment import Assignment, AssignmentSubmission
    from app.db.models.lms_note import LMSNote

    models = [
        User, Course, Lesson, LessonCompletion, Quiz, QuizAnswer, Note, ChatHistory,
        AnalyticsEvent, StudentPerformance, Recommendation, LearningTwin, VoiceSession,
        UserCourse, Notification, ActivityLog, Assignment, AssignmentSubmission, LMSNote
    ]
    
    for model in models:
        table_name = model.__tablename__
        coll = mongo_db[table_name]
        
        # Load all documents from the collection
        cursor = coll.find({})
        docs = await cursor.to_list(length=None)
        
        if docs:
            logger.info("Loading %d documents into cache table %s...", len(docs), table_name)
            for doc in docs:
                # Remove MongoDB _id
                doc.pop("_id", None)
                
                # Instantiate model object
                obj = model()
                for col in model.__table__.columns:
                    if col.name in doc:
                        val = doc[col.name]
                        setattr(obj, col.name, val)
                session.add(obj)
            await session.flush()
            
    await session.commit()
    logger.info("MongoDB to SQLite cache synchronization complete.")
