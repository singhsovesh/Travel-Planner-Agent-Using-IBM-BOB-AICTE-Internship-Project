"""
Weather service using Open-Meteo API (free, no API key required).
Fetches current & forecast weather for travel planning.
"""
import logging
import requests
from datetime import datetime, timedelta
from config import Config

logger = logging.getLogger(__name__)

# WMO weather code descriptions
WMO_CODES = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Depositing rime fog",
    51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
    61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
    71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow",
    77: "Snow grains",
    80: "Slight showers", 81: "Moderate showers", 82: "Violent showers",
    85: "Slight snow showers", 86: "Heavy snow showers",
    95: "Thunderstorm", 96: "Thunderstorm with hail", 99: "Thunderstorm with heavy hail",
}


def geocode_destination(destination: str) -> tuple[float, float] | None:
    """Resolve a destination name to (lat, lon) via Nominatim."""
    try:
        url = f"{Config.GEOCODING_API_URL}/search"
        params = {"q": destination, "format": "json", "limit": 1}
        headers = {"User-Agent": "IBMTravelPlannerAgent/1.0"}
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if data:
            return float(data[0]["lat"]), float(data[0]["lon"])
    except Exception as exc:
        logger.warning("Geocoding failed for '%s': %s", destination, exc)
    return None


def get_weather_forecast(destination: str, days: int = 7) -> dict:
    """
    Fetch weather forecast for a destination.
    Returns structured dict with current conditions and daily forecast.
    """
    coords = geocode_destination(destination)
    if not coords:
        return {
            "error": f"Could not find location: {destination}",
            "destination": destination,
        }

    lat, lon = coords
    days = min(days, 16)  # Open-Meteo max 16 days

    try:
        url = f"{Config.WEATHER_API_BASE_URL}/forecast"
        params = {
            "latitude": lat,
            "longitude": lon,
            "current": [
                "temperature_2m", "relative_humidity_2m", "wind_speed_10m",
                "weather_code", "apparent_temperature",
            ],
            "daily": [
                "weather_code", "temperature_2m_max", "temperature_2m_min",
                "precipitation_sum", "wind_speed_10m_max", "uv_index_max",
            ],
            "forecast_days": days,
            "timezone": "auto",
        }
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        # Parse current conditions
        current = data.get("current", {})
        current_units = data.get("current_units", {})
        current_parsed = {
            "temperature": f"{current.get('temperature_2m', 'N/A')}{current_units.get('temperature_2m', '°C')}",
            "feels_like": f"{current.get('apparent_temperature', 'N/A')}{current_units.get('apparent_temperature', '°C')}",
            "humidity": f"{current.get('relative_humidity_2m', 'N/A')}%",
            "wind_speed": f"{current.get('wind_speed_10m', 'N/A')} km/h",
            "condition": WMO_CODES.get(current.get("weather_code", -1), "Unknown"),
        }

        # Parse daily forecast
        daily = data.get("daily", {})
        daily_units = data.get("daily_units", {})
        forecast_days = []
        dates = daily.get("time", [])
        for i, date in enumerate(dates):
            forecast_days.append({
                "date": date,
                "condition": WMO_CODES.get(daily.get("weather_code", [])[i] if i < len(daily.get("weather_code", [])) else -1, "Unknown"),
                "max_temp": f"{daily.get('temperature_2m_max', [])[i] if i < len(daily.get('temperature_2m_max', [])) else 'N/A'}{daily_units.get('temperature_2m_max', '°C')}",
                "min_temp": f"{daily.get('temperature_2m_min', [])[i] if i < len(daily.get('temperature_2m_min', [])) else 'N/A'}{daily_units.get('temperature_2m_min', '°C')}",
                "precipitation": f"{daily.get('precipitation_sum', [])[i] if i < len(daily.get('precipitation_sum', [])) else 0} mm",
                "uv_index": daily.get("uv_index_max", [])[i] if i < len(daily.get("uv_index_max", [])) else "N/A",
                "wind_speed": f"{daily.get('wind_speed_10m_max', [])[i] if i < len(daily.get('wind_speed_10m_max', [])) else 'N/A'} km/h",
            })

        return {
            "destination": destination,
            "latitude": lat,
            "longitude": lon,
            "timezone": data.get("timezone", "UTC"),
            "current": current_parsed,
            "forecast": forecast_days,
        }

    except Exception as exc:
        logger.error("Weather fetch error for '%s': %s", destination, exc)
        return {"error": str(exc), "destination": destination}


def weather_summary_text(weather_data: dict) -> str:
    """Convert weather data dict to a compact text summary for LLM context."""
    if "error" in weather_data:
        return f"Weather data unavailable: {weather_data['error']}"

    current = weather_data.get("current", {})
    forecast = weather_data.get("forecast", [])[:5]

    lines = [
        f"Current weather in {weather_data['destination']}: "
        f"{current.get('condition', 'N/A')}, {current.get('temperature', 'N/A')}, "
        f"feels like {current.get('feels_like', 'N/A')}, "
        f"humidity {current.get('humidity', 'N/A')}, wind {current.get('wind_speed', 'N/A')}.",
        "5-day forecast:",
    ]
    for day in forecast:
        lines.append(
            f"  {day['date']}: {day['condition']}, "
            f"High {day['max_temp']} / Low {day['min_temp']}, "
            f"Rain {day['precipitation']}, UV {day['uv_index']}"
        )
    return "\n".join(lines)
