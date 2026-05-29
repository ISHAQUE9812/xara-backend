import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from app.screens.service import ScreenService
from app.screens.repository import ScreenRepository
from app.ads.repository import AdRepository
from app.screens.schema import ScreenAssignMediaRequest

@pytest.fixture
def mock_db():
    db = MagicMock()
    db.__getitem__ = MagicMock(return_value=MagicMock())
    return db

@pytest.mark.asyncio
async def test_create_screen(mock_db, monkeypatch):
    """Test screen creation"""
    monkeypatch.setattr("app.screens.repository.get_db", lambda: mock_db)
    
    mock_db["screens"].insert_one = AsyncMock()
    
    result = await ScreenService.create_screen(
        name_or_data="Mumbai Screen",
        location="Mumbai Mall",
        resolution="1920x1080"
    )
    
    assert result is not None
    assert result["screen_name"] == "Mumbai Screen"
    assert result["location"] == "Mumbai Mall"
    assert result["resolution"] == "1920x1080"
    assert result["status"] == "offline"

@pytest.mark.asyncio
async def test_get_all_screens(mock_db, monkeypatch):
    """Test getting all screens"""
    monkeypatch.setattr("app.screens.repository.get_db", lambda: mock_db)
    
    mock_screens = [
        {
            "screen_id": "SCR-1",
            "screen_name": "Screen 1",
            "location": "Location 1",
            "status": "online"
        }
    ]
    cursor_mock = MagicMock()
    cursor_mock.sort = MagicMock(return_value=cursor_mock)
    cursor_mock.to_list = AsyncMock(return_value=mock_screens)
    mock_db["screens"].find = MagicMock(return_value=cursor_mock)
    
    result = await ScreenService.get_all_screens()
    assert len(result) == 1
    assert result[0]["screen_id"] == "SCR-1"

@pytest.mark.asyncio
async def test_update_metrics(mock_db, monkeypatch):
    """Test updating metrics"""
    monkeypatch.setattr("app.screens.repository.get_db", lambda: mock_db)
    
    screen = {
        "screen_id": "SCR-1",
        "audience": 0,
        "engagement": 0
    }
    
    mock_db["screens"].find_one = AsyncMock(side_effect=lambda query: screen)
    
    async def fake_update_one(query, update):
        if "$set" in update:
            screen.update(update["$set"])
        class FakeUpdateResult:
            matched_count = 1
        return FakeUpdateResult()
        
    mock_db["screens"].update_one = AsyncMock(side_effect=fake_update_one)
    
    result = await ScreenService.update_metrics("SCR-1", audience=10, engagement=85)
    
    assert result["audience"] == 10
    assert result["engagement"] == 85

