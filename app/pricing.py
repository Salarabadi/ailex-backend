# app/pricing.py
from typing import List, Dict

# MVP: قیمت‌های ثابت — بعداً از DB (persona_plan_matrix / source_pricing) خوانده می‌شود
BASE_PRICES_CENTS: Dict[str, Dict[str, int]] = {
    # persona_code -> plan_code -> base price (cents)
    "asset_security": {
        "basic": 0,
        "pro": 0,
        "enterprise": 0,
    }
}

SOURCE_PRICES_CENTS: Dict[str, int] = {
    # منابع رایگان MVP
    "justia": 0,
    "google_scholar": 0,
    "courtlistener": 0,
    "public_records": 0,
}

def compute_quote(persona_code: str, plan_code: str, sources: List[str], coupon_code: str | None = None):
    # پایه
    base = BASE_PRICES_CENTS.get(persona_code, {}).get(plan_code)
    if base is None:
        raise ValueError("Invalid persona/plan")

    # جمع منابع
    add_ons = 0
    items = []
    for s in sources:
        unit = SOURCE_PRICES_CENTS.get(s)
        if unit is None:
            raise ValueError(f"Unknown source: {s}")
        add_ons += unit
        items.append({"type": "source", "code": s, "amount_cents": unit})

    # تخفیف (MVP: فقط نمونه)
    discount_cents = 0
    if coupon_code:
        # مثال: کوپن DEMO10 = ده درصد
        if coupon_code.upper() == "DEMO10":
            discount_cents = round(0.10 * (base + add_ons))

    subtotal = base + add_ons - discount_cents
    tax_cents = 0  # MVP
    total = subtotal + tax_cents

    return {
        "currency": "USD",
        "persona_code": persona_code,
        "plan_code": plan_code,
        "line_items": (
            [{"type": "base", "amount_cents": base}] +
            items +
            ([{"type": "discount", "amount_cents": -discount_cents}] if discount_cents else [])
        ),
        "subtotal_cents": subtotal,
        "tax_cents": tax_cents,
        "total_cents": total,
        "coupon_applied": coupon_code.upper() if coupon_code else None,
    }
