from app.db import SessionLocal
from app import models
import uuid

def run():
    db = SessionLocal()

    # Persona
    persona = models.Persona(code="asset_security", name="Asset Security")
    db.merge(persona)

    # Plans
    basic = models.Plan(code="basic", name="Basic")
    pro = models.Plan(code="pro", name="Pro")
    ent = models.Plan(code="enterprise", name="Enterprise")
    db.merge(basic)
    db.merge(pro)
    db.merge(ent)

    # Sources (free for now)
    s1 = models.Source(code="justia", category="events/laws")
    s2 = models.Source(code="google_scholar", category="events/laws")
    s3 = models.Source(code="courtlistener", category="events/laws")
    s4 = models.Source(code="public_records", category="person/entity")

    for s in [s1, s2, s3, s4]:
        db.merge(s)

    db.commit()
    db.close()
    print("✅ Seed data inserted")

if __name__ == "__main__":
    run()
