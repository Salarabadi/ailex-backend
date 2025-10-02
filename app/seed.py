# app/seed.py
from app.db import SessionLocal
from app import models


# <-- این خط، جدول‌ها را اگر نبودند می‌سازد
Base.metadata.create_all(bind=engine)


def run():
    db = SessionLocal()
    try:
        # ---- Persona ----
        persona = models.Persona(code="asset_security", name="Asset Security")
        db.merge(persona)

        # ---- Plans ----
        basic = models.Plan(code="basic", name="Basic")
        pro   = models.Plan(code="pro",   name="Pro")
        ent   = models.Plan(code="enterprise", name="Enterprise")
        db.merge(basic); db.merge(pro); db.merge(ent)

        # ---- Persona × Plan Matrix (قیمت پایه MVP صفر؛ بعداً از ادمین تنظیم می‌کنیم) ----
        # اگر مدل PersonaPlanMatrix داری و می‌خوای مقدار نمونه هم داشته باشی، این بخش رو باز کن:
        # from sqlalchemy import select
        # p = db.execute(select(models.Persona).where(models.Persona.code=="asset_security")).scalar_one()
        # for pl in (basic, pro, ent):
        #     ppm = models.PersonaPlanMatrix(persona_id=p.id, plan_id=pl.id,
        #                                    base_price_cents=0, included_reports=0)
        #     db.merge(ppm)

        # ---- Sources (همه رایگان برای MVP) ----
        s1 = models.Source(code="justia",          category="events/laws",  status="active")
        s2 = models.Source(code="google_scholar",  category="events/laws",  status="active")
        s3 = models.Source(code="courtlistener",   category="events/laws",  status="active")
        s4 = models.Source(code="public_records",  category="person/entity", status="active")
        for s in (s1, s2, s3, s4):
            db.merge(s)

        db.commit()
        print("✅ Seed data inserted/updated successfully.")
    except Exception as e:
        db.rollback()
        print("❌ Seed failed:", e)
        raise
    finally:
        db.close()

if __name__ == "__main__":
    run()
