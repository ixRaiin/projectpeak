from __future__ import annotations
from typing import cast
from datetime import datetime, date as dt_date
from functools import wraps
from flask import Blueprint, jsonify, request, g, current_app
from sqlalchemy import or_, text
from sqlalchemy.exc import IntegrityError
from .extensions import db
from .models import Project, Client,Category,Component,ProjectCategory
from .auth import _get_token_from_request, _verify_token

bp = Blueprint("projects", __name__, url_prefix="/api/projects")

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

# --- helpers ---
def _parse_date(s: str | None) -> dt_date | None:
    if not s:
        return None
    try:
        return dt_date.fromisoformat(s)  # expects YYYY-MM-DD
    except Exception:
        return None


def _parse_float(x):
    if x is None or x == "":
        return None
    try:
        return float(x)
    except Exception:
        return None


def project_json(p: Project) -> dict:
    return {
        "id": p.id,
        "code": p.code,
        "client_id": p.client_id,
        "name": p.name,
        "description": p.description,
        "project_type": p.project_type,
        "status": p.status,
        "start_date": p.start_date.isoformat() if p.start_date else None,
        "end_date": p.end_date.isoformat() if p.end_date else None,
        "budget_amount_usd": p.budget_amount_usd,
        "tax_rate": p.tax_rate,
        "currency": p.currency,
        "created_at": p.created_at.isoformat() if p.created_at else None,
        "updated_at": p.updated_at.isoformat() if p.updated_at else None,
        "deleted_at": p.deleted_at.isoformat() if p.deleted_at else None,
    }


def _get_project_or_404(pid: int) -> Project | None:
    p = Project.query.get(pid)
    return None if (not p or p.deleted_at is not None) else p


def pc_json(pc: ProjectCategory) -> dict:
    return {
        "id": pc.id,
        "project_id": pc.project_id,
        "category_id": pc.category_id,
        "base_cost_usd": pc.base_cost_usd,
    }


def bom_json(b: ProjectComponent) -> dict:
    return {
        "id": b.id,
        "project_id": b.project_id,
        "category_id": b.category_id,
        "component_id": b.component_id,
        "quantity": b.quantity,
        "unit_price_usd": b.unit_price_usd,
        "note": b.note,
    }


# --- routes: projects ---
@bp.get("")
@require_auth
def list_projects():
    q = Project.query.filter(Project.deleted_at.is_(None))
    client_id = request.args.get("client_id", type=int)
    if client_id:
        q = q.filter(Project.client_id == client_id)

    search = (request.args.get("q") or "").strip()
    if search:
        like = f"%{search}%"
        q = q.filter(
            or_(
                Project.name.ilike(like),
                Project.code.ilike(like),
                Project.project_type.ilike(like),
            )
        )

    q = q.order_by(Project.created_at.desc())
    items = [project_json(p) for p in q.all()]
    return jsonify(projects=items)


@bp.post("")
@require_auth
def create_project():
    data = request.get_json(silent=True) or {}

    client_id = data.get("client_id")
    name = (data.get("name") or "").strip()
    if not client_id or not name:
        return jsonify(error="client_id and name are required"), 400

    client = Client.query.get(client_id)
    if not client or client.deleted_at is not None:
        return jsonify(error="invalid client_id"), 400

    p = Project(
        client_id=client_id,
        name=name,
        description=(data.get("description") or "").strip() or None,
        project_type=(data.get("project_type") or "").strip() or None,
        start_date=_parse_date(data.get("start_date")),
        end_date=_parse_date(data.get("end_date")),
        budget_amount_usd=_parse_float(data.get("budget_amount_usd")),
        tax_rate=_parse_float(data.get("tax_rate")),
        currency=(data.get("currency") or "USD")[:3],
        status=(data.get("status") or "planned"),
    )
    db.session.add(p)
    db.session.commit()  # triggers code auto-generation
    return jsonify(project_json(p)), 201


