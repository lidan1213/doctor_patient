import json
import logging
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.middleware.identity_router import get_request_context, RequestContext
from app.db.session import get_db
from app.models.report import MedicalReport
from app.schemas.report import ReportUploadResponse, ReportInterpretResponse, ReportSection
from app.core.multimodal.ocr import extract_text, interpret_report

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/report", tags=["report"])

ALLOWED_MIMES = {
    "image/png", "image/jpeg", "image/jpg", "image/gif",
    "application/pdf",
}

MAX_FILE_SIZE = settings.max_upload_size_mb * 1024 * 1024
# 本地存储目录（MinIO 不可用时的 fallback）
LOCAL_STORAGE = Path(settings.minio_endpoint.replace(":", "_") if "minio" not in settings.minio_endpoint else "./data/reports")
LOCAL_STORAGE.mkdir(parents=True, exist_ok=True)


def _save_locally(file_bytes: bytes, filename: str) -> str:
    """保存文件到本地磁盘，返回相对路径。"""
    date_prefix = datetime.now(timezone.utc).strftime("%Y/%m/%d")
    save_dir = LOCAL_STORAGE / date_prefix
    save_dir.mkdir(parents=True, exist_ok=True)
    object_path = f"{date_prefix}/{uuid.uuid4().hex}_{filename}"
    dest = LOCAL_STORAGE / object_path
    dest.write_bytes(file_bytes)
    logger.info(f"Saved locally: {dest} ({len(file_bytes)} bytes)")
    return object_path


def _read_locally(object_path: str) -> bytes:
    """从本地磁盘读取文件。"""
    full_path = LOCAL_STORAGE / object_path
    if not full_path.exists():
        raise FileNotFoundError(f"文件不存在: {object_path}")
    return full_path.read_bytes()


@router.post("/upload", response_model=ReportUploadResponse)
async def upload(
    file: UploadFile = File(...),
    ctx: RequestContext = Depends(get_request_context),
    db: AsyncSession = Depends(get_db),
):
    """上传医学报告（图片或PDF），返回报告ID并关联到当前患者。"""
    if file.content_type not in ALLOWED_MIMES:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件格式: {file.content_type}。支持: {', '.join(sorted(ALLOWED_MIMES))}",
        )

    file_bytes = await file.read()
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail=f"文件超过 {settings.max_upload_size_mb}MB 限制")

    # 保存文件（本地 fallback）
    object_path = _save_locally(file_bytes, file.filename or "report.bin")

    # 写入数据库，关联到当前用户
    report = MedicalReport(
        user_id=ctx.user_id,
        report_path=object_path,
        filename=file.filename or "unknown",
        file_type=file.content_type or "application/octet-stream",
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)

    return ReportUploadResponse(
        report_id=str(report.id),
        filename=file.filename or "unknown",
        status="uploaded",
        uploaded_at=report.created_at.isoformat() if report.created_at else datetime.now(timezone.utc).isoformat(),
    )


@router.post("/interpret/{report_id}", response_model=ReportInterpretResponse)
async def interpret(
    report_id: str,
    ctx: RequestContext = Depends(get_request_context),
    db: AsyncSession = Depends(get_db),
):
    """解读指定报告：从存储取出 → OCR 提取文字 → AI 结构化解读。"""
    # 查找报告记录
    try:
        report_id_int = int(report_id)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"无效的报告ID: {report_id}")
    result = await db.execute(select(MedicalReport).where(MedicalReport.id == report_id_int))
    report = result.scalar_one_or_none()
    if report is None:
        raise HTTPException(status_code=404, detail=f"报告不存在: {report_id}")

    # 读取文件
    try:
        file_bytes = _read_locally(report.report_path)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e

    # OCR 提取文字
    try:
        raw_text = await extract_text(file_bytes)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"OCR 识别失败: {e}") from e

    # AI 解读
    try:
        result_data = await interpret_report(raw_text)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"报告解读失败: {e}") from e

    # 保存 OCR 结果到数据库
    report.ocr_text = raw_text
    report.interpretation = json.dumps(result_data, ensure_ascii=False)
    await db.commit()

    sections = [
        ReportSection(title=s.get("title", ""), content=s.get("content", ""))
        for s in result_data.get("sections", [])
    ]

    return ReportInterpretResponse(
        report_id=report_id,
        summary=result_data.get("summary", ""),
        sections=sections,
    )
