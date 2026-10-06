from sqlalchemy import update
from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP

import models
import schemas
import security
import audit

MONEY_QUANTIZE = Decimal("0.01")

def money(value) -> Decimal:
    return Decimal(str(value)).quantize(
        MONEY_QUANTIZE, rounding=ROUND_HALF_UP
    )

def calculate_invoice_status(
        invoice_total: Decimal,
        amount_paid: Decimal) -> str:
    invoice_total = money(invoice_total)
    amount_paid = money(amount_paid)

    if amount_paid <= Decimal("0.00"):
        return "UNPAID"
    if amount_paid >= invoice_total:
        return "PAID"
    
    return "PARTIALLY_PAID"

def create_business(
    db: Session,
    business: schemas.BusinessCreate
):
    db_business = models.Business(
        name=business.name,
        email=business.email
    )

    db.add(db_business)
    db.commit()
    db.refresh(db_business)

    return db_business


def create_customer(
    db: Session,
    customer: schemas.CustomerCreate,
    business_id: int
):
    business = (
        db.query(models.Business)
        .filter(models.Business.id == business_id)
        .first()
    )

    if business is None:
        raise HTTPException(
            status_code=404,
            detail="Business not found"
        )

    db_customer = models.Customer(
        business_id=business_id,
        first_name=customer.first_name,
        last_name=customer.last_name,
        email=customer.email,
        phone=customer.phone
    )

    db.add(db_customer)
    db.commit()
    db.refresh(db_customer)

    return db_customer


def get_customers(
    db: Session,
    business_id: int
):
    return (
        db.query(models.Customer)
        .filter(
            models.Customer.business_id == business_id
        )
        .all()
    )
def create_vehicle(
    db: Session,
    vehicle: schemas.VehicleCreate,
    business_id: int
):
    customer = (db.query(models.Customer)
                .filter(models.Customer.id == vehicle.customer_id,
                        models.Customer.business_id == business_id,
                        models.Customer.deleted_at.is_(None))

                .first()
    )

    if customer is None:
        raise HTTPException(
            status_code=404,
            detail="Customer not found"
        )

    db_vehicle = models.Vehicle(
        business_id=vehicle.business_id,
        customer_id=vehicle.customer_id,
        registration=vehicle.registration,
        vin=vehicle.vin,
        make=vehicle.make,
        model=vehicle.model,
        year=vehicle.year,
        mileage=vehicle.mileage
    )

    db.add(db_vehicle)
    db.commit()
    db.refresh(db_vehicle)

    return db_vehicle


def get_vehicles(
    db: Session,
    business_id: int,
    page: int = 1,
    page_size: int = 25,
    search: str | None = None,
    include_archived: bool = False
):
    if page < 1:
        raise HTTPException(
            status_code=400,
            detail="Page must be greater than or equal to 1"
        )

    if page_size < 1 or page_size > 100:
        raise HTTPException(
            status_code=400,
            detail="Page size must be between 1 and 100"
        )

    query = (
        db.query(models.Vehicle)
        .filter(
            models.Vehicle.business_id == business_id
        )
    )

    if not include_archived:
        query = query.filter(
            models.Vehicle.deleted_at.is_(None)
        )

    if search:
        search_term = search.strip()

        if search_term:
            search_pattern = f"%{search_term}%"

            query = query.filter(
                (
                    models.Vehicle.registration.ilike(
                        search_pattern
                    )
                )
                | (
                    models.Vehicle.vin.ilike(
                        search_pattern
                    )
                )
                | (
                    models.Vehicle.make.ilike(
                        search_pattern
                    )
                )
                | (
                    models.Vehicle.model.ilike(
                        search_pattern
                    )
                )
            )

    total = query.count()

    offset = (page - 1) * page_size

    vehicles = (
        query
        .order_by(
            models.Vehicle.created_at.desc(),
            models.Vehicle.id.desc()
        )
        .offset(offset)
        .limit(page_size)
        .all()
    )

    total_pages = (
        (total + page_size - 1) // page_size
        if total > 0
        else 0
    )

    return {
        "items": vehicles,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages
    }

def create_service_record(
    db: Session,
    service: schemas.ServiceRecordCreate,
    business_id: int
):
    vehicle = (db.query(models.Vehicle)
                .filter(models.Vehicle.id == service.vehicle_id,
                        models.Vehicle.business_id == service.business_id,
                        models.Vehicle.deleted_at.is_(None))
                .first()
    )

    if vehicle is None:
        raise HTTPException(
            status_code=404,
            detail="Vehicle not found"
        )
    
    parts_cost = money(service.parts_cost)
    labour_cost = money(service.labour_cost)

    total_cost = (
        parts_cost +
        labour_cost
    )

    db_service = models.ServiceRecord(
        business_id=service.business_id,
        vehicle_id=service.vehicle_id,
        mileage=service.mileage,
        description=service.description,
        parts_cost=parts_cost,
        labour_cost=labour_cost,
        total_cost=total_cost,
        technician=service.technician
    )

    db.add(db_service)
    db.commit()
    db.refresh(db_service)

    return db_service


def get_service_history(
    db: Session,
    business_id: int,
    vehicle_id: int
):
    return (
        db.query(models.ServiceRecord)
        .filter(
            models.ServiceRecord.business_id == business_id,
            models.ServiceRecord.vehicle_id == vehicle_id
        )
        .order_by(
            models.ServiceRecord.service_date.desc()
        )
        .all()
    )
