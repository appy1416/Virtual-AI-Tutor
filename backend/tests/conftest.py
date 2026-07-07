import os
os.environ["TESTING"] = "True"

import asyncio
import pytest
import pytest_asyncio
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.core.database import get_db, mongo_db, MongoSession

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[MongoSession, None]:
    """
    Yields an isolated MongoSession wrapper for mock MongoDB, clearing collections 
    after each test to guarantee complete test isolation.
    """
    session = MongoSession(mongo_db)
    yield session
    
    # Drop all documents in all mock collections after the test completes
    collections = await mongo_db.list_collection_names()
    for coll in collections:
        await mongo_db[coll].delete_many({})

@pytest_asyncio.fixture
async def client(db_session: MongoSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Yields an AsyncClient for testing route responses, overriding standard get_db dependency.
    """
    async def _override_get_db():
        yield db_session
            
    app.dependency_overrides[get_db] = _override_get_db
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
        
    app.dependency_overrides.clear()
