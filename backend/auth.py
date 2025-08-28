from __future__ import annotations
import time
from datetime import datetime, timedelta
from typing import Optional, Tuple
import jwt
from flask import Blueprint, current_app, jsonify, request, make_response
from werkzeug.security import generate_password_hash, check_password_hash
from .extensions import db
from .models import User

bp = Blueprint("auth", __name__, url_prefix="/api/auth")


def _issue_token(user_id: int) -> str:
    exp = datetime.utcnow() + timedelta(minutes=current_app.config["JWT_EXPIRES_MIN"])
    payload = {
        "sub": str(user_id),
        "iat": int(time.time()),
        "exp": int(exp.timestamp()),
    }
    return jwt.encode(payload, current_app.config["JWT_SECRET"], algorithm="HS256")


def _verify_token(token: str) -> tuple[bool, int | None]:
    try:
        data = jwt.decode(token, current_app.config["JWT_SECRET"], algorithms=["HS256"])
        return True, int(data["sub"])
    except Exception:
        return False, None


def _get_token_from_request() -> Optional[str]:
    token = request.cookies.get(current_app.config["COOKIE_NAME"])
    if token:
        return token
    authz = request.headers.get("Authorization", "")
    if authz.startswith("Bearer "):
        return authz.split(" ", 1)[1].strip()
    return None


@bp.post("/register")
def register():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    if not name or not email or not password:
        return jsonify(error="name, email, and password are required"), 400
    if len(password) < 8:
        return jsonify(error="password must be at least 8 characters"), 400
    if User.query.filter_by(email=email).first():
        return jsonify(error="email already registered"), 409
    user = User(
        name=name,
        email=email,
        password_hash=generate_password_hash(
            password, method="pbkdf2:sha256", salt_length=16
        ),
    )
    db.session.add(user)
    db.session.commit()
    token = _issue_token(user.id)
    resp = make_response(jsonify(id=user.id, name=user.name, email=user.email))
    resp.set_cookie(
        current_app.config["COOKIE_NAME"],
        token,
        max_age=current_app.config["JWT_EXPIRES_MIN"] * 60,
        httponly=True,
        samesite="Lax",
        secure=False,
        path="/",
    )
    return resp, 201


@bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    user = User.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify(error="invalid credentials"), 401
    token = _issue_token(user.id)
    resp = make_response(jsonify(id=user.id, name=user.name, email=user.email))
    resp.set_cookie(
        current_app.config["COOKIE_NAME"],
        token,
        max_age=current_app.config["JWT_EXPIRES_MIN"] * 60,
        httponly=True,
        samesite="Lax",
        secure=False,
        path="/",
    )
    return resp


@bp.post("/logout")
def logout():
    resp = make_response(jsonify(ok=True))
    resp.set_cookie(
        current_app.config["COOKIE_NAME"],
        "",
        max_age=0,
        httponly=True,
        samesite="Lax",
        secure=False,
        path="/",
    )
    return resp


@bp.get("/me")
def me():
    token = _get_token_from_request()
    if not token:
        return jsonify(user=None)
    ok, user_id = _verify_token(token)
    if not ok or not user_id:
        return jsonify(user=None)
    user = User.query.get(user_id)
    if not user or user.deleted_at is not None:
        return jsonify(user=None)
    return jsonify(user={"id": user.id, "name": user.name, "email": user.email})


@bp.get("/debug/verify")
def debug_verify():
    token = _get_token_from_request()
    if not token:
        return jsonify(valid=False, error="no token on request"), 400
    try:
        data = jwt.decode(token, current_app.config["JWT_SECRET"], algorithms=["HS256"])
        return jsonify(valid=True, claims=data)
    except ExpiredSignatureError:
        return jsonify(valid=False, error="expired"), 401
    except InvalidTokenError as e:
        return jsonify(valid=False, error=str(e)), 400