def create_job_card(db: Session, job_card: schemas.JobCardCreate, business_id: int, user_id: int):

    vehicle = (db.query(models.Vehicle)
                .filter(models.Vehicle.id == job_card.vehicle_id,
                        models.Vehicle.business_id == job_card.business_id,
                        models.Vehicle.deleted_at.is_(None))
                .first()
    )

    if vehicle is None:
        raise HTTPException(
            status_code=404,
            detail="Vehicle not found"
        )
    
    if job_card.assigned_staff_id is not None:
        staff = (db.query(models.User)
                    .filter(models.User.id == job_card.assigned_staff_id,
                            models.User.business_id == job_card.business_id)
                    .first()
        )

        if staff is None:
            raise HTTPException(
                status_code=404,
                detail="Assigned staff not found"
            )
        
    db_job_card = models.JobCard(
        business_id=job_card.business_id,
        vehicle_id=job_card.vehicle_id,
        assigned_staff_id=job_card.assigned_staff_id,
        status=job_card.status,
        description=job_card.description,
        estimated_cost=job_card.estimated_cost,
        final_cost=0
    )

    db.add(db_job_card)

    audit.create_audit_log(
        db=db,
        user_id=user_id,
        action="JOB_CARD_CREATED",
        entity_type="JobCard",
        entity_id=db_job_card.id,
        details=f"Job card created for vehicle {vehicle.id}"
    )

    db.commit()
    db.refresh(db_job_card)

    return db_job_card


def get_job_cards(
    db: Session,
    business_id: int,
    page: int = 1,
    page_size: int = 25,
    search: str | None = None,
    status: str | None = None,
    vehicle_id: int | None = None
):
    if page < 1:
        raise HTTPException(
            status_code=400,
            detail="Page must be greater than or equal to 1"
        )

    if page_size < 1 or page_size > 100:
        raise HTTPException(
            status_code=400,
            detail="Page size must be between 1 and 100"
        )

    query = (
        db.query(models.JobCard)
        .filter(
            models.JobCard.business_id == business_id
        )
    )

    # Status filter
    if status:
        valid_statuses = {
            "RECEIVED",
            "INSPECTION",
            "QUOTED",
            "APPROVED",
            "IN_PROGRESS",
            "COMPLETED",
            "COLLECTED",
            "CANCELLED"
        }

        if status not in valid_statuses:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid job card status: {status}"
            )

        query = query.filter(
            models.JobCard.status == status
        )

    # Vehicle filter
    if vehicle_id is not None:
        vehicle = (
            db.query(models.Vehicle)
            .filter(
                models.Vehicle.id == vehicle_id,
                models.Vehicle.business_id == business_id
            )
            .first()
        )

        if vehicle is None:
            raise HTTPException(
                status_code=404,
                detail="Vehicle not found"
            )

        query = query.filter(
            models.JobCard.vehicle_id == vehicle_id
        )

    # Search description
    if search:
        search_term = search.strip()

        if search_term:
            search_pattern = f"%{search_term}%"

            query = query.filter(
                models.JobCard.description.ilike(
                    search_pattern
                )
            )

    total = query.count()

    offset = (page - 1) * page_size

    job_cards = (
        query
        .order_by(
            models.JobCard.created_at.desc(),
            models.JobCard.id.desc()
        )
        .offset(offset)
        .limit(page_size)
        .all()
    )

    total_pages = (
        (total + page_size - 1) // page_size
        if total > 0
        else 0
    )

    return {
        "items": job_cards,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages
    }

def update_job_card_status(
    db: Session,
    job_card_id: int,
    status: str,
    business_id: int,
    user_id: int,
    final_cost: float | None = None,
    assigned_staff_id: int | None = None 
):
    job_card = (
        db.query(models.JobCard)
        .filter(models.JobCard.id == job_card_id,
                models.JobCard.business_id == business_id)
        .first()
    )

    if job_card is None:
        raise HTTPException(
            status_code=404,
            detail="Job card not found"
        )

    if assigned_staff_id is not None:
        staff = (
            db.query(models.User)
            .filter(
                models.User.id == assigned_staff_id,
                models.User.business_id == job_card.business_id
            )
            .first()
        )

        if staff is None:
            raise HTTPException(
                status_code=404,
                detail="Staff member not found for this business"
            )

        job_card.assigned_staff_id = assigned_staff_id

    job_card.status = status

    audit.create_audit_log(
        db=db,
        business_id=business_id,
        user_id=user_id,
        action=f"JOB_CARD_STATUS_CHANGED",
        entity_type="JobCard",
        entity_id=job_card.id,
        details=f"Job card status changed to {update.status}"
    )

    if final_cost is not None:
        job_card.final_cost = final_cost

    if status == "COMPLETED":
        job_card.completed_at = datetime.utcnow()

    db.commit()
    db.refresh(job_card)

    return job_card

def get_job_card(
    db: Session,
    job_card_id: int,
    business_id: int
):
    job_card = (
        db.query(models.JobCard)
        .filter(
            models.JobCard.id == job_card_id,
            models.JobCard.business_id == business_id
        )
        .first()
    )

    if job_card is None:
        raise HTTPException(
            status_code=404,
            detail="Job card not found"
        )

    return job_card

def create_quote(
    db: Session,
    quote: schemas.QuoteCreate,
    business_id: int
):
    job_card = (
        db.query(models.JobCard)
        .filter(
            models.JobCard.id == quote.job_card_id,
            models.JobCard.business_id == business_id
        )
        .first()
    )

    if job_card is None:
        raise HTTPException(
            status_code=404,
            detail="Job card not found"
        )

    if job_card.status == "CANCELLED":
        raise HTTPException(
            status_code=400,
            detail="Cannot create a quote for a cancelled job card"
        )

    db_quote = models.Quote(
        business_id=business_id,
        job_card_id=quote.job_card_id,
        status="DRAFT",
        valid_until=quote.valid_until,
        subtotal=Decimal("0.00"),
        vat=Decimal("0.00"),
        total=Decimal("0.00")
    )

    db.add(db_quote)
    db.flush()

    subtotal = Decimal("0.00")

    for item in quote.items:
        quantity = Decimal(str(item.quantity))
        unit_price = money(item.unit_price)

        item_total = money(quantity * unit_price)

        db_item = models.QuoteItem(
            quote_id=db_quote.id,
            description=item.description,
            quantity=item.quantity,
            unit_price=unit_price,
            total=item_total
        )

        db.add(db_item)

        subtotal += item_total

    subtotal = money(subtotal)

    vat = money(
        subtotal * Decimal("0.15")
    )

    total = money(
        subtotal + vat
    )

    db_quote.subtotal = subtotal
    db_quote.vat = vat
    db_quote.total = total

    db.commit()
    db.refresh(db_quote)

    return db_quote


