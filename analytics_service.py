"""
Analytics service — trip statistics, popular destinations, carbon footprint.
Reads from the SQLAlchemy DB where available, falls back to in-memory data.
"""
import logging
from collections import Counter
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)

# Carbon kg per km by mode
CARBON_KG_PER_KM = {
    "flight": 0.255,
    "train": 0.041,
    "bus": 0.089,
    "car": 0.171,
    "ferry": 0.187,
}

# Approximate flight distances (km) from major hubs to popular destinations
APPROX_DISTANCES = {
    "paris": 8800, "london": 9100, "dubai": 2200, "singapore": 5600,
    "tokyo": 6700, "new york": 12500, "bali": 5500, "bangkok": 4600,
    "amsterdam": 8700, "rome": 7400, "barcelona": 8200, "sydney": 12000,
    "toronto": 11400, "los angeles": 13800, "miami": 13000, "istanbul": 5800,
    "cairo": 4900, "mumbai": 900, "delhi": 1400, "bangalore": 1700,
    "maldives": 3000, "mauritius": 4600, "kenya": 5800, "south africa": 8300,
}


def estimate_carbon_footprint(destination: str, transport_mode: str = "flight", distance_km: float = None) -> dict:
    """Estimate carbon footprint for a trip."""
    dest_key = destination.lower().split(",")[0].strip()
    if distance_km is None:
        distance_km = APPROX_DISTANCES.get(dest_key, 5000)

    kg_per_km = CARBON_KG_PER_KM.get(transport_mode, CARBON_KG_PER_KM["flight"])
    total_kg = round(distance_km * kg_per_km * 2, 1)  # round trip

    # Trees needed to offset (1 tree absorbs ~21kg CO2/year)
    trees_year = round(total_kg / 21, 1)

    rating = "Low" if total_kg < 200 else "Medium" if total_kg < 800 else "High"

    return {
        "destination": destination,
        "transport_mode": transport_mode,
        "distance_km": distance_km,
        "carbon_kg": total_kg,
        "rating": rating,
        "trees_to_offset_1yr": trees_year,
        "offset_tips": [
            "Consider carbon offset programs when booking flights",
            "Use public transport at destination",
            "Choose eco-certified hotels",
            "Offset via platforms like Gold Standard or Verra",
        ],
        "greener_alternatives": _greener_alternatives(transport_mode),
    }


def _greener_alternatives(mode: str) -> list[str]:
    if mode == "flight":
        return ["Take a train if distance < 700km", "Choose direct flights (fewer emissions)", "Economy class is greener than business"]
    if mode == "car":
        return ["Use electric rental car", "Share rides with other travelers", "Use public transport at destination"]
    return ["Your choice is already relatively eco-friendly!"]


def get_trip_stats(bookings: list[dict]) -> dict:
    """Compute aggregate trip statistics from booking list."""
    if not bookings:
        return _empty_stats()

    confirmed = [b for b in bookings if b.get("status") == "confirmed"]
    cancelled = [b for b in bookings if b.get("status") == "cancelled"]

    # Countries visited
    destinations = [b.get("destination", "") for b in confirmed]
    dest_counter = Counter(destinations)
    top_destinations = [{"destination": d, "count": c} for d, c in dest_counter.most_common(5)]

    # Total nights
    total_nights = 0
    for b in confirmed:
        try:
            d1 = datetime.fromisoformat(b.get("start_date", "2024-01-01"))
            d2 = datetime.fromisoformat(b.get("end_date", "2024-01-01"))
            total_nights += max(0, (d2 - d1).days)
        except Exception:
            pass

    # Trip types
    type_counter = Counter(b.get("booking_type", "trip") for b in confirmed)

    # Upcoming trips
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    upcoming = [b for b in confirmed if b.get("start_date", "") >= now]
    past = [b for b in confirmed if b.get("start_date", "") < now]

    return {
        "total_bookings": len(bookings),
        "confirmed_trips": len(confirmed),
        "cancelled_trips": len(cancelled),
        "upcoming_trips": len(upcoming),
        "past_trips": len(past),
        "total_nights_traveled": total_nights,
        "unique_destinations": len(set(destinations)),
        "top_destinations": top_destinations,
        "booking_types": dict(type_counter),
        "traveler_level": _traveler_level(total_nights),
    }


def _traveler_level(nights: int) -> dict:
    if nights < 14:
        return {"level": "Explorer", "icon": "🌱", "next_at": 14}
    elif nights < 60:
        return {"level": "Adventurer", "icon": "🧭", "next_at": 60}
    elif nights < 180:
        return {"level": "Globe-Trotter", "icon": "🌍", "next_at": 180}
    else:
        return {"level": "World Citizen", "icon": "🏆", "next_at": None}


def _empty_stats() -> dict:
    return {
        "total_bookings": 0, "confirmed_trips": 0, "cancelled_trips": 0,
        "upcoming_trips": 0, "past_trips": 0, "total_nights_traveled": 0,
        "unique_destinations": 0, "top_destinations": [],
        "booking_types": {}, "traveler_level": _traveler_level(0),
    }


def get_global_popular_destinations() -> list[dict]:
    """Static curated list of globally popular destinations with metadata."""
    return [
        {"destination": "Paris, France",      "country": "France",    "region": "Europe",        "trend": "up",   "avg_cost_usd": 180, "best_months": "Apr–Jun, Sep–Oct"},
        {"destination": "Tokyo, Japan",        "country": "Japan",     "region": "Asia",          "trend": "up",   "avg_cost_usd": 120, "best_months": "Mar–Apr, Oct–Nov"},
        {"destination": "Bali, Indonesia",     "country": "Indonesia", "region": "Asia",          "trend": "up",   "avg_cost_usd": 75,  "best_months": "Apr–Oct"},
        {"destination": "New York, USA",       "country": "USA",       "region": "Americas",      "trend": "stable","avg_cost_usd": 250, "best_months": "Sep–Nov, Mar–May"},
        {"destination": "Dubai, UAE",          "country": "UAE",       "region": "Middle East",   "trend": "up",   "avg_cost_usd": 200, "best_months": "Oct–Apr"},
        {"destination": "Santorini, Greece",   "country": "Greece",    "region": "Europe",        "trend": "up",   "avg_cost_usd": 160, "best_months": "Apr–Jun, Sep–Oct"},
        {"destination": "London, UK",          "country": "UK",        "region": "Europe",        "trend": "stable","avg_cost_usd": 220, "best_months": "Jun–Aug"},
        {"destination": "Bangkok, Thailand",   "country": "Thailand",  "region": "Asia",          "trend": "up",   "avg_cost_usd": 60,  "best_months": "Nov–Apr"},
        {"destination": "Maldives",            "country": "Maldives",  "region": "Asia",          "trend": "up",   "avg_cost_usd": 400, "best_months": "Nov–Apr"},
        {"destination": "Rome, Italy",         "country": "Italy",     "region": "Europe",        "trend": "stable","avg_cost_usd": 140, "best_months": "Apr–Jun, Sep–Oct"},
        {"destination": "Sydney, Australia",   "country": "Australia", "region": "Oceania",       "trend": "stable","avg_cost_usd": 180, "best_months": "Sep–Nov, Mar–May"},
        {"destination": "Istanbul, Turkey",    "country": "Turkey",    "region": "Europe/Asia",   "trend": "up",   "avg_cost_usd": 80,  "best_months": "Apr–Jun, Sep–Oct"},
    ]
