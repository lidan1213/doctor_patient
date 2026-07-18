import pytest
from pydantic import ValidationError

from app.schemas.auth import LoginRequest, RegisterRequest
from app.schemas.chat import ChatRequest
from app.schemas.search import SearchRequest


class TestLoginRequest:
    def test_valid(self):
        req = LoginRequest(username="test", password="secret")
        assert req.username == "test"

    def test_missing_username(self):
        with pytest.raises(ValidationError):
            LoginRequest(password="secret")

    def test_missing_password(self):
        with pytest.raises(ValidationError):
            LoginRequest(username="test")


class TestRegisterRequest:
    def test_default_role_is_patient(self):
        req = RegisterRequest(username="test", password="secret", name="Test User")
        assert req.role == "patient"

    def test_explicit_role(self):
        req = RegisterRequest(username="doc", password="s", name="Doctor", role="doctor")
        assert req.role == "doctor"

    def test_missing_name(self):
        with pytest.raises(ValidationError):
            RegisterRequest(username="test", password="secret")


class TestChatRequest:
    def test_default_session_id(self):
        req = ChatRequest(message="hello")
        assert req.session_id == "default"

    def test_custom_session_id(self):
        req = ChatRequest(message="hello", session_id="sess-123")
        assert req.session_id == "sess-123"


class TestSearchRequest:
    def test_filters_is_optional(self):
        req = SearchRequest(query="test")
        assert req.filters is None

    def test_with_filters(self):
        req = SearchRequest(query="test", filters={"type": "guideline"})
        assert req.filters == {"type": "guideline"}


from app.schemas.chat import ChatHistoryItem, ChatHistoryResponse, ChatDetailMessage, ChatDetailResponse
from app.schemas.patient import PatientProfileResponse, PatientProfileUpdate, CarePlanItem, CarePlanResponse
from app.schemas.doctor import PatientRecordResponse


class TestChatHistoryItem:
    def test_valid(self):
        item = ChatHistoryItem(session_id="s1", first_message="hello", message_count=5, last_message_at="2025-01-01T00:00:00")
        assert item.session_id == "s1"
        assert item.message_count == 5

    def test_defaults(self):
        item = ChatHistoryItem(session_id="s1", first_message="", message_count=0, last_message_at="")
        assert item.message_count == 0


class TestChatHistoryResponse:
    def test_empty(self):
        resp = ChatHistoryResponse(items=[], total=0)
        assert resp.page == 1
        assert resp.items == []


class TestPatientProfileResponse:
    def test_minimal(self):
        resp = PatientProfileResponse(user_id=1)
        assert resp.user_id == 1
        assert resp.gender is None

    def test_full(self):
        resp = PatientProfileResponse(
            user_id=1, gender="male", birthday="1990-01-01", blood_type="A",
            allergies="penicillin", medical_history={"asthma": True},
        )
        assert resp.blood_type == "A"


class TestPatientProfileUpdate:
    def test_all_fields_optional(self):
        update = PatientProfileUpdate()
        assert update.gender is None

    def test_partial_update(self):
        update = PatientProfileUpdate(gender="female")
        assert update.gender == "female"
        assert update.blood_type is None


class TestPatientRecordResponse:
    def test_empty(self):
        resp = PatientRecordResponse(patient_id=1)
        assert resp.patient_id == 1
        assert resp.cases == []

    def test_full(self):
        resp = PatientRecordResponse(
            patient_id=1, patient_name="张三", patient_role="patient",
            cases=[{"case_id": "C001"}], visits=[{"visit_id": "V001"}], prescriptions=[{"drug": "aspirin"}],
        )
        assert resp.patient_name == "张三"
        assert len(resp.cases) == 1