def update_quote_status(
    db: Session,
    quote_id: int,
    status: str,
    business_id: int,
    user_id: int
):
    quote = (
        db.query(models.Quote)
        .filter(models.Quote.id == quote_id,
                models.Quote.business_id == business_id)
        .first()
    )

    if quote is None:
        raise HTTPException(
            status_code=404,
            detail="Quote not found"
        )

    current_status = quote.status

    allowed_transitions = {
        "DRAFT": ["SENT"],
        "SENT": ["APPROVED", "REJECTED", "EXPIRED"],
        "APPROVED": [],
        "REJECTED": [],
        "EXPIRED": []
    }

    allowed_next_statuses = allowed_transitions.get(
        current_status,
        []
    )

    if status not in allowed_next_statuses:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Invalid quote status transition: "
                f"{current_status} -> {status}"
            )
        )

    quote.status = status

    audit.create_audit_log(
        db=db,
        user_id=user_id,
        action=f"QUOTE_{status}",
        entity_type="Quote",
        entity_id=quote.id,
        details=f"Quote status changed from {current_status} to {status}"
    )

    db.commit()
    db.refresh(quote)

    return quote

def create_invoice_from_quote(
    db: Session,
    quote_id: int,
    business_id: int,
    user_id: int
):
    quote = (
        db.query(models.Quote)
        .filter(models.Quote.id == quote_id,
                models.Quote.business_id == business_id)
        .first()
    )

    if quote is None:
        raise HTTPException(
            status_code=404,
            detail="Quote not found"
        )

    if quote.status != "APPROVED":
        raise HTTPException(
            status_code=400,
            detail="Only approved quotes can be converted into invoices"
        )

    invoice_number = f"INV-{quote.business_id}-{quote.id}"

    existing_invoice = (
        db.query(models.Invoice)
        .filter(
            models.Invoice.quote_id == quote.id,
            models.Invoice.business_id == business_id
        )
        .first()
    )

    if existing_invoice is not None:
        raise HTTPException(
            status_code=400,
            detail="An invoice has already been created for this quote"
        )

    invoice = models.Invoice(
        business_id=quote.business_id,
        quote_id=quote.id,
        invoice_number=invoice_number,
        status="UNPAID",
        subtotal=money(quote.subtotal),
        vat=money(quote.vat),
        total=money(quote.total),
        due_date=None
    )

    db.add(invoice)
    db.flush()

    quote_items = (
        db.query(models.QuoteItem)
        .filter(
            models.QuoteItem.quote_id == quote.id
        )
        .all()
    )

    for item in quote_items:
        invoice_item = models.InvoiceItem(
            invoice_id=invoice.id,
            description=item.description,
            quantity=item.quantity,
            unit_price=item.unit_price,
            total=item.total
        )

        db.add(invoice_item)

    audit.create_audit_log(
        db=db,
        business_id=business_id,
        user_id=user_id,
        action="INVOICE_CREATED",
        entity_type="Invoice",
        entity_id=invoice.id,
        details=(f"Invoice {db_invoice.invoice_number}"
        f" created from quote {quote.id}")
    )


    db.commit()
    db.refresh(invoice)

    return invoice

def get_quotes(
    db: Session,
    business_id: int,
    page: int = 1,
    page_size: int = 25,
    status: str | None = None,
    job_card_id: int | None = None
):
    if page < 1:
        raise HTTPException(
            status_code=400,
            detail="Page must be greater than or equal to 1"
        )

    if page_size < 1 or page_size > 100:
        raise HTTPException(
            status_code=400,
            detail="Page size must be between 1 and 100"
        )

    query = (
        db.query(models.Quote)
        .filter(
            models.Quote.business_id == business_id
        )
    )

    if status:
        valid_statuses = {
            "DRAFT",
            "SENT",
            "APPROVED",
            "REJECTED",
            "EXPIRED"
        }

        if status not in valid_statuses:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid quote status: {status}"
            )

        query = query.filter(
            models.Quote.status == status
        )

    if job_card_id is not None:
        job_card = (
            db.query(models.JobCard)
            .filter(
                models.JobCard.id == job_card_id,
                models.JobCard.business_id == business_id
            )
            .first()
        )

        if job_card is None:
            raise HTTPException(
                status_code=404,
                detail="Job card not found"
            )

        query = query.filter(
            models.Quote.job_card_id == job_card_id
        )

    total = query.count()

    offset = (page - 1) * page_size

    quotes = (
        query
        .order_by(
            models.Quote.created_at.desc(),
            models.Quote.id.desc()
        )
        .offset(offset)
        .limit(page_size)
        .all()
    )

    total_pages = (
        (total + page_size - 1) // page_size
        if total > 0
        else 0
    )

    return {
        "items": quotes,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages
    }

def create_user(db: Session, user: schemas.UserCreate,business_id: int, created_by_user_id: int):

    if user.role == "OWNER":
        raise HTTPException(
            status_code=403,
            detail="Owner accounts can only be created during business registration"
        )
    
    business = (
        db.query(models.Business)
        .filter(models.Business.id == user.business_id)
        .first()
    )

    if business is None:
        raise HTTPException(
            status_code=404,
            detail="Business not found"
        )

    existing_user = (
        db.query(models.User)
        .filter(
            models.User.business_id == user.business_id,
            models.User.email == user.email
        )
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=409,
            detail="A user with this email already exists in this business"
        )

    db_user = models.User(
        business_id=user.business_id,
        name=user.name,
        email=user.email,
        password_hash=security.hash_password(user.password),
        role=user.role
    )

    db.add(db_user)

    audit.create_audit_log(
        db=db,
        user_id=user_id,
        action="USER_CREATED",
        entity_type="User",
        entity_id=db_user.id,
        details=f"User {db_user.email} was created"
    )

    db.commit()
    db.refresh(db_user)

    return db_user


