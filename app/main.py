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





# --- Stripe Checkout (FastAPI) ---
import os, stripe
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

CHECKOUT_SUCCESS_URL = os.getenv("CHECKOUT_SUCCESS_URL", "https://ailex.phiogre.com/success")
CHECKOUT_CANCEL_URL  = os.getenv("CHECKOUT_CANCEL_URL",  "https://ailex.phiogre.com/cancel")

class CheckoutCreateBody(BaseModel):
    amount_cents: int              # مبلغ به سنت (مثلاً 2000 برای $20)
    product_name: str = "Ailex Plan"
    quantity: int = 1
    customer_email: str | None = None

@router.post("/create-checkout")
def create_checkout(body: CheckoutCreateBody):
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "usd",
                    "product_data": {"name": body.product_name},
                    "unit_amount": body.amount_cents,
                },
                "quantity": body.quantity,
            }],
            mode="payment",
            success_url=CHECKOUT_SUCCESS_URL + "?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=CHECKOUT_CANCEL_URL,
            customer_email=body.customer_email,
        )
        return {"id": session.id, "url": session.url}
    except Exception as e:
        # برای اینکه در پرو‌د خطای 500 نگیریم
        raise HTTPException(status_code=400, detail=str(e))

# اگر قبلاً app = FastAPI() داری، مطمئن شو این روتر mount بشه:
# app.include_router(router)







from fastapi import Request

STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")  # بعداً از Stripe Dashboard می‌گیری

@router.post("/stripe/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig = request.headers.get("stripe-signature")

    try:
        if STRIPE_WEBHOOK_SECRET:
            event = stripe.Webhook.construct_event(
                payload, sig, STRIPE_WEBHOOK_SECRET
            )
        else:
            # فقط برای توسعه؛ در prod حتماً از secret استفاده کن
            event = stripe.Event.construct_from(await request.json(), stripe.api_key)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        # TODO: اینجا اشتراک/سفارش را Paid کن، در DB ثبت کن و ایمیل بفرست
        print("✅ Paid session:", session.get("id"))

    return {"ok": True}





from fastapi import FastAPI
from app import payment

app = FastAPI()

# اضافه کردن روت‌های پرداخت
app.include_router(payment.router)
