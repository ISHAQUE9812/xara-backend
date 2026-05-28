"""
Tests for XARA Screen Service
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.screen_service import ScreenService
from app.models.screen_model import ScreenModel
from bson import ObjectId


@pytest.fixture
def mock_db():
    """Mock MongoDB database"""
    db = MagicMock()
    db.__getitem__ = MagicMock(return_value=MagicMock())
    return db


@pytest.fixture
def screen_service(mock_db):
    """Create screen service with mock db"""
    return ScreenService(mock_db)


@pytest.mark.asyncio
async def test_register_new_screen(screen_service, mock_db):
    """Test screen registration for a brand new screen ID (creation path)"""
    screen_data = {
        "screen_id": "SCREEN_001",
        "name": "Test Screen",
        "location": "Test Location",
        "resolution": "1920x1080"
    }
    
    # Mock find_one to return None first (doesn't exist), then return the created doc
    mock_id = ObjectId()
    mock_db["screens"].find_one = AsyncMock(
        side_effect=[
            None,  # First call during check: does not exist
            {
                "_id": mock_id,
                "screen_id": "SCREEN_001",
                "uuid": "test-uuid",
                "name": "Test Screen",
                "location": "Test Location",
                "resolution": "1920x1080"
            }  # Second call after insert: return the created doc
        ]
    )
    
    mock_db["screens"].insert_one = AsyncMock(
        return_value=MagicMock(inserted_id=mock_id)
    )
    
    result = await screen_service.register_screen(screen_data)
    
    assert result is not None
    assert result["id"] == str(mock_id)
    assert result["screen_id"] == "SCREEN_001"
    mock_db["screens"].insert_one.assert_called_once()


@pytest.mark.asyncio
async def test_register_existing_screen(screen_service, mock_db):
    """Test screen registration for an already existing screen ID (idempotent update path)"""
    screen_data = {
        "screen_id": "SCREEN_001",
        "name": "Updated Screen Name",
        "location": "Test Location",
        "resolution": "1920x1080"
    }
    
    mock_id = ObjectId()
    # Mock find_one to return the existing screen, then return the updated screen doc
    mock_db["screens"].find_one = AsyncMock(
        side_effect=[
            {
                "_id": mock_id,
                "screen_id": "SCREEN_001",
                "uuid": "test-uuid",
                "name": "Old Screen Name",
                "location": "Test Location",
                "resolution": "1920x1080"
            },  # First call during check: exists
            {
                "_id": mock_id,
                "screen_id": "SCREEN_001",
                "uuid": "test-uuid",
                "name": "Updated Screen Name",
                "location": "Test Location",
                "resolution": "1920x1080"
            }  # Second call: return updated doc
        ]
    )
    
    mock_db["screens"].update_one = AsyncMock(
        return_value=MagicMock(modified_count=1)
    )
    
    result = await screen_service.register_screen(screen_data)
    
    assert result is not None
    assert result["name"] == "Updated Screen Name"
    mock_db["screens"].update_one.assert_called_once()


@pytest.mark.asyncio
async def test_get_screen_by_id(screen_service, mock_db):
    """Test getting screen by ID"""
    mock_db["screens"].find_one = AsyncMock(
        return_value={
            "_id": ObjectId(),
            "screen_id": "SCREEN_001",
            "name": "Test Screen"
        }
    )
    
    result = await screen_service.get_screen_by_id("SCREEN_001")
    
    assert result is not None
    assert result["screen_id"] == "SCREEN_001"


@pytest.mark.asyncio
async def test_update_screen_status(screen_service, mock_db):
    """Test updating screen status"""
    mock_db["screens"].update_one = AsyncMock(
        return_value=MagicMock(modified_count=1)
    )
    mock_db["screens"].find_one = AsyncMock(
        return_value={
            "_id": ObjectId(),
            "screen_id": "SCREEN_001",
            "status": "online"
        }
    )
    
    result = await screen_service.update_screen_status("SCREEN_001", "offline")
    
    assert result is not None
    mock_db["screens"].update_one.assert_called_once()


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
