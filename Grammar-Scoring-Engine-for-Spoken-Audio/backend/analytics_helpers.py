"""
Analytics helper functions for Grammar Scoring Engine.
Calculate streaks, improvements, peak times, and recommendations.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from pymongo.database import Database


def calculate_streak(user_email: str, db: Database) -> int:
    """
    Count consecutive days going back from today where user has at least 1 session.
    
    Args:
        user_email: Normalized user email
        db: MongoDB database instance
        
    Returns:
        int: Number of consecutive days with at least 1 session
    """
    if db is None:
        return 0
    
    # Normalized email
    normalized_email = user_email.strip().lower()
    
    # Get all sessions for this user, sorted by date descending
    cursor = db.analyses.find(
        {"email": normalized_email},
        {"createdAt": 1}
    ).sort("createdAt", -1)
    
    sessions = list(cursor)
    if not sessions:
        return 0
    
    # Get today's date (at midnight UTC)
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Track which days have sessions
    days_with_sessions = set()
    for session in sessions:
        created_at_str = session.get("createdAt")
        if isinstance(created_at_str, str):
            # Parse ISO format string
            try:
                created_at = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
            except:
                created_at = datetime.fromisoformat(created_at_str)
        else:
            created_at = created_at_str
        
        session_date = created_at.replace(hour=0, minute=0, second=0, microsecond=0)
        days_with_sessions.add(session_date)
    
    # Count consecutive days backward from today
    streak = 0
    current_date = today
    
    while current_date in days_with_sessions:
        streak += 1
        current_date -= timedelta(days=1)
    
    return streak


def calculate_improvement_pct(user_email: str, db: Database) -> float:
    """
    Calculate improvement percentage: this week average vs last week average.
    This week = Mon–today, Last week = last Mon–last Sun.
    
    Args:
        user_email: Normalized user email
        db: MongoDB database instance
        
    Returns:
        float: Percentage change. 0.0 if not enough data.
    """
    if db is None:
        return 0.0
    
    normalized_email = user_email.strip().lower()
    
    # Get today's date
    today = datetime.utcnow()
    
    # Calculate week boundaries (assuming week starts on Monday)
    # This week: Monday of current week to today
    monday_this_week = today - timedelta(days=today.weekday())
    monday_this_week = monday_this_week.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Last week: Monday of last week to Sunday of last week
    monday_last_week = monday_this_week - timedelta(days=7)
    sunday_last_week = monday_last_week + timedelta(days=6)
    sunday_last_week = sunday_last_week.replace(hour=23, minute=59, second=59, microsecond=999999)
    
    # Get sessions for this week
    this_week_sessions = list(db.analyses.find({
        "email": normalized_email,
        "createdAt": {
            "$gte": monday_this_week.isoformat(),
            "$lte": today.isoformat()
        }
    }))
    
    # Get sessions for last week
    last_week_sessions = list(db.analyses.find({
        "email": normalized_email,
        "createdAt": {
            "$gte": monday_last_week.isoformat(),
            "$lte": sunday_last_week.isoformat()
        }
    }))
    
    if not this_week_sessions or not last_week_sessions:
        return 0.0
    
    # Calculate averages
    this_week_avg = sum(
        session.get("analysis", {}).get("score", 0)
        for session in this_week_sessions
    ) / len(this_week_sessions)
    
    last_week_avg = sum(
        session.get("analysis", {}).get("score", 0)
        for session in last_week_sessions
    ) / len(last_week_sessions)
    
    if last_week_avg == 0:
        return 0.0
    
    # Calculate percentage change
    improvement = ((this_week_avg - last_week_avg) / last_week_avg) * 100
    return round(improvement, 2)


def calculate_peak_time(user_email: str, db: Database) -> str:
    """
    Group last 30 sessions by hour into morning/afternoon/evening.
    Return the label with highest average score.
    
    Morning = 6–11, Afternoon = 12–17, Evening = 18–23
    
    Args:
        user_email: Normalized user email
        db: MongoDB database instance
        
    Returns:
        str: "morning", "afternoon", or "evening"
    """
    if db is None:
        return "morning"
    
    normalized_email = user_email.strip().lower()
    
    # Get last 30 sessions
    cursor = db.analyses.find(
        {"email": normalized_email},
        {"createdAt": 1, "analysis.score": 1}
    ).sort("createdAt", -1).limit(30)
    
    sessions = list(cursor)
    
    time_scores = {
        "morning": {"scores": [], "count": 0},
        "afternoon": {"scores": [], "count": 0},
        "evening": {"scores": [], "count": 0}
    }
    
    for session in sessions:
        created_at_str = session.get("createdAt")
        score = session.get("analysis", {}).get("score", 0)
        
        if isinstance(created_at_str, str):
            try:
                created_at = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
            except:
                created_at = datetime.fromisoformat(created_at_str)
        else:
            created_at = created_at_str
        
        hour = created_at.hour
        
        if 6 <= hour <= 11:
            time_scores["morning"]["scores"].append(score)
            time_scores["morning"]["count"] += 1
        elif 12 <= hour <= 17:
            time_scores["afternoon"]["scores"].append(score)
            time_scores["afternoon"]["count"] += 1
        elif 18 <= hour <= 23 or 0 <= hour <= 5:
            time_scores["evening"]["scores"].append(score)
            time_scores["evening"]["count"] += 1
    
    # Calculate averages
    averages = {}
    for time_period, data in time_scores.items():
        if data["count"] > 0:
            averages[time_period] = sum(data["scores"]) / data["count"]
        else:
            averages[time_period] = 0
    
    # Return the time period with highest average
    peak = max(averages, key=averages.get)
    return peak if averages[peak] > 0 else "morning"


def generate_recommendations(user_email: str, db: Database) -> List[Dict[str, str]]:
    """
    Generate rule-based recommendations based on user's data.
    Return max 3 items with label and message.
    
    Rules:
    - If articles errors > 30% → Focus on articles (label: "Focus Area")
    - If avg session duration < 3 mins → Try longer recordings (label: "Habit Tip")
    - If morning sessions score higher → Practice before noon (label: "Timing Insight")
    - If current_streak < 3 → Build daily habit (label: "Habit Tip")
    
    Args:
        user_email: Normalized user email
        db: MongoDB database instance
        
    Returns:
        list: Max 3 dicts with "label" and "message" keys
    """
    if db is None:
        return []
    
    normalized_email = user_email.strip().lower()
    recommendations = []
    
    # Get all sessions for analysis
    cursor = db.analyses.find(
        {"email": normalized_email},
        {
            "createdAt": 1,
            "analysis.score": 1,
            "analysis.duration": 1,
            "analysis.error_breakdown": 1
        }
    ).sort("createdAt", -1)
    
    sessions = list(cursor)
    
    if not sessions:
        return []
    
    # Rule 1: Articles error analysis
    total_errors = 0
    article_errors = 0
    total_duration = 0
    
    for session in sessions:
        analysis = session.get("analysis", {})
        error_breakdown = analysis.get("error_breakdown", {})
        
        article_errors += error_breakdown.get("articles", 0)
        total_errors += sum(error_breakdown.values())
        total_duration += analysis.get("duration", 0)
    
    if total_errors > 0 and article_errors / total_errors > 0.30:
        recommendations.append({
            "label": "Focus Area",
            "message": "Focus on article usage (a, an, the) with daily drills"
        })
    
    # Rule 2: Session duration check
    if sessions and total_duration / len(sessions) < 3 * 60:  # duration in seconds
        recommendations.append({
            "label": "Habit Tip",
            "message": "Try longer recordings — aim for 3–5 minutes per session"
        })
    
    # Rule 3: Peak time analysis
    peak_time = calculate_peak_time(normalized_email, db)
    if peak_time == "morning":
        recommendations.append({
            "label": "Timing Insight",
            "message": "Your scores peak in the morning — practice before noon"
        })
    
    # If less than 3 recommendations, add streak check
    if len(recommendations) < 3:
        streak = calculate_streak(normalized_email, db)
        if streak < 3:
            recommendations.append({
                "label": "Habit Tip",
                "message": "Build a daily habit — even one short recording per day compounds fast"
            })
    
    return recommendations[:3]
