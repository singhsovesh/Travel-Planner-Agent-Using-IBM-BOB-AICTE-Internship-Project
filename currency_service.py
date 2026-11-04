"""
Currency conversion service.
Uses ExchangeRate-API (free tier) with 1-hour in-memory cache.
Falls back to static rates if API unavailable.
"""
import logging
import time
import requests

logger = logging.getLogger(__name__)

# ── Static fallback rates (USD base, updated periodically) ──────────────────
FALLBACK_RATES = {
    "USD": 1.0, "EUR": 0.92, "GBP": 0.79, "INR": 83.5,
    "JPY": 149.5, "AED": 3.67, "AUD": 1.53, "CAD": 1.36,
    "CHF": 0.88, "CNY": 7.24, "SGD": 1.34, "THB": 35.2,
    "MYR": 4.71, "IDR": 15700, "PHP": 56.8, "KRW": 1330,
    "BRL": 4.97, "MXN": 17.1, "ZAR": 18.6, "EGP": 30.9,
    "TRY": 32.1, "NZD": 1.63, "HKD": 7.82, "SEK": 10.4,
    "NOK": 10.6, "DKK": 6.88, "PLN": 4.02, "CZK": 22.8,
    "HUF": 354, "ILS": 3.72, "SAR": 3.75, "QAR": 3.64,
}

CURRENCY_NAMES = {
    "USD": "US Dollar", "EUR": "Euro", "GBP": "British Pound",
    "INR": "Indian Rupee", "JPY": "Japanese Yen", "AED": "UAE Dirham",
    "AUD": "Australian Dollar", "CAD": "Canadian Dollar",
    "CHF": "Swiss Franc", "CNY": "Chinese Yuan", "SGD": "Singapore Dollar",
    "THB": "Thai Baht", "MYR": "Malaysian Ringgit", "IDR": "Indonesian Rupiah",
    "PHP": "Philippine Peso", "KRW": "South Korean Won",
    "BRL": "Brazilian Real", "MXN": "Mexican Peso", "ZAR": "South African Rand",
    "SAR": "Saudi Riyal", "QAR": "Qatari Riyal", "NZD": "New Zealand Dollar",
    "HKD": "Hong Kong Dollar", "SEK": "Swedish Krona",
}

CURRENCY_SYMBOLS = {
    "USD": "$", "EUR": "€", "GBP": "£", "INR": "₹", "JPY": "¥",
    "AED": "د.إ", "AUD": "A$", "CAD": "C$", "CHF": "Fr", "CNY": "¥",
    "SGD": "S$", "THB": "฿", "KRW": "₩", "BRL": "R$", "SAR": "﷼",
    "NZD": "NZ$", "HKD": "HK$", "QAR": "QR",
}

# ── Cache ────────────────────────────────────────────────────────────────────
_cache: dict = {"rates": {}, "last_fetch": 0}
CACHE_TTL = 3600  # 1 hour


def _fetch_rates() -> dict:
    """Fetch latest rates from ExchangeRate-API (free, no key needed for basic)."""
    now = time.time()
    if _cache["rates"] and (now - _cache["last_fetch"]) < CACHE_TTL:
        return _cache["rates"]
    try:
        # Free endpoint — no API key needed for USD base
        resp = requests.get(
            "https://open.er-api.com/v6/latest/USD",
            timeout=8,
        )
        if resp.status_code == 200:
            data = resp.json()
            if data.get("result") == "success":
                _cache["rates"] = data["rates"]
                _cache["last_fetch"] = now
                logger.info("Currency rates refreshed from ExchangeRate-API")
                return _cache["rates"]
    except Exception as exc:
        logger.warning("Currency API unavailable, using fallback rates: %s", exc)
    # Fallback
    _cache["rates"] = FALLBACK_RATES.copy()
    _cache["last_fetch"] = now
    return _cache["rates"]


def convert(amount: float, from_currency: str, to_currency: str) -> dict:
    """Convert an amount between two currencies."""
    from_c = from_currency.upper()
    to_c = to_currency.upper()
    rates = _fetch_rates()

    if from_c not in rates or to_c not in rates:
        return {"error": f"Unsupported currency: {from_c} or {to_c}"}

    # Convert via USD base
    amount_usd = amount / rates[from_c]
    converted = amount_usd * rates[to_c]

    return {
        "from_currency": from_c,
        "to_currency": to_c,
        "from_amount": round(amount, 2),
        "to_amount": round(converted, 2),
        "rate": round(rates[to_c] / rates[from_c], 6),
        "symbol": CURRENCY_SYMBOLS.get(to_c, to_c),
        "name": CURRENCY_NAMES.get(to_c, to_c),
    }


def convert_budget(budget_usd: float, target_currencies: list[str] = None) -> dict:
    """Convert a USD budget into multiple currencies at once."""
    targets = target_currencies or ["EUR", "GBP", "INR", "JPY", "AED", "AUD"]
    rates = _fetch_rates()
    result = {
        "original_usd": budget_usd,
        "conversions": {},
        "rates_timestamp": _cache["last_fetch"],
    }
    for cur in targets:
        c = cur.upper()
        if c in rates:
            amount = round(budget_usd * rates[c], 2)
            result["conversions"][c] = {
                "amount": amount,
                "symbol": CURRENCY_SYMBOLS.get(c, c),
                "name": CURRENCY_NAMES.get(c, c),
                "rate": round(rates[c], 4),
            }
    return result


def get_supported_currencies() -> list[dict]:
    """Return list of all supported currencies."""
    rates = _fetch_rates()
    result = []
    for code in sorted(rates.keys()):
        result.append({
            "code": code,
            "name": CURRENCY_NAMES.get(code, code),
            "symbol": CURRENCY_SYMBOLS.get(code, code),
            "rate_vs_usd": round(rates[code], 4),
        })
    return result
