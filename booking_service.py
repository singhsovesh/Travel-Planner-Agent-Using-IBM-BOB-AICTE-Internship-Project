"""
Booking management module.
Manages trip bookings, alerts, and schedule optimization using IBM Granite.
"""
import logging
import json
import re
import uuid
from datetime import datetime
from typing import Optional
from granite_client import granite

logger = logging.getLogger(__name__)

# In-memory booking store (in production, replace with a database)
_bookings: dict[str, dict] = {}

SYSTEM_PROMPT = (
    "You are an expert travel planner AI powered by IBM Granite. "
    "Help manage travel bookings, optimize schedules, and provide alerts. "
    "Always respond in valid JSON when asked to do so."
)


# ─── Booking CRUD ────────────────────────────────────────────────────────────

def create_booking(
    trip_name: str,
    destination: str,
    start_date: str,
    end_date: str,
    traveler_name: str,
    booking_type: str = "trip",  # trip / flight / hotel / activity
    details: dict = None,
) -> dict:
    """Create a new booking entry."""
    booking_id = str(uuid.uuid4())[:8].upper()
    booking = {
        "id": booking_id,
        "trip_name": trip_name,
        "destination": destination,
        "start_date": start_date,
        "end_date": end_date,
        "traveler_name": traveler_name,
        "booking_type": booking_type,
        "status": "confirmed",
        "details": details or {},
        "alerts": [],
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }
    _bookings[booking_id] = booking
    logger.info("Booking created: %s for %s", booking_id, destination)
    return booking


def get_booking(booking_id: str) -> Optional[dict]:
    """Retrieve a booking by ID."""
    return _bookings.get(booking_id.upper())


def list_bookings() -> list[dict]:
    """List all bookings sorted by start date."""
    return sorted(_bookings.values(), key=lambda b: b.get("start_date", ""))


def update_booking(booking_id: str, updates: dict) -> Optional[dict]:
    """Update an existing booking."""
    booking = _bookings.get(booking_id.upper())
    if not booking:
        return None
    booking.update(updates)
    booking["updated_at"] = datetime.utcnow().isoformat()
    return booking


def cancel_booking(booking_id: str) -> Optional[dict]:
    """Cancel a booking."""
    return update_booking(booking_id, {"status": "cancelled"})


def add_alert(booking_id: str, alert_message: str, alert_type: str = "info") -> Optional[dict]:
    """Add an alert to a booking."""
    booking = _bookings.get(booking_id.upper())
    if not booking:
        return None
    alert = {
        "id": str(uuid.uuid4())[:6],
        "type": alert_type,  # info / warning / urgent
        "message": alert_message,
        "timestamp": datetime.utcnow().isoformat(),
        "read": False,
    }
    booking["alerts"].append(alert)
    booking["updated_at"] = datetime.utcnow().isoformat()
    return booking


# ─── AI-powered features ──────────────────────────────────────────────────────

def optimize_schedule(itinerary: dict, constraints: str = "") -> dict:
    """
    Use IBM Granite to optimize a travel schedule based on constraints.
    e.g., avoiding traffic, grouping nearby attractions, optimizing costs.
    """
    prompt_messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                f"Optimize this travel schedule:\n{json.dumps(itinerary, indent=2)}\n\n"
                f"Constraints and goals: {constraints or 'minimize travel time, group nearby attractions, '
                'ensure rest time, optimize for cost'}\n\n"
                "Return the optimized schedule in the same JSON format with a "
                '"optimization_notes" field explaining the key changes made.'
            ),
        },
    ]
    try:
        response = granite.chat(prompt_messages)
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        return json.loads(response)
    except Exception as exc:
        logger.error("Schedule optimization error: %s", exc)
        itinerary["optimization_error"] = str(exc)
        return itinerary


def check_travel_alerts(destination: str, travel_date: str) -> dict:
    """
    Use IBM Granite to provide travel alerts and advisories for a destination.
    """
    prompt_messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                f"Provide current travel alerts and advisories for {destination} "
                f"for travel around {travel_date}.\n\n"
                "Respond ONLY with a JSON object:\n"
                "{\n"
                '  "destination": "city/country",\n'
                '  "overall_safety_level": "Safe/Exercise Caution/High Risk",\n'
                '  "alerts": [\n'
                '    {"type": "safety/health/natural/political", "message": "alert text", "severity": "low/medium/high"}\n'
                "  ],\n"
                '  "health_advisories": ["advisory1"],\n'
                '  "natural_disaster_risk": "Low/Medium/High",\n'
                '  "local_laws_to_know": ["law1", "law2"],\n'
                '  "emergency_numbers": {"police": "...", "ambulance": "...", "fire": "..."},\n'
                '  "nearest_embassy_tip": "Check your government travel website for embassy details"\n'
                "}"
            ),
        },
    ]
    try:
        response = granite.chat(prompt_messages)
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        return json.loads(response)
    except Exception as exc:
        logger.error("Travel alerts error for %s: %s", destination, exc)
        return {"error": str(exc)}


def get_packing_list(
    destination: str,
    duration_days: int,
    climate: str = "temperate",
    activities: list[str] = None,
) -> dict:
    """
    Generate a personalized packing list using IBM Granite.
    """
    activity_str = ", ".join(activities) if activities else "general sightseeing"
    prompt_messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                f"Create a comprehensive packing list for a {duration_days}-day trip to {destination}.\n"
                f"Climate: {climate}\n"
                f"Activities: {activity_str}\n\n"
                "Respond ONLY with a JSON object:\n"
                "{\n"
                '  "destination": "city",\n'
                '  "essentials": ["Passport", "Travel insurance"],\n'
                '  "clothing": ["item1", "item2"],\n'
                '  "electronics": ["item1"],\n'
                '  "toiletries": ["item1"],\n'
                '  "medications": ["First aid kit"],\n'
                '  "activity_specific": ["item1"],\n'
                '  "documents": ["Passport", "Visa copy"],\n'
                '  "money": ["Local currency tip", "Card advice"],\n'
                '  "tips": ["Pack light", "Roll clothes"]\n'
                "}"
            ),
        },
    ]
    try:
        response = granite.chat(prompt_messages)
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        return json.loads(response)
    except Exception as exc:
        logger.error("Packing list error for %s: %s", destination, exc)
        return {"error": str(exc)}
