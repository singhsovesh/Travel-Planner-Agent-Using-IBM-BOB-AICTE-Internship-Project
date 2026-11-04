"""
Conversational AI chat agent for the Travel Planner.
Handles free-form user queries and routes to appropriate services.
Uses IBM Granite for natural language understanding and response generation.
"""
import logging
import json
import re
from granite_client import granite

logger = logging.getLogger(__name__)

# Conversation history per session (keyed by session_id)
_conversation_histories: dict[str, list[dict]] = {}

TRAVEL_AGENT_SYSTEM_PROMPT = """You are an intelligent IBM Travel Planner Agent powered by IBM Granite AI.
You help users plan their perfect trips with personalized recommendations.

Your capabilities include:
- Suggesting travel destinations based on preferences and budget
- Building detailed day-by-day itineraries
- Providing weather forecasts and packing advice
- Recommending transport options (flights, trains, buses)
- Suggesting accommodations (hotels, hostels, resorts, Airbnb)
- Sharing local tips, hidden gems, and cultural etiquette
- Providing visa and entry requirements
- Estimating travel budgets
- Generating packing lists
- Travel safety alerts and advisories
- Optimizing travel schedules

Be warm, helpful, and proactive. Ask clarifying questions when needed.
If the user asks about a specific service (weather, transport, etc.), guide them to use the dedicated tools.
Always provide practical, actionable advice.
"""

INTENT_DETECTION_PROMPT = """Analyze this travel-related user message and detect the intent.
Respond ONLY with a JSON object:
{
  "intent": "one of: destination_suggestion, itinerary_build, weather_check, transport_query, accommodation_query, visa_info, budget_estimate, packing_list, travel_alerts, local_tips, general_chat",
  "entities": {
    "destination": "extracted destination or null",
    "origin": "extracted origin or null",
    "start_date": "YYYY-MM-DD or null",
    "duration_days": number or null,
    "budget": "low/moderate/high/luxury or null",
    "nationality": "country name or null"
  },
  "confidence": 0.95
}

User message: """


def detect_intent(message: str) -> dict:
    """Use IBM Granite to detect intent from user message."""
    try:
        prompt = f"{INTENT_DETECTION_PROMPT}{message}"
        response = granite.generate(prompt, max_tokens=300)
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
    except Exception as exc:
        logger.warning("Intent detection failed: %s", exc)
    return {"intent": "general_chat", "entities": {}, "confidence": 0.5}


def chat(session_id: str, user_message: str) -> dict:
    """
    Process a user message through the IBM Granite travel agent.
    Maintains conversation history per session.
    
    Returns:
        {
            "response": "agent response text",
            "intent": "detected intent",
            "suggestions": ["follow-up suggestion 1", ...],
            "session_id": "session_id"
        }
    """
    # Initialize or retrieve conversation history
    if session_id not in _conversation_histories:
        _conversation_histories[session_id] = [
            {"role": "system", "content": TRAVEL_AGENT_SYSTEM_PROMPT}
        ]

    history = _conversation_histories[session_id]

    # Detect intent for routing hints
    intent_data = detect_intent(user_message)
    intent = intent_data.get("intent", "general_chat")
    entities = intent_data.get("entities", {})

    # Add user message to history
    history.append({"role": "user", "content": user_message})

    try:
        # Generate response using full conversation history
        response_text = granite.chat(history)

        # Add assistant response to history
        history.append({"role": "assistant", "content": response_text})

        # Keep history manageable (last 20 exchanges + system prompt)
        if len(history) > 41:
            _conversation_histories[session_id] = [history[0]] + history[-40:]

        # Generate contextual follow-up suggestions
        suggestions = _generate_suggestions(intent, entities)

        return {
            "response": response_text,
            "intent": intent,
            "entities": entities,
            "suggestions": suggestions,
            "session_id": session_id,
        }

    except Exception as exc:
        logger.error("Chat error for session %s: %s", session_id, exc)
        exc_str = str(exc)
        if "no_associated_service_instance_error" in exc_str:
            error_msg = (
                "IBM Granite connection failed: your watsonx.ai project is not associated with a "
                "Watson Machine Learning (WML) service instance.\n\n"
                "To fix this:\n"
                "1. Go to https://dataplatform.cloud.ibm.com/projects/\n"
                "2. Open your project → Manage → Services & integrations\n"
                "3. Click 'Associate service' and add your Watson Machine Learning instance\n"
                "4. If you don't have a WML instance, create one at https://cloud.ibm.com/catalog/services/watson-machine-learning (Lite tier is free)"
            )
        elif "403" in exc_str or "401" in exc_str or "unauthorized" in exc_str.lower():
            error_msg = (
                "IBM Granite authentication failed (HTTP 403/401). "
                "Please verify your IBM_WATSONX_API_KEY and IBM_WATSONX_PROJECT_ID in the .env file are correct."
            )
        elif "not found" in exc_str.lower() or "404" in exc_str or "model" in exc_str.lower():
            error_msg = (
                "IBM Granite model not found. "
                "Your IBM_GRANITE_MODEL_ID in the .env file is invalid for this account. "
                "Supported model: ibm/granite-4-h-small — please update your .env file."
            )
        elif "Missing IBM watsonx" in exc_str or "EnvironmentError" in exc_str:
            error_msg = (
                "IBM watsonx.ai credentials are missing. "
                "Please set IBM_WATSONX_API_KEY and IBM_WATSONX_PROJECT_ID in your .env file."
            )
        else:
            error_msg = (
                "I apologize, but I'm having trouble connecting to IBM Granite right now. "
                "Please ensure your IBM Cloud credentials are configured in the .env file and try again."
            )
        return {
            "response": error_msg,
            "intent": "error",
            "entities": {},
            "suggestions": [],
            "session_id": session_id,
            "error": str(exc),
        }


def reset_conversation(session_id: str) -> bool:
    """Clear conversation history for a session."""
    if session_id in _conversation_histories:
        del _conversation_histories[session_id]
        return True
    return False


def _generate_suggestions(intent: str, entities: dict) -> list[str]:
    """Generate contextual quick-reply suggestions based on intent."""
    destination = entities.get("destination", "your destination")
    suggestions_map = {
        "destination_suggestion": [
            "Build a full itinerary for one of these",
            "Show me the weather forecast",
            "What are the visa requirements?",
        ],
        "itinerary_build": [
            "Optimize this schedule",
            "Suggest accommodations",
            "What should I pack?",
        ],
        "weather_check": [
            "What should I pack for this weather?",
            "Is this a good time to visit?",
            "Show me the full 7-day forecast",
        ],
        "transport_query": [
            "Find me accommodation options",
            "What are the visa requirements?",
            "Build a complete itinerary",
        ],
        "accommodation_query": [
            "Show me transport options",
            "What activities are nearby?",
            "Estimate my total budget",
        ],
        "visa_info": [
            "What vaccinations do I need?",
            "What documents should I carry?",
            "Show me transport options",
        ],
        "budget_estimate": [
            "How can I reduce costs?",
            "Find budget accommodations",
            "Build an itinerary within this budget",
        ],
        "packing_list": [
            "What's the weather forecast?",
            "Any travel safety alerts?",
            "What are the local customs?",
        ],
        "general_chat": [
            "Suggest a destination for me",
            "Build a travel itinerary",
            "Check weather at a destination",
            "Estimate my travel budget",
        ],
    }
    return suggestions_map.get(intent, suggestions_map["general_chat"])
