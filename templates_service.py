"""
Itinerary templates service.
Pre-built community itinerary templates that users can clone and customize.
"""
import json
import logging
from datetime import date, timedelta

logger = logging.getLogger(__name__)

TEMPLATES = [
    {
        "id": "tpl_paris_7d",
        "title": "Classic Paris in 7 Days",
        "destination": "Paris, France",
        "duration_days": 7,
        "budget_level": "moderate",
        "template_category": "city",
        "description": "The quintessential Paris experience — Eiffel Tower, Louvre, Versailles, Montmartre, and Seine cruises.",
        "tags": ["Romance", "Culture", "Art", "Food"],
        "avg_cost_usd": 1800,
        "likes": 342,
        "highlights": ["Eiffel Tower at sunrise", "Louvre full day", "Day trip to Versailles", "Montmartre & Sacré-Cœur", "Seine river cruise"],
    },
    {
        "id": "tpl_japan_10d",
        "title": "Japan Explorer: Tokyo to Kyoto",
        "destination": "Japan",
        "duration_days": 10,
        "budget_level": "moderate",
        "template_category": "cultural",
        "description": "Tokyo city life, Mt. Fuji views, Kyoto temples, Osaka street food — the perfect Japan circuit.",
        "tags": ["Culture", "Food", "Temples", "Nature"],
        "avg_cost_usd": 2400,
        "likes": 518,
        "highlights": ["Shibuya crossing", "Mt. Fuji day trip", "Arashiyama bamboo grove", "Dotonbori Osaka", "Fushimi Inari shrine"],
    },
    {
        "id": "tpl_bali_5d",
        "title": "Bali Budget Bliss",
        "destination": "Bali, Indonesia",
        "duration_days": 5,
        "budget_level": "low",
        "template_category": "beach",
        "description": "Temples, rice terraces, surf beaches and sunsets — maximum Bali on a backpacker budget.",
        "tags": ["Beach", "Wellness", "Budget", "Temples"],
        "avg_cost_usd": 600,
        "likes": 289,
        "highlights": ["Tanah Lot temple sunset", "Tegallalang rice terraces", "Seminyak beach", "Ubud monkey forest", "Cooking class"],
    },
    {
        "id": "tpl_dubai_4d",
        "title": "Dubai Luxury Long Weekend",
        "destination": "Dubai, UAE",
        "duration_days": 4,
        "budget_level": "luxury",
        "template_category": "luxury",
        "description": "Burj Khalifa, desert safaris, world-class dining and the Mall of the Emirates.",
        "tags": ["Luxury", "Shopping", "Desert", "Architecture"],
        "avg_cost_usd": 2000,
        "likes": 201,
        "highlights": ["Burj Khalifa sunset", "Desert safari & dune bashing", "Dubai Mall & Fountain show", "Gold Souk", "Dhow dinner cruise"],
    },
    {
        "id": "tpl_europe_backpack_14d",
        "title": "Backpacker Europe: 5 Countries in 14 Days",
        "destination": "Western Europe",
        "duration_days": 14,
        "budget_level": "low",
        "template_category": "backpacking",
        "description": "London → Paris → Amsterdam → Berlin → Prague on a shoestring — hostels, trains, and hidden gems.",
        "tags": ["Backpacking", "Budget", "Multi-country", "History"],
        "avg_cost_usd": 1400,
        "likes": 634,
        "highlights": ["London free museums", "Paris on €30/day", "Amsterdam canals by bike", "Berlin Wall", "Prague Old Town"],
    },
    {
        "id": "tpl_maldives_honeymoon_7d",
        "title": "Maldives Honeymoon Escape",
        "destination": "Maldives",
        "duration_days": 7,
        "budget_level": "luxury",
        "template_category": "honeymoon",
        "description": "Overwater bungalows, private snorkelling, sunset cruises and spa indulgence.",
        "tags": ["Honeymoon", "Beach", "Luxury", "Romance"],
        "avg_cost_usd": 5000,
        "likes": 412,
        "highlights": ["Overwater villa sunrise", "Snorkelling with manta rays", "Private beach dinner", "Dolphin cruise", "Spa day"],
    },
    {
        "id": "tpl_nyc_5d",
        "title": "New York City in 5 Days",
        "destination": "New York, USA",
        "duration_days": 5,
        "budget_level": "moderate",
        "template_category": "city",
        "description": "Manhattan, Brooklyn, Central Park, Times Square, museums and the best food in the world.",
        "tags": ["City", "Culture", "Food", "Shopping"],
        "avg_cost_usd": 1600,
        "likes": 387,
        "highlights": ["Statue of Liberty", "Central Park & MET", "Brooklyn Bridge walk", "Times Square", "High Line"],
    },
    {
        "id": "tpl_thailand_adventure_10d",
        "title": "Thailand Adventure: Bangkok to Islands",
        "destination": "Thailand",
        "duration_days": 10,
        "budget_level": "low",
        "template_category": "adventure",
        "description": "Bangkok temples, Chiang Mai elephants, Krabi rock climbing and Koh Phi Phi beaches.",
        "tags": ["Adventure", "Beach", "Culture", "Budget"],
        "avg_cost_usd": 1000,
        "likes": 521,
        "highlights": ["Grand Palace Bangkok", "Elephant sanctuary Chiang Mai", "Phi Phi Islands", "Railay Beach", "Night markets"],
    },
]

