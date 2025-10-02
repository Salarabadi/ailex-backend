# app/seed.py
from app.db import SessionLocal, engine
from app import models
from app.models import Base

# ساخت جدول‌ها اگه نبودند
Base.metadata.create_all(bind=engine)

def run():
    db = SessionLocal()
    try:
        persona = models.Persona(code="asset_security", name="Asset Security")
        db.merge(persona)

        basic = models.Plan(code="basic", name="Basic")
        pro   = models.Plan(code="pro", name="Pro")
        ent   = models.Plan(code="enterprise", name="Enterprise")
        for p in (basic, pro, ent):
            db.merge(p)

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
