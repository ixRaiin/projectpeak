from datetime import datetime
from functools import wraps

from flask import Blueprint, jsonify, request, g
from .extensions import db
from .models import Client

# use the helpers we already built in auth.py
from .auth import _get_token_from_request, _verify_token

bp = Blueprint("clients", __name__, url_prefix="/api/clients")


# --- auth guard (cookie or Bearer) ---
def require_auth(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        token = _get_token_from_request()
        if not token:
            return jsonify(error="authentication required"), 401
        ok, user_id = _verify_token(token)
        if not ok or not user_id:
            return jsonify(error="invalid token"), 401
        g.user_id = user_id
        return fn(*args, **kwargs)

    return wrapper


# --- serializers ---
def client_json(c: Client) -> dict:
    return {
        "id": c.id,
        "name": c.name,
        "contact_name": c.contact_name,
        "email": c.email,
        "phone": c.phone,
        "address": c.address,
        "notes": c.notes,
        "created_at": c.created_at.isoformat() if c.created_at else None,
        "updated_at": c.updated_at.isoformat() if c.updated_at else None,
        "deleted_at": c.deleted_at.isoformat() if c.deleted_at else None,
    }


# --- routes ---
@bp.get("")
@require_auth
def list_clients():
    q = Client.query.filter(Client.deleted_at.is_(None))
    search = request.args.get("q", "").strip()
    if search:
        like = f"%{search}%"
        q = q.filter(
            db.or_(
                Client.name.ilike(like),
                Client.email.ilike(like),
                Client.contact_name.ilike(like),
            )
        )
    q = q.order_by(Client.created_at.desc())
    items = [client_json(c) for c in q.all()]
    return jsonify(clients=items)


@bp.post("")
@require_auth
def create_client():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify(error="name is required"), 400

    c = Client(
        name=name,
        contact_name=(data.get("contact_name") or "").strip() or None,
        email=(data.get("email") or "").strip() or None,
        phone=(data.get("phone") or "").strip() or None,
        address=(data.get("address") or "").strip() or None,
        notes=(data.get("notes") or "").strip() or None,
    )
    db.session.add(c)
    db.session.commit()
    return jsonify(client_json(c)), 201


def _get_client_or_404(cid: int) -> Client | None:
    c = Client.query.get(cid)
    return None if (not c or c.deleted_at is not None) else c


@bp.get("/<int:cid>")
@require_auth
def get_client(cid: int):
    c = _get_client_or_404(cid)
    if not c:
        return jsonify(error="not found"), 404
    return jsonify(client_json(c))


@bp.patch("/<int:cid>")
@require_auth
def update_client(cid: int):
    c = _get_client_or_404(cid)
    if not c:
        return jsonify(error="not found"), 404
    data = request.get_json(silent=True) or {}
    fields = ["name", "contact_name", "email", "phone", "address", "notes"]
    for f in fields:
        if f in data:
            val = (data[f] or "").strip()
            setattr(c, f, val or None)
    db.session.commit()
    return jsonify(client_json(c))


@bp.delete("/<int:cid>")
@require_auth
def delete_client(cid: int):
    c = _get_client_or_404(cid)
    if not c:
        return jsonify(error="not found"), 404
    c.deleted_at = datetime.utcnow()
    db.session.commit()
    return ("", 204)
