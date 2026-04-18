import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestRegister:
    async def test_register_success(self, async_client: AsyncClient):
        resp = await async_client.post("/api/v1/auth/register", json={
            "email": "newuser@example.com",
            "password": "strongpassword123",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    async def test_register_duplicate_email(self, async_client: AsyncClient, test_user):
        resp = await async_client.post("/api/v1/auth/register", json={
            "email": "test@example.com",  # same as test_user
            "password": "another_password",
        })
        assert resp.status_code == 400
        assert "already exists" in resp.json()["detail"]

    async def test_register_invalid_email(self, async_client: AsyncClient):
        resp = await async_client.post("/api/v1/auth/register", json={
            "email": "not-an-email",
            "password": "password123",
        })
        assert resp.status_code == 422  # validation error

    async def test_register_missing_password(self, async_client: AsyncClient):
        resp = await async_client.post("/api/v1/auth/register", json={
            "email": "valid@example.com",
        })
        assert resp.status_code == 422


@pytest.mark.asyncio
class TestLogin:
    async def test_login_success(self, async_client: AsyncClient, test_user):
        resp = await async_client.post(
            "/api/v1/auth/login",
            data={"username": "test@example.com", "password": "testpassword123"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    async def test_login_wrong_password(self, async_client: AsyncClient, test_user):
        resp = await async_client.post(
            "/api/v1/auth/login",
            data={"username": "test@example.com", "password": "wrong_password"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert resp.status_code == 400
        assert "Incorrect" in resp.json()["detail"]

    async def test_login_nonexistent_user(self, async_client: AsyncClient):
        resp = await async_client.post(
            "/api/v1/auth/login",
            data={"username": "nobody@example.com", "password": "password"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert resp.status_code == 400

    async def test_login_missing_fields(self, async_client: AsyncClient):
        resp = await async_client.post(
            "/api/v1/auth/login",
            data={},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert resp.status_code == 422


@pytest.mark.asyncio
class TestMe:
    async def test_me_authenticated(self, async_client: AsyncClient, test_user):
        token = test_user["token"]
        resp = await async_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == "test@example.com"
        assert data["is_active"] is True

    async def test_me_no_token(self, async_client: AsyncClient):
        resp = await async_client.get("/api/v1/auth/me")
        assert resp.status_code == 401

    async def test_me_invalid_token(self, async_client: AsyncClient):
        resp = await async_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid.token.here"},
        )
        assert resp.status_code == 401

    async def test_me_expired_token(self, async_client: AsyncClient):
        from datetime import timedelta
        from app.core.security import create_access_token

        expired = create_access_token("fake-id", expires_delta=timedelta(seconds=-10))
        resp = await async_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {expired}"},
        )
        assert resp.status_code == 401
