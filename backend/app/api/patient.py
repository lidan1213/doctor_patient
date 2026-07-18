import logging
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.middleware.identity_router import get_request_context, RequestContext
from app.models.patient import PatientProfile
from app.models.care_plan import CarePlan
from app.schemas.patient import (
    PatientProfileResponse,
    PatientProfileUpdate,
    CarePlanItem,
    CarePlanResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/patient", tags=["patient"])


@router.get("/profile", response_model=PatientProfileResponse)
async def get_profile(
    ctx: RequestContext = Depends(get_request_context),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(PatientProfile).where(PatientProfile.user_id == ctx.user_id)
    )
    profile = result.scalar_one_or_none()

    if profile is None:
        return PatientProfileResponse(user_id=ctx.user_id)

    return PatientProfileResponse(
        user_id=profile.user_id,
        gender=profile.gender,
        birthday=profile.birthday.isoformat() if profile.birthday else None,
        blood_type=profile.blood_type,
        allergies=profile.allergies,
        medical_history=profile.medical_history,
        personalization_config=profile.personalization_config,
    )


@router.put("/profile", response_model=PatientProfileResponse)
async def update_profile(
    update: PatientProfileUpdate,
    ctx: RequestContext = Depends(get_request_context),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(PatientProfile).where(PatientProfile.user_id == ctx.user_id)
    )
    profile = result.scalar_one_or_none()

    if profile is None:
        profile = PatientProfile(user_id=ctx.user_id)
        db.add(profile)

    if update.gender is not None:
        profile.gender = update.gender
    if update.birthday is not None:
        try:
            profile.birthday = date.fromisoformat(update.birthday)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid birthday format, use YYYY-MM-DD",
            )
    if update.blood_type is not None:
        profile.blood_type = update.blood_type
    if update.allergies is not None:
        profile.allergies = update.allergies
    if update.medical_history is not None:
        profile.medical_history = update.medical_history
    if update.personalization_config is not None:
        profile.personalization_config = update.personalization_config

    await db.commit()
    await db.refresh(profile)

    return PatientProfileResponse(
        user_id=profile.user_id,
        gender=profile.gender,
        birthday=profile.birthday.isoformat() if profile.birthday else None,
        blood_type=profile.blood_type,
        allergies=profile.allergies,
        medical_history=profile.medical_history,
        personalization_config=profile.personalization_config,
    )


@router.get("/care-plan", response_model=CarePlanResponse)
async def get_care_plan(
    ctx: RequestContext = Depends(get_request_context),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(CarePlan)
        .where(
            CarePlan.user_id == ctx.user_id,
            CarePlan.status == "active",
        )
        .order_by(CarePlan.created_at.desc())
    )
    plans = result.scalars().all()

    return CarePlanResponse(
        plans=[
            CarePlanItem(
                id=p.id,
                title=p.title,
                description=p.description,
                medication_schedule=p.medication_schedule,
                follow_up_date=p.follow_up_date,
                status=p.status,
            )
            for p in plans
        ],
        total=len(plans),
    )