def get_users(db: Session, business_id: int):
    return (
        db.query(models.User)
        .filter(models.User.business_id == business_id)
        .order_by(models.User.created_at.asc())
        .all()
    )

def register_business(
    db: Session,
    onboarding: schemas.OnboardingRequest
):
    existing_business = (
        db.query(models.Business)
        .filter(models.Business.email == onboarding.business_email)
        .first()
    )

    if existing_business:
        raise HTTPException(
            status_code=400,
            detail="A business with this email already exists"
        )

    existing_user = (
        db.query(models.User)
        .filter(models.User.email == onboarding.owner_email)
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="A user with this email already exists"
        )

    business = models.Business(
        name=onboarding.business_name,
        email=onboarding.business_email
    )

    db.add(business)
    db.flush()

    owner = models.User(
        business_id=business.id,
        name=onboarding.owner_name,
        email=onboarding.owner_email,
        password_hash=security.hash_password(
            onboarding.password
        ),
        role="OWNER"
    )

    db.add(owner)
    db.commit()

    db.refresh(business)
    db.refresh(owner)

    return business, owner


def get_customers(
    db: Session,
    business_id: int,
    page: int = 1,
    page_size: int = 25,
    search: str | None = None,
    include_archived: bool = False
):
    if page < 1:
        raise HTTPException(
            status_code=400,
            detail="Page must be greater than or equal to 1"
        )

    if page_size < 1 or page_size > 100:
        raise HTTPException(
            status_code=400,
            detail="Page size must be between 1 and 100"
        )

    query = (
        db.query(models.Customer)
        .filter(
            models.Customer.business_id == business_id
        )
    )

    if not include_archived:
        query = query.filter(
            models.Customer.deleted_at.is_(None)
        )

    if search:
        search_term = search.strip()

        if search_term:
            search_pattern = f"%{search_term}%"

            query = query.filter(
                (
                    models.Customer.first_name.ilike(search_pattern)
                )
                | (
                    models.Customer.last_name.ilike(search_pattern)
                )
                | (
                    models.Customer.email.ilike(search_pattern)
                )
                | (
                    models.Customer.phone.ilike(search_pattern)
                )
            )

    total = query.count()

    offset = (page - 1) * page_size

    customers = (
        query
        .order_by(
            models.Customer.created_at.desc(),
            models.Customer.id.desc()
        )
        .offset(offset)
        .limit(page_size)
        .all()
    )

    total_pages = (
        (total + page_size - 1) // page_size
        if total > 0
        else 0
    )

    return {
        "items": customers,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages
    }

def update_customer(
    db: Session,
    customer_id: int,
    customer_update: schemas.CustomerUpdate,
    business_id: int
):
    customer = get_customer(
        db,
        customer_id,
        business_id
    )

    update_data = customer_update.model_dump(
        exclude_unset=True
    )

    for field, value in update_data.items():
        setattr(customer, field, value)

    db.commit()
    db.refresh(customer)

    return customer


def delete_customer(
    db: Session,
    customer_id: int,
    business_id: int,
    user_id: int
):
    customer = get_customer(
        db,
        customer_id,
        business_id
    )

    customer.deleted_at = datetime.utcnow()
    audit.create_audit_log(
        db=db,
        user_id=user_id,
        action="CUSTOMER_ARCHIVED",
        entity_type="Customer",
        entity_id=customer.id,
        details=f"Customer {customer.first_name} {customer.last_name} archived"
    )
    db.commit()
    db.refresh(customer)

    return customer

def get_vehicle(
    db: Session,
    vehicle_id: int,
    business_id: int
):
    vehicle = (
        db.query(models.Vehicle)
        .filter(
            models.Vehicle.id == vehicle_id,
            models.Vehicle.business_id == business_id,
            models.Vehicle.deleted_at.is_(None) 
        )
        .first()
    )

    if vehicle is None:
        raise HTTPException(
            status_code=404,
            detail="Vehicle not found"
        )

    return vehicle


def update_vehicle(
    db: Session,
    vehicle_id: int,
    vehicle_update: schemas.VehicleUpdate,
    business_id: int
):
    vehicle = get_vehicle(
        db,
        vehicle_id,
        business_id
    )

    update_data = vehicle_update.model_dump(
        exclude_unset=True
    )

    if "customer_id" in update_data:
        customer = (
            db.query(models.Customer)
            .filter(
                models.Customer.id == update_data["customer_id"],
                models.Customer.business_id == business_id,
                models.Customer.deleted_at.is_(None)
            )
            .first()
        )

        if customer is None:
            raise HTTPException(
                status_code=404,
                detail="Customer not found in your business"
            )

    for field, value in update_data.items():
        setattr(vehicle, field, value)

    db.commit()
    db.refresh(vehicle)

    return vehicle


def delete_vehicle(
    db: Session,
    vehicle_id: int,
    business_id: int,
    user_id: int
):
    vehicle = get_vehicle(
        db,
        vehicle_id,
        business_id
    )

    vehicle.deleted_at = datetime.utcnow()

    audit.create_audit_log(
        db=db,
        user_id=user_id,
        action="VEHICLE_ARCHIVED",
        entity_type="Vehicle",
        entity_id=vehicle.id,
        details=f"Vehicle {vehicle.registration} archived"
    )
    db.commit()
    db.refresh(vehicle)

    return vehicle

def get_service_record(
    db: Session,
    service_record_id: int,
    business_id: int
):
    service_record = (
        db.query(models.ServiceRecord)
        .filter(
            models.ServiceRecord.id == service_record_id,
            models.ServiceRecord.business_id == business_id
        )
        .first()
    )

    if service_record is None:
        raise HTTPException(
            status_code=404,
            detail="Service record not found"
        )

    return service_record

