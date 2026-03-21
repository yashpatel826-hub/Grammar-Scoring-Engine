"""
MongoDB persistence layer for auth and analysis history.
"""

from __future__ import annotations

import hashlib
import secrets
from datetime import datetime
from typing import Any, Dict, List, Optional

from pymongo import ASCENDING, DESCENDING, MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

from config import MONGO_DB_NAME, MONGO_URI


_client: Optional[MongoClient] = None
_db: Optional[Database] = None


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def _hash_password(password: str, salt: Optional[str] = None) -> str:
    chosen_salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        chosen_salt.encode("utf-8"),
        100_000,
    ).hex()
    return f"{chosen_salt}${digest}"


def _verify_password(password: str, stored_hash: str) -> bool:
    try:
        salt, _ = stored_hash.split("$", 1)
    except ValueError:
        return False
    return secrets.compare_digest(_hash_password(password, salt), stored_hash)


def get_database() -> Optional[Database]:
    global _client, _db

    if _db is not None:
        return _db

    if not MONGO_URI.strip():
        return None

    try:
        _client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=3000)
        _client.admin.command("ping")
        _db = _client[MONGO_DB_NAME]

        _db.users.create_index([("email", ASCENDING)], unique=True)
        _db.analyses.create_index([("email", ASCENDING), ("createdAt", DESCENDING)])

        return _db
    except Exception:
        _client = None
        _db = None
        return None


def is_db_available() -> bool:
    return get_database() is not None


def _users_col(db: Database) -> Collection:
    return db.users


def _analyses_col(db: Database) -> Collection:
    return db.analyses


def create_user(name: str, email: str, password: str) -> Dict[str, Any]:
    db = get_database()
    if db is None:
        return {"success": False, "error": "MongoDB is not configured or reachable."}

    normalized_email = _normalize_email(email)
    clean_name = name.strip()

    if not clean_name:
        return {"success": False, "error": "Name is required."}

    if len(password) < 8:
        return {"success": False, "error": "Password must be at least 8 characters."}

    existing = _users_col(db).find_one({"email": normalized_email}, {"_id": 1})
    if existing:
        return {"success": False, "error": "Email already registered."}

    now = datetime.utcnow().isoformat()
    _users_col(db).insert_one(
        {
            "name": clean_name,
            "email": normalized_email,
            "passwordHash": _hash_password(password),
            "createdAt": now,
            "updatedAt": now,
        }
    )

    return {
        "success": True,
        "user": {
            "name": clean_name,
            "email": normalized_email,
        },
    }


def authenticate_user(email: str, password: str) -> Dict[str, Any]:
    db = get_database()
    if db is None:
        return {"success": False, "error": "MongoDB is not configured or reachable."}

    normalized_email = _normalize_email(email)
    user_doc = _users_col(db).find_one({"email": normalized_email})
    if not user_doc:
        return {"success": False, "error": "Invalid email or password."}

    stored_hash = user_doc.get("passwordHash", "")
    if not _verify_password(password, stored_hash):
        return {"success": False, "error": "Invalid email or password."}

    return {
        "success": True,
        "user": {
            "name": user_doc.get("name", ""),
            "email": user_doc.get("email", normalized_email),
        },
    }


def save_analysis(email: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
    db = get_database()
    if db is None:
        return {"success": False, "error": "MongoDB is not configured or reachable."}

    normalized_email = _normalize_email(email)
    created_at = datetime.utcnow().isoformat()
    record = {
        "email": normalized_email,
        "createdAt": created_at,
        "analysis": analysis,
    }
    inserted = _analyses_col(db).insert_one(record)

    response_record = {
        **analysis,
        "id": str(inserted.inserted_id),
        "createdAt": created_at,
    }
    return {"success": True, "record": response_record}


def get_analysis_history(email: str, limit: int = 100) -> List[Dict[str, Any]]:
    db = get_database()
    if db is None:
        return []

    normalized_email = _normalize_email(email)
    cursor = (
        _analyses_col(db)
        .find({"email": normalized_email})
        .sort("createdAt", DESCENDING)
        .limit(max(1, min(limit, 300)))
    )

    history: List[Dict[str, Any]] = []
    for doc in cursor:
        analysis = doc.get("analysis", {})
        history.append(
            {
                **analysis,
                "id": str(doc.get("_id")),
                "createdAt": doc.get("createdAt"),
            }
        )

    return history