from datetime import datetime

from pydantic import BaseModel


class ReportInfo(BaseModel):
    id: int
    filename: str
    file_type: str
    ocr_text: str | None = None
    interpretation: str | None = None
    created_at: str | None = None


class PatientRecordResponse(BaseModel):
    patient_id: int
    patient_name: str | None = None
    patient_role: str | None = None
    cases: list[dict] = []
    visits: list[dict] = []
    prescriptions: list[dict] = []
    reports: list[ReportInfo] = []
