"""
Payment Routes — Razorpay subscription management.
Create subscriptions, verify payments, handle webhooks.
"""

import hmac
import hashlib
import json
from fastapi import APIRouter, Depends, HTTPException, Request, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone
import razorpay
import structlog

from app.core.database import get_db
from app.core.config import settings
from app.models.models import User, Subscription, PaymentLog, UserPlan
from app.models.schemas import (
    CreateSubscriptionRequest, SubscriptionResponse, VerifyPaymentRequest
)
from app.auth.jwt_handler import get_current_user

router = APIRouter()
logger = structlog.get_logger()


def get_razorpay_client():
    """Get Razorpay client instance."""
    return razorpay.Client(
        auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
    )


@router.post("/subscribe", response_model=SubscriptionResponse)
async def create_subscription(
    data: CreateSubscriptionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a Razorpay subscription for the Pro plan.
    Returns the subscription ID and Razorpay key for frontend checkout.
    """
    if current_user.plan == UserPlan.PRO:
        raise HTTPException(status_code=400, detail="You are already on the Pro plan")

    if not settings.RAZORPAY_KEY_ID:
        raise HTTPException(status_code=503, detail="Payment system not configured")

    try:
        client = get_razorpay_client()

        # Create Razorpay subscription
        subscription = client.subscription.create({
            "plan_id": settings.RAZORPAY_PLAN_ID_PRO,
            "customer_notify": 1,
            "quantity": 1,
            "total_count": 12,  # 12 months
            "notes": {
                "user_id": current_user.id,
                "user_email": current_user.email,
            },
        })

        # Save subscription record
        db_sub = Subscription(
            user_id=current_user.id,
            razorpay_subscription_id=subscription["id"],
            razorpay_plan_id=settings.RAZORPAY_PLAN_ID_PRO,
            status="created",
        )
        db.add(db_sub)
        await db.commit()

        logger.info("subscription_created", user_id=current_user.id, sub_id=subscription["id"])

        return SubscriptionResponse(
            subscription_id=subscription["id"],
            razorpay_key_id=settings.RAZORPAY_KEY_ID,
            plan_id=settings.RAZORPAY_PLAN_ID_PRO,
            amount=settings.PRO_PLAN_PRICE,
            currency="INR",
        )

    except razorpay.errors.BadRequestError as e:
        logger.error("razorpay_error", error=str(e))
        raise HTTPException(status_code=400, detail=f"Payment error: {str(e)}")
    except Exception as e:
        logger.error("subscription_create_error", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to create subscription")


@router.post("/verify")
async def verify_payment(
    data: VerifyPaymentRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Verify Razorpay payment signature after successful payment.
    Upgrades user to Pro plan on success.
    """
    if not settings.RAZORPAY_KEY_SECRET:
        raise HTTPException(status_code=503, detail="Payment system not configured")

    # Verify signature
    msg = f"{data.razorpay_payment_id}|{data.razorpay_subscription_id}"
    expected_sig = hmac.new(
        settings.RAZORPAY_KEY_SECRET.encode("utf-8"),
        msg.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(expected_sig, data.razorpay_signature):
        raise HTTPException(status_code=400, detail="Invalid payment signature")

    # Update subscription status
    result = await db.execute(
        select(Subscription).where(
            Subscription.razorpay_subscription_id == data.razorpay_subscription_id,
            Subscription.user_id == current_user.id,
        )
    )
    subscription = result.scalar_one_or_none()
    if subscription:
        subscription.status = "active"
        subscription.starts_at = datetime.now(timezone.utc)

    # Upgrade user to Pro
    current_user.plan = UserPlan.PRO

    # Log payment
    log = PaymentLog(
        user_id=current_user.id,
        subscription_id=data.razorpay_subscription_id,
        razorpay_payment_id=data.razorpay_payment_id,
        razorpay_signature=data.razorpay_signature,
        status="captured",
        event_type="payment.verified",
    )
    db.add(log)
    await db.commit()

    logger.info("payment_verified", user_id=current_user.id, payment_id=data.razorpay_payment_id)
    return {"message": "Payment verified. Your account has been upgraded to Pro!", "plan": "pro"}


@router.post("/webhook")
async def razorpay_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Razorpay webhook handler for subscription lifecycle events.
    Verify webhook signature before processing.
    """
    body = await request.body()
    signature = request.headers.get("X-Razorpay-Signature", "")

    # Verify webhook signature
    if settings.RAZORPAY_KEY_SECRET:
        expected = hmac.new(
            settings.RAZORPAY_KEY_SECRET.encode("utf-8"),
            body,
            hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(expected, signature):
            raise HTTPException(status_code=400, detail="Invalid webhook signature")

    try:
        payload = json.loads(body)
        event = payload.get("event", "")
        entity = payload.get("payload", {})

        logger.info("webhook_received", event=event)

        # Handle subscription cancelled / expired
        if event in ("subscription.cancelled", "subscription.expired"):
            sub_data = entity.get("subscription", {}).get("entity", {})
            sub_id = sub_data.get("id")
            if sub_id:
                result = await db.execute(
                    select(Subscription).where(Subscription.razorpay_subscription_id == sub_id)
                )
                sub = result.scalar_one_or_none()
                if sub:
                    sub.status = "cancelled" if event == "subscription.cancelled" else "expired"
                    # Downgrade user
                    user_result = await db.execute(select(User).where(User.id == sub.user_id))
                    user = user_result.scalar_one_or_none()
                    if user:
                        user.plan = UserPlan.FREE
                    await db.commit()
                    logger.info("subscription_cancelled", sub_id=sub_id)

        # Log all webhook events
        log = PaymentLog(
            event_type=event,
            payload=payload,
            status="webhook_received",
        )
        db.add(log)
        await db.commit()

    except Exception as e:
        logger.error("webhook_error", error=str(e))

    return {"status": "ok"}


@router.get("/status")
async def get_subscription_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current user's subscription status."""
    result = await db.execute(
        select(Subscription)
        .where(Subscription.user_id == current_user.id)
        .order_by(Subscription.created_at.desc())
    )
    sub = result.scalar_one_or_none()

    return {
        "plan": current_user.plan,
        "subscription": {
            "id": sub.razorpay_subscription_id if sub else None,
            "status": sub.status if sub else None,
            "starts_at": sub.starts_at if sub else None,
            "ends_at": sub.ends_at if sub else None,
        } if sub else None,
    }


@router.get("/plans")
async def get_plans():
    """Return available subscription plans."""
    return {
        "plans": [
            {
                "id": "free",
                "name": "Free",
                "price": 0,
                "currency": "INR",
                "features": [
                    "1 scan per day",
                    "Basic security report",
                    "PDF download",
                    "7-day history",
                ],
                "limits": {"scans_per_day": 1},
            },
            {
                "id": "pro",
                "name": settings.PRO_PLAN_NAME,
                "price": settings.PRO_PLAN_PRICE // 100,
                "currency": "INR",
                "price_display": f"₹{settings.PRO_PLAN_PRICE // 100}/month",
                "features": [
                    "Unlimited scans",
                    "AI-powered detailed reports",
                    "PDF download",
                    "Full scan history",
                    "Priority support",
                    "Email reports",
                ],
                "limits": {"scans_per_day": "unlimited"},
                "razorpay_plan_id": settings.RAZORPAY_PLAN_ID_PRO,
            },
        ]
    }
