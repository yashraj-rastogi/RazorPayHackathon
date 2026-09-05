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
    allow_origin_regex=r"https://.*\.vercel\.app|http://localhost(:\d+)?",
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


from fastapi import Request
from backend.routers.webhooks import twilio_reply_webhook


@app.get("/")
async def root():
    return {
        "service": "RevGuard",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.post("/")
async def root_post_handler(request: Request):
    """
    Handle POST / directly.
    If Twilio sends webhook to the root ngrok URL instead of /api/v1/webhooks/twilio-reply,
    delegate directly to twilio_reply_webhook so inbound replies are never lost.
    """
    return await twilio_reply_webhook(request)
