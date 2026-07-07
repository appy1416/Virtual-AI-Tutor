import os
import logging
import urllib.parse
import uuid
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings

logger = logging.getLogger("edutwin.database")

# Detect test mode to run isolated mock Mongo
is_testing = os.getenv("TESTING") == "True"

mongo_client = None
mongo_db = None

if is_testing:
    # Use mongomock-motor for in-memory MongoDB mocking during tests
    from mongomock_motor import AsyncMongoMockClient  # type: ignore
    mongo_client = AsyncMongoMockClient()
    mongo_db = mongo_client["edutwin_test_db"]
    logger.info("Initialized in-memory Mock MongoDB client for testing.")
else:
    # Parse and URL encode credentials dynamically if password has @
    mongo_url = settings.MONGODB_URI
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
                
    logger.info("Initializing MongoDB client connecting to Atlas...")
    mongo_client = AsyncIOMotorClient(mongo_url)
    mongo_db = mongo_client.get_default_database("edutwin_db")


class Base:
    """
    Lightweight Base class to represent MongoDB documents.
    Subclasses should define `__tablename__` to map to a collection.
    """
    __tablename__ = None

    def __init__(self, **kwargs):
        self.id = kwargs.get("id") or str(uuid.uuid4())
        
        for key, val in kwargs.items():
            if key != "id":
                setattr(self, key, val)
                
        created_at = kwargs.get("created_at") or datetime.now(timezone.utc)
        if isinstance(created_at, str):
            try:
                created_at = datetime.fromisoformat(created_at)
            except Exception:
                pass
        self.created_at = created_at
        
        updated_at = kwargs.get("updated_at") or datetime.now(timezone.utc)
        if isinstance(updated_at, str):
            try:
                updated_at = datetime.fromisoformat(updated_at)
            except Exception:
                pass
        self.updated_at = updated_at

    def to_dict(self) -> dict:
        data = {}
        for k, v in self.__dict__.items():
            if not k.startswith("_"):
                data[k] = v
        return data


class MongoSession:
    """
    Compatibility wrapper mimicking SQLAlchemy session commits.
    Used by routers or services calling db.add(), db.delete(), and db.commit().
    Supports async context manager ('async with') protocol.
    """
    def __init__(self, db_client):
        self.db = db_client
        self._objects = []
        self._deletes = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    def add(self, obj):
        if obj not in self._objects:
            self._objects.append(obj)

    def add_all(self, objs):
        for o in objs:
            self.add(o)

    async def delete(self, obj):
        if obj not in self._deletes:
            self._deletes.append(obj)

    async def commit(self):
        for obj in self._objects:
            coll = obj.__tablename__
            doc = obj.to_dict()
            await self.db[coll].update_one({"id": obj.id}, {"$set": doc}, upsert=True)
        self._objects.clear()

        for obj in self._deletes:
            coll = obj.__tablename__
            await self.db[coll].delete_one({"id": obj.id})
        self._deletes.clear()

    async def flush(self):
        await self.commit()

    async def rollback(self):
        self._objects.clear()
        self._deletes.clear()

    async def close(self):
        pass

    async def refresh(self, obj):
        coll = obj.__tablename__
        doc = await self.db[coll].find_one({"id": obj.id})
        if doc:
            for k, v in doc.items():
                if k != "_id":
                    setattr(obj, k, v)


async def get_db():
    session = MongoSession(mongo_db)
    try:
        yield session
    finally:
        await session.close()


async def verify_mongodb_connection():
    try:
        await mongo_db.command("ping")
        logger.info("MongoDB Atlas connection verified successfully.")
        await setup_database_indexes()
    except Exception as e:
        logger.critical(f"MongoDB connection failed: {e}")
        raise RuntimeError(f"Database connection error: {e}")


async def setup_database_indexes():
    try:
        await mongo_db["users"].create_index("email", unique=True)
        await mongo_db["chat_sessions"].create_index("student_id")
        await mongo_db["analytics_events"].create_index("student_id")
        await mongo_db["lessons"].create_index("course_id")
        await mongo_db["quizzes"].create_index("lesson_id")
        logger.info("Database indexes successfully configured.")
    except Exception as e:
        logger.warning(f"Error creating database indexes: {e}")
