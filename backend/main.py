from fastapi import FastAPI
from routes import businesses
from routes import customers
from routes import vehicles
from routes import service_records
from routes import job_cards
from routes import quotes
from routes import users
from routes import auth
from routes import onboarding
from routes import invoices
from routes import dashboard
from routes import reports
from routes import payments

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="HRN Cloud AutoVault API",
    version="1.0.0")

app.include_router(
    businesses.router
    )
app.include_router(
    customers.router
    )
app.include_router(
    vehicles.router
)
app.include_router(
    service_records.router
)
app.include_router(
    job_cards.router
)

app.include_router(
    quotes.router
)
app.include_router(
    users.router
)

app.include_router(
    auth.router
)
app.include_router(
    onboarding.router
)
app.include_router(
    invoices.router
)
app.include_router(
    dashboard.router
)
app.include_router(
    reports.router
)
app.include_router(
    payments.router
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

@app.get("/")
def root ():
    return {"product": "HRN Cloud AutoVault",
             "status": "running",
             "version": "0.1.0"}

@app.get("/health")
def healthCheck():
    return {"status": "healthy"}
