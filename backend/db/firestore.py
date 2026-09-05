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

# Try importing google.cloud.firestore first (lightweight, ~50MB, no google-api-python-client)
# If not found, try firebase_admin.
_FIREBASE_AVAILABLE = True
try:
    from google.cloud import firestore as fs
    from google.oauth2 import service_account
    _MODE = "google_cloud"
except ImportError:
    try:
        import firebase_admin
        from firebase_admin import credentials, firestore as fs
        _MODE = "firebase_admin"
    except ImportError:
        _FIREBASE_AVAILABLE = False
        _MODE = "none"
        logger.warning("Neither google-cloud-firestore nor firebase_admin installed; Firestore calls will no-op.")


_db = None


def get_db():
    """Lazy-initialize and return the Firestore client."""
    global _db
    if _db is not None:
        return _db

    if not _FIREBASE_AVAILABLE or _MODE == "none":
        raise RuntimeError("Neither google-cloud-firestore nor firebase-admin is installed.")

    project_id = os.getenv("FIRESTORE_PROJECT_ID")
    cred_json = os.getenv("FIREBASE_CREDENTIALS_JSON") or os.getenv("FIREBASE_SERVICE_ACCOUNT_KEY")
    cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

    cred_dict = None
    if cred_json:
        import json
        try:
            cred_dict = json.loads(cred_json)
        except Exception:
            import base64
            cred_dict = json.loads(base64.b64decode(cred_json).decode("utf-8"))

    if _MODE == "google_cloud":
        from google.oauth2 import service_account
        if cred_dict:
            creds = service_account.Credentials.from_service_account_info(cred_dict)
            _db = fs.Client(project=project_id or cred_dict.get("project_id"), credentials=creds)
        elif cred_path and os.path.exists(cred_path):
            _db = fs.Client.from_service_account_json(cred_path, project=project_id)
        else:
            local_fallback = os.path.join(os.getcwd(), "rev-gaurd-firebase-adminsdk-fbsvc-6a7b4f0363.json")
            if os.path.exists(local_fallback):
                _db = fs.Client.from_service_account_json(local_fallback, project=project_id)
            else:
                _db = fs.Client(project=project_id)
        return _db

    # Fallback for firebase_admin
    if not firebase_admin._apps:
        cred = None
        if cred_dict:
            cred = credentials.Certificate(cred_dict)
        elif cred_path and os.path.exists(cred_path):
            cred = credentials.Certificate(cred_path)
        else:
            local_fallback = os.path.join(os.getcwd(), "rev-gaurd-firebase-adminsdk-fbsvc-6a7b4f0363.json")
            if os.path.exists(local_fallback):
                cred = credentials.Certificate(local_fallback)
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
