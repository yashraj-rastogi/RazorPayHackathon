"""
RevGuard — Events Router.
POST /api/v1/events        — ingest one event
POST /api/v1/events/seed   — seed synthetic dataset (dev only)
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from backend.models.event import NormalizedRevenueEvent
from backend.services.ingestion import ingest_event

router = APIRouter(prefix="/api/v1/events", tags=["events"])


class SeedRequest(BaseModel):
    count: int = 250
    dataset_version: str = "v1"
    seed: int = 42


@router.post("", status_code=status.HTTP_201_CREATED)
async def ingest(event: NormalizedRevenueEvent):
    """Ingest one revenue failure event. Idempotent on event_id."""
    try:
        result = ingest_event(event)
        if result["is_duplicate"]:
            return {
                "status": "duplicate",
                "case_id": result["case_id"],
                "message": "Duplicate event — existing case returned.",
            }
        return {
            "status": "created",
            "case_id": result["case_id"],
            "policy_decision": result["policy_decision"],
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/seed", status_code=status.HTTP_201_CREATED)
async def seed_dataset(req: SeedRequest):
    """
    Seed synthetic events from the generator.
    Development/demo only — protect this endpoint in production.
    """
    try:
        import sys
        sys.path.insert(0, ".")
        from data.generator import generate
        events, _ = generate(req.seed, req.count)

        created = 0
        duplicates = 0
        errors = 0

        for e_dict in events:
            # Strip _meta field — not part of schema
            meta = e_dict.pop("_meta", {})
            try:
                event = NormalizedRevenueEvent(**e_dict)
                result = ingest_event(event)
                if result["is_duplicate"]:
                    duplicates += 1
                else:
                    created += 1
            except Exception as exc:
                import logging
                logging.getLogger(__name__).error(f"Error seeding event {e_dict.get('event_id')}: {exc}")
                errors += 1

        return {
            "status": "seeded",
            "dataset_version": req.dataset_version,
            "seed": req.seed,
            "records_created": created,
            "duplicates_blocked": duplicates,
            "errors": errors,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