@bp.get("/<int:pid>")
@require_auth
def get_project(pid: int):
    p = _get_project_or_404(pid)
    if not p:
        return jsonify(error="not found"), 404
    return jsonify(project_json(p))


@bp.patch("/<int:pid>")
@require_auth
def update_project(pid: int):
    p = _get_project_or_404(pid)
    if not p:
        return jsonify(error="not found"), 404

    data = request.get_json(silent=True) or {}

    if "client_id" in data:
        cid = data.get("client_id")
        client = Client.query.get(cid)
        if not client or client.deleted_at is not None:
            return jsonify(error="invalid client_id"), 400
        p.client_id = cid

    fields_text = ["name", "description", "project_type", "status", "currency"]
    for f in fields_text:
        if f in data:
            val = (data.get(f) or "").strip()
            setattr(
                p,
                f,
                (
                    (val or None)
                    if f in {"description", "project_type"}
                    else (val or getattr(p, f))
                ),
            )

    if "start_date" in data:
        p.start_date = _parse_date(data.get("start_date"))
    if "end_date" in data:
        p.end_date = _parse_date(data.get("end_date"))
    if "budget_amount_usd" in data:
        p.budget_amount_usd = _parse_float(data.get("budget_amount_usd"))
    if "tax_rate" in data:
        p.tax_rate = _parse_float(data.get("tax_rate"))

    db.session.commit()
    return jsonify(project_json(p))


@bp.delete("/<int:pid>")
@require_auth
def delete_project(pid: int):
    p = _get_project_or_404(pid)
    if not p:
        return jsonify(error="not found"), 404
    p.deleted_at = datetime.utcnow()
    db.session.commit()
    return ("", 204)


# --- routes: project categories ---
@bp.get("/<int:pid>/categories")
@require_auth
def list_project_categories(pid: int):
    p = _get_project_or_404(pid)
    if not p:
        return jsonify(error="not found"), 404
    rows = ProjectCategory.query.filter_by(project_id=pid).all()
    return jsonify(categories=[pc_json(x) for x in rows])


@bp.post("/<int:pid>/categories")
@require_auth
def add_project_category(pid: int):
    p = _get_project_or_404(pid)
    if not p:
        return jsonify(error="not found"), 404
    data = request.get_json(silent=True) or {}
    try:
        category_id = data.get("category_id")
        if not category_id:
            return jsonify(error="category_id is required"), 400

        cat = Category.query.get(category_id)
        if not cat or getattr(cat, "deleted_at", None) is not None:
            return jsonify(error="invalid category_id"), 400

        base = float(data.get("base_cost_usd") or 0.0)

        pc = ProjectCategory(
            project_id=pid,
            category_id=category_id,
            base_cost_usd=base,
        )
        db.session.add(pc)
        db.session.commit()
        return jsonify(pc_json(pc)), 201

    except IntegrityError:
        db.session.rollback()
        return jsonify(error="category already added to this project"), 409
    except Exception:
        current_app.logger.exception("add_project_category failed")
        db.session.rollback()
        return jsonify(error="internal error"), 500


@bp.delete("/<int:pid>/categories/<int:pcid>")
@require_auth
def delete_project_category(pid: int, pcid: int):
    p = _get_project_or_404(pid)
    if not p:
        return jsonify(error="not found"), 404
    pc = ProjectCategory.query.get(pcid)
    if not pc or pc.project_id != pid:
        return jsonify(error="not found"), 404
    db.session.delete(pc)
    db.session.commit()
    return ("", 204)


# --- routes: project BOM (components) ---
@bp.get("/<int:pid>/components")
@require_auth
def list_project_components(pid: int):
    p = _get_project_or_404(pid)
    if not p:
        return jsonify(error="not found"), 404
    rows = ProjectComponent.query.filter_by(project_id=pid).all()
    return jsonify(components=[bom_json(x) for x in rows])


