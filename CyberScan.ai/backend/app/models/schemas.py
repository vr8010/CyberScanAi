"""
Pydantic Schemas — Request/Response models for all API endpoints.
"""

from pydantic import BaseModel, EmailStr, HttpUrl, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# ── Enums ─────────────────────────────────────────────────────────────────────

class UserPlanSchema(str, Enum):
    FREE = "free"
    PRO = "pro"


class ScanStatusSchema(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class SeveritySchema(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# ── Auth ──────────────────────────────────────────────────────────────────────

class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    full_name: Optional[str] = Field(None, max_length=100)

    @validator("password")
    def password_strength(cls, v):
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserResponse"


class TokenData(BaseModel):
    user_id: Optional[str] = None


# ── User ──────────────────────────────────────────────────────────────────────

class UserResponse(BaseModel):
    id: str
    email: str
    full_name: Optional[str]
    plan: UserPlanSchema
    is_verified: bool
    is_admin: bool = False
    total_scans: int
    scans_today: int
    created_at: datetime

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(None, max_length=100)


# ── Scan ──────────────────────────────────────────────────────────────────────

class ScanRequest(BaseModel):
    url: str = Field(..., description="Target website URL to scan")

    @validator("url")
    def validate_url(cls, v):
        v = v.strip()
        if not v.startswith(("http://", "https://")):
            v = "https://" + v
        # Basic domain validation
        from urllib.parse import urlparse
        parsed = urlparse(v)
        if not parsed.netloc:
            raise ValueError("Invalid URL provided")
        return v


class Vulnerability(BaseModel):
    name: str
    severity: SeveritySchema
    description: str
    recommendation: str
    references: Optional[List[str]] = []


class RawFinding(BaseModel):
    check: str
    status: str   # "pass" | "fail" | "warning"
    detail: str


class ScanResultResponse(BaseModel):
    id: str
    target_url: str
    status: ScanStatusSchema
    risk_score: Optional[float]
    overall_severity: Optional[SeveritySchema]
    summary: Optional[str]
    vulnerabilities: Optional[List[Dict[str, Any]]] = []
    raw_findings: Optional[List[Dict[str, Any]]] = []
    ai_report: Optional[str]
    ssl_valid: Optional[bool]
    ssl_expiry_days: Optional[int]
    server_header: Optional[str]
    response_time_ms: Optional[int]
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    error_message: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class ScanHistoryItem(BaseModel):
    id: str
    target_url: str
    status: ScanStatusSchema
    risk_score: Optional[float]
    overall_severity: Optional[SeveritySchema]
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    created_at: datetime

    class Config:
        from_attributes = True


# ── Payment ───────────────────────────────────────────────────────────────────

class CreateSubscriptionRequest(BaseModel):
    plan: str = "pro"


class SubscriptionResponse(BaseModel):
    subscription_id: str
    razorpay_key_id: str
    plan_id: str
    amount: int
    currency: str = "INR"


class VerifyPaymentRequest(BaseModel):
    razorpay_payment_id: str
    razorpay_subscription_id: str
    razorpay_signature: str


class WebhookPayload(BaseModel):
    event: str
    payload: Dict[str, Any]


# ── Admin ─────────────────────────────────────────────────────────────────────

class AdminStats(BaseModel):
    total_users: int
    pro_users: int
    free_users: int
    total_scans: int
    scans_today: int
    avg_risk_score: Optional[float]


# Update forward reference
Token.model_rebuild()


# ── Scheduled Scan ────────────────────────────────────────────────────────────

class ScheduledScanCreate(BaseModel):
    url: str
    frequency: str          # daily | weekly | monthly
    day_of_week: Optional[str] = None   # mon|tue|wed|thu|fri|sat|sun
    hour: int = Field(8, ge=0, le=23)
    email_notify: bool = True

    @validator("frequency")
    def validate_frequency(cls, v):
        if v not in ("daily", "weekly", "monthly"):
            raise ValueError("frequency must be daily, weekly, or monthly")
        return v

    @validator("day_of_week")
    def validate_day(cls, v, values):
        if values.get("frequency") == "weekly":
            valid = ("mon","tue","wed","thu","fri","sat","sun")
            if v not in valid:
                raise ValueError(f"day_of_week must be one of {valid}")
        return v


class ScheduledScanUpdate(BaseModel):
    url: Optional[str] = None
    frequency: Optional[str] = None
    day_of_week: Optional[str] = None
    hour: Optional[int] = Field(None, ge=0, le=23)
    email_notify: Optional[bool] = None
    is_active: Optional[bool] = None


class ScheduledScanResponse(BaseModel):
    id: str
    url: str
    frequency: str
    day_of_week: Optional[str]
    hour: int
    email_notify: bool
    is_active: bool
    last_run_at: Optional[datetime]
    next_run_at: Optional[datetime]
    run_count: int
    created_at: datetime

    class Config:
        from_attributes = True
