from fastapi import FastAPI
import os

app = FastAPI(title="Ailex API")


# --- create tables on startup (safe if not exists) ---
@app.on_event("startup")
def create_tables_if_needed():
    Base.metadata.create_all(bind=engine)
# -----------------------------------------------------


@app.get("/healthz")
def healthcheck():
    return {"status": "ok", "env": os.getenv("APP_ENV", "dev")}

@app.get("/")
def root():
    return {"message": "Welcome to Ailex API"}
