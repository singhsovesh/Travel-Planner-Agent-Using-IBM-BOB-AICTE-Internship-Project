"""
SQLAlchemy database models for IBM Travel Planner Agent.
Replaces the in-memory dicts with persistent storage.
"""
from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import uuid

db = SQLAlchemy()


def _uuid():
    return str(uuid.uuid4())


def _now():
    return datetime.now(timezone.utc)


# ── User ──────────────────────────────────────────────────────────────────────

class User(db.Model, UserMixin):
    __tablename__ = "users"

    id         = db.Column(db.String(36), primary_key=True, default=_uuid)
    email      = db.Column(db.String(255), unique=True, nullable=False, index=True)
    username   = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    first_name = db.Column(db.String(80), default="")
    last_name  = db.Column(db.String(80), default="")
    nationality= db.Column(db.String(80), default="")
    phone      = db.Column(db.String(30), default="")
    avatar_color = db.Column(db.String(10), default="#0f62fe")

    # Preferences (stored as JSON string)
    travel_style   = db.Column(db.String(30), default="balanced")
    budget_pref    = db.Column(db.String(20), default="moderate")
    currency_pref  = db.Column(db.String(10), default="USD")
    language_pref  = db.Column(db.String(10), default="en")
    home_city      = db.Column(db.String(100), default="")

    is_active  = db.Column(db.Boolean, default=True)
    is_verified= db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime(timezone=True), default=_now)
    last_login = db.Column(db.DateTime(timezone=True), nullable=True)

    # Relationships
    bookings    = db.relationship("Booking", backref="user", lazy="dynamic", cascade="all,delete")
    itineraries = db.relationship("SavedItinerary", backref="user", lazy="dynamic", cascade="all,delete")
    chat_sessions = db.relationship("ChatSession", backref="user", lazy="dynamic", cascade="all,delete")

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "username": self.username,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "nationality": self.nationality,
            "phone": self.phone,
            "travel_style": self.travel_style,
            "budget_pref": self.budget_pref,
            "currency_pref": self.currency_pref,
            "language_pref": self.language_pref,
            "home_city": self.home_city,
            "avatar_color": self.avatar_color,
            "is_verified": self.is_verified,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f"<User {self.username}>"


# ── Booking ───────────────────────────────────────────────────────────────────

class Booking(db.Model):
    __tablename__ = "bookings"

    id            = db.Column(db.String(8), primary_key=True)
    user_id       = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=True, index=True)
    trip_name     = db.Column(db.String(200), nullable=False)
    destination   = db.Column(db.String(200), nullable=False)
    start_date    = db.Column(db.String(20), nullable=False)
    end_date      = db.Column(db.String(20), nullable=False)
    traveler_name = db.Column(db.String(200), nullable=False)
    booking_type  = db.Column(db.String(30), default="trip")
    status        = db.Column(db.String(20), default="confirmed", index=True)
    details_json  = db.Column(db.Text, default="{}")
    alerts_json   = db.Column(db.Text, default="[]")
    created_at    = db.Column(db.DateTime(timezone=True), default=_now)
    updated_at    = db.Column(db.DateTime(timezone=True), default=_now, onupdate=_now)

    def to_dict(self):
        import json
        return {
            "id": self.id,
            "booking_id": self.id,
            "user_id": self.user_id,
            "trip_name": self.trip_name,
            "destination": self.destination,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "traveler_name": self.traveler_name,
            "booking_type": self.booking_type,
            "status": self.status,
            "details": json.loads(self.details_json or "{}"),
            "alerts": json.loads(self.alerts_json or "[]"),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


# ── SavedItinerary ────────────────────────────────────────────────────────────

class SavedItinerary(db.Model):
    __tablename__ = "saved_itineraries"

    id          = db.Column(db.String(36), primary_key=True, default=_uuid)
    user_id     = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=True, index=True)
    destination = db.Column(db.String(200), nullable=False)
    title       = db.Column(db.String(300), nullable=False)
    duration_days = db.Column(db.Integer, default=7)
    budget_level  = db.Column(db.String(20), default="moderate")
    is_public   = db.Column(db.Boolean, default=False)
    is_template = db.Column(db.Boolean, default=False)
    template_category = db.Column(db.String(50), default="")
    likes       = db.Column(db.Integer, default=0)
    data_json   = db.Column(db.Text, default="{}")
    created_at  = db.Column(db.DateTime(timezone=True), default=_now)

    def to_dict(self):
        import json
        return {
            "id": self.id,
            "user_id": self.user_id,
            "destination": self.destination,
            "title": self.title,
            "duration_days": self.duration_days,
            "budget_level": self.budget_level,
            "is_public": self.is_public,
            "is_template": self.is_template,
            "template_category": self.template_category,
            "likes": self.likes,
            "data": json.loads(self.data_json or "{}"),
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ── ChatSession ───────────────────────────────────────────────────────────────

class ChatSession(db.Model):
    __tablename__ = "chat_sessions"

    id         = db.Column(db.String(36), primary_key=True, default=_uuid)
    user_id    = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=True, index=True)
    session_key= db.Column(db.String(100), nullable=False, index=True)
    title      = db.Column(db.String(200), default="New Conversation")
    history_json = db.Column(db.Text, default="[]")
    message_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime(timezone=True), default=_now)
    updated_at = db.Column(db.DateTime(timezone=True), default=_now, onupdate=_now)

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "message_count": self.message_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ── AnalyticsEvent ────────────────────────────────────────────────────────────

class AnalyticsEvent(db.Model):
    __tablename__ = "analytics_events"

    id         = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id    = db.Column(db.String(36), nullable=True, index=True)
    event_type = db.Column(db.String(50), nullable=False, index=True)
    destination= db.Column(db.String(200), nullable=True)
    metadata_json = db.Column(db.Text, default="{}")
    created_at = db.Column(db.DateTime(timezone=True), default=_now, index=True)
