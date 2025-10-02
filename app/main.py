from fastapi import FastAPI
import os

app = FastAPI(title="Ailex API")

@app.get("/healthz")
def healthcheck():
    return {"status": "ok", "env": os.getenv("APP_ENV", "dev")}

@app.get("/")
def root():
    return {"message": "Welcome to Ailex API"}
