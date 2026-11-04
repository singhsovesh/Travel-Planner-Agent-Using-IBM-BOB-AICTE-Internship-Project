"""
Transport and accommodation recommendation module.
Uses IBM Granite to suggest transport options and accommodation.
"""
import logging
import json
import re
from granite_client import granite

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are an expert travel planner AI powered by IBM Granite. "
    "Provide accurate, up-to-date transport and accommodation advice. "
    "Always respond in valid JSON when asked to do so."
)


def get_transport_options(
    origin: str,
    destination: str,
    travel_date: str = "",
    budget: str = "moderate",
    preferences: str = "",
) -> dict:
    """
    Get transport options between two locations using IBM Granite.
    Covers flights, trains, buses, ferries, and car hire.
    """
    date_context = f" on {travel_date}" if travel_date else ""

    prompt_messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                f"Suggest transport options from {origin} to {destination}{date_context}.\n"
                f"Budget: {budget}\n"
                f"Preferences: {preferences or 'none'}\n\n"
                "Respond ONLY with a JSON object:\n"
                "{\n"
                '  "origin": "city",\n'
                '  "destination": "city",\n'
                '  "options": [\n'
                "    {\n"
                '      "mode": "Flight/Train/Bus/Ferry/Car",\n'
                '      "operator": "Airline or company name",\n'
                '      "estimated_duration": "2h 30m",\n'
                '      "estimated_cost_usd": 150,\n'
                '      "comfort_level": "High/Medium/Low",\n'
                '      "booking_tip": "Where to book",\n'
                '      "pros": ["pro1", "pro2"],\n'
                '      "cons": ["con1"],\n'
                '      "recommended": true\n'
                "    }\n"
                "  ],\n"
                '  "recommended_option": "Mode",\n'
                '  "local_transport_at_destination": [\n'
                '    {"mode": "Metro", "cost": "$2/trip", "tip": "Buy day pass"}\n'
                "  ]\n"
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
        logger.error("Transport options error (%s -> %s): %s", origin, destination, exc)
        return {"error": str(exc)}


def get_accommodation_recommendations(
    destination: str,
    check_in: str,
    check_out: str,
    budget: str = "moderate",
    accommodation_type: str = "hotel",
    num_guests: int = 1,
    preferences: str = "",
) -> dict:
    """
    Get accommodation recommendations for a destination using IBM Granite.
    """
    prompt_messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                f"Recommend accommodations in {destination}.\n"
                f"Check-in: {check_in}, Check-out: {check_out}\n"
                f"Type: {accommodation_type}, Budget: {budget}, Guests: {num_guests}\n"
                f"Preferences: {preferences or 'central location, good reviews'}\n\n"
                "Respond ONLY with a JSON object:\n"
                "{\n"
                '  "destination": "city",\n'
                '  "recommendations": [\n'
                "    {\n"
                '      "name": "Hotel/Hostel name",\n'
                '      "type": "Hotel/Hostel/Airbnb/Resort",\n'
                '      "area": "Neighbourhood",\n'
                '      "estimated_price_usd_per_night": 80,\n'
                '      "rating": 4.2,\n'
                '      "highlights": ["WiFi", "Breakfast included"],\n'
                '      "nearby_attractions": ["attraction1"],\n'
                '      "booking_platform": "Booking.com / Airbnb / Hotels.com",\n'
                '      "pros": ["pro1"],\n'
                '      "cons": ["con1"]\n'
                "    }\n"
                "  ],\n"
                '  "booking_tips": ["tip1", "tip2"],\n'
                '  "best_areas_to_stay": ["area1", "area2"]\n'
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
        logger.error("Accommodation error for %s: %s", destination, exc)
        return {"error": str(exc)}


def get_visa_information(
    nationality: str,
    destination_country: str,
) -> dict:
    """
    Get visa requirements and entry information using IBM Granite.
    """
    prompt_messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                f"Provide visa and entry requirements for a {nationality} passport holder "
                f"travelling to {destination_country}.\n\n"
                "Respond ONLY with a JSON object:\n"
                "{\n"
                '  "nationality": "country",\n'
                '  "destination": "country",\n'
                '  "visa_required": true,\n'
                '  "visa_type": "Tourist/e-Visa/Visa on Arrival/Visa Free",\n'
                '  "max_stay_days": 30,\n'
                '  "cost_usd": 50,\n'
                '  "processing_time": "3-5 business days",\n'
                '  "required_documents": ["Passport", "Bank statement"],\n'
                '  "application_link": "official embassy website",\n'
                '  "important_notes": ["note1", "note2"],\n'
                '  "health_requirements": ["Yellow fever vaccine if coming from..."],\n'
                '  "customs_rules": ["currency limit", "prohibited items"]\n'
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
        logger.error("Visa info error for %s -> %s: %s", nationality, destination_country, exc)
        return {"error": str(exc)}
