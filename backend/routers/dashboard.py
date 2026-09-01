"""
RevGuard — Dashboard Router.
GET /api/v1/dashboard/summary — live financial and policy summary from Firestore.
"""

from fastapi import APIRouter
from backend.db.firestore import query_collection

router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])


@router.get("/summary")
async def dashboard_summary():
    """
    Returns live summary computed from Firestore recovery_cases collection.
    NOT from evaluation_run — those are two separate data sources.
    """
    all_cases = query_collection("recovery_cases", limit=1000)

    # Revenue at risk = sum of amounts for non-CLOSED, non-RECOVERED cases
    revenue_at_risk = 0
    revenue_recovered = 0
    recovered_count = 0
    recoverable_count = 0

    policy_counts = {"auto": 0, "review": 0, "blocked": 0}
    root_causes: dict[str, int] = {}

    for case in all_cases:
        amount = case.get("amount", 0)
        policy = (case.get("policy") or {}).get("decision", "")
        status = case.get("status", "")
        diagnosis = case.get("diagnosis") or {}
        bucket = diagnosis.get("bucket", "unknown")

        # Root cause counting
        root_causes[bucket] = root_causes.get(bucket, 0) + 1

        # Policy counts
        if policy == "AUTO":
            policy_counts["auto"] += 1
        elif policy == "QUEUE_FOR_REVIEW":
            policy_counts["review"] += 1
        elif policy == "BLOCKED":
            policy_counts["blocked"] += 1

        # Revenue tracking
        if status == "RECOVERED":
            revenue_recovered += amount
            recovered_count += 1
        if status not in ("CLOSED",):
            revenue_at_risk += amount
            if policy in ("AUTO", "QUEUE_FOR_REVIEW"):
                recoverable_count += 1

    recovery_rate = round(recovered_count / max(recoverable_count, 1), 3)
    total_cases = len(all_cases)

    return {
        "revenue_at_risk": revenue_at_risk,
        "revenue_at_risk_rupees": round(revenue_at_risk / 100, 2),
        "revenue_recovered": revenue_recovered,
        "revenue_recovered_rupees": round(revenue_recovered / 100, 2),
        "recovery_rate": recovery_rate,
        "total_cases": total_cases,
        "cases": policy_counts,
        "root_causes": root_causes,
    }
