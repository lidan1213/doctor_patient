import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.middleware.identity_router import get_request_context, RequestContext
from app.models.user import User, UserRole
from app.models.conversation import Conversation
from app.models.report import MedicalReport
from app.core.knowledge import search as kb_search

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin", tags=["admin"])


async def _require_admin(ctx: RequestContext):
    if ctx.role != UserRole.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅管理员可访问")


# ── 用户管理 ──

@router.get("/users")
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    ctx: RequestContext = Depends(get_request_context),
    db: AsyncSession = Depends(get_db),
):
    await _require_admin(ctx)
    offset = (page - 1) * page_size
    total = await db.scalar(select(func.count(User.id)))
    result = await db.execute(
        select(User).order_by(User.created_at.desc()).offset(offset).limit(page_size)
    )
    users = result.scalars().all()
    return {
        "total": total or 0,
        "page": page,
        "page_size": page_size,
        "users": [
            {
                "id": u.id,
                "username": u.username,
                "role": u.role.value,
                "name": u.name,
                "created_at": u.created_at.isoformat() if u.created_at else None,
                "is_active": getattr(u, "is_active", True),
            }
            for u in users
        ],
    }


# ── 系统统计 ──

@router.get("/stats")
async def get_stats(
    ctx: RequestContext = Depends(get_request_context),
    db: AsyncSession = Depends(get_db),
):
    await _require_admin(ctx)

    total_users = await db.scalar(select(func.count(User.id)))
    by_role = await db.execute(
        select(User.role, func.count(User.id)).group_by(User.role)
    )
    role_counts = {row[0].value: row[1] for row in by_role}

    total_conversations = await db.scalar(select(func.count(Conversation.id)))
    total_reports = await db.scalar(select(func.count(MedicalReport.id)))

    return {
        "total_users": total_users or 0,
        "users_by_role": role_counts,
        "total_conversations": total_conversations or 0,
        "total_reports": total_reports or 0,
    }


# ── 知识库管理 ──

@router.get("/knowledge/search")
async def search_kb(
    q: str = Query(..., min_length=1),
    collection: str = Query("kb_professional"),
    top_k: int = Query(10, ge=1, le=50),
    ctx: RequestContext = Depends(get_request_context),
):
    await _require_admin(ctx)
    results = kb_search(q, collection, top_k)
    return {
        "query": q,
        "collection": collection,
        "total": len(results),
        "results": [
            {
                "id": r["id"],
                "title": r["metadata"].get("title", ""),
                "content_preview": r["content"][:200],
                "content_length": len(r["content"]),
                "type": r["metadata"].get("type", ""),
            }
            for r in results
        ],
    }
