"""
RevGuard — Firestore client wrapper.

In real usage, set GOOGLE_APPLICATION_CREDENTIALS env var to your
service account JSON, or use Firebase Admin SDK with explicit credentials.
"""

import os
import logging
from datetime import datetime, timezone
from typing import Optional, Any

logger = logging.getLogger(__name__)

# Try to import Firebase Admin; fall back gracefully for unit tests
try:
    import firebase_admin
    from firebase_admin import credentials, firestore as fs
    _FIREBASE_AVAILABLE = True
except ImportError:
    _FIREBASE_AVAILABLE = False
    logger.warning("firebase_admin not installed; Firestore calls will no-op.")


_db = None


def get_db():
    """Lazy-initialize and return the Firestore client."""
    global _db
    if _db is not None:
        return _db

    if not _FIREBASE_AVAILABLE:
        raise RuntimeError("firebase_admin is not installed. Run: pip install firebase-admin")

    if not firebase_admin._apps:
        project_id = os.getenv("FIRESTORE_PROJECT_ID")
        cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

        if cred_path and os.path.exists(cred_path):
            cred = credentials.Certificate(cred_path)
        else:
            cred = credentials.ApplicationDefault()

        firebase_admin.initialize_app(cred, {"projectId": project_id})

    _db = fs.client()
    return _db


# ─── Generic Helpers ─────────────────────────────────────────────

def doc_to_dict(doc) -> Optional[dict]:
    """Convert a Firestore DocumentSnapshot to dict, or None if missing."""
    if not doc.exists:
        return None
    d = doc.to_dict()
    d["_id"] = doc.id
    return d


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def collection(name: str):
    return get_db().collection(name)


# ─── CRUD helpers ────────────────────────────────────────────────

def set_document(collection_name: str, doc_id: str, data: dict) -> None:
    collection(collection_name).document(doc_id).set(data)


def get_document(collection_name: str, doc_id: str) -> Optional[dict]:
    doc = collection(collection_name).document(doc_id).get()
    return doc_to_dict(doc)


def update_document(collection_name: str, doc_id: str, data: dict) -> None:
    data["updated_at"] = now_utc().isoformat()
    collection(collection_name).document(doc_id).update(data)


def query_collection(
    collection_name: str,
    filters: Optional[list[tuple]] = None,
    order_by: Optional[str] = None,
    descending: bool = False,
    limit: int = 100,
) -> list[dict]:
    """
    Query a collection with optional filters.
    filters = [(field, op, value), ...]
    """
    ref = collection(collection_name)
    if filters:
        for field, op, value in filters:
            ref = ref.where(field, op, value)
    if order_by:
        direction = fs.Query.DESCENDING if descending else fs.Query.ASCENDING
        ref = ref.order_by(order_by, direction=direction)
    ref = ref.limit(limit)
    return [doc_to_dict(d) for d in ref.stream()]
