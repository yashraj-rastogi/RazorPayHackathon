"""
RevGuard — Metrics Router.
GET /api/v1/metrics — returns the latest evaluation_run document.
This is separate from /dashboard/summary which uses live case data.
"""

from fastapi import APIRouter, HTTPException
from backend.db.firestore import query_collection

router = APIRouter(prefix="/api/v1", tags=["metrics"])


@router.get("/metrics")
async def get_metrics():
    """
    Returns the latest evaluation run from the evaluation_runs collection.
    This is powered by evaluation/evaluate.py — not live case queries.
    """
    runs = query_collection(
        "evaluation_runs",
        order_by="created_at",
        descending=True,
        limit=1,
    )
    if not runs:
        raise HTTPException(
            status_code=404,
            detail="No evaluation runs found. Run: python evaluation/evaluate.py first."
        )
    return runs[0]
