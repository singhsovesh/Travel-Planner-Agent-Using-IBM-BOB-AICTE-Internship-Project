"""
Authentication module — register, login, logout, profile.
Uses Flask-Login for session management and SQLAlchemy for persistence.
"""
import logging
import re
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User

logger = logging.getLogger(__name__)
auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")
login_manager = LoginManager()


@login_manager.user_loader
def load_user(user_id: str):
    return db.session.get(User, user_id)


@login_manager.unauthorized_handler
def unauthorized():
    return jsonify({"error": "Authentication required", "code": "UNAUTHORIZED"}), 401


# ── Helpers ────────────────────────────────────────────────────────────────────

def _validate_email(email: str) -> bool:
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email))

def _validate_password(pwd: str) -> tuple[bool, str]:
    if len(pwd) < 8:
        return False, "Password must be at least 8 characters"
    return True, ""


# ── Endpoints ─────────────────────────────────────────────────────────────────

@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json(force=True)
    email    = (data.get("email", "") or "").strip().lower()
    username = (data.get("username", "") or "").strip()
    password = data.get("password", "") or ""
    first_name = data.get("first_name", "") or ""
    last_name  = data.get("last_name", "") or ""

    if not email or not username or not password:
        return jsonify({"error": "email, username and password are required"}), 400
    if not _validate_email(email):
        return jsonify({"error": "Invalid email address"}), 400
    ok, msg = _validate_password(password)
    if not ok:
        return jsonify({"error": msg}), 400
    if len(username) < 3:
        return jsonify({"error": "Username must be at least 3 characters"}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email already registered"}), 409
    if User.query.filter_by(username=username).first():
        return jsonify({"error": "Username already taken"}), 409

    user = User(
        email=email, username=username,
        first_name=first_name, last_name=last_name,
    )
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    login_user(user, remember=True)
    logger.info("New user registered: %s", email)
    return jsonify({"message": "Registration successful", "user": user.to_dict()}), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(force=True)
    identifier = (data.get("email") or data.get("username") or "").strip().lower()
    password   = data.get("password", "") or ""
    remember   = data.get("remember", True)

    if not identifier or not password:
        return jsonify({"error": "Email/username and password are required"}), 400

    user = User.query.filter_by(email=identifier).first() or \
           User.query.filter_by(username=identifier).first()

    if not user or not user.check_password(password):
        return jsonify({"error": "Invalid credentials"}), 401
    if not user.is_active:
        return jsonify({"error": "Account is deactivated"}), 403

    login_user(user, remember=remember)
    user.last_login = datetime.now(timezone.utc)
    db.session.commit()
    logger.info("User logged in: %s", user.email)
    return jsonify({"message": "Login successful", "user": user.to_dict()})


@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    session.clear()
    return jsonify({"message": "Logged out successfully"})


@auth_bp.route("/me", methods=["GET"])
def me():
    if current_user.is_authenticated:
        return jsonify({"user": current_user.to_dict(), "authenticated": True})
    return jsonify({"user": None, "authenticated": False})


@auth_bp.route("/profile", methods=["PUT"])
@login_required
def update_profile():
    data = request.get_json(force=True)
    allowed = ["first_name", "last_name", "nationality", "phone",
               "travel_style", "budget_pref", "currency_pref",
               "language_pref", "home_city", "avatar_color"]
    for field in allowed:
        if field in data:
            setattr(current_user, field, data[field])
    db.session.commit()
    return jsonify({"message": "Profile updated", "user": current_user.to_dict()})


@auth_bp.route("/change-password", methods=["POST"])
@login_required
def change_password():
    data = request.get_json(force=True)
    current_pwd = data.get("current_password", "")
    new_pwd     = data.get("new_password", "")

    if not current_user.check_password(current_pwd):
        return jsonify({"error": "Current password is incorrect"}), 400
    ok, msg = _validate_password(new_pwd)
    if not ok:
        return jsonify({"error": msg}), 400

    current_user.set_password(new_pwd)
    db.session.commit()
    return jsonify({"message": "Password changed successfully"})


@auth_bp.route("/delete-account", methods=["DELETE"])
@login_required
def delete_account():
    data = request.get_json(force=True)
    if not current_user.check_password(data.get("password", "")):
        return jsonify({"error": "Password incorrect"}), 400
    user_id = current_user.id
    logout_user()
    user = db.session.get(User, user_id)
    db.session.delete(user)
    db.session.commit()
    return jsonify({"message": "Account deleted"})
