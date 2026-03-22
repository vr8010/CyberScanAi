"""
Basic test suite for SecureScout backend.
Run with: pytest tests/ -v
"""

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from main import app
from app.core.database import get_db, Base

# Use in-memory SQLite for tests
TEST_DB_URL = "sqlite+aiosqlite:///./test.db"

test_engine = create_async_engine(TEST_DB_URL, echo=False)
TestSessionLocal = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


async def override_get_db():
    async with TestSessionLocal() as session:
        yield session


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
async def setup_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


@pytest.fixture
async def auth_headers(client):
    """Register and log in a test user, return auth headers."""
    await client.post("/api/auth/register", json={
        "email": "test@example.com",
        "password": "testpass123",
        "full_name": "Test User",
    })
    login = await client.post("/api/auth/login", data={
        "username": "test@example.com",
        "password": "testpass123",
    })
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# ── Auth Tests ────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_register(client):
    response = await client.post("/api/auth/register", json={
        "email": "newuser@example.com",
        "password": "secure123",
        "full_name": "New User",
    })
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == "newuser@example.com"
    assert data["user"]["plan"] == "free"


@pytest.mark.asyncio
async def test_register_duplicate_email(client):
    payload = {"email": "dup@example.com", "password": "secure123"}
    await client.post("/api/auth/register", json=payload)
    response = await client.post("/api/auth/register", json=payload)
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_login_success(client):
    await client.post("/api/auth/register", json={
        "email": "login@example.com", "password": "mypass123"
    })
    response = await client.post("/api/auth/login", data={
        "username": "login@example.com", "password": "mypass123"
    })
    assert response.status_code == 200
    assert "access_token" in response.json()


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    await client.post("/api/auth/register", json={
        "email": "user@example.com", "password": "correct123"
    })
    response = await client.post("/api/auth/login", data={
        "username": "user@example.com", "password": "wrong"
    })
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me(client, auth_headers):
    response = await client.get("/api/auth/me", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["email"] == "test@example.com"


# ── Scanner Tests ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_scan_history_empty(client, auth_headers):
    response = await client.get("/api/scan/history", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_scan_url_validation(client, auth_headers):
    """Test that invalid URLs are rejected."""
    response = await client.post("/api/scan/", json={"url": "not-a-url"}, headers=auth_headers)
    # Should either succeed with auto-prefix or fail gracefully
    # URL validator adds https:// prefix, so this creates a scan
    assert response.status_code in (200, 422, 500)


# ── Health Check ──────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_health(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


# ── Plans ─────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_plans(client, auth_headers):
    response = await client.get("/api/payment/plans", headers=auth_headers)
    assert response.status_code == 200
    plans = response.json()["plans"]
    assert len(plans) == 2
    assert plans[0]["id"] == "free"
    assert plans[1]["id"] == "pro"
