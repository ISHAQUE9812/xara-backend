from datetime import datetime, timezone
from types import SimpleNamespace

from fastapi import FastAPI, HTTPException, status
from fastapi.testclient import TestClient

from app.routes import auth
from app.auth import role_middleware
from app.auth.password_handler import hash_password, verify_password
from app.auth.jwt_handler import create_access_token, decode_token


class FakeUserCollection:
    def __init__(self, initial_users=None):
        self.initial_users = initial_users or {}
        self.inserted = []

    async def find_one(self, query):
        if "email" in query:
            email = query["email"]
            user = self.initial_users.get(email)
            if user:
                return dict(user)
            return None
        if "$or" in query:
            value = query["$or"][0]["email"]
            user = self.initial_users.get(value)
            if user:
                return dict(user)
            return None
        return None

    async def insert_one(self, document):
        self.inserted.append(dict(document))
        email = document["email"]
        stored = dict(document)
        stored["_id"] = "user-id-123"
        self.initial_users[email] = stored
        return SimpleNamespace(inserted_id="user-id-123")


class FakeDB:
    def __init__(self, users):
        self._collections = {"users": FakeUserCollection(users)}

    def __getitem__(self, item):
        return self._collections[item]


def build_app(fake_db):
    app = FastAPI()
    app.include_router(auth.router, prefix="/auth")
    app.dependency_overrides[auth.get_db] = lambda: fake_db
    return app


def test_password_handler_hashes_and_verifies():
    hashed = hash_password("secret123")
    assert hashed != "secret123"
    assert verify_password("secret123", hashed)
    assert not verify_password("wrongpassword", hashed)


def test_jwt_handler_create_and_decode_token():
    token = create_access_token(user_id="abc123", role="admin", email="admin@example.com", name="Admin User")
    payload = decode_token(token)
    assert payload["sub"] == "abc123"
    assert payload["role"] == "admin"
    assert payload["email"] == "admin@example.com"


def test_signup_creates_user_and_returns_message():
    fake_db = FakeDB(users={})
    app = build_app(fake_db)
    client = TestClient(app)

    response = client.post(
        "/auth/signup",
        json={
            "name": "Ishaque",
            "email": "ishaque@gmail.com",
            "password": "123456",
            "role": "admin",
        },
    )

    assert response.status_code == 201
    assert response.json() == {"message": "User created successfully"}
    assert len(fake_db["users"].inserted) == 1


def test_login_returns_token_and_user_payload():
    hashed = hash_password("123456")
    fake_db = FakeDB(
        users={
            "ishaque@gmail.com": {
                "_id": "user-id-123",
                "name": "Ishaque",
                "email": "ishaque@gmail.com",
                "hashed_password": hashed,
                "role": "admin",
                "is_active": True,
                "created_at": datetime.now(timezone.utc),
            }
        }
    )
    app = build_app(fake_db)
    client = TestClient(app)

    response = client.post("/auth/login", json={"email": "ishaque@gmail.com", "password": "123456"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["token"]
    assert payload["user"] == {
        "id": "user-id-123",
        "name": "Ishaque",
        "email": "ishaque@gmail.com",
        "role": "admin",
    }


def test_admin_dashboard_rejects_user_role():
    fake_db = FakeDB(users={})
    app = build_app(fake_db)

    async def fake_current_user():
        return {
            "id": "user-id-123",
            "name": "Ishaque",
            "email": "ishaque@gmail.com",
            "role": "user",
        }

    app.dependency_overrides[role_middleware.get_current_user] = fake_current_user
    client = TestClient(app)

    response = client.get("/auth/admin/dashboard")

    assert response.status_code == 403
    assert response.json()["detail"] == "Admin access required"


def test_user_dashboard_allows_logged_in_user():
    fake_db = FakeDB(users={})
    app = build_app(fake_db)

    async def fake_current_user():
        return {
            "id": "user-id-123",
            "name": "Ishaque",
            "email": "ishaque@gmail.com",
            "role": "user",
        }

    app.dependency_overrides[role_middleware.get_current_user] = fake_current_user
    client = TestClient(app)

    response = client.get("/auth/user/dashboard")

    assert response.status_code == 200
    assert response.json()["user"]["role"] == "user"
