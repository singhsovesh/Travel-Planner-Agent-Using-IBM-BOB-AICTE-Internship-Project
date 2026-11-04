"""
Multi-Agent Architecture for IBM Travel Planner.
Specialist AI agents that each handle a specific domain.
An Orchestrator routes queries to the right agent(s).
"""
import logging
import json
import re
from granite_client import granite

logger = logging.getLogger(__name__)

# ── Base Agent ────────────────────────────────────────────────────────────────

class BaseAgent:
    name: str = "BaseAgent"
    description: str = "Base travel agent"
    system_prompt: str = "You are an IBM Granite AI travel specialist."

    def run(self, query: str, context: dict = None) -> dict:
        ctx_str = f"\nContext: {json.dumps(context)}" if context else ""
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": f"{query}{ctx_str}"},
        ]
        try:
            response = granite.chat(messages)
            return {"agent": self.name, "response": response, "success": True}
        except Exception as exc:
            logger.error("%s error: %s", self.name, exc)
            return {"agent": self.name, "error": str(exc), "success": False}

    def _parse_json(self, text: str) -> dict:
        try:
            m = re.search(r'\{.*\}', text, re.DOTALL)
            return json.loads(m.group()) if m else json.loads(text)
        except Exception:
            return {"raw": text}


# ── Specialist Agents ─────────────────────────────────────────────────────────

class WeatherAgent(BaseAgent):
    name = "WeatherAgent"
    description = "Specialises in weather analysis, seasonal travel advice, and climate comparisons."
    system_prompt = (
        "You are a meteorological travel expert AI powered by IBM Granite. "
        "Specialise in: weather patterns, best travel seasons, climate comparisons, "
        "what to pack for specific weather, and how weather affects travel plans. "
        "Be precise with temperatures and seasonal advice. Always respond in valid JSON when asked."
    )

    def analyze_for_travel(self, destination: str, month: str) -> dict:
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": (
                f"Analyze {destination} weather for {month} from a traveler's perspective.\n"
                "Respond as JSON:\n"
                '{"destination":"","month":"","avg_temp_c":0,"condition":"","rain_days_per_month":0,'
                '"humidity":"low/medium/high","uv_risk":"low/medium/high","best_for":[],'
                '"avoid_if":[],"packing_essentials":[],"weather_verdict":"Great/Good/Fair/Poor"}'
            )},
        ]
        try:
            response = granite.chat(messages)
            return self._parse_json(response)
        except Exception as exc:
            return {"error": str(exc)}


class VisaAgent(BaseAgent):
    name = "VisaAgent"
    description = "Expert on visa requirements, entry conditions, passport validity, and travel documents."
    system_prompt = (
        "You are a visa and immigration specialist AI powered by IBM Granite. "
        "Provide accurate visa information: types, processing times, costs, documents required, "
        "health requirements, passport validity rules, and common rejection reasons. "
        "Always note that information should be verified with official embassy sources. "
        "Respond in valid JSON when requested."
    )

    def check_requirements(self, nationality: str, destination: str) -> dict:
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": (
                f"Detailed visa requirements for {nationality} passport holders traveling to {destination}.\n"
                "JSON format:\n"
                '{"nationality":"","destination":"","visa_required":true,"visa_type":"","'
                'processing_days":0,"fee_usd":0,"validity_days":0,"entries":"single/multiple",'
                '"documents":[],"health_requirements":[],"processing_options":[],'
                '"tips":[],"official_source":"embassy website URL"}'
            )},
        ]
        try:
            response = granite.chat(messages)
            return self._parse_json(response)
        except Exception as exc:
            return {"error": str(exc)}


class BudgetAgent(BaseAgent):
    name = "BudgetAgent"
    description = "Specialist in travel cost optimisation, money-saving strategies, and budget planning."
    system_prompt = (
        "You are a travel budget expert AI powered by IBM Granite. "
        "Specialise in: cost breakdowns, budget optimisation strategies, cheapest travel periods, "
        "free vs paid activities, currency advice, tipping culture, and money-saving hacks. "
        "Be specific with numbers and always provide actionable cost-saving tips."
    )

    def optimize_budget(self, destination: str, current_budget_usd: float, duration_days: int, travelers: int = 1) -> dict:
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": (
                f"Optimize a ${current_budget_usd} USD budget for {travelers} traveler(s) "
                f"going to {destination} for {duration_days} days.\n"
                "JSON format:\n"
                '{"destination":"","budget_usd":0,"daily_budget":0,"is_realistic":true,'
                '"optimized_breakdown":{"accommodation":0,"food":0,"transport":0,"activities":0,"buffer":0},'
                '"free_activities":[],"paid_priorities":[],"money_saving_hacks":[],'
                '"cheapest_booking_platforms":[],"local_price_tips":[],"verdict":"comfortable/tight/impossible"}'
            )},
        ]
        try:
            response = granite.chat(messages)
            return self._parse_json(response)
        except Exception as exc:
            return {"error": str(exc)}


