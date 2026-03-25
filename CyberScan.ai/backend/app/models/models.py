"""
Database Models — User, ScanResult, Payment, Subscription
"""

from sqlalchemy import (
    Column, String, Integer, Float, Boolean, Text,
    DateTime, ForeignKey, JSON
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from app.core.database import Base


def generate_uuid():
    return str(uuid.uuid4())


class UserPlan(str, enum.Enum):
    FREE = "free"
    PRO = "pro"


class ScanStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class SeverityLevel(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# ── User ─────────────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=generate_uuid)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)

    plan = Column(String, default=UserPlan.FREE, nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)

    # Scan tracking
    scans_today = Column(Integer, default=0)
    last_scan_date = Column(DateTime(timezone=True), nullable=True)
    total_scans = Column(Integer, default=0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    scans = relationship("ScanResult", back_populates="user", cascade="all, delete-orphan")
    subscriptions = relationship("Subscription", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.email} [{self.plan}]>"


# ── ScanResult ───────────────────────────────────────────────────────────────

class ScanResult(Base):
    __tablename__ = "scan_results"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    target_url = Column(String, nullable=False)
    status = Column(String, default=ScanStatus.PENDING)

    # Scores & Summary
    risk_score = Column(Float, nullable=True)         # 0–100
    overall_severity = Column(String, nullable=True)
    summary = Column(Text, nullable=True)              # AI-generated summary

    # Raw findings stored as JSON arrays
    raw_findings = Column(JSON, default=list)          # [{check, status, detail}]
    vulnerabilities = Column(JSON, default=list)       # [{name, severity, description, fix}]

    # AI report
    ai_report = Column(Text, nullable=True)            # Full markdown report

    # Metadata
    ssl_valid = Column(Boolean, nullable=True)
    ssl_expiry_days = Column(Integer, nullable=True)
    server_header = Column(String, nullable=True)
    response_time_ms = Column(Integer, nullable=True)

    # Counts by severity
    critical_count = Column(Integer, default=0)
    high_count = Column(Integer, default=0)
    medium_count = Column(Integer, default=0)
    low_count = Column(Integer, default=0)

    error_message = Column(Text, nullable=True)
    scan_duration_ms = Column(Integer, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", back_populates="scans")

    def __repr__(self):
        return f"<ScanResult {self.target_url} score={self.risk_score}>"


# ── Subscription / Payment ────────────────────────────────────────────────────

class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    razorpay_subscription_id = Column(String, unique=True, nullable=True)
    razorpay_plan_id = Column(String, nullable=True)
    razorpay_customer_id = Column(String, nullable=True)

    status = Column(String, default="created")  # created, active, cancelled, expired
    plan = Column(String, default=UserPlan.PRO)

    starts_at = Column(DateTime(timezone=True), nullable=True)
    ends_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="subscriptions")


class PaymentLog(Base):
    __tablename__ = "payment_logs"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    subscription_id = Column(String, nullable=True)

    razorpay_payment_id = Column(String, nullable=True)
    razorpay_order_id = Column(String, nullable=True)
    razorpay_signature = Column(String, nullable=True)

    amount = Column(Integer, nullable=True)          # In paise (INR smallest unit)
    currency = Column(String, default="INR")
    status = Column(String, default="pending")       # pending, captured, failed

    event_type = Column(String, nullable=True)       # webhook event name
    payload = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())


# ── AttackSurfaceResult ───────────────────────────────────────────────────────

class AttackSurfaceResult(Base):
    __tablename__ = "attack_surface_results"

    id         = Column(String, primary_key=True, default=generate_uuid)
    user_id    = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    domain     = Column(String, nullable=False)
    url        = Column(String, nullable=False)
    result     = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", backref="attack_surface_results")

class ScheduledScan(Base):
    __tablename__ = "scheduled_scans"

    id         = Column(String, primary_key=True, default=generate_uuid)
    user_id    = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    url        = Column(String, nullable=False)
    frequency  = Column(String, nullable=False)   # daily | weekly | monthly
    day_of_week = Column(String, nullable=True)   # mon-sun (weekly only)
    hour       = Column(Integer, nullable=False, default=8)  # 0-23 UTC

    email_notify = Column(Boolean, default=True)
    is_active    = Column(Boolean, default=True)

    last_run_at  = Column(DateTime(timezone=True), nullable=True)
    next_run_at  = Column(DateTime(timezone=True), nullable=True)
    run_count    = Column(Integer, default=0)

    created_at   = Column(DateTime(timezone=True), server_default=func.now())
    updated_at   = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", backref="scheduled_scans")
