"""
Destination intelligence module.
Uses IBM Granite to suggest, describe, and rank travel destinations.
"""
import logging
import json
import re
from granite_client import granite

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = (
    "You are an expert travel planner AI powered by IBM Granite. "
    "You provide accurate, practical, and personalized travel advice. "
    "Always respond in valid JSON when asked to do so. "
    "Be concise, helpful, and safety-conscious."
)


def suggest_destinations(
    preferences: str,
    budget: str = "moderate",
    duration_days: int = 7,
    departure_from: str = "",
    travel_style: str = "balanced",
) -> dict:
    """
    Use IBM Granite to suggest top travel destinations based on user preferences.
    Returns structured dict with destination recommendations.
    """
    departure_context = f" departing from {departure_from}" if departure_from else ""

    prompt_messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                f"Suggest 5 travel destinations{departure_context} for a {duration_days}-day trip.\n"
                f"User preferences: {preferences}\n"
                f"Budget level: {budget}\n"
                f"Travel style: {travel_style}\n\n"
                "Respond ONLY with a JSON object in this exact format:\n"
                "{\n"
                '  "destinations": [\n'
                "    {\n"
                '      "name": "City, Country",\n'
                '      "country": "Country",\n'
                '      "why": "2-sentence reason this suits the user",\n'
                '      "best_season": "Month range",\n'
                '      "estimated_budget_usd_per_day": 120,\n'
                '      "highlights": ["highlight1", "highlight2", "highlight3"],\n'
                '      "travel_style_tags": ["tag1", "tag2"],\n'
                '      "visa_ease": "Easy/Moderate/Complex"\n'
                "    }\n"
                "  ]\n"
                "}"
            ),
        },
    ]

    try:
        response = granite.chat(prompt_messages)
        # Extract JSON from the response
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        # Fallback: try parsing entire response
        return json.loads(response)
    except (json.JSONDecodeError, Exception) as exc:
        logger.error("Destination suggestion error: %s", exc)
        return {
            "destinations": [],
            "error": str(exc),
            "raw_response": response if 'response' in dir() else "",
        }


def describe_destination(destination: str, focus: str = "general") -> str:
    """
    Get a rich description of a destination from IBM Granite.
    focus: general | culture | food | adventure | family | budget
    """
    prompt_messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                f"Write a travel guide overview for {destination}.\n"
                f"Focus: {focus} travel.\n"
                "Cover: must-see attractions, local culture, food, practical tips, "
                "best time to visit, and safety. Keep it under 400 words."
            ),
        },
    ]
    try:
        return granite.chat(prompt_messages)
    except Exception as exc:
        logger.error("Destination description error: %s", exc)
        return f"Unable to load description for {destination}."


def get_local_tips(destination: str, interests: list[str] = None) -> dict:
    """
    Get hyper-local tips including hidden gems, etiquette, and insider advice.
    """
    interest_str = ", ".join(interests) if interests else "general sightseeing"
    prompt_messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                f"Give insider local travel tips for {destination}.\n"
                f"Traveller interests: {interest_str}\n\n"
                "Respond ONLY with a JSON object:\n"
                "{\n"
                '  "hidden_gems": ["place1", "place2"],\n'
                '  "local_etiquette": ["tip1", "tip2"],\n'
                '  "best_local_food": ["dish1", "dish2"],\n'
                '  "avoid": ["thing1", "thing2"],\n'
                '  "money_saving_tips": ["tip1", "tip2"],\n'
                '  "safety_tips": ["tip1", "tip2"]\n'
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
        logger.error("Local tips error for %s: %s", destination, exc)
        return {"error": str(exc)}