CATEGORIES = ["city", "cultural", "beach", "luxury", "backpacking", "honeymoon", "adventure", "family", "wellness"]


def list_templates(category: str = None, budget: str = None, max_days: int = None) -> list[dict]:
    """List available itinerary templates with optional filters."""
    results = TEMPLATES[:]
    if category:
        results = [t for t in results if t.get("template_category") == category]
    if budget:
        results = [t for t in results if t.get("budget_level") == budget]
    if max_days:
        results = [t for t in results if t.get("duration_days", 99) <= max_days]
    return sorted(results, key=lambda t: t.get("likes", 0), reverse=True)


def get_template(template_id: str) -> dict | None:
    """Get a single template by ID."""
    return next((t for t in TEMPLATES if t["id"] == template_id), None)


def clone_template(template_id: str, start_date: str = None, customizations: dict = None) -> dict:
    """
    Clone a template into a usable itinerary skeleton.
    Fills in actual dates and applies any customizations.
    """
    tpl = get_template(template_id)
    if not tpl:
        return {"error": f"Template {template_id} not found"}

    start = date.fromisoformat(start_date) if start_date else date.today() + timedelta(days=30)
    duration = tpl["duration_days"]

    # Build basic day structure from highlights
    days = []
    highlights = tpl.get("highlights", [])
    for i in range(duration):
        day_date = (start + timedelta(days=i)).isoformat()
        highlight = highlights[i] if i < len(highlights) else f"Explore {tpl['destination']}"
        days.append({
            "day": i + 1,
            "date": day_date,
            "theme": highlight,
            "morning": {"activity": highlight, "description": f"Visit {highlight}", "location": tpl["destination"], "duration_hours": 3, "cost_usd": 20, "tips": "Book in advance for popular attractions"},
            "afternoon": {"activity": "Local exploration", "description": "Explore local neighborhoods and cuisine", "location": tpl["destination"], "duration_hours": 4, "cost_usd": 30, "tips": "Try local street food"},
            "evening": {"activity": "Dinner & local experience", "description": "Dinner at a local restaurant", "location": tpl["destination"], "duration_hours": 2, "cost_usd": 40, "tips": "Make reservations for popular restaurants"},
            "meals": {"breakfast": "Hotel / local café", "lunch": "Local restaurant", "dinner": "Recommended restaurant"},
            "daily_budget_usd": tpl["avg_cost_usd"] // duration,
            "transport": "Local transport / taxi",
        })

    cloned = {
        "destination": tpl["destination"],
        "title": tpl["title"],
        "duration_days": duration,
        "start_date": start.isoformat(),
        "budget_level": tpl["budget_level"],
        "estimated_total_cost_usd": tpl["avg_cost_usd"],
        "days": days,
        "template_id": template_id,
        "cloned_from": tpl["title"],
        "tags": tpl["tags"],
        "packing_tips": ["Pack light for this trip", "Bring a universal adapter", "Get travel insurance"],
        "emergency_contacts": {"police": "Local emergency number", "ambulance": "Local emergency number"},
    }

    # Apply customizations
    if customizations:
        cloned.update(customizations)

    return cloned


def get_categories() -> list[str]:
    return CATEGORIES
