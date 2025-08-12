# backend/catalog.py
from __future__ import annotations

from datetime import datetime
from functools import wraps

from flask import Blueprint, jsonify, request, g
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from .extensions import db
from .models import Category, Component
from .auth import _get_token_from_request, _verify_token

bp = Blueprint("catalog", __name__, url_prefix="/api")


# ---------------------- auth wrapper ----------------------
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


# ---------------------- helpers ----------------------
def category_json(c: Category) -> dict:
    return {"id": c.id, "name": c.name, "description": c.description}


def component_json(x: Component) -> dict:
    return {
        "id": x.id,
        "category_id": x.category_id,
        "name": x.name,
        "default_unit_price_usd": x.default_unit_price_usd,
        "uom": x.uom,
    }


# ====================== Categories ======================


@bp.get("/categories")
@require_auth
def list_categories():
    """List categories, default hides soft-deleted.
    Query params:
      - q: case-insensitive name contains
      - include_deleted: true/false (default false)
    """
    q = (request.args.get("q") or "").strip()
    include_deleted = (request.args.get("include_deleted") or "false").lower() in (
        "1",
        "true",
        "yes",
    )

    qry = Category.query
    if not include_deleted:
        qry = qry.filter(Category.deleted_at.is_(None))
    if q:
        like = f"%{q}%"
        qry = qry.filter(Category.name.ilike(like))

    items = [category_json(c) for c in qry.order_by(Category.name).all()]
    return jsonify(categories=items)


@bp.get("/categories/<int:cid>")
@require_auth
def get_category(cid: int):
    c = Category.query.get(cid)
    if not c or c.deleted_at is not None:
        return jsonify(error="not found"), 404
    return jsonify(category_json(c)), 200


@bp.post("/categories")
@require_auth
def create_category():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify(error="name is required"), 400

    # Is there a category with this name (case-insensitive)?
    exists = Category.query.filter(func.lower(Category.name) == name.lower()).first()
    if exists:
        # If it was soft-deleted, "revive" it instead of 409
        if exists.deleted_at is not None:
            exists.deleted_at = None
            desc = (data.get("description") or "").strip() or None
            if desc is not None:
                exists.description = desc
            db.session.commit()
            return jsonify(category_json(exists)), 200
        # otherwise conflict
        return jsonify(error="category already exists", id=exists.id), 409

    c = Category(name=name, description=(data.get("description") or "").strip() or None)
    db.session.add(c)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify(error="category already exists"), 409
    return jsonify(category_json(c)), 201


@bp.route("/categories/<int:cid>", methods=["PATCH", "PUT"])
@require_auth
def update_category(cid: int):
    c = Category.query.get(cid)
    if not c or c.deleted_at is not None:
        return jsonify(error="not found"), 404

    data = request.get_json(silent=True) or {}

    if "name" in data:
        new_name = (data.get("name") or "").strip()
        if not new_name:
            return jsonify(error="name cannot be empty"), 400
        dup = Category.query.filter(
            func.lower(Category.name) == new_name.lower(), Category.id != cid
        ).first()
        if dup:
            # if the duplicate exists but is soft-deleted, tell the client which id to restore
            if dup.deleted_at is not None:
                return (
                    jsonify(error="category already exists (soft-deleted)", id=dup.id),
                    409,
                )
            return jsonify(error="category already exists", id=dup.id), 409
        c.name = new_name

    if "description" in data:
        c.description = (data.get("description") or "").strip() or None

    if request.method == "PUT" and "name" not in data:
        return jsonify(error="name is required for PUT"), 400

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify(error="category already exists"), 409

    return jsonify(category_json(c))


@bp.delete("/categories/<int:cid>")
@require_auth
def delete_category(cid: int):
    """Soft delete category (set deleted_at)."""
    c = Category.query.get(cid)
    if not c:
        return jsonify(error="not found"), 404
    if c.deleted_at is None:
        c.deleted_at = datetime.utcnow()
        db.session.commit()
    return ("", 204)


@bp.post("/categories/<int:cid>/restore")
@require_auth
def restore_category(cid: int):
    c = Category.query.get(cid)
    if not c:
        return jsonify(error="not found"), 404
    if c.deleted_at is not None:
        c.deleted_at = None
        db.session.commit()
    return jsonify(category_json(c)), 200


# ====================== Components ======================


@bp.get("/components")
@require_auth
def list_components():
    qry = Component.query
    cid = request.args.get("category_id", type=int)
    q = (request.args.get("q") or "").strip()

    if cid:
        qry = qry.filter(Component.category_id == cid)
    if q:
        like = f"%{q}%"
        qry = qry.filter(Component.name.ilike(like))

    items = [component_json(x) for x in qry.order_by(Component.name).all()]
    return jsonify(components=items)


@bp.post("/components")
@require_auth
def create_component():
    data = request.get_json(silent=True) or {}
    category_id = data.get("category_id")
    name = (data.get("name") or "").strip()
    if not category_id or not name:
        return jsonify(error="category_id and name are required"), 400

    # ensure category exists and isn't soft-deleted
    cat = Category.query.get(category_id)
    if not cat or cat.deleted_at is not None:
        return jsonify(error="invalid category_id"), 400

    comp = Component(
        category_id=category_id,
        name=name,
        default_unit_price_usd=data.get("default_unit_price_usd"),
        uom=(data.get("uom") or "").strip() or None,
    )
    db.session.add(comp)
    db.session.commit()
    return jsonify(component_json(comp)), 201


@bp.patch("/components/<int:comp_id>")
@require_auth
def update_component(comp_id: int):
    comp = Component.query.get(comp_id)
    if not comp:
        return jsonify(error="not found"), 404

    data = request.get_json(silent=True) or {}

    for f in ("name", "uom"):
        if f in data:
            setattr(comp, f, (data.get(f) or "").strip() or None)

    if "default_unit_price_usd" in data:
        comp.default_unit_price_usd = data.get("default_unit_price_usd")

    if "category_id" in data:
        new_cid = data.get("category_id")
        cat = Category.query.get(new_cid)
        if not cat or cat.deleted_at is not None:
            return jsonify(error="invalid category_id"), 400
        comp.category_id = new_cid

    db.session.commit()
    return jsonify(component_json(comp))


@bp.delete("/components/<int:comp_id>")
@require_auth
def delete_component(comp_id: int):
    comp = Component.query.get(comp_id)
    if not comp:
        return jsonify(error="not found"), 404
    db.session.delete(comp)
    db.session.commit()
    return ("", 204)
