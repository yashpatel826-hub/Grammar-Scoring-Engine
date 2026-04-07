"""
FastAPI router for Analytics endpoints.
Endpoints for dashboard data retrieval and analysis.
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Query, Header
from pymongo.database import Database

from database import get_database
from analytics_helpers import (
    calculate_streak,
    calculate_improvement_pct,
    calculate_peak_time,
    generate_recommendations
)


router = APIRouter(prefix="/api/analytics", tags=["analytics"])


def get_user_email_from_header(authorization: Optional[str] = Header(None)) -> str:
    """
    Extract user email from Authorization header.
    
    For now, the app uses localStorage with user email stored directly.
    In a production environment, this would validate a JWT token.
    
    Args:
        authorization: Authorization header (not currently used)
        
    Returns:
        str: User email
        
    Raises:
        HTTPException: If user is not authenticated
    """
    # For now, we receive email from frontend in query params or headers
    # This is handled by the endpoint passing user email directly
    # In production, extract from JWT token in the header
    raise HTTPException(status_code=401, detail="User not authenticated")


@router.get("/summary")
async def analytics_summary(email: str = Query(..., min_length=3)):
    """
    Get summary analytics for the user.
    
    Returns:
    - current_score: Most recent session score
    - avg_7day: Average score last 7 days
    - avg_30day: Average score last 30 days
    - improvement_pct: This week vs last week percentage change
    - total_sessions: Total number of sessions
    - total_speaking_minutes: Total speaking time from all sessions
    - current_streak: Consecutive days with sessions
    - best_session: Best session with score and date
    - peak_time: Time of day with best performance
    """
    db = get_database()
    if db is None:
        raise HTTPException(status_code=503, detail="Database not available")
    
    normalized_email = email.strip().lower()
    
    # Get all sessions for this user
    cursor = db.analyses.find(
        {"email": normalized_email},
        {
            "createdAt": 1,
            "analysis.score": 1,
            "analysis.duration": 1
        }
    ).sort("createdAt", -1)
    
    sessions = list(cursor)
    
    if not sessions:
        return {
            "current_score": 0,
            "avg_7day": 0,
            "avg_30day": 0,
            "improvement_pct": 0,
            "total_sessions": 0,
            "total_speaking_minutes": 0,
            "current_streak": 0,
            "best_session": None,
            "peak_time": "morning"
        }
    
    # Current score (most recent)
    current_score = sessions[0].get("analysis", {}).get("score", 0)
    
    # Calculate date ranges
    now = datetime.utcnow()
    seven_days_ago = now - timedelta(days=7)
    thirty_days_ago = now - timedelta(days=30)
    
    # Calculate averages for date ranges
    sessions_7day = [
        s for s in sessions
        if _parse_datetime(s.get("createdAt")) >= seven_days_ago
    ]
    sessions_30day = [
        s for s in sessions
        if _parse_datetime(s.get("createdAt")) >= thirty_days_ago
    ]
    
    avg_7day = sum(
        s.get("analysis", {}).get("score", 0) for s in sessions_7day
    ) / len(sessions_7day) if sessions_7day else 0
    
    avg_30day = sum(
        s.get("analysis", {}).get("score", 0) for s in sessions_30day
    ) / len(sessions_30day) if sessions_30day else 0
    
    # Total sessions and speaking minutes
    total_sessions = len(sessions)
    total_speaking_minutes = sum(
        s.get("analysis", {}).get("duration", 0) for s in sessions
    ) / 60
    
    # Streak
    streak = calculate_streak(normalized_email, db)
    
    # Best session
    best_session_data = max(
        sessions,
        key=lambda s: s.get("analysis", {}).get("score", 0)
    )
    best_score = best_session_data.get("analysis", {}).get("score", 0)
    best_date = best_session_data.get("createdAt", "")
    
    best_session = {
        "score": best_score,
        "date": best_date,
        "session_id": str(best_session_data.get("_id", ""))
    } if best_session_data else None
    
    # Peak time
    peak_time = calculate_peak_time(normalized_email, db)
    
    # Improvement percentage
    improvement_pct = calculate_improvement_pct(normalized_email, db)
    
    return {
        "current_score": round(current_score, 2),
        "avg_7day": round(avg_7day, 2),
        "avg_30day": round(avg_30day, 2),
        "improvement_pct": improvement_pct,
        "total_sessions": total_sessions,
        "total_speaking_minutes": round(total_speaking_minutes, 2),
        "current_streak": streak,
        "best_session": best_session,
        "peak_time": peak_time
    }


@router.get("/score-trend")
async def score_trend(email: str = Query(..., min_length=3), days: int = Query(30, ge=1, le=365)):
    """
    Get score trend data for the past N days.
    
    Returns: List of {date, score} sorted by date ascending.
    If multiple sessions on same day, returns average score.
    """
    db = get_database()
    if db is None:
        raise HTTPException(status_code=503, detail="Database not available")
    
    normalized_email = email.strip().lower()
    
    # Date range
    now = datetime.utcnow()
    start_date = now - timedelta(days=days)
    
    # Get sessions in date range
    cursor = db.analyses.find({
        "email": normalized_email,
        "createdAt": {
            "$gte": start_date.isoformat(),
            "$lte": now.isoformat()
        }
    }, {
        "createdAt": 1,
        "analysis.score": 1
    }).sort("createdAt", 1)
    
    sessions = list(cursor)
    
    # Group by date
    date_scores: Dict[str, List[float]] = {}
    for session in sessions:
        created_at = _parse_datetime(session.get("createdAt"))
        date_key = created_at.strftime("%Y-%m-%d")
        score = session.get("analysis", {}).get("score", 0)
        
        if date_key not in date_scores:
            date_scores[date_key] = []
        date_scores[date_key].append(score)
    
    # Calculate averages and build result
    result = []
    for date_key in sorted(date_scores.keys()):
        avg_score = sum(date_scores[date_key]) / len(date_scores[date_key])
        result.append({
            "date": date_key,
            "score": round(avg_score, 2)
        })
    
    return result


@router.get("/error-breakdown")
async def error_breakdown(email: str = Query(..., min_length=3), days: int = Query(30, ge=1, le=365)):
    """
    Get aggregated error breakdown for the past N days.
    
    Returns: {articles, tense, preposition, agreement, other}
    """
    db = get_database()
    if db is None:
        raise HTTPException(status_code=503, detail="Database not available")
    
    normalized_email = email.strip().lower()
    
    # Date range
    now = datetime.utcnow()
    start_date = now - timedelta(days=days)
    
    # Get sessions in date range
    cursor = db.analyses.find({
        "email": normalized_email,
        "createdAt": {
            "$gte": start_date.isoformat(),
            "$lte": now.isoformat()
        }
    }, {
        "analysis.error_breakdown": 1
    })
    
    sessions = list(cursor)
    
    # Aggregate error breakdown
    aggregated = {
        "articles": 0,
        "tense": 0,
        "preposition": 0,
        "agreement": 0,
        "other": 0
    }
    
    for session in sessions:
        error_breakdown = session.get("analysis", {}).get("error_breakdown", {})
        if error_breakdown:
            aggregated["articles"] += error_breakdown.get("articles", 0)
            aggregated["tense"] += error_breakdown.get("tense", 0)
            aggregated["preposition"] += error_breakdown.get("preposition", 0)
            aggregated["agreement"] += error_breakdown.get("agreement", 0)
            aggregated["other"] += error_breakdown.get("other", 0)
    
    return aggregated


@router.get("/heatmap")
async def heatmap(email: str = Query(..., min_length=3), weeks: int = Query(5, ge=1, le=52)):
    """
    Get practice heatmap: 7 days × N weeks of session counts.
    
    Returns 7 rows (Mon-Sun) with week counts for each week.
    """
    db = get_database()
    if db is None:
        raise HTTPException(status_code=503, detail="Database not available")
    
    normalized_email = email.strip().lower()
    
    # Get all sessions
    cursor = db.analyses.find(
        {"email": normalized_email},
        {"createdAt": 1}
    ).sort("createdAt", -1)
    
    sessions = list(cursor)
    
    if not sessions:
        # Return empty heatmap
        return [
            {"day": day, "counts": [0] * weeks}
            for day in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        ]
    
    # Calculate week range
    now = datetime.utcnow()
    start_date = now - timedelta(weeks=weeks)
    
    # Count sessions per day per week
    # Dictionary: {week_index: {weekday: count}}
    heatmap_data: Dict[int, Dict[int, int]] = {}
    
    for session in sessions:
        created_at = _parse_datetime(session.get("createdAt"))
        
        if created_at < start_date:
            continue
        
        # Calculate week index (0 = oldest week in range)
        weeks_back = (now.date() - created_at.date()).days // 7
        week_index = weeks - 1 - weeks_back
        
        if week_index < 0 or week_index >= weeks:
            continue
        
        weekday = created_at.weekday()
        
        if week_index not in heatmap_data:
            heatmap_data[week_index] = {}
        heatmap_data[week_index][weekday] = heatmap_data[week_index].get(weekday, 0) + 1
    
    # Build result
    day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    result = []
    
    for day_idx, day_name in enumerate(day_names):
        counts = []
        for week_idx in range(weeks):
            count = 0
            if week_idx in heatmap_data and day_idx in heatmap_data[week_idx]:
                count = heatmap_data[week_idx][day_idx]
            counts.append(count)
        
        result.append({
            "day": day_name,
            "counts": counts
        })
    
    return result


@router.get("/insights")
async def insights(email: str = Query(..., min_length=3)):
    """
    Get user insights: most improved area, most repeated error, peak time, best session.
    """
    db = get_database()
    if db is None:
        raise HTTPException(status_code=503, detail="Database not available")
    
    normalized_email = email.strip().lower()
    
    # Get all sessions
    cursor = db.analyses.find(
        {"email": normalized_email},
        {
            "createdAt": 1,
            "analysis.score": 1,
            "analysis.error_breakdown": 1
        }
    ).sort("createdAt", -1)
    
    sessions = list(cursor)
    
    if not sessions:
        return {
            "most_improved_area": None,
            "most_repeated_error": None,
            "peak_time": "morning",
            "best_session": None
        }
    
    # Most improved area
    total_errors = {}
    error_categories = ["articles", "tense", "preposition", "agreement", "other"]
    
    for session in sessions:
        error_breakdown = session.get("analysis", {}).get("error_breakdown", {})
        for category in error_categories:
            count = error_breakdown.get(category, 0)
            if category not in total_errors:
                total_errors[category] = 0
            total_errors[category] += count
    
    total_error_count = sum(total_errors.values())
    most_improved = None
    if total_errors and total_error_count > 0:
        # Most improved = area with highest errors (most room to improve)
        most_repeated_cat = max(total_errors, key=total_errors.get)
        improvement_pct = (total_errors[most_repeated_cat] / total_error_count) * 100
        most_improved = {
            "category": most_repeated_cat.replace("_", " ").title(),
            "improvement_pct": round(improvement_pct, 2)
        }
    
    # Most repeated error
    most_repeated_error = None
    if total_errors:
        most_repeated_cat = max(total_errors, key=total_errors.get)
        most_repeated_error = {
            "category": most_repeated_cat.replace("_", " ").title(),
            "count": total_errors[most_repeated_cat]
        }
    
    # Peak time
    peak_time = calculate_peak_time(normalized_email, db)
    
    # Best session
    if sessions:
        best_session_data = sessions[0]  # Already sorted desc
        for s in sessions:
            if s.get("analysis", {}).get("score", 0) > best_session_data.get("analysis", {}).get("score", 0):
                best_session_data = s
        
        best_session = {
            "score": best_session_data.get("analysis", {}).get("score", 0),
            "date": best_session_data.get("createdAt", "")
        }
    else:
        best_session = None
    
    return {
        "most_improved_area": most_improved,
        "most_repeated_error": most_repeated_error,
        "peak_time": peak_time,
        "best_session": best_session
    }


@router.get("/recommendations")
async def recommendations(email: str = Query(..., min_length=3)):
    """
    Get personalized recommendations based on user data.
    
    Returns up to 3 recommendations with label and message.
    """
    db = get_database()
    if db is None:
        raise HTTPException(status_code=503, detail="Database not available")
    
    normalized_email = email.strip().lower()
    
    # Generate recommendations
    recs = generate_recommendations(normalized_email, db)
    
    return recs


def _parse_datetime(dt_str: Optional[str]) -> datetime:
    """
    Parse ISO format datetime string.
    
    Args:
        dt_str: ISO format datetime string
        
    Returns:
        datetime object
    """
    if not dt_str:
        return datetime.utcnow()
    
    try:
        # Handle Z suffix
        if isinstance(dt_str, str) and dt_str.endswith("Z"):
            dt_str = dt_str[:-1] + "+00:00"
        return datetime.fromisoformat(dt_str)
    except:
        try:
            return datetime.fromisoformat(dt_str)
        except:
            return datetime.utcnow()
