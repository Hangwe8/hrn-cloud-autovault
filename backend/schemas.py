from pydantic import BaseModel, ConfigDict, Field, field_validator
from datetime import datetime
from decimal import Decimal
from typing import Literal


class BusinessCreate(BaseModel):
    name: str
    email: str


class BusinessResponse(BaseModel):
    id: int
    name: str
    email: str

    model_config = ConfigDict(from_attributes=True)


class CustomerCreate(BaseModel):
    first_name: str
    last_name: str
    email: str | None = None
    phone: str

class CustomerUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
    phone: str | None = None

class CustomerResponse(BaseModel):
    id: int
    business_id: int
    first_name: str
    last_name: str
    email: str | None
    phone: str
    model_config = ConfigDict(from_attributes=True)

class CustomerListResponse(BaseModel):
    items: list[CustomerResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

class VehicleCreate(BaseModel):
    customer_id: int
    registration: str
    vin: str | None = None
    make: str
    model: str
    year: int | None = None
    mileage: int | None = Field(default=None, ge=0)

class VehicleUpdate(BaseModel):
    registration: str | None = None
    vin: str | None = None
    make: str | None = None
    model: str | None = None
    year: int | None = None
    mileage: int | None = Field(default=None, ge=0)
    customer_id: int | None = None

class VehicleResponse(BaseModel):
    id: int
    business_id: int
    customer_id: int
    registration: str
    vin: str | None
    make: str
    model: str
    year: int | None
    mileage: int | None
    model_config = ConfigDict(from_attributes=True)

class VehicleListResponse(BaseModel):
    items: list[VehicleResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

class ServiceRecordCreate(BaseModel):
    vehicle_id: int
    mileage: int | None = Field
    description: str
    parts_cost: Decimal = Field(default=Decimal("0.00"),ge=0)
    labour_cost: Decimal = Field(default=Decimal("0.00"),ge=0)
    technician: str | None = None


class ServiceRecordResponse(BaseModel):
    id: int
    business_id: int
    vehicle_id: int
    service_date: datetime
    mileage: int | None
    description: str
    parts_cost: Decimal
    labour_cost: Decimal
    total_cost: Decimal
    technician: str | None
    model_config = ConfigDict(from_attributes=True)

JobStatus = Literal[
    "RECEIVED",
    "INSPECTION",
    "QUOTED",
    "APPROVED",
    "IN_PROGRESS",
    "COMPLETED",
    "COLLECTED",
    "CANCELLED"
]


class JobCardCreate(BaseModel):
    vehicle_id: int
    assigned_staff_id: int | None = None
    description: str
    estimated_cost: Decimal = Field(default=Decimal("0.00"), ge=0)
    status: JobStatus = "RECEIVED"


class JobCardResponse(BaseModel):
    id: int
    business_id: int
    vehicle_id: int
    assigned_staff_id: int | None
    status: str
    description: str
    estimated_cost: Decimal
    final_cost: Decimal
    created_at: datetime
    completed_at: datetime | None

    model_config = ConfigDict(from_attributes=True)

class JobCardListResponse(BaseModel):
    items: list[JobCardResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

class JobCardStatusUpdate(BaseModel):
    status: JobStatus
    final_cost: Decimal| None = Field(default=None, ge=0)
    assigned_staff_id: int | None = None
QuoteStatus = Literal[
    "DRAFT",
    "SENT",
    "APPROVED",
    "REJECTED",
    "EXPIRED"
]


class QuoteItemCreate(BaseModel):
    description: str
    quantity: Decimal = Field(default=Decimal("1"), gt=0)
    unit_price: Decimal = Field(default=Decimal("0.00"), ge=0)


class QuoteCreate(BaseModel):
    job_card_id: int
    items: list[QuoteItemCreate]
    valid_until: datetime | None = None


class QuoteItemResponse(BaseModel):
    id: int
    quote_id: int
    description: str
    quantity: Decimal
    unit_price: Decimal
    total: Decimal

    model_config = ConfigDict(from_attributes=True)


class QuoteResponse(BaseModel):
    id: int
    business_id: int
    job_card_id: int
    status: str
    subtotal: Decimal
    vat: Decimal
    total: Decimal
    created_at: datetime
    valid_until: datetime | None

    model_config = ConfigDict(from_attributes=True)

class QuoteStatusUpdate(BaseModel):
    status: QuoteStatus

InvoiceStatus = Literal[
    "UNPAID",
    "PARTIALLY_PAID",
    "PAID",
    "OVERDUE",
    "CANCELLED"
]


class InvoiceResponse(BaseModel):
    id: int
    business_id: int
    quote_id: int | None
    invoice_number: str
    status: str
    subtotal: Decimal
    vat: Decimal
    total: Decimal
    created_at: datetime
    due_date: datetime | None

    model_config = ConfigDict(from_attributes=True)
UserRole = Literal[
    "OWNER",
    "ADMIN",
    "MANAGER",
    "STAFF"
]


class UserCreate(BaseModel):
    name: str
    email: str
    password: str
    role: UserRole = "STAFF"


class UserResponse(BaseModel):
    id: int
    business_id: int
    name: str
    email: str
    role: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class LoginRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str

class OnboardingRequest(BaseModel):
    business_name: str
    business_email: str
    owner_name: str
    owner_email: str
    password: str


class DashboardSummaryResponse(BaseModel):
    total_customers: int
    total_vehicles: int
    open_job_cards: int
    quotes_awaiting_approval: int
    outstanding_invoices: Decimal
    monthly_revenue: Decimal

class DashboardStatusCount(BaseModel):
    status: str
    count: int


class DashboardRecentActivity(BaseModel):
    id: int
    action: str
    entity_type: str
    entity_id: int | None
    details: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DashboardResponse(BaseModel):
    summary: DashboardSummaryResponse
    job_cards_by_status: list[DashboardStatusCount]
    quotes_by_status: list[DashboardStatusCount]
    invoices_by_status: list[DashboardStatusCount]
    recent_activity: list[DashboardRecentActivity]

class DashboardDateRange(BaseModel):
    start_date: datetime
    end_date: datetime

class MonthlyRevenue(BaseModel):
    month: str
    revenue: Decimal

class JobPerformanceResponse(BaseModel):
    total_completed_jobs: int
    average_completed_job_value: Decimal

PaymentMethod = Literal[
    "CASH",
    "CARD",
    "EFT",
    "DEBIT_ORDER",
    "OTHER"
]


class PaymentCreate(BaseModel):
    invoice_id: int
    amount: Decimal = Field(
        ...,
        gt=0
    )
    payment_method: PaymentMethod
    reference: str | None = Field(
        default=None,
        max_length=255
        )
    
    @field_validator("reference")
    @classmethod
    def validate_reference(cls, value: str | None) -> str | None:
        if value is None:
            return None
        
        value = value.strip()

        if not value:
            return None
        return value

class PaymentReverseRequest(BaseModel):
    reason: str = Field(
        ...,
        min_length=3, max_length=1000
    )

    @field_validator("reason")
    @classmethod
    def validate_reason(cls, value: str) -> str:
        value = value.strip()

        if len(value) < 3:
            raise ValueError("Reason must be at least 3 characters long.")

        return value


class PaymentResponse(BaseModel):
    id: int
    business_id: int
    invoice_id: int
    amount: Decimal
    payment_method: str
    reference: str | None
    paid_at: datetime
    created_at: datetime
    reversed_at: datetime | None
    reversal_reason: str | None

    model_config = ConfigDict(
        from_attributes=True
    )

class InvoiceBalanceResponse(BaseModel):
    invoice_id: int
    invoice_total: Decimal
    amount_paid: Decimal
    balance: Decimal
    status: str

class PaymentSummaryResponse(BaseModel):
    total_payments: int
    total_received: Decimal
    total_reversed: Decimal
    active_received: Decimal

class PaymentReversalResponse(BaseModel):
    payment_id: int
    invoice_id: int
    amount: Decimal
    payment_method: str
    reference: str | None
    paid_at: datetime
    reversal_reason: str | None
    reversed_at: datetime

    model_config = ConfigDict(from_attributes=True)