class ItineraryAgent(BaseAgent):
    name = "ItineraryAgent"
    description = "Expert at building optimal day-by-day travel schedules minimising transit time."
    system_prompt = (
        "You are an expert travel itinerary planner AI powered by IBM Granite. "
        "Specialise in: logical sequencing of attractions, minimising transit time between sites, "
        "respecting opening hours, grouping nearby places, optimal meal timing, and rest periods. "
        "Build itineraries that are realistic, enjoyable, and exhaustive. Respond in valid JSON."
    )


class SafetyAgent(BaseAgent):
    name = "SafetyAgent"
    description = "Specialist in travel safety, risk assessment, health advisories, and emergency preparedness."
    system_prompt = (
        "You are a travel safety expert AI powered by IBM Granite. "
        "Specialise in: destination safety levels, crime patterns, health risks, scam warnings, "
        "natural disaster risks, political stability, safe neighborhoods, and emergency procedures. "
        "Always be thorough but not alarmist. Recommend government travel advisory sites for current info."
    )

    def assess_safety(self, destination: str) -> dict:
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": (
                f"Comprehensive safety assessment for travelers visiting {destination}.\n"
                "JSON:\n"
                '{"destination":"","overall_safety":"1-10","safety_rating":"Safe/Moderate/Risky",'
                '"crime_level":"low/medium/high","common_scams":[],"safe_areas":[],"avoid_areas":[],'
                '"health_risks":[],"natural_hazards":[],"political_stability":"stable/unstable",'
                '"solo_female_travel":"safe/moderate/risky","lgbtq_safety":"safe/moderate/risky",'
                '"emergency_numbers":{"police":"","ambulance":"","fire":""},'
                '"travel_advisory_url":"","tips":[]}'
            )},
        ]
        try:
            response = granite.chat(messages)
            return self._parse_json(response)
        except Exception as exc:
            return {"error": str(exc)}


class LocalExpertAgent(BaseAgent):
    name = "LocalExpertAgent"
    description = "Deep local knowledge: hidden gems, authentic experiences, cultural etiquette, food recommendations."
    system_prompt = (
        "You are a local expert travel guide AI powered by IBM Granite. "
        "Specialise in: hidden gems tourists miss, authentic local experiences, cultural dos and don'ts, "
        "best local food spots (not tourist traps), neighborhood character, local festivals, and insider tips. "
        "Think like a well-travelled local resident, not a guidebook."
    )


# ── Orchestrator ──────────────────────────────────────────────────────────────

AGENTS = {
    "weather":   WeatherAgent(),
    "visa":      VisaAgent(),
    "budget":    BudgetAgent(),
    "itinerary": ItineraryAgent(),
    "safety":    SafetyAgent(),
    "local":     LocalExpertAgent(),
}

ROUTING_SYSTEM = """You are a travel query router. Given a user query, identify which specialist agents should handle it.
Available agents: weather, visa, budget, itinerary, safety, local
Respond ONLY with JSON: {"primary_agent": "agent_name", "supporting_agents": ["agent2"], "reason": "brief reason"}"""


def route_query(query: str) -> dict:
    """Use IBM Granite to route a query to the appropriate agent(s)."""
    messages = [
        {"role": "system", "content": ROUTING_SYSTEM},
        {"role": "user", "content": f"Route this travel query: {query}"},
    ]
    try:
        response = granite.chat(messages)
        m = re.search(r'\{.*\}', response, re.DOTALL)
        if m:
            return json.loads(m.group())
    except Exception as exc:
        logger.warning("Routing failed: %s", exc)
    # Default fallback
    return {"primary_agent": "itinerary", "supporting_agents": [], "reason": "default routing"}


def run_multi_agent(query: str, context: dict = None) -> dict:
    """
    Run the multi-agent orchestration.
    Routes the query and runs primary + supporting agents.
    """
    routing = route_query(query)
    primary_name = routing.get("primary_agent", "itinerary")
    support_names = routing.get("supporting_agents", [])

    primary_agent = AGENTS.get(primary_name, AGENTS["itinerary"])
    primary_result = primary_agent.run(query, context)

    supporting_results = []
    for agent_name in support_names[:2]:  # max 2 supporting agents
        agent = AGENTS.get(agent_name)
        if agent:
            result = agent.run(query, context)
            supporting_results.append(result)

    return {
        "routing": routing,
        "primary": primary_result,
        "supporting": supporting_results,
        "agents_used": [primary_name] + support_names[:2],
    }


def get_agent_info() -> list[dict]:
    """Return info about all available agents."""
    return [
        {"id": k, "name": v.name, "description": v.description}
        for k, v in AGENTS.items()
    ]