def get_service_records(
    db: Session,
    business_id: int,
    page: int = 1,
    page_size: int = 25,
    vehicle_id: int | None = None
):
    if page < 1:
        raise HTTPException(
            status_code=400,
            detail="Page must be greater than or equal to 1"
        )

    if page_size < 1 or page_size > 100:
        raise HTTPException(
            status_code=400,
            detail="Page size must be between 1 and 100"
        )

    query = (
        db.query(models.ServiceRecord)
        .filter(
            models.ServiceRecord.business_id == business_id
        )
    )

    if vehicle_id is not None:
        vehicle = (
            db.query(models.Vehicle)
            .filter(
                models.Vehicle.id == vehicle_id,
                models.Vehicle.business_id == business_id,
                models.Vehicle.deleted_at.is_(None)
            )
            .first()
        )

        if vehicle is None:
            raise HTTPException(
                status_code=404,
                detail="Vehicle not found"
            )

        query = query.filter(
            models.ServiceRecord.vehicle_id == vehicle_id
        )

    total = query.count()

    offset = (page - 1) * page_size

    records = (
        query
        .order_by(
            models.ServiceRecord.service_date.desc(),
            models.ServiceRecord.id.desc()
        )
        .offset(offset)
        .limit(page_size)
        .all()
    )

    total_pages = (
        (total + page_size - 1) // page_size
        if total > 0
        else 0
    )

    return {
        "items": records,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages
    }

def get_invoice(
    db: Session,
    invoice_id: int,
    business_id: int
):
    invoice = (
        db.query(models.Invoice)
        .filter(
            models.Invoice.id == invoice_id,
            models.Invoice.business_id == business_id
        )
        .first()
    )

    if invoice is None:
        raise HTTPException(
            status_code=404,
            detail="Invoice not found"
        )

    return invoice

def get_invoices(
    db: Session,
    business_id: int,
    page: int = 1,
    page_size: int = 25,
    status: str | None = None,
    payment_state: str | None = None,
    overdue_only: bool = False
):
    if page < 1:
        raise HTTPException(
            status_code=400,
            detail="Page must be greater than or equal to 1"
        )

    if page_size < 1 or page_size > 100:
        raise HTTPException(
            status_code=400,
            detail="Page size must be between 1 and 100"
        )

    valid_statuses = {
        "UNPAID",
        "PARTIALLY_PAID",
        "PAID",
        "OVERDUE",
        "CANCELLED"
    }

    valid_payment_states = {
        "UNPAID",
        "PARTIALLY_PAID",
        "PAID"
    }

    if status and status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid invoice status: {status}"
        )

    if payment_state and payment_state not in valid_payment_states:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid payment state: {payment_state}"
        )

    query = (
        db.query(
            models.Invoice,
            func.coalesce(
                func.sum(
                    models.Payment.amount
                ),
                0
            ).label("amount_paid")
        )
        .outerjoin(
            models.Payment,
            (
                models.Payment.invoice_id
                == models.Invoice.id
            )
            & (
                models.Payment.business_id
                == business_id
            )
            & (
                models.Payment.reversed_at.is_(None)
            )
        )
        .filter(
            models.Invoice.business_id == business_id
        )
        .group_by(
            models.Invoice.id
        )
    )

    if status:
        query = query.filter(
            models.Invoice.status == status
        )

    if overdue_only:
        now = datetime.utcnow()

        query = query.filter(
            models.Invoice.due_date.is_not(None),
            models.Invoice.due_date < now,
            models.Invoice.status != "PAID",
            models.Invoice.status != "CANCELLED"
        )

    rows = query.order_by(
        models.Invoice.created_at.desc(),
        models.Invoice.id.desc()
    ).all()

    filtered_rows = []

    for invoice, amount_paid in rows:
        amount_paid = money(amount_paid)

        calculated_state = calculate_invoice_status(
            invoice.total,
            amount_paid
        )

        if (
            payment_state
            and calculated_state != payment_state
        ):
            continue

        filtered_rows.append(invoice)

    total = len(filtered_rows)

    offset = (page - 1) * page_size

    paginated_invoices = filtered_rows[
        offset:offset + page_size
    ]

    total_pages = (
        (total + page_size - 1) // page_size
        if total > 0
        else 0
    )

    return {
        "items": paginated_invoices,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages
    }

def get_dashboard_summary(
    db: Session,
    business_id: int,
    start_date: datetime | None = None,
    end_date: datetime | None = None
):
    total_customers = (
        db.query(models.Customer)
        .filter(
            models.Customer.business_id == business_id,
            models.Customer.deleted_at.is_(None)
        )
        .count()
    )

    total_vehicles = (
        db.query(models.Vehicle)
        .filter(
            models.Vehicle.business_id == business_id,
            models.Vehicle.deleted_at.is_(None)
        )
        .count()
    )

    open_job_cards = (
        db.query(models.JobCard)
        .filter(
            models.JobCard.business_id == business_id,
            models.JobCard.status.notin_(
                ["COMPLETED", "COLLECTED", "CANCELLED"]
            )
        )
        .count()
    )

    quotes_awaiting_approval = (
        db.query(models.Quote)
        .filter(
            models.Quote.business_id == business_id,
            models.Quote.status == "SENT"
        )
        .count()
    )

    paid_subquery = (
        db.query(
            models.Payment.invoice_id.label("invoice_id"),
            func.coalesce(func.sum(models.Payment.amount), 0).label("paid")
        )
        .filter(
            models.Payment.business_id == business_id,
            models.Payment.reversed_at.is_(None)
        )
        .group_by(models.Payment.invoice_id)
        .subquery()
    )

    outstanding_invoices = (
        db.query(
            func.coalesce(
                func.sum(
                    models.Invoice.total -
                    func.coalesce(paid_subquery.c.paid, 0)
                ),
                0
            )
        )
        .outerjoin(
            paid_subquery,
            paid_subquery.c.invoice_id == models.Invoice.id
        )
        .filter(
            models.Invoice.business_id == business_id,
            models.Invoice.status.in_(
                ["UNPAID", "PARTIALLY_PAID", "OVERDUE"]
            )
        )
        .scalar()
    )
    

    now = datetime.now(timezone.utc)


    if start_date is not None:
        month_start = now.replace(
            day=1,
            hour=0,
            minute=0,
            second=0,
            microsecond=0
        )
    
    if end_date is not None:
        end_date = now

    monthly_revenue = (
        db.query(models.Invoice)
        .filter(
            models.Invoice.business_id == business_id,
            models.Invoice.status == "PAID",
            models.Invoice.created_at >= start_date,
            models.Invoice.created_at <= end_date
        )
        .with_entities(
            func.coalesce(
                func.sum(models.Invoice.total),
                0
            )
        )
        .scalar()
    )

    return {
        "total_customers": total_customers,
        "total_vehicles": total_vehicles,
        "open_job_cards": open_job_cards,
        "quotes_awaiting_approval": quotes_awaiting_approval,
        "outstanding_invoices": money(
            outstanding_invoices
        ),
        "monthly_revenue": money(
            monthly_revenue
        )
    }