@bp.post("/<int:pid>/components")
@require_auth
def add_project_component(pid: int):
    p = _get_project_or_404(pid)
    if not p:
        return jsonify(error="not found"), 404
    data = request.get_json(silent=True) or {}
    try:
        category_id = data.get("category_id")
        component_id = data.get("component_id")
        if not category_id or not component_id:
            return jsonify(error="category_id and component_id are required"), 400

        cat = Category.query.get(category_id)
        if not cat or getattr(cat, "deleted_at", None) is not None:
            return jsonify(error="invalid category_id"), 400

        comp = Component.query.get(component_id)
        if not comp:
            return jsonify(error="invalid component_id"), 400

        qty = float(data.get("quantity") or 1.0)
        unit = data.get("unit_price_usd")
        unit_price = None if unit in (None, "") else float(unit)

        b = ProjectComponent(
            project_id=pid,
            category_id=category_id,
            component_id=component_id,
            quantity=qty,
            unit_price_usd=unit_price,
            note=(data.get("note") or "").strip() or None,
        )
        db.session.add(b)
        db.session.commit()
        return jsonify(bom_json(b)), 201

    except IntegrityError:
        db.session.rollback()
        return jsonify(error="component already exists on this project"), 409
    except Exception:
        current_app.logger.exception("add_project_component failed")
        db.session.rollback()
        return jsonify(error="internal error"), 500


@bp.delete("/<int:pid>/components/<int:bid>")
@require_auth
def delete_project_component(pid: int, bid: int):
    p = _get_project_or_404(pid)
    if not p:
        return jsonify(error="not found"), 404
    b = ProjectComponent.query.get(bid)
    if not b or b.project_id != pid:
        return jsonify(error="not found"), 404
    db.session.delete(b)
    db.session.commit()
    return ("", 204)


# --- routes: project summary (planned vs actual) ---
@bp.get("/<int:pid>/summary")
@require_auth
def project_summary(pid: int):
    p = _get_project_or_404(pid)
    if not p:
        return jsonify(error="not found"), 404

    planned_sql = text(
        """
        SELECT pc.category_id,
               pc.base_cost_usd
               + COALESCE(SUM(b.quantity * COALESCE(b.unit_price_usd, comp.default_unit_price_usd)), 0) AS planned_usd
        FROM project_categories pc
        LEFT JOIN project_components b
          ON b.project_id = pc.project_id AND b.category_id = pc.category_id
        LEFT JOIN components comp ON comp.id = b.component_id
        WHERE pc.project_id = :pid
        GROUP BY pc.category_id, pc.base_cost_usd
    """
    )

    actual_sql = text(
        """
        SELECT el.category_id, COALESCE(SUM(el.line_total_usd), 0) AS actual_usd
        FROM expenses e
        JOIN expense_lines el ON el.expense_id = e.id
        WHERE e.project_id = :pid
        GROUP BY el.category_id
    """
    )

    rows_planned = db.session.execute(planned_sql, {"pid": pid}).mappings().all()
    rows_actual = db.session.execute(actual_sql, {"pid": pid}).mappings().all()
    planned_map = {r["category_id"]: float(r["planned_usd"]) for r in rows_planned}
    actual_map = {r["category_id"]: float(r["actual_usd"]) for r in rows_actual}

    cat_ids = list({*planned_map.keys(), *actual_map.keys()})
    names = (
        {c.id: c.name for c in Category.query.filter(Category.id.in_(cat_ids)).all()}
        if cat_ids
        else {}
    )

    per_category = []
    for cid in sorted(cat_ids):
        p_val = planned_map.get(cid, 0.0)
        a_val = actual_map.get(cid, 0.0)
        per_category.append(
            {
                "category_id": cid,
                "category_name": names.get(cid),
                "planned_usd": p_val,
                "actual_usd": a_val,
                "variance_usd": p_val - a_val,
            }
        )

    totals = {
        "planned_total_usd": sum(x["planned_usd"] for x in per_category),
        "actual_total_usd": sum(x["actual_usd"] for x in per_category),
    }
    totals["variance_total_usd"] = (
        totals["planned_total_usd"] - totals["actual_total_usd"]
    )

    return jsonify(per_category=per_category, totals=totals)
