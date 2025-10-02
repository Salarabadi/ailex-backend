# app/main.py
from fastapi import FastAPI
import os

from app.db import engine, Base, SessionLocal
from app import models  # مهم: برای register شدن مدل‌ها
# ── ایجاد جداول در استارتاپ (idempotent) ──
def _create_tables():
    Base.metadata.create_all(bind=engine)

app = FastAPI(title="Ailex API")

@app.on_event("startup")
def on_startup():
    _create_tables()

@app.get("/healthz")
def healthcheck():
    return {"status": "ok", "env": os.getenv("APP_ENV", "dev")}

# ── Endpoints ساده برای تست داده‌های Seed ──
@app.get("/personas")
def get_personas():
    db = SessionLocal()
    try:
        rows = db.query(models.Persona).all()
        return [{"id": str(r.id), "code": r.code, "name": r.name} for r in rows]
    finally:
        db.close()

@app.get("/plans")
def get_plans():
    db = SessionLocal()
    try:
        rows = db.query(models.Plan).all()
        return [{"id": str(r.id), "code": r.code, "name": r.name} for r in rows]
    finally:
        db.close()

@app.get("/sources")
def get_sources():
    db = SessionLocal()
    try:
        rows = db.query(models.Source).all()
        return [{"id": str(r.id), "code": r.code, "category": r.category, "status": r.status} for r in rows]
    finally:
        db.close()

@app.get("/")
def root():
    return {"message": "Welcome to Ailex API"}




# app/main.py (افزودنی‌ها)
from pydantic import BaseModel, Field
from typing import List, Optional
import os

from app.pricing import compute_quote
import stripe

STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")  # بعداً در Render ستش می‌کنی
if STRIPE_SECRET_KEY:
    stripe.api_key = STRIPE_SECRET_KEY

# ---------- Schemas ----------
class QuoteRequest(BaseModel):
    persona_code: str = Field(..., examples=["asset_security"])
    plan_code: str = Field(..., examples=["basic", "pro", "enterprise"])
    sources: List[str] = Field(default_factory=list, examples=[["justia","google_scholar"]])
    coupon_code: Optional[str] = Field(default=None, examples=["DEMO10"])

class QuoteResponse(BaseModel):
    currency: str
    persona_code: str
    plan_code: str
    line_items: List[dict]
    subtotal_cents: int
    tax_cents: int
    total_cents: int
    coupon_applied: Optional[str] = None

class CheckoutRequest(BaseModel):
    persona_code: str
    plan_code: str
    sources: List[str] = []
    coupon_code: Optional[str] = None
    # ایمیل اختیاری؛ اگر Stripe داشته باشیم برای رسید تست مفیده
    customer_email: Optional[str] = None

class CheckoutResponse(BaseModel):
    provider: str
    mode: str
    amount_cents: int
    currency: str
    # اگر Stripe فعال باشد:
    client_secret: Optional[str] = None
    payment_intent_id: Optional[str] = None
    # اگر Stripe فعال نباشد (حالت Mock):
    mock_paid: Optional[bool] = None

# ---------- Endpoints ----------
@app.post("/quote", response_model=QuoteResponse)
def post_quote(body: QuoteRequest):
    q = compute_quote(
        persona_code=body.persona_code,
        plan_code=body.plan_code,
        sources=body.sources,
        coupon_code=body.coupon_code,
    )
    return q

@app.post("/checkout", response_model=CheckoutResponse)
def post_checkout(body: CheckoutRequest):
    q = compute_quote(
        persona_code=body.persona_code,
        plan_code=body.plan_code,
        sources=body.sources,
        coupon_code=body.coupon_code,
    )

    # اگر کلید Stripe موجود بود: PaymentIntent بساز
    if STRIPE_SECRET_KEY:
        intent = stripe.PaymentIntent.create(
            amount=q["total_cents"],
            currency=q["currency"].lower(),
            receipt_email=body.customer_email,
            automatic_payment_methods={"enabled": True},
            metadata={
                "persona": body.persona_code,
                "plan": body.plan_code,
                "sources": ",".join(body.sources),
                "coupon": body.coupon_code or "",
            },
        )
        return CheckoutResponse(
            provider="stripe",
            mode="payment_intent",
            amount_cents=q["total_cents"],
            currency=q["currency"],
            client_secret=intent.client_secret,
            payment_intent_id=intent.id,
        )

    # حالت Mock (بدون Stripe) – برای تست UI
    return CheckoutResponse(
        provider="mock",
        mode="simulate",
        amount_cents=q["total_cents"],
        currency=q["currency"],
        mock_paid=True,
    )
