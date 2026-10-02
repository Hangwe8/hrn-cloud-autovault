from datetime import datetime, timezone

from sqlalchemy import ForeignKey, String, UniqueConstraint, Numeric, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class Business(Base):
    __tablename__ = "businesses"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True
    )

    created_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow
    )

    users: Mapped[list["User"]] = relationship(
        back_populates="business"
    )

    customers: Mapped[list["Customer"]] = relationship(
        back_populates="business"
    )


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True
    )

    business_id: Mapped[int] = mapped_column(
        ForeignKey("businesses.id"),
        nullable=False
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    role: Mapped[str] = mapped_column(
        String(50),
        default="STAFF"
    )

    created_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow
    )

    business: Mapped["Business"] = relationship(
        back_populates="users"
    )


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True
    )

    business_id: Mapped[int] = mapped_column(
        ForeignKey("businesses.id"),
        nullable=False
    )

    first_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    last_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    email: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )

    phone: Mapped[str] = mapped_column(
        String(30),
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        nullable=True
    )

    business: Mapped["Business"] = relationship(
        back_populates="customers"
    )

    vehicles: Mapped[list["Vehicle"]] = relationship(
        back_populates="customer"
    )


class Vehicle(Base):
    __tablename__ = "vehicles"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True
    )

    business_id: Mapped[int] = mapped_column(
        ForeignKey("businesses.id"),
        nullable=False
    )

    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id"),
        nullable=False
    )

    registration: Mapped[str] = mapped_column(
        String(30),
        nullable=False
    )

    vin: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True
    )

    make: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    model: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    year: Mapped[int | None] = mapped_column(
        nullable=True
    )

    mileage: Mapped[int | None] = mapped_column(
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        nullable=True
    )

    customer: Mapped["Customer"] = relationship(
        back_populates="vehicles"
    )
class ServiceRecord(Base):
    __tablename__ = "service_records"

    __table_args__ = (
        CheckConstraint("parts_cost >= 0", name="ck_service_parts_cost_non_negative"),
        CheckConstraint("labour_cost >= 0", name="ck_service_labour_cost_non_negative"),
        CheckConstraint("total_cost >= 0", name="ck_service_total_cost_non_negative"),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True
    )

    business_id: Mapped[int] = mapped_column(
        ForeignKey("businesses.id"),
        nullable=False
    )

    vehicle_id: Mapped[int] = mapped_column(
        ForeignKey("vehicles.id"),
        nullable=False
    )

    service_date: Mapped[datetime] = mapped_column(
        default=datetime.utcnow
    )

    mileage: Mapped[int | None] = mapped_column(
        nullable=True
    )

    description: Mapped[str] = mapped_column(
        String(1000),
        nullable=False
    )

    parts_cost: Mapped[float] = mapped_column(
        Numeric(12, 2),
        default=0
    )

    labour_cost: Mapped[float] = mapped_column(
        Numeric(12, 2),
        default=0
    )

    total_cost: Mapped[float] = mapped_column(
        Numeric(12, 2),
        default=0
    )

    technician: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )
class JobCard(Base):
    __tablename__ = "job_cards"

    __table_args__ = (
        CheckConstraint("estimated_cost >= 0", name="ck_job_card_estimated_cost_non_negative"),
        CheckConstraint("final_cost >= 0", name="ck_job_card_final_cost_non_negative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    business_id: Mapped[int] = mapped_column(
        ForeignKey("businesses.id"),
        nullable=False
    )
    vehicle_id: Mapped[int] = mapped_column(
        ForeignKey("vehicles.id"),
        nullable=False
    )
    assigned_staff_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="RECEIVED",
        nullable=False
    )

    description: Mapped[str] = mapped_column(
        String(2000),
        nullable=False
    )

    estimated_cost: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    final_cost: Mapped[float] = mapped_column(Numeric(12, 2), default=0)

    created_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        nullable=True
    )
