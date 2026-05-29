from dataclasses import dataclass, field
from datetime import datetime, timedelta
from io import BytesIO
from typing import Any, Dict, List

import pytest
from fastapi import UploadFile

from app.media.service import MediaService
from app.screens.playback_engine import PlaybackEngine
from app.screens.schema import ScreenAssignMediaRequest
from app.screens.service import ScreenService


class FakeAsyncCursor:
    def __init__(self, items: List[Dict[str, Any]]):
        self.items = items

    def __aiter__(self):
        self._iter = iter(self.items)
        return self

    async def __anext__(self):
        try:
            return next(self._iter)
        except StopIteration:
            raise StopAsyncIteration

    def sort(self, *args, **kwargs):
        return self

    async def to_list(self, length: int):
        return list(self.items)


class FakeCollection:
    def __init__(self, docs: List[Dict[str, Any]] = None):
        self.docs = docs or []
        self.updated = []

    async def insert_one(self, document: Dict[str, Any]):
        self.docs.append(document)
        class Result:
            inserted_id = "fake-id"
        return Result()

    async def find_one(self, query: Dict[str, Any]):
        if "screen_id" in query:
            for item in self.docs:
                if item.get("screen_id") == query["screen_id"]:
                    return item
        if "media_id" in query:
            for item in self.docs:
                if item.get("media_id") == query["media_id"]:
                    return item
        if "ad_id" in query:
            for item in self.docs:
                if item.get("ad_id") == query["ad_id"]:
                    return item
        return None

    async def update_one(self, query: Dict[str, Any], update: Dict[str, Any], upsert: bool = False):
        self.updated.append((query, update))
        matched = 0
        if "screen_id" in query:
            screen_id = query["screen_id"]
            for item in self.docs:
                if item.get("screen_id") == screen_id:
                    matched = 1
                    if "$set" in update:
                        item.update(update["$set"])
        class FakeResult:
            matched_count = matched
        return FakeResult()

    async def update_many(self, query: Dict[str, Any], update: Dict[str, Any]):
        self.updated.append((query, update))

    async def to_list(self, length: int):
        return list(self.docs)

    def find(self, query: Dict[str, Any] = None):
        return FakeAsyncCursor(self.docs)


class FakeDB:
    def __init__(self, screens=None, media=None, ads=None, screen_ad_mappings=None):
        self._collections = {
            "screens": FakeCollection(screens or []),
            "media": FakeCollection(media or []),
            "ads": FakeCollection(ads or []),
            "screen_ad_mappings": FakeCollection(screen_ad_mappings or []),
        }

    def __getitem__(self, item):
        if item not in self._collections:
            self._collections[item] = FakeCollection()
        return self._collections[item]


@pytest.mark.asyncio
async def test_media_service_save_upload_writes_file_and_metadata(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)

    fake_db = FakeDB()

    monkeypatch.setattr("app.media.service.get_db", lambda: fake_db)

    file_obj = BytesIO(b"video-bytes")
    upload_file = UploadFile(filename="nike.mp4", file=file_obj)

    saved = await MediaService.save_upload(
        file=upload_file,
        title="Nike Campaign",
        media_type="video",
        uploaded_by="user-1",
        duration=10,
    )

    uploaded_path = tmp_path / "media" / f"{saved['media_id']}.mp4"
    assert uploaded_path.exists()
    assert saved["title"] == "Nike Campaign"
    assert saved["type"] == "video"
    assert saved["duration"] == 10
    assert saved["uploaded_by"] == "user-1"


