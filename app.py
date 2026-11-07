"""
IBM Travel Planner Agent — Production Flask Application v2.0
All endpoints with caching, rate limiting, auth, and streaming AI.
"""
import io
import json
import logging
import uuid
from datetime import datetime, timezone

from flask import Flask, request, jsonify, render_template, Response, stream_with_context, send_file
from flask_cors import CORS
from flask_login import current_user, login_required
from flask_mail import Mail, Message
from flask_caching import Cache
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from config import Config
from models import db, User, Booking, SavedItinerary, ChatSession, AnalyticsEvent

# Services
from weather_service import get_weather_forecast
from destination_service import suggest_destinations, describe_destination, get_local_tips
from itinerary_service import build_itinerary, optimize_itinerary, estimate_budget
from transport_accommodation_service import (
    get_transport_options, get_accommodation_recommendations, get_visa_information,
)
from booking_service import optimize_schedule, check_travel_alerts, get_packing_list
from chat_agent import chat, reset_conversation
from currency_service import convert, convert_budget, get_supported_currencies
from pdf_service import generate_itinerary_pdf, generate_booking_pdf
from analytics_service import estimate_carbon_footprint, get_trip_stats, get_global_popular_destinations
from templates_service import list_templates, get_template, clone_template, get_categories
from agents import run_multi_agent, get_agent_info
from auth import auth_bp, login_manager

# ── App Setup ─────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config.update(Config.to_flask())

# Extensions
CORS(app, supports_credentials=True)
db.init_app(app)
login_manager.init_app(app)
mail = Mail(app)
cache = Cache(app)
limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=["300 per hour", "60 per minute"],
    storage_uri=Config.RATELIMIT_STORAGE_URI,
)

# Blueprints
app.register_blueprint(auth_bp)

# Create tables on first run
with app.app_context():
    db.create_all()
    logger.info("Database tables created/verified")


# ── Analytics helper ──────────────────────────────────────────────────────────
def _track(event_type: str, destination: str = None, metadata: dict = None):
    try:
        event = AnalyticsEvent(
            user_id=current_user.id if current_user.is_authenticated else None,
            event_type=event_type,
            destination=destination,
            metadata_json=json.dumps(metadata or {}),
        )
        db.session.add(event)
        db.session.commit()
    except Exception:
        pass  # analytics must never break core flow


# ── Health ────────────────────────────────────────────────────────────────────

@app.route("/api/health", methods=["GET"])
def health():
    missing = Config.validate()
    return jsonify({
        "status": "ok",
        "app": Config.APP_NAME,
        "version": Config.APP_VERSION,
        "model": Config.IBM_GRANITE_MODEL_ID,
        "ibm_credentials_configured": len(missing) == 0,
        "missing_credentials": missing,
        "authenticated": current_user.is_authenticated,
        "features": ["auth", "db", "pdf", "currency", "streaming", "caching", "rate-limiting",
                     "multi-agent", "analytics", "templates", "pwa"],
    })


# ── Chat ──────────────────────────────────────────────────────────────────────

@app.route("/api/chat", methods=["POST"])
@limiter.limit("30 per minute")
def chat_endpoint():
    data = request.get_json(force=True)
    message = (data.get("message") or "").strip()
    if not message:
        return jsonify({"error": "message is required"}), 400
    session_id = data.get("session_id") or str(uuid.uuid4())
    result = chat(session_id, message)
    _track("chat", metadata={"session_id": session_id, "intent": result.get("intent")})
    return jsonify(result)


