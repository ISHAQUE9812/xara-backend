"""
Pytest configuration for XARA backend tests
"""

import asyncio

import pytest
import pytest_asyncio
from motor.motor_asyncio import AsyncIOMotorClient

from app.core.config import settings
from app.core.database import close_mongo_connection, connect_to_mongo, db


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_db():
    """Setup test database before running tests"""
    await connect_to_mongo()
    yield
    await close_mongo_connection()


@pytest_asyncio.fixture
async def mock_db():
    """Provide test database connection"""
    return db.db


@pytest.fixture
def anyio_backend():
    """Use asyncio for anyio tests"""
    return "asyncio"