@pytest.mark.asyncio
async def test_screen_service_assign_media_enforces_single_mode(monkeypatch):
    screen = {
        "screen_id": "SCR-001",
        "screen_name": "Mumbai Screen",
        "playlist": [],
        "status": "offline",
        "mode": "single",
        "playlist_limit": 5,
        "rotation_interval": 10,
        "current_media_index": 0,
        "audience": 0,
        "engagement": 0,
    }
    ads = [
        {
            "ad_id": "MED-1",
            "media_id": "MED-1",
            "title": "Nike",
            "type": "video",
            "file_url": "/media/nike.mp4",
            "url": "/media/nike.mp4",
            "duration": 10,
            "user_id": "user-1",
            "uploaded_by": "user-1",
        },
        {
            "ad_id": "MED-2",
            "media_id": "MED-2",
            "title": "Pepsi",
            "type": "image",
            "file_url": "/media/pepsi.png",
            "url": "/media/pepsi.png",
            "duration": 0,
            "user_id": "user-1",
            "uploaded_by": "user-1",
        },
    ]
    fake_db = FakeDB(screens=[screen], ads=ads)

    captured = {"broadcast": [], "send": []}

    async def fake_broadcast(event):
        captured["broadcast"].append(event)

    async def fake_send(screen_id, event):
        captured["send"].append(event)

    monkeypatch.setattr("app.screens.repository.get_db", lambda: fake_db)
    monkeypatch.setattr("app.ads.repository.get_db", lambda: fake_db)
    monkeypatch.setattr("app.screens.service.manager.broadcast_event", fake_broadcast)
    monkeypatch.setattr("app.screens.service.manager.send_to_screen", fake_send)

    data = ScreenAssignMediaRequest(
        screen_id="SCR-001",
        mode="single",
        playlist_limit=5,
        rotation_interval=10,
        playlist=["MED-1", "MED-2"],
    )

    updated = await ScreenService.assign_media(data)

    assert updated["playlist"] == ["MED-1"]
    assert updated["current_media_id"] == "MED-1"
    assert updated["current_media_index"] == 0
    assert captured["broadcast"][0]["event"] == "playback_changed"
    assert captured["broadcast"][0]["current_media_id"] == "MED-1"
    assert captured["send"][0]["event"] == "media_changed"
    assert captured["send"][0]["media_id"] == "MED-1"


@pytest.mark.asyncio
async def test_playback_engine_rotates_multi_mode(monkeypatch):
    screen = {
        "screen_id": "SCR-1",
        "mode": "multi",
        "playlist": ["MED-1", "MED-2"],
        "current_media_index": 0,
        "rotation_interval": 10,
        "status": "online",
    }
    mapping = {
        "screen_id": "SCR-1",
        "mode": "multi",
        "ad_ids": ["MED-1", "MED-2"]
    }
    ads = [
        {
            "ad_id": "MED-1",
            "media_id": "MED-1",
            "title": "Nike",
            "type": "video",
            "file_url": "/media/nike.mp4",
            "url": "/media/nike.mp4",
            "duration": 10,
            "user_id": "user-1",
            "uploaded_by": "user-1",
        },
        {
            "ad_id": "MED-2",
            "media_id": "MED-2",
            "title": "Pepsi",
            "type": "image",
            "file_url": "/media/pepsi.png",
            "url": "/media/pepsi.png",
            "duration": 0,
            "user_id": "user-1",
            "uploaded_by": "user-1",
        },
    ]
    fake_db = FakeDB(screens=[screen], ads=ads, screen_ad_mappings=[mapping])

    captured = {"broadcast": [], "send": []}

    async def fake_broadcast(event):
        captured["broadcast"].append(event)

    async def fake_send(screen_id, event):
        captured["send"].append(event)

    monkeypatch.setattr("app.screens.repository.get_db", lambda: fake_db)
    monkeypatch.setattr("app.ads.repository.get_db", lambda: fake_db)
    monkeypatch.setattr("app.websocket.manager.manager.broadcast_event", fake_broadcast)
    monkeypatch.setattr("app.websocket.manager.manager.send_to_screen", fake_send)

    engine = PlaybackEngine()
    engine.last_rotations["SCR-1"] = datetime.utcnow() - timedelta(seconds=20)

    await engine._process_screens()

    updated = fake_db["screens"].docs[0]
    assert updated["current_media_index"] == 1
    assert updated["current_media_id"] == "MED-2"
    assert captured["broadcast"][0]["event"] == "playback_changed"
    assert captured["broadcast"][0]["current_media_index"] == 1
    assert captured["send"][0]["event"] == "media_changed"
    assert captured["send"][0]["media_id"] == "MED-2"

