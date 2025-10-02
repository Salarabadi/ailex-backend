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
