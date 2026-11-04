"""
Configuration loader for IBM Travel Planner Agent.
Reads all settings from .env via python-dotenv.
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # ── IBM watsonx.ai ────────────────────────────────────────────────────────
    IBM_WATSONX_API_KEY:    str = os.getenv("IBM_WATSONX_API_KEY", "")
    IBM_WATSONX_URL:        str = os.getenv("IBM_WATSONX_URL", "https://us-south.ml.cloud.ibm.com")
    IBM_WATSONX_PROJECT_ID: str = os.getenv("IBM_WATSONX_PROJECT_ID", "")
    IBM_GRANITE_MODEL_ID:   str = os.getenv("IBM_GRANITE_MODEL_ID", "ibm/granite-4-h-small")

    # ── External APIs ─────────────────────────────────────────────────────────
    WEATHER_API_BASE_URL: str = os.getenv("WEATHER_API_BASE_URL", "https://api.open-meteo.com/v1")
    GEOCODING_API_URL:    str = os.getenv("GEOCODING_API_URL", "https://nominatim.openstreetmap.org")
    EXCHANGERATE_API_KEY: str = os.getenv("EXCHANGERATE_API_KEY", "")        # optional
    PEXELS_API_KEY:       str = os.getenv("PEXELS_API_KEY", "")              # optional

    # ── Database ──────────────────────────────────────────────────────────────
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///travel_agent.db")
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False
    SQLALCHEMY_ECHO: bool = os.getenv("SQLALCHEMY_ECHO", "false").lower() == "true"

    # ── Flask ─────────────────────────────────────────────────────────────────
    FLASK_SECRET_KEY: str = os.getenv("FLASK_SECRET_KEY", "travel_agent_secret_key_change_in_production")
    FLASK_DEBUG:      bool = os.getenv("FLASK_DEBUG", "False").lower() == "true"
    FLASK_HOST:       str  = os.getenv("FLASK_HOST", "0.0.0.0")
    FLASK_PORT:       int  = int(os.getenv("FLASK_PORT", "5000"))

    # ── Mail (Flask-Mail / SMTP) ──────────────────────────────────────────────
    MAIL_SERVER:    str  = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT:      int  = int(os.getenv("MAIL_PORT", "587"))
    MAIL_USE_TLS:   bool = os.getenv("MAIL_USE_TLS", "true").lower() == "true"
    MAIL_USERNAME:  str  = os.getenv("MAIL_USERNAME", "")
    MAIL_PASSWORD:  str  = os.getenv("MAIL_PASSWORD", "")
    MAIL_FROM:      str  = os.getenv("MAIL_FROM", "noreply@ibm-travel-planner.com")
    MAIL_ENABLED:   bool = os.getenv("MAIL_ENABLED", "false").lower() == "true"

    # ── Caching ───────────────────────────────────────────────────────────────
    CACHE_TYPE:              str = os.getenv("CACHE_TYPE", "SimpleCache")
    CACHE_DEFAULT_TIMEOUT:   int = int(os.getenv("CACHE_DEFAULT_TIMEOUT", "3600"))

    # ── Rate Limiting ─────────────────────────────────────────────────────────
    RATELIMIT_DEFAULT:        str = os.getenv("RATELIMIT_DEFAULT", "200 per hour")
    RATELIMIT_STORAGE_URI:    str = os.getenv("RATELIMIT_STORAGE_URI", "memory://")

    # ── Application ───────────────────────────────────────────────────────────
    MAX_ITINERARY_DAYS: int = int(os.getenv("MAX_ITINERARY_DAYS", "14"))
    DEFAULT_CURRENCY:   str = os.getenv("DEFAULT_CURRENCY", "USD")
    APP_NAME:           str = os.getenv("APP_NAME", "IBM Travel Planner Agent")
    APP_VERSION:        str = "2.0.0"

    # ── Granite generation ────────────────────────────────────────────────────
    GRANITE_MAX_TOKENS:  int   = 1500
    GRANITE_TEMPERATURE: float = 0.7
    GRANITE_TOP_P:       float = 0.9

    @classmethod
    def validate(cls) -> list:
        """Return list of missing required config keys."""
        missing = []
        if not cls.IBM_WATSONX_API_KEY or cls.IBM_WATSONX_API_KEY == "your_ibm_cloud_api_key_here":
            missing.append("IBM_WATSONX_API_KEY")
        if not cls.IBM_WATSONX_PROJECT_ID or cls.IBM_WATSONX_PROJECT_ID == "your_watsonx_project_id_here":
            missing.append("IBM_WATSONX_PROJECT_ID")
        return missing

    @classmethod
    def to_flask(cls) -> dict:
        """Return dict of Flask config keys."""
        return {
            "SECRET_KEY":                    cls.FLASK_SECRET_KEY,
            "SQLALCHEMY_DATABASE_URI":       cls.DATABASE_URL,
            "SQLALCHEMY_TRACK_MODIFICATIONS":cls.SQLALCHEMY_TRACK_MODIFICATIONS,
            "SQLALCHEMY_ECHO":               cls.SQLALCHEMY_ECHO,
            "MAIL_SERVER":                   cls.MAIL_SERVER,
            "MAIL_PORT":                     cls.MAIL_PORT,
            "MAIL_USE_TLS":                  cls.MAIL_USE_TLS,
            "MAIL_USERNAME":                 cls.MAIL_USERNAME,
            "MAIL_PASSWORD":                 cls.MAIL_PASSWORD,
            "MAIL_DEFAULT_SENDER":           cls.MAIL_FROM,
            "CACHE_TYPE":                    cls.CACHE_TYPE,
            "CACHE_DEFAULT_TIMEOUT":         cls.CACHE_DEFAULT_TIMEOUT,
            "RATELIMIT_DEFAULT":             cls.RATELIMIT_DEFAULT,
            "RATELIMIT_STORAGE_URI":         cls.RATELIMIT_STORAGE_URI,
        }
