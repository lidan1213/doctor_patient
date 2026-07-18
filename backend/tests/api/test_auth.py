import pytest


class TestRegister:
    async def test_register_success(self, async_client):
        resp = await async_client.post("/api/auth/register", json={
            "username": "alice", "password": "pass123", "name": "Alice", "role": "patient",
        })
        assert resp.status_code == 201
        assert resp.json()["message"] == "Registration successful"

    async def test_register_duplicate_username(self, async_client):
        await async_client.post("/api/auth/register", json={
            "username": "bob", "password": "pass123", "name": "Bob", "role": "patient",
        })
        resp = await async_client.post("/api/auth/register", json={
            "username": "bob", "password": "pass456", "name": "Bob2", "role": "patient",
        })
        assert resp.status_code == 409

    async def test_register_doctor_role(self, async_client):
        resp = await async_client.post("/api/auth/register", json={
            "username": "drdave", "password": "pass123", "name": "Dr. Dave", "role": "doctor",
        })
        assert resp.status_code == 201


class TestLogin:
    async def test_login_success(self, async_client):
        await async_client.post("/api/auth/register", json={
            "username": "charlie", "password": "pass123", "name": "Charlie",
        })
        resp = await async_client.post("/api/auth/login", json={
            "username": "charlie", "password": "pass123",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "token" in data
        assert data["user"]["username"] == "charlie"
        assert data["user"]["role"] == "patient"

    async def test_login_wrong_password(self, async_client):
        await async_client.post("/api/auth/register", json={
            "username": "diana", "password": "pass123", "name": "Diana",
        })
        resp = await async_client.post("/api/auth/login", json={
            "username": "diana", "password": "wrongpass",
        })
        assert resp.status_code == 401

    async def test_login_nonexistent_user(self, async_client):
        resp = await async_client.post("/api/auth/login", json={
            "username": "nobody", "password": "pass123",
        })
        assert resp.status_code == 401


class TestMe:
    async def test_me_authenticated(self, async_client, auth_token):
        resp = await async_client.get("/api/auth/me", headers={
            "Authorization": f"Bearer {auth_token}",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["username"] == "testuser"

    async def test_me_no_token(self, async_client):
        resp = await async_client.get("/api/auth/me")
        assert resp.status_code == 401
