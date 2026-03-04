"""FastAPI application entry point."""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import router

app = FastAPI(
    title="FinSight Lite API",
    description="Anomaly detection pipeline for banking transactions",
    version="1.0.0",
)

_default_origins = ["http://localhost:3000", "http://localhost:5173"]
_extra = os.environ.get("CORS_ORIGINS", "")
_origins = _default_origins + [o.strip() for o in _extra.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/")
def root():
    return {
        "service": "FinSight Lite API",
        "docs": "/docs",
        "health": "/health",
        "frontend": "http://localhost:3000",
    }


@app.get("/health")
def health():
    return {"status": "healthy"}