@app.route("/api/chat/stream", methods=["POST"])
@limiter.limit("20 per minute")
def chat_stream():
    """Server-Sent Events streaming chat endpoint."""
    data = request.get_json(force=True)
    message = (data.get("message") or "").strip()
    if not message:
        return jsonify({"error": "message is required"}), 400
    session_id = data.get("session_id") or str(uuid.uuid4())

    def generate():
        try:
            from granite_client import granite
            from chat_agent import TRAVEL_AGENT_SYSTEM_PROMPT, detect_intent, _generate_suggestions, _conversation_histories

            if session_id not in _conversation_histories:
                _conversation_histories[session_id] = [{"role": "system", "content": TRAVEL_AGENT_SYSTEM_PROMPT}]
            history = _conversation_histories[session_id]
            intent_data = detect_intent(message)
            intent = intent_data.get("intent", "general_chat")
            history.append({"role": "user", "content": message})

            # Send intent first
            yield f"data: {json.dumps({'type': 'intent', 'intent': intent})}\n\n"

            # Stream the response
            full_response = []
            try:
                stream = granite.stream(history)
                for chunk in stream:
                    if chunk:
                        full_response.append(chunk)
                        yield f"data: {json.dumps({'type': 'chunk', 'text': chunk})}\n\n"
            except Exception:
                # Fallback: non-streaming
                response_text = granite.chat(history)
                full_response.append(response_text)
                # Simulate streaming by sending the full text in one chunk
                yield f"data: {json.dumps({'type': 'chunk', 'text': response_text})}\n\n"

            complete_text = "".join(full_response)
            history.append({"role": "assistant", "content": complete_text})
            if len(history) > 41:
                _conversation_histories[session_id] = [history[0]] + history[-40:]

            suggestions = _generate_suggestions(intent, intent_data.get("entities", {}))
            yield f"data: {json.dumps({'type': 'done', 'suggestions': suggestions, 'session_id': session_id})}\n\n"

        except Exception as exc:
            yield f"data: {json.dumps({'type': 'error', 'message': str(exc)})}\n\n"

    return Response(stream_with_context(generate()), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.route("/api/chat/reset", methods=["POST"])
def reset_chat():
    data = request.get_json(force=True)
    session_id = data.get("session_id", "")
    reset_conversation(session_id)
    return jsonify({"status": "reset", "session_id": session_id})


# ── Destinations ──────────────────────────────────────────────────────────────

@app.route("/api/destinations/suggest", methods=["POST"])
@limiter.limit("20 per minute")
@cache.cached(timeout=1800, key_prefix=lambda: f"dest_suggest_{request.get_json(force=True)}")
def suggest_destinations_endpoint():
    data = request.get_json(force=True)
    result = suggest_destinations(
        preferences=data.get("preferences", ""),
        budget=data.get("budget", "moderate"),
        duration_days=int(data.get("duration_days", 7)),
        departure_from=data.get("departure_from", ""),
        travel_style=data.get("travel_style", "balanced"),
    )
    _track("destination_suggest", metadata={"budget": data.get("budget")})
    return jsonify(result)


@app.route("/api/destinations/describe", methods=["POST"])
@limiter.limit("30 per minute")
def describe_destination_endpoint():
    data = request.get_json(force=True)
    destination = data.get("destination", "")
    if not destination:
        return jsonify({"error": "destination is required"}), 400
    description = describe_destination(destination, focus=data.get("focus", "general"))
    _track("destination_describe", destination=destination)
    return jsonify({"destination": destination, "description": description})


@app.route("/api/destinations/local-tips", methods=["POST"])
@limiter.limit("20 per minute")
def local_tips_endpoint():
    data = request.get_json(force=True)
    destination = data.get("destination", "")
    if not destination:
        return jsonify({"error": "destination is required"}), 400
    result = get_local_tips(destination, interests=data.get("interests", []))
    _track("local_tips", destination=destination)
    return jsonify(result)


@app.route("/api/destinations/popular", methods=["GET"])
@cache.cached(timeout=86400)
def popular_destinations():
    return jsonify({"destinations": get_global_popular_destinations()})


# ── Weather ────────────────────────────────────────────────────────────────────

@app.route("/api/weather", methods=["POST"])
@limiter.limit("60 per minute")
@cache.cached(timeout=3600, key_prefix=lambda: f"weather_{request.get_json(force=True).get('destination','')}_{request.get_json(force=True).get('days',7)}")
def weather_endpoint():
    data = request.get_json(force=True)
    destination = data.get("destination", "")
    if not destination:
        return jsonify({"error": "destination is required"}), 400
    result = get_weather_forecast(destination, days=int(data.get("days", 7)))
    _track("weather_check", destination=destination)
    return jsonify(result)


# ── Itinerary ─────────────────────────────────────────────────────────────────

@app.route("/api/itinerary/build", methods=["POST"])
@limiter.limit("10 per minute")
def build_itinerary_endpoint():
    data = request.get_json(force=True)
    destination = data.get("destination", "")
    start_date  = data.get("start_date", "")
    if not destination or not start_date:
        return jsonify({"error": "destination and start_date are required"}), 400
    result = build_itinerary(
        destination=destination,
        start_date=start_date,
        duration_days=int(data.get("duration_days", 7)),
        preferences=data.get("preferences", ""),
        budget=data.get("budget", "moderate"),
        travel_style=data.get("travel_style", "balanced"),
        accommodation_type=data.get("accommodation_type", "hotel"),
        include_weather=data.get("include_weather", True),
    )
    _track("itinerary_build", destination=destination)
    return jsonify(result)


@app.route("/api/itinerary/optimize", methods=["POST"])
@limiter.limit("10 per minute")
def optimize_itinerary_endpoint():
    data = request.get_json(force=True)
    itinerary = data.get("itinerary", {})
    feedback  = data.get("feedback", "")
    if not itinerary:
        return jsonify({"error": "itinerary is required"}), 400
    return jsonify(optimize_itinerary(itinerary, feedback))


@app.route("/api/itinerary/save", methods=["POST"])
@limiter.limit("20 per minute")
def save_itinerary():
    """Save an itinerary to the database."""
    data      = request.get_json(force=True)
    itinerary = data.get("itinerary", {})
    if not itinerary:
        return jsonify({"error": "itinerary is required"}), 400
    saved = SavedItinerary(
        user_id=current_user.id if current_user.is_authenticated else None,
        destination=itinerary.get("destination", ""),
        title=data.get("title", f"Trip to {itinerary.get('destination', 'Unknown')}"),
        duration_days=itinerary.get("duration_days", 7),
        budget_level=itinerary.get("budget_level", "moderate"),
        is_public=data.get("is_public", False),
        data_json=json.dumps(itinerary),
    )
    db.session.add(saved)
    db.session.commit()
    return jsonify({"message": "Itinerary saved", "id": saved.id}), 201


@app.route("/api/itinerary/<itin_id>", methods=["GET"])
def get_saved_itinerary(itin_id):
    itin = db.session.get(SavedItinerary, itin_id)
    if not itin:
        return jsonify({"error": "Itinerary not found"}), 404
    if not itin.is_public and (not current_user.is_authenticated or itin.user_id != current_user.id):
        return jsonify({"error": "Not authorized"}), 403
    return jsonify(itin.to_dict())


@app.route("/api/itinerary/budget", methods=["POST"])
@limiter.limit("20 per minute")
def budget_estimate_endpoint():
    data = request.get_json(force=True)
    destination = data.get("destination", "")
    if not destination:
        return jsonify({"error": "destination is required"}), 400
    result = estimate_budget(
        destination=destination,
        duration_days=int(data.get("duration_days", 7)),
        travel_style=data.get("travel_style", "balanced"),
        num_travelers=int(data.get("num_travelers", 1)),
    )
    _track("budget_estimate", destination=destination)
    return jsonify(result)


# ── PDF Export ────────────────────────────────────────────────────────────────

@app.route("/api/itinerary/pdf", methods=["POST"])
@limiter.limit("10 per minute")
def export_itinerary_pdf():
    data = request.get_json(force=True)
    itinerary = data.get("itinerary", {})
    if not itinerary:
        return jsonify({"error": "itinerary is required"}), 400
    try:
        pdf_bytes = generate_itinerary_pdf(itinerary)
        dest = itinerary.get("destination", "itinerary").replace(",", "").replace(" ", "_")
        return send_file(
            io.BytesIO(pdf_bytes),
            mimetype="application/pdf",
            as_attachment=True,
            download_name=f"itinerary_{dest}.pdf",
        )
    except Exception as exc:
        logger.error("PDF generation error: %s", exc)
        return jsonify({"error": f"PDF generation failed: {exc}"}), 500


@app.route("/api/bookings/<booking_id>/pdf", methods=["GET"])
@limiter.limit("10 per minute")
def export_booking_pdf(booking_id):
    booking = db.session.get(Booking, booking_id.upper())
    if not booking:
        return jsonify({"error": "Booking not found"}), 404
    try:
        pdf_bytes = generate_booking_pdf(booking.to_dict())
        return send_file(
            io.BytesIO(pdf_bytes),
            mimetype="application/pdf",
            as_attachment=True,
            download_name=f"booking_TRV-{booking_id}.pdf",
        )
    except Exception as exc:
        return jsonify({"error": f"PDF generation failed: {exc}"}), 500


# ── Currency ──────────────────────────────────────────────────────────────────

@app.route("/api/currency/convert", methods=["POST"])
@limiter.limit("120 per minute")
def currency_convert():
    data = request.get_json(force=True)
    amount       = float(data.get("amount", 0))
    from_currency = data.get("from", "USD")
    to_currency   = data.get("to", "INR")
    return jsonify(convert(amount, from_currency, to_currency))


@app.route("/api/currency/budget", methods=["POST"])
@limiter.limit("60 per minute")
def currency_budget():
    data = request.get_json(force=True)
    budget_usd = float(data.get("budget_usd", 0))
    currencies = data.get("currencies", ["EUR", "GBP", "INR", "JPY", "AED", "AUD"])
    return jsonify(convert_budget(budget_usd, currencies))


@app.route("/api/currency/list", methods=["GET"])
@cache.cached(timeout=3600)
def currency_list():
    return jsonify({"currencies": get_supported_currencies()})


# ── Transport & Accommodation ─────────────────────────────────────────────────

@app.route("/api/transport", methods=["POST"])
@limiter.limit("20 per minute")
def transport_endpoint():
    data = request.get_json(force=True)
    origin      = data.get("origin", "")
    destination = data.get("destination", "")
    if not origin or not destination:
        return jsonify({"error": "origin and destination are required"}), 400
    result = get_transport_options(
        origin=origin, destination=destination,
        travel_date=data.get("travel_date", ""),
        budget=data.get("budget", "moderate"),
        preferences=data.get("preferences", ""),
    )
    _track("transport_query", destination=destination)
    return jsonify(result)


@app.route("/api/accommodation", methods=["POST"])
@limiter.limit("20 per minute")
def accommodation_endpoint():
    data = request.get_json(force=True)
    destination = data.get("destination", "")
    if not destination:
        return jsonify({"error": "destination is required"}), 400
    result = get_accommodation_recommendations(
        destination=destination,
        check_in=data.get("check_in", ""),
        check_out=data.get("check_out", ""),
        budget=data.get("budget", "moderate"),
        accommodation_type=data.get("accommodation_type", "hotel"),
        num_guests=int(data.get("num_guests", 1)),
        preferences=data.get("preferences", ""),
    )
    _track("accommodation_query", destination=destination)
    return jsonify(result)


@app.route("/api/visa", methods=["POST"])
@limiter.limit("20 per minute")
@cache.cached(timeout=86400, key_prefix=lambda: f"visa_{request.get_json(force=True).get('nationality','')}_{request.get_json(force=True).get('destination_country','')}")
def visa_endpoint():
    data = request.get_json(force=True)
    nationality         = data.get("nationality", "")
    destination_country = data.get("destination_country", "")
    if not nationality or not destination_country:
        return jsonify({"error": "nationality and destination_country are required"}), 400
    result = get_visa_information(nationality, destination_country)
    _track("visa_check", destination=destination_country)
    return jsonify(result)


# ── Bookings (DB-backed) ──────────────────────────────────────────────────────

@app.route("/api/bookings", methods=["GET"])
def list_bookings_endpoint():
    if current_user.is_authenticated:
        bookings = Booking.query.filter_by(user_id=current_user.id).order_by(Booking.start_date).all()
    else:
        # Return session-scoped bookings (stored in cookie session_bookings)
        from flask import session as flask_session
        ids = flask_session.get("booking_ids", [])
        bookings = [Booking.query.get(bid) for bid in ids if Booking.query.get(bid)]
    return jsonify({"bookings": [b.to_dict() for b in bookings if b]})


@app.route("/api/bookings", methods=["POST"])
@limiter.limit("30 per minute")
def create_booking_endpoint():
    from flask import session as flask_session
    data = request.get_json(force=True)
    required = ["trip_name", "destination", "start_date", "end_date", "traveler_name"]
    missing_fields = [f for f in required if not data.get(f)]
    if missing_fields:
        return jsonify({"error": f"Missing required fields: {', '.join(missing_fields)}"}), 400

    import uuid as _uuid_mod
    booking_id = str(_uuid_mod.uuid4())[:8].upper()
    booking = Booking(
        id=booking_id,
        user_id=current_user.id if current_user.is_authenticated else None,
        trip_name=data["trip_name"],
        destination=data["destination"],
        start_date=data["start_date"],
        end_date=data["end_date"],
        traveler_name=data["traveler_name"],
        booking_type=data.get("booking_type", "trip"),
        status="confirmed",
        details_json=json.dumps(data.get("details", {})),
        alerts_json="[]",
    )
    db.session.add(booking)
    db.session.commit()

    # Track anonymous session bookings
    if not current_user.is_authenticated:
        ids = flask_session.get("booking_ids", [])
        ids.append(booking_id)
        flask_session["booking_ids"] = ids

    _track("booking_create", destination=data["destination"])
    logger.info("Booking created: %s for %s", booking_id, data["destination"])
    return jsonify(booking.to_dict()), 201


@app.route("/api/bookings/<booking_id>", methods=["GET"])
def get_booking_endpoint(booking_id):
    booking = db.session.get(Booking, booking_id.upper())
    if not booking:
        return jsonify({"error": "Booking not found"}), 404
    return jsonify(booking.to_dict())


@app.route("/api/bookings/<booking_id>", methods=["PUT"])
def update_booking_endpoint(booking_id):
    booking = db.session.get(Booking, booking_id.upper())
    if not booking:
        return jsonify({"error": "Booking not found"}), 404
    data = request.get_json(force=True)
    for field in ["trip_name", "destination", "start_date", "end_date", "traveler_name", "booking_type", "status"]:
        if field in data:
            setattr(booking, field, data[field])
    if "details" in data:
        booking.details_json = json.dumps(data["details"])
    db.session.commit()
    return jsonify(booking.to_dict())


@app.route("/api/bookings/<booking_id>/cancel", methods=["POST"])
def cancel_booking_endpoint(booking_id):
    booking = db.session.get(Booking, booking_id.upper())
    if not booking:
        return jsonify({"error": "Booking not found"}), 404
    booking.status = "cancelled"
    db.session.commit()
    return jsonify(booking.to_dict())


@app.route("/api/bookings/<booking_id>/alerts", methods=["POST"])
def add_alert_endpoint(booking_id):
    booking = db.session.get(Booking, booking_id.upper())
    if not booking:
        return jsonify({"error": "Booking not found"}), 404
    data = request.get_json(force=True)
    message = data.get("message", "")
    if not message:
        return jsonify({"error": "message is required"}), 400
    alerts = json.loads(booking.alerts_json or "[]")
    alerts.append({
        "id": str(uuid.uuid4())[:6],
        "type": data.get("type", "info"),
        "message": message,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "read": False,
    })
    booking.alerts_json = json.dumps(alerts)
    db.session.commit()
    return jsonify(booking.to_dict())


# ── Multi-Agent ───────────────────────────────────────────────────────────────

@app.route("/api/agents/list", methods=["GET"])
def list_agents():
    return jsonify({"agents": get_agent_info()})


@app.route("/api/agents/run", methods=["POST"])
@limiter.limit("15 per minute")
def run_agent():
    data    = request.get_json(force=True)
    query   = data.get("query", "")
    context = data.get("context", {})
    if not query:
        return jsonify({"error": "query is required"}), 400
    result = run_multi_agent(query, context)
    _track("agent_run", metadata={"agents": result.get("agents_used", [])})
    return jsonify(result)


# ── Analytics ─────────────────────────────────────────────────────────────────

@app.route("/api/analytics/stats", methods=["GET"])
def analytics_stats():
    if current_user.is_authenticated:
        bookings = [b.to_dict() for b in Booking.query.filter_by(user_id=current_user.id).all()]
    else:
        from flask import session as flask_session
        ids = flask_session.get("booking_ids", [])
        bookings = [b.to_dict() for bid in ids if (b := db.session.get(Booking, bid))]
    return jsonify(get_trip_stats(bookings))


@app.route("/api/analytics/carbon", methods=["POST"])
def carbon_footprint():
    data = request.get_json(force=True)
    destination    = data.get("destination", "")
    transport_mode = data.get("transport_mode", "flight")
    distance_km    = data.get("distance_km")
    if not destination:
        return jsonify({"error": "destination is required"}), 400
    return jsonify(estimate_carbon_footprint(destination, transport_mode, distance_km))


@app.route("/api/analytics/popular", methods=["GET"])
@cache.cached(timeout=3600)
def analytics_popular():
    return jsonify({"destinations": get_global_popular_destinations()})


# ── Itinerary Templates ───────────────────────────────────────────────────────

@app.route("/api/templates", methods=["GET"])
@cache.cached(timeout=1800, key_prefix=lambda: f"tpl_{request.args.get('category','')}_{request.args.get('budget','')}_{request.args.get('max_days','')}")
def get_templates():
    return jsonify({
        "templates": list_templates(
            category=request.args.get("category"),
            budget=request.args.get("budget"),
            max_days=int(request.args.get("max_days", 0)) or None,
        ),
        "categories": get_categories(),
    })


@app.route("/api/templates/<template_id>", methods=["GET"])
def get_template_endpoint(template_id):
    tpl = get_template(template_id)
    if not tpl:
        return jsonify({"error": "Template not found"}), 404
    return jsonify(tpl)


@app.route("/api/templates/<template_id>/clone", methods=["POST"])
@limiter.limit("20 per minute")
def clone_template_endpoint(template_id):
    data = request.get_json(force=True)
    result = clone_template(
        template_id,
        start_date=data.get("start_date"),
        customizations=data.get("customizations"),
    )
    _track("template_clone", metadata={"template_id": template_id})
    return jsonify(result)


# ── AI-powered Utilities ──────────────────────────────────────────────────────

@app.route("/api/schedule/optimize", methods=["POST"])
@limiter.limit("10 per minute")
def schedule_optimize_endpoint():
    data = request.get_json(force=True)
    itinerary = data.get("itinerary", {})
    if not itinerary:
        return jsonify({"error": "itinerary is required"}), 400
    return jsonify(optimize_schedule(itinerary, constraints=data.get("constraints", "")))


@app.route("/api/alerts", methods=["POST"])
@limiter.limit("20 per minute")
def travel_alerts_endpoint():
    data = request.get_json(force=True)
    destination = data.get("destination", "")
    if not destination:
        return jsonify({"error": "destination is required"}), 400
    result = check_travel_alerts(destination, travel_date=data.get("travel_date", ""))
    _track("travel_alerts", destination=destination)
    return jsonify(result)


@app.route("/api/packing-list", methods=["POST"])
@limiter.limit("20 per minute")
def packing_list_endpoint():
    data = request.get_json(force=True)
    destination = data.get("destination", "")
    if not destination:
        return jsonify({"error": "destination is required"}), 400
    result = get_packing_list(
        destination=destination,
        duration_days=int(data.get("duration_days", 7)),
        climate=data.get("climate", "temperate"),
        activities=data.get("activities", []),
    )
    _track("packing_list", destination=destination)
    return jsonify(result)


# ── My Saved Itineraries ──────────────────────────────────────────────────────

@app.route("/api/my/itineraries", methods=["GET"])
@login_required
def my_itineraries():
    itins = SavedItinerary.query.filter_by(user_id=current_user.id).order_by(SavedItinerary.created_at.desc()).all()
    return jsonify({"itineraries": [i.to_dict() for i in itins]})


@app.route("/api/my/itineraries/<itin_id>", methods=["DELETE"])
@login_required
def delete_itinerary(itin_id):
    itin = db.session.get(SavedItinerary, itin_id)
    if not itin or itin.user_id != current_user.id:
        return jsonify({"error": "Not found or not authorized"}), 404
    db.session.delete(itin)
    db.session.commit()
    return jsonify({"message": "Deleted"})


# ── PWA Manifest ──────────────────────────────────────────────────────────────

@app.route("/manifest.json")
def pwa_manifest():
    return jsonify({
        "name": "IBM Travel Planner Agent",
        "short_name": "TravelAI",
        "description": "AI-powered travel planning with IBM Granite",
        "start_url": "/app",
        "display": "standalone",
        "background_color": "#161616",
        "theme_color": "#0f62fe",
        "orientation": "portrait-primary",
        "icons": [
            {"src": "/static/icons/icon-192.png", "sizes": "192x192", "type": "image/png"},
            {"src": "/static/icons/icon-512.png", "sizes": "512x512", "type": "image/png"},
        ],
        "categories": ["travel", "productivity"],
        "shortcuts": [
            {"name": "AI Chat", "url": "/app", "description": "Chat with AI travel agent"},
            {"name": "Book Trip", "url": "/book", "description": "Manual trip booking"},
        ],
    })


@app.route("/service-worker.js")
def service_worker():
    sw_content = """
const CACHE_NAME = 'ibm-travel-v3';
const STATIC_ASSETS = ['/', '/app', '/book', '/static/css/style.css', '/static/js/app.js'];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE_NAME).then(c => c.addAll(STATIC_ASSETS)));
  self.skipWaiting();
});

self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(keys =>
    Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k)))
  ));
  self.clients.claim();
});

self.addEventListener('fetch', e => {
  if (e.request.url.includes('/api/')) return; // Never cache API calls
  e.respondWith(
    caches.match(e.request).then(cached => cached || fetch(e.request).then(response => {
      const clone = response.clone();
      caches.open(CACHE_NAME).then(c => c.put(e.request, clone));
      return response;
    })).catch(() => caches.match('/'))
  );
});
"""
    return Response(sw_content, mimetype="application/javascript")


# ── Frontend Pages ────────────────────────────────────────────────────────────

@app.route("/")
def home():
    return render_template("home.html", app_name=Config.APP_NAME)

@app.route("/app")
@app.route("/home")
def index():
    return render_template("index.html", app_name=Config.APP_NAME)

@app.route("/book")
def book():
    return render_template("book.html", app_name=Config.APP_NAME)

@app.route("/login")
def login_page():
    return render_template("login.html", app_name=Config.APP_NAME)

@app.route("/register")
def register_page():
    return render_template("register.html", app_name=Config.APP_NAME)

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html", app_name=Config.APP_NAME)


# ── Error Handlers ────────────────────────────────────────────────────────────

@app.errorhandler(404)
def not_found(e):
    if request.path.startswith("/api/"):
        return jsonify({"error": "Endpoint not found"}), 404
    return render_template("home.html", app_name=Config.APP_NAME), 404

@app.errorhandler(429)
def rate_limited(e):
    return jsonify({"error": "Rate limit exceeded. Please slow down.", "retry_after": str(e.description)}), 429

@app.errorhandler(500)
def server_error(e):
    if request.path.startswith("/api/"):
        return jsonify({"error": "Internal server error", "detail": str(e)}), 500
    return render_template("home.html", app_name=Config.APP_NAME), 500


# ── Entry Point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    logger.info("Starting %s v%s on %s:%s", Config.APP_NAME, Config.APP_VERSION, Config.FLASK_HOST, Config.FLASK_PORT)
    missing = Config.validate()
    if missing:
        logger.warning("IBM Credentials not configured: %s", missing)
    app.run(host=Config.FLASK_HOST, port=Config.FLASK_PORT, debug=Config.FLASK_DEBUG)
