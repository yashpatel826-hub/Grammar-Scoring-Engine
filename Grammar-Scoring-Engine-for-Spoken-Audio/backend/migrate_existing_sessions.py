"""
One-time migration script to backfill analytics fields in existing analysis_history documents.

This script adds:
- audio_duration_seconds: extracted from existing analysis.duration field (default 0.0)
- error_breakdown: extracted from error_summary or defaulted to zeros

Run this script once to prepare the database for analytics:
    python migrate_existing_sessions.py
"""

from datetime import datetime
from typing import Any, Dict, Optional
from pymongo import MongoClient
from config import MONGO_URI, MONGO_DB_NAME


def parse_error_summary(error_summary: Optional[Dict[str, Any]]) -> Dict[str, int]:
    """
    Extract error_breakdown from error_summary or return defaults.
    
    This parses the existing error analysis structure and maps errors to categories:
    - article_error → articles
    - tense_error → tense
    - preposition_error → preposition
    - verb_agreement_error → agreement
    - All others → other
    
    Args:
        error_summary: Error summary dict from existing analysis
        
    Returns:
        Dict with keys: articles, tense, preposition, agreement, other
    """
    breakdown = {
        "articles": 0,
        "tense": 0,
        "preposition": 0,
        "agreement": 0,
        "other": 0
    }
    
    if not error_summary or not isinstance(error_summary, dict):
        return breakdown
    
    # Map error types to categories
    for error_type, count in error_summary.items():
        if isinstance(count, int) and count > 0:
            if error_type == "article_error":
                breakdown["articles"] += count
            elif error_type == "tense_error":
                breakdown["tense"] += count
            elif error_type == "preposition_error":
                breakdown["preposition"] += count
            elif error_type == "verb_agreement_error":
                breakdown["agreement"] += count
            elif error_type != "total_errors":  # Skip the total
                breakdown["other"] += count
    
    return breakdown


def migrate_sessions():
    """
    Backfill audio_duration_seconds and error_breakdown fields.
    
    Modifies existing documents in-place:
    - If field exists, leaves it unchanged
    - If field missing, adds with default value
    """
    if not MONGO_URI.strip():
        print("ERROR: MONGO_URI not configured in config.py")
        print("Set MONGO_URI environment variable or update config.py")
        return False
    
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=3000)
        client.admin.command("ping")
        db = client[MONGO_DB_NAME]
        
        print(f"\nConnected to MongoDB: {MONGO_DB_NAME}")
        print("=" * 60)
        
        # Count documents
        total_docs = db.analyses.count_documents({})
        print(f"Total analyses documents: {total_docs}")
        
        if total_docs == 0:
            print("No documents to migrate.")
            return True
        
        # Migrate: add missing audio_duration_seconds
        result_duration = db.analyses.update_many(
            {"audio_duration_seconds": {"$exists": False}},
            [{
                "$set": {
                    "audio_duration_seconds": {
                        "$cond": {
                            "if": {"$isNumber": "$analysis.duration"},
                            "then": "$analysis.duration",
                            "else": 0.0
                        }
                    }
                }
            }]
        )
        
        print(f"\nAudio duration field:")
        print(f"  Updated: {result_duration.modified_count}")
        print(f"  Matched: {result_duration.matched_count}")
        
        # Migrate: add missing error_breakdown
        # This is more complex, so we'll do it document-by-document
        cursor = db.analyses.find(
            {"error_breakdown": {"$exists": False}},
            {"analysis.error_summary": 1}
        )
        
        updated_count = 0
        for doc in cursor:
            error_summary = doc.get("analysis", {}).get("error_summary", {})
            error_breakdown = parse_error_summary(error_summary)
            
            db.analyses.update_one(
                {"_id": doc["_id"]},
                {"$set": {"error_breakdown": error_breakdown}}
            )
            updated_count += 1
        
        print(f"\nError breakdown field:")
        print(f"  Updated: {updated_count}")
        
        # Verify
        missing_duration = db.analyses.count_documents({
            "audio_duration_seconds": {"$exists": False}
        })
        missing_breakdown = db.analyses.count_documents({
            "error_breakdown": {"$exists": False}
        })
        
        print(f"\nVerification:")
        print(f"  Documents missing audio_duration_seconds: {missing_duration}")
        print(f"  Documents missing error_breakdown: {missing_breakdown}")
        
        print("\n" + "=" * 60)
        print("Migration completed successfully!")
        return True
        
    except Exception as e:
        print(f"\nERROR during migration: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if 'client' in locals():
            client.close()


if __name__ == "__main__":
    print("\nGrammar Scoring Engine - Analytics Migration")
    print("=" * 60)
    print("This script backfills analytics fields in existing sessions.")
    print()
    
    success = migrate_sessions()
    exit(0 if success else 1)