def get_dashboard(
    db: Session,
    business_id: int
):
    summary = get_dashboard_summary(
        db,
        business_id
    )

    job_card_rows = (
        db.query(
            models.JobCard.status,
            func.count(models.JobCard.id)
        )
        .filter(
            models.JobCard.business_id == business_id
        )
        .group_by(models.JobCard.status)
        .all()
    )

    quote_rows = (
        db.query(
            models.Quote.status,
            func.count(models.Quote.id)
        )
        .filter(
            models.Quote.business_id == business_id
        )
        .group_by(models.Quote.status)
        .all()
    )

    invoice_rows = (
        db.query(
            models.Invoice.status,
            func.count(models.Invoice.id)
        )
        .filter(
            models.Invoice.business_id == business_id
        )
        .group_by(models.Invoice.status)
        .all()
    )

    recent_activity = (
        db.query(models.AuditLog)
        .filter(
            models.AuditLog.business_id == business_id
        )
        .order_by(
            models.AuditLog.created_at.desc()
        )
        .limit(10)
        .all()
    )

    return {
        "summary": summary,

        "job_cards_by_status": [
            {
                "status": status,
                "count": count
            }
            for status, count in job_card_rows
        ],

        "quotes_by_status": [
            {
                "status": status,
                "count": count
            }
            for status, count in quote_rows
        ],

        "invoices_by_status": [
            {
                "status": status,
                "count": count
            }
            for status, count in invoice_rows
        ],

        "recent_activity": recent_activity
    }

def get_job_performance(
    db: Session,
    business_id: int
):
    completed_jobs = (
        db.query(models.JobCard)
        .filter(
            models.JobCard.business_id == business_id,
            models.JobCard.status == "COMPLETED"
        )
        .all()
    )

    total_completed_jobs = len(completed_jobs)

    if total_completed_jobs == 0:
        average_completed_job_value = Decimal("0.00")
    else:
        total_value = sum(
            (
                money(job.final_cost)
                for job in completed_jobs
            ),
            Decimal("0.00")
        )

        average_completed_job_value = money(
            total_value / total_completed_jobs
        )

    return {
        "total_completed_jobs": total_completed_jobs,
        "average_completed_job_value": average_completed_job_value
    }

def get_monthly_revenue(db: Session, business_id: int):
    rows = (
        db.query(
            func.date_trunc(
                "month",
                models.Payment.paid_at
            ).label("month"),
            func.coalesce(
                func.sum(models.Payment.amount),
                0
            ).label("revenue")
        )
        .filter(
            models.Payment.business_id == business_id,
            models.Payment.reversed_at.is_(None)
        )
        .group_by(
            func.date_trunc(
                "month",
                models.Payment.paid_at
            )
        )
        .order_by(
            func.date_trunc(
                "month",
                models.Payment.paid_at
            )
        )
        .all()
    )

    return [
        {
            "month": month.strftime("%Y-%m"),
            "revenue": money(revenue)
        }
        for month, revenue in rows
    ]

def create_payment(
    db: Session,
    payment,
    business_id: int,
    user_id: int
):
    try: 
        invoice = (
            db.query(models.Invoice)
            .filter(
                models.Invoice.id == payment.invoice_id,
                models.Invoice.business_id == business_id
            )
            .first()
        )

        if invoice is None:
            raise HTTPException(
                status_code=404,
                detail="Invoice not found"
            )

        if invoice.status == "CANCELLED":
            raise HTTPException(
                status_code=400,
                detail="Cannot pay a cancelled invoice"
            )

        existing_paid = (
            db.query(models.Payment)
            .filter(
                models.Payment.invoice_id == invoice.id,
                models.Payment.business_id == business_id
            )
            .with_entities(
                func.coalesce(
                    func.sum(models.Payment.amount),
                    0
                )
            )
            .scalar()
        )

        existing_paid = money(existing_paid)

        payment_amount = money(
            payment.amount
        )

        remaining_balance = money(
            invoice.total - existing_paid
        )
        if remaining_balance <= Decimal("0.00"):
            raise HTTPException(
                status_code=400,
                detail="Invoice is already fully paid"
            )

        if payment_amount > remaining_balance:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Payment exceeds remaining balance "
                    f"of {remaining_balance}"
                )
            )

        db_payment = models.Payment(
            business_id=business_id,
            invoice_id=invoice.id,
            amount=payment_amount,
            payment_method=payment.payment_method,
            reference=payment.reference
        )

        db.add(db_payment)
        db.flush()

        new_paid_total = money(
            existing_paid + payment_amount
        )

        invoice.status = calculate_invoice_status(invoice.total, new_paid_total)

        audit.create_audit_log(
            db=db,
            business_id=business_id,
            user_id=user_id,
            action="PAYMENT_CREATED",
            entity_type="Payment",
            entity_id=db_payment.id,
            details=(
                f"Payment of R{payment_amount} recorded "
                f"against invoice {invoice.invoice_number}"
            )
        )

        db.commit()
        db.refresh(db_payment)

        return db_payment
    
    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise 

