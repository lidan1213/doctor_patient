from datetime import datetime

from sqlalchemy import String, DateTime, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base


class MedicalReport(Base):
    """患者上传的医学报告（图片/PDF）。"""

    __tablename__ = "medical_reports"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    report_path: Mapped[str] = mapped_column(String(256), nullable=False, comment="MinIO 存储路径")
    filename: Mapped[str] = mapped_column(String(128), nullable=False)
    file_type: Mapped[str] = mapped_column(String(32), nullable=False, comment="MIME 类型")
    ocr_text: Mapped[str | None] = mapped_column(Text, nullable=True, comment="OCR 提取的原文")
    interpretation: Mapped[str | None] = mapped_column(Text, nullable=True, comment="AI 解读结果（JSON）")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