class Quote(Base):
    __tablename__ = "quotes"

    __table_args__ = (
        CheckConstraint("subtotal >= 0", name="ck_quote_subtotal_non_negative"),
        CheckConstraint("vat >= 0", name="ck_quote_vat_non_negative"),
        CheckConstraint("total >= 0", name="ck_quote_total_non_negative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    business_id: Mapped[int] = mapped_column(
        ForeignKey("businesses.id"),
        nullable=False
    )

    job_card_id: Mapped[int] = mapped_column(
        ForeignKey("job_cards.id"),
        nullable=False
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="DRAFT",
        nullable=False
    )

    subtotal: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    vat: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    total: Mapped[float] = mapped_column(Numeric(12, 2), default=0)

    created_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow
    )

    valid_until: Mapped[datetime | None] = mapped_column(
        nullable=True
    )


class QuoteItem(Base):
    __tablename__ = "quote_items"

    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_quote_item_quantity_positive"),
        CheckConstraint("unit_price >= 0", name="ck_quote_item_unit_price_non_negative"),
        CheckConstraint("total >= 0", name="ck_quote_item_total_non_negative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    quote_id: Mapped[int] = mapped_column(
        ForeignKey("quotes.id"),
        nullable=False
    )

    description: Mapped[str] = mapped_column(
        String(500),
        nullable=False
    )

    quantity: Mapped[float] = mapped_column(
        default=1
    )

    unit_price: Mapped[float] = mapped_column( 
        Numeric(12, 2),
        default=0
    )

    total: Mapped[float] = mapped_column(
        Numeric(12, 2),
        default=0
    )
class Invoice(Base):
    __tablename__ = "invoices"
    __table_args__ = (
        UniqueConstraint('business_id', 'quote_id', name='uq_invoices_business_quote'),
    )
    __table_args__ = (
        CheckConstraint("subtotal >= 0", name="ck_invoice_subtotal_non_negative"),
        CheckConstraint("vat >= 0", name="ck_invoice_vat_non_negative"),
        CheckConstraint("total >= 0", name="ck_invoice_total_non_negative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    business_id: Mapped[int] = mapped_column(
        ForeignKey("businesses.id"),
        nullable=False
    )

    quote_id: Mapped[int | None] = mapped_column(
        ForeignKey("quotes.id"),
        nullable=True
    )

    invoice_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        unique=True
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="UNPAID",
        nullable=False
    )

    subtotal: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    vat: Mapped[float] = mapped_column(Numeric(12, 2),default=0)
    total: Mapped[float] = mapped_column(Numeric(12, 2),default=0)

    created_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow
    )

    due_date: Mapped[datetime | None] = mapped_column(
        nullable=True
    )

class InvoiceItem(Base):
    __tablename__ = "invoice_items"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_invoice_item_quantity_positive"),
        CheckConstraint("unit_price >= 0", name="ck_invoice_item_unit_price_non_negative"),
        CheckConstraint("total >= 0", name="ck_invoice_item_total_non_negative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    invoice_id: Mapped[int] = mapped_column(
        ForeignKey("invoices.id"),
        nullable=False
    )

    description: Mapped[str] = mapped_column(
        String(500),
        nullable=False
    )

    quantity: Mapped[float] = mapped_column(
        default=1
    )

    unit_price: Mapped[float] = mapped_column(
        Numeric(12, 2),
        default=0
    )

    total: Mapped[float] = mapped_column(
        Numeric(12, 2),
        default=0
    )

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    business_id: Mapped[int] = mapped_column(
        ForeignKey("businesses.id"),
        nullable=False
    )

    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True
    )

    action: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    entity_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    entity_id: Mapped[int | None] = mapped_column(
        nullable=True
    )

    details: Mapped[str | None] = mapped_column(
        String(2000),
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow,
        nullable=False
    )

class Payment(Base):
    __tablename__ = "payments"

    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_payment_amount_positive"),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True
    )

    business_id: Mapped[int] = mapped_column(
        ForeignKey("businesses.id"),
        nullable=False
    )

    invoice_id: Mapped[int] = mapped_column(
        ForeignKey("invoices.id"),
        nullable=False
    )

    amount: Mapped[float] = mapped_column(
        Numeric(12, 2),
        nullable=False
    )

    payment_method: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    reference: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )

    reversed_at: Mapped[datetime | None] = mapped_column(
        nullable=True
    )

    reversal_reason: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True
    )

    paid_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow,
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow,
        nullable=False
    )


