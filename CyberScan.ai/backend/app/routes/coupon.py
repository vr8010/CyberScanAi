"""
Coupon Routes — Redeem a coupon code to upgrade to Pro.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
import structlog

from app.core.database import get_db
from app.models.models import User, UserPlan
from app.auth.jwt_handler import get_current_user

router = APIRouter()
logger = structlog.get_logger()

# Valid coupon codes → plan they unlock
# Add/remove codes here as needed
VALID_COUPONS: dict[str, str] = {
    "PROLIFE":    "pro",
    "SECUREPRO":  "pro",
    "LAUNCH2024": "pro",
    "FREEPRO":    "pro",
}


class CouponRequest(BaseModel):
    code: str


@router.post("/redeem")
async def redeem_coupon(
    data: CouponRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    code = data.code.strip().upper()

    if code not in VALID_COUPONS:
        raise HTTPException(status_code=400, detail="Invalid or expired coupon code.")

    if current_user.plan == UserPlan.PRO:
        raise HTTPException(status_code=400, detail="You are already on the Pro plan.")

    current_user.plan = UserPlan.PRO
    await db.commit()

    logger.info("coupon_redeemed", user_id=current_user.id, code=code)
    return {"message": "Coupon applied! Your account has been upgraded to Pro.", "plan": "pro"}