def reverse_payment(
    db: Session,
    payment_id: int,
    reason: str,
    business_id: int,
    user_id: int
):
    try:
        payment = (
            db.query(models.Payment)
            .filter(
                models.Payment.id == payment_id,
                models.Payment.business_id == business_id
            )
            .first()
        )

        if payment is None:
            raise HTTPException(
                status_code=404,
                detail="Payment not found"
            )

        if payment.reversed_at is not None:
            raise HTTPException(
                status_code=400,
                detail="Payment has already been reversed"
            )

        invoice = (
            db.query(models.Invoice)
            .filter(
                models.Invoice.id == payment.invoice_id,
                models.Invoice.business_id == business_id
            )
            .first()
        )

        if invoice is None:
            raise HTTPException(
                status_code=404,
                detail="Invoice not found"
            )

        payment.reversed_at = datetime.utcnow()
        payment.reversal_reason = reason

        active_paid_amount = (
            db.query(
                func.coalesce(
                    func.sum(models.Payment.amount),
                    0
                )
            )
            .filter(
                models.Payment.invoice_id == invoice.id,
                models.Payment.business_id == business_id,
                models.Payment.reversed_at.is_(None)
            )
            .scalar()
        )

        active_paid_amount = money(active_paid_amount)

        if active_paid_amount <= Decimal("0.00"):
            invoice.status = "UNPAID"
        elif active_paid_amount < money(invoice.total):
            invoice.status = "PARTIALLY_PAID"
        else:
            invoice.status = "PAID"

        audit.create_audit_log(
            db=db,
            business_id=business_id,
            user_id=user_id,
            action="PAYMENT_REVERSED",
            entity_type="Payment",
            entity_id=payment.id,
            details=(
                f"Payment of R{money(payment.amount)} reversed. "
                f"Reason: {reason}"
            )
        )

        db.commit()
        db.refresh(payment)

        return payment
    
    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise

def get_payments(
    db: Session,
    business_id: int,
    page: int = 1,
    page_size: int = 25,
    invoice_id: int | None = None,
    payment_method: str | None = None,
    payment_status: str = "ACTIVE",
    start_date: datetime | None = None,
    end_date: datetime | None = None
):
    if page < 1:
        raise HTTPException(
            status_code=400,
            detail="Page must be greater than or equal to 1"
        )

    if page_size < 1 or page_size > 100:
        raise HTTPException(
            status_code=400,
            detail="Page size must be between 1 and 100"
        )

    valid_methods = {
        "CASH",
        "CARD",
        "EFT",
        "DEBIT_ORDER",
        "OTHER"
    }

    valid_payment_statuses = {
        "ACTIVE",
        "REVERSED",
        "ALL"
    }

    if payment_method and payment_method not in valid_methods:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid payment method: {payment_method}"
        )

    if payment_status not in valid_payment_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid payment status: {payment_status}"
        )

    if start_date and end_date and start_date > end_date:
        raise HTTPException(
            status_code=400,
            detail="start_date cannot be after end_date"
        )

    query = (
        db.query(models.Payment)
        .filter(
            models.Payment.business_id == business_id
        )
    )

    if invoice_id is not None:
        invoice = (
            db.query(models.Invoice)
            .filter(
                models.Invoice.id == invoice_id,
                models.Invoice.business_id == business_id
            )
            .first()
        )

        if invoice is None:
            raise HTTPException(
                status_code=404,
                detail="Invoice not found"
            )

        query = query.filter(
            models.Payment.invoice_id == invoice_id
        )

    if payment_method:
        query = query.filter(
            models.Payment.payment_method == payment_method
        )

    if payment_status == "ACTIVE":
        query = query.filter(
            models.Payment.reversed_at.is_(None)
        )

    elif payment_status == "REVERSED":
        query = query.filter(
            models.Payment.reversed_at.is_not(None)
        )

    if start_date:
        query = query.filter(
            models.Payment.paid_at >= start_date
        )

    if end_date:
        query = query.filter(
            models.Payment.paid_at <= end_date
        )

    total = query.count()

    offset = (page - 1) * page_size

    payments = (
        query
        .order_by(
            models.Payment.paid_at.desc(),
            models.Payment.id.desc()
        )
        .offset(offset)
        .limit(page_size)
        .all()
    )

    total_pages = (
        (total + page_size - 1) // page_size
        if total > 0
        else 0
    )

    return {
        "items": payments,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages
    }

def get_invoice_payments(
    db: Session,
    invoice_id: int,
    business_id: int
):
    invoice = (
        db.query(models.Invoice)
        .filter(
            models.Invoice.id == invoice_id,
            models.Invoice.business_id == business_id
        )
        .first()
    )

    if invoice is None:
        raise HTTPException(
            status_code=404,
            detail="Invoice not found"
        )

    return (
        db.query(models.Payment)
        .filter(
            models.Payment.invoice_id == invoice_id,
            models.Payment.business_id == business_id
        )
        .order_by(
            models.Payment.paid_at.desc()
        )
        .all()
    )
def get_invoice_balance(
    db: Session,
    invoice_id: int,
    business_id: int
):
    invoice = (
        db.query(models.Invoice)
        .filter(
            models.Invoice.id == invoice_id,
            models.Invoice.business_id == business_id,
        )
        .first()
    )

    if invoice is None:
        raise HTTPException(
            status_code=404,
            detail="Invoice not found"
        )

    amount_paid = (
        db.query(models.Payment)
        .filter(
            models.Payment.invoice_id == invoice_id,
            models.Payment.business_id == business_id,
            models.Payment.reversed_at.is_(None)
        )
        .with_entities(
            func.coalesce(
                func.sum(models.Payment.amount),
                0
            )
        )
        .scalar()
    )

    amount_paid = money(amount_paid)

    balance = money(
        invoice.total - amount_paid
    )

    return {
        "invoice_id": invoice.id,
        "invoice_total": money(invoice.total),
        "amount_paid": amount_paid,
        "balance": balance,
        "status": invoice.status
    }

