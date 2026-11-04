"""
Itinerary builder module.
Uses IBM Granite to create detailed, day-by-day travel itineraries.
"""
import logging
import json
import re
from datetime import datetime, timedelta
from granite_client import granite
from weather_service import get_weather_forecast, weather_summary_text

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are an expert travel planner AI powered by IBM Granite. "
    "Create realistic, detailed, and enjoyable travel itineraries. "
    "Consider opening hours, travel times, meal breaks, and rest periods. "
    "Always respond in valid JSON when asked to do so."
)


def build_itinerary(
    destination: str,
    start_date: str,
    duration_days: int,
    preferences: str = "",
    budget: str = "moderate",
    travel_style: str = "balanced",
    accommodation_type: str = "hotel",
    include_weather: bool = True,
) -> dict:
    """
    Build a complete day-by-day itinerary using IBM Granite.
    
    Args:
        destination: Travel destination (city/country)
        start_date: ISO date string YYYY-MM-DD
        duration_days: Number of days for the trip
        preferences: User's interests and preferences
        budget: low / moderate / high / luxury
        travel_style: relaxed / balanced / active / adventure / cultural
        accommodation_type: hostel / hotel / boutique / resort / airbnb
        include_weather: Whether to include weather context
    
    Returns:
        Structured itinerary dict
    """
    # Gather weather context
    weather_context = ""
    weather_data = {}
    if include_weather:
        weather_data = get_weather_forecast(destination, days=min(duration_days, 16))
        weather_context = f"\nWeather context:\n{weather_summary_text(weather_data)}\n"

    prompt_messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                f"Create a detailed {duration_days}-day travel itinerary for {destination}.\n"
                f"Start date: {start_date}\n"
                f"Preferences: {preferences or 'general sightseeing and culture'}\n"
                f"Budget: {budget}\n"
                f"Travel style: {travel_style}\n"
                f"Accommodation type: {accommodation_type}\n"
                f"{weather_context}\n"
                "Respond ONLY with a JSON object in this exact format:\n"
                "{\n"
                '  "destination": "City, Country",\n'
                '  "duration_days": ' + str(duration_days) + ',\n'
                '  "start_date": "' + start_date + '",\n'
                '  "budget_level": "moderate",\n'
                '  "estimated_total_cost_usd": 1200,\n'
                '  "days": [\n'
                "    {\n"
                '      "day": 1,\n'
                '      "date": "YYYY-MM-DD",\n'
                '      "theme": "Arrival & Orientation",\n'
                '      "morning": {\n'
                '        "activity": "Activity name",\n'
                '        "description": "Short description",\n'
                '        "location": "Place name",\n'
                '        "duration_hours": 2,\n'
                '        "cost_usd": 15,\n'
                '        "tips": "Helpful tip"\n'
                "      },\n"
                '      "afternoon": { same structure },\n'
                '      "evening": { same structure },\n'
                '      "meals": {\n'
                '        "breakfast": "Restaurant or suggestion",\n'
                '        "lunch": "Restaurant or suggestion",\n'
                '        "dinner": "Restaurant or suggestion"\n'
                "      },\n"
                '      "accommodation": "Hotel/hostel name or area",\n'
                '      "transport": "How to get around today",\n'
                '      "daily_budget_usd": 150,\n'
                '      "weather_note": "Brief weather note for the day"\n'
                "    }\n"
                "  ],\n"
                '  "packing_tips": ["tip1", "tip2"],\n'
                '  "emergency_contacts": {\n'
                '    "police": "local number",\n'
                '    "ambulance": "local number",\n'
                '    "tourist_helpline": "number if available"\n'
                "  }\n"
                "}"
            ),
        },
    ]

    try:
        response = granite.chat(prompt_messages)
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            itinerary = json.loads(json_match.group())
        else:
            itinerary = json.loads(response)

        # Attach weather data
        itinerary["weather_forecast"] = weather_data.get("forecast", [])
        itinerary["current_weather"] = weather_data.get("current", {})
        return itinerary

    except (json.JSONDecodeError, Exception) as exc:
        logger.error("Itinerary build error for %s: %s", destination, exc)
        return {
            "destination": destination,
            "error": str(exc),
            "raw_response": response if 'response' in dir() else "",
        }


def optimize_itinerary(itinerary: dict, feedback: str) -> dict:
    """
    Optimize an existing itinerary based on user feedback using IBM Granite.
    """
    prompt_messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                f"Here is a travel itinerary:\n{json.dumps(itinerary, indent=2)}\n\n"
                f"User feedback / change request: {feedback}\n\n"
                "Please modify the itinerary accordingly and return the updated "
                "itinerary in the same JSON format."
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
        logger.error("Itinerary optimization error: %s", exc)
        itinerary["optimization_error"] = str(exc)
        return itinerary


def estimate_budget(
    destination: str,
    duration_days: int,
    travel_style: str = "balanced",
    num_travelers: int = 1,
) -> dict:
    """
    Generate a detailed budget estimate using IBM Granite.
    """
    prompt_messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                f"Estimate the travel budget for {destination} for {duration_days} days "
                f"({num_travelers} traveler(s)), travel style: {travel_style}.\n\n"
                "Respond ONLY with a JSON object:\n"
                "{\n"
                '  "destination": "City, Country",\n'
                '  "duration_days": ' + str(duration_days) + ',\n'
                '  "num_travelers": ' + str(num_travelers) + ',\n'
                '  "currency": "USD",\n'
                '  "daily_breakdown": {\n'
                '    "accommodation": 80,\n'
                '    "food": 40,\n'
                '    "transport": 20,\n'
                '    "activities": 30,\n'
                '    "miscellaneous": 10\n'
                "  },\n"
                '  "total_estimated_usd": 1800,\n'
                '  "budget_tips": ["tip1", "tip2"],\n'
                '  "cost_of_living_note": "Short note about cost of living"\n'
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
        logger.error("Budget estimation error: %s", exc)
        return {"error": str(exc)}
