import pytest


class TestPatientRecord:
    async def test_patient_record_requires_auth(self, async_client):
        resp = await async_client.get("/api/doctor/patient/1")
        assert resp.status_code == 401

    async def test_patient_role_cannot_access(self, async_client, auth_token):
        resp = await async_client.get(
            "/api/doctor/patient/1",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 403
        assert "Only doctors" in resp.json()["detail"]

    async def test_patient_not_found(self, async_client):
        """Register as doctor, then query nonexistent patient."""
        await async_client.post("/api/auth/register", json={
            "username": "testdoctor", "password": "testpass", "name": "Doctor", "role": "doctor",
        })
        login_resp = await async_client.post("/api/auth/login", json={
            "username": "testdoctor", "password": "testpass",
        })
        token = login_resp.json()["token"]

        resp = await async_client.get(
            "/api/doctor/patient/9999",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 404

    async def test_patient_record_returns_mock_data(self, async_client):
        """Register as doctor, register a patient, query that patient."""
        # Register a patient first
        await async_client.post("/api/auth/register", json={
            "username": "somepatient", "password": "testpass", "name": "张三", "role": "patient",
        })
        patient_resp = await async_client.post("/api/auth/login", json={
            "username": "somepatient", "password": "testpass",
        })
        patient_id = patient_resp.json()["user"]["id"]

        # Register and login as doctor
        await async_client.post("/api/auth/register", json={
            "username": "dr_wang", "password": "testpass", "name": "王医生", "role": "doctor",
        })
        doctor_resp = await async_client.post("/api/auth/login", json={
            "username": "dr_wang", "password": "testpass",
        })
        doctor_token = doctor_resp.json()["token"]

        resp = await async_client.get(
            f"/api/doctor/patient/{patient_id}",
            headers={"Authorization": f"Bearer {doctor_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["patient_id"] == patient_id
        assert data["patient_name"] == "张三"
        assert isinstance(data["cases"], list)
        assert isinstance(data["visits"], list)
        assert isinstance(data["prescriptions"], list)