def get_payment_summary(
    db: Session,
    business_id: int,
    start_date: datetime | None = None,
    end_date: datetime | None = None
):
    base_filter = [
        models.Payment.business_id == business_id
    ]

    if start_date is not None:
        base_filter.append(
            models.Payment.paid_at >= start_date
        )

    if end_date is not None:
        base_filter.append(
            models.Payment.paid_at <= end_date
        )

    total_payments = (
        db.query(models.Payment)
        .filter(*base_filter)
        .count()
    )

    total_received = (
        db.query(
            func.coalesce(
                func.sum(models.Payment.amount),
                0
            )
        )
        .filter(*base_filter)
        .scalar()
    )

    total_reversed = (
        db.query(
            func.coalesce(
                func.sum(models.Payment.amount),
                0
            )
        )
        .filter(
            *base_filter,
            models.Payment.reversed_at.is_not(None)
        )
        .scalar()
    )

    active_received = (
        db.query(
            func.coalesce(
                func.sum(models.Payment.amount),
                0
            )
        )
        .filter(
            *base_filter,
            models.Payment.reversed_at.is_(None)
        )
        .scalar()
    )

    return {
        "total_payments": total_payments,
        "total_received": money(total_received),
        "total_reversed": money(total_reversed),
        "active_received": money(active_received)
    }

def get_payment_reversals(
    db: Session,
    business_id: int,
    start_date: datetime | None = None,
    end_date: datetime | None = None
):
    query = (
        db.query(models.Payment)
        .filter(
            models.Payment.business_id == business_id,
            models.Payment.reversed_at.is_not(None)
        )
    )

    if start_date is not None:
        query = query.filter(
            models.Payment.reversed_at >= start_date
        )

    if end_date is not None:
        query = query.filter(
            models.Payment.reversed_at <= end_date
        )

    payments = (
        query
        .order_by(models.Payment.reversed_at.desc())
        .all()
    )

    return payments
        
def get_customer_vehicle_summary(
    db: Session,
    business_id: int,
    customer_id: int
):
    customer = (
        db.query(models.Customer)
        .filter(
            models.Customer.id == customer_id,
            models.Customer.business_id == business_id,
            models.Customer.deleted_at.is_(None)
        )
        .first()
    )

    if customer is None:
        raise HTTPException(
            status_code=404,
            detail="Customer not found"
        )

    vehicles = (
        db.query(models.Vehicle)
        .filter(
            models.Vehicle.business_id == business_id,
            models.Vehicle.customer_id == customer_id,
            models.Vehicle.deleted_at.is_(None)
        )
        .order_by(
            models.Vehicle.created_at.desc(),
            models.Vehicle.id.desc()
        )
        .all()
    )

    return {
        "customer": customer,
        "total_vehicles": len(vehicles),
        "vehicles": vehicles
    }

def get_vehicle_360(
    db: Session,
    business_id: int,
    vehicle_id: int
):
    vehicle = (
        db.query(models.Vehicle)
        .filter(
            models.Vehicle.id == vehicle_id,
            models.Vehicle.business_id == business_id,
            models.Vehicle.deleted_at.is_(None)
        )
        .first()
    )

    if vehicle is None:
        raise HTTPException(
            status_code=404,
            detail="Vehicle not found"
        )

    customer = (
        db.query(models.Customer)
        .filter(
            models.Customer.id == vehicle.customer_id,
            models.Customer.business_id == business_id,
            models.Customer.deleted_at.is_(None)
        )
        .first()
    )

    if customer is None:
        raise HTTPException(
            status_code=404,
            detail="Vehicle owner not found"
        )

    latest_service = (
        db.query(models.ServiceRecord)
        .filter(
            models.ServiceRecord.vehicle_id == vehicle.id,
            models.ServiceRecord.business_id == business_id
        )
        .order_by(
            models.ServiceRecord.service_date.desc(),
            models.ServiceRecord.id.desc()
        )
        .first()
    )

    open_job_card = (
        db.query(models.JobCard)
        .filter(
            models.JobCard.vehicle_id == vehicle.id,
            models.JobCard.business_id == business_id,
            models.JobCard.status.notin_(
                [
                    "COMPLETED",
                    "COLLECTED",
                    "CANCELLED"
                ]
            )
        )
        .order_by(
            models.JobCard.created_at.desc(),
            models.JobCard.id.desc()
        )
        .first()
    )

    payment_totals = (
        db.query(
            models.Payment.invoice_id.label("invoice_id"),
            func.coalesce(
                func.sum(models.Payment.amount),
                0
            ).label("amount_paid")
        )
        .filter(
            models.Payment.business_id == business_id,
            models.Payment.reversed_at.is_(None)
        )
        .group_by(
            models.Payment.invoice_id
        )
        .subquery()
    )

    outstanding_amount = (
        db.query(
            func.coalesce(
                func.sum(
                    models.Invoice.total
                    - func.coalesce(
                        payment_totals.c.amount_paid,
                        0
                    )
                ),
                0
            )
        )
        .join(
            models.Quote,
            models.Invoice.quote_id == models.Quote.id
        )
        .join(
            models.JobCard,
            models.Quote.job_card_id == models.JobCard.id
        )
        .outerjoin(
            payment_totals,
            payment_totals.c.invoice_id
            == models.Invoice.id
        )
        .filter(
            models.Invoice.business_id == business_id,
            models.JobCard.business_id == business_id,
            models.JobCard.vehicle_id == vehicle.id,
            models.Invoice.status.notin_(
                ["PAID", "CANCELLED"]
            )
        )
        .scalar()
    )

    return {
        "vehicle": vehicle,
        "customer": customer,
        "latest_service": latest_service,
        "open_job_card": open_job_card,
        "outstanding_amount": money(
            outstanding_amount or Decimal("0.00")
        )
    }
