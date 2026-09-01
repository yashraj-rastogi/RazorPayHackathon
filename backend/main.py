"""
RevGuard — FastAPI Application Entry Point.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend import config
from backend.routers import events, cases, dashboard, webhooks, metrics, simulate

app = FastAPI(
    title="RevGuard API",
    description="AI-powered recovery controller for failed recurring payments.",
    version="1.0.0",
)

# ─── CORS ─────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Routers ──────────────────────────────────────────────────────
app.include_router(events.router)
app.include_router(cases.router)
app.include_router(dashboard.router)
app.include_router(webhooks.router)
app.include_router(metrics.router)
app.include_router(simulate.router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "revguard-api"}


@app.get("/")
async def root():
    return {
        "service": "RevGuard",
        "version": "1.0.0",
        "docs": "/docs",
    }
