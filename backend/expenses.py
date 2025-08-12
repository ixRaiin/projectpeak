# backend/expenses.py
from __future__ import annotations
from functools import wraps
from datetime import date as dt_date
from flask import Blueprint, jsonify, request, g, current_app
from sqlalchemy.exc import IntegrityError
from .extensions import db
from .models import Expense, ExpenseLine, Project, Category
from .auth import _get_token_from_request, _verify_token

bp = Blueprint("expenses", __name__, url_prefix="/api")

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

def _parse_date(s: str | None) -> dt_date | None:
    if not s: return None
    try: return dt_date.fromisoformat(s)
    except Exception: return None

def line_json(x: ExpenseLine) -> dict:
    return {
        "id": x.id,
        "category_id": x.category_id,
        "description": x.description,
        "quantity": x.quantity,
        "unit_price_usd": x.unit_price_usd,
        "line_total_usd": x.line_total_usd,
    }

def exp_json(e: Expense) -> dict:
    return {
        "id": e.id,
        "project_id": e.project_id,
        "expense_date": e.expense_date.isoformat() if getattr(e, "expense_date", None) else None,  # your model names expense_date
        "vendor": e.vendor,
        "reference_no": e.reference_no,
        "note": e.note,
        "subtotal_usd": e.subtotal_usd,
        "tax_usd": e.tax_usd,
        "total_usd": e.total_usd,
        "lines": [line_json(x) for x in e.lines],
    }

def _recalc(e: Expense, project_tax_rate: float | None):
    # subtotal = sum of line totals (lines are tax-exclusive)
    e.subtotal_usd = sum((ln.quantity or 0.0) * (ln.unit_price_usd or 0.0) for ln in e.lines)
    rate = project_tax_rate or 0.0
    e.tax_usd = round(e.subtotal_usd * rate, 2)
    e.total_usd = round(e.subtotal_usd + e.tax_usd, 2)

@bp.get("/projects/<int:pid>/expenses")
@require_auth
def list_expenses(pid: int):
    p = Project.query.get(pid)
    if not p or p.deleted_at is not None:
        return jsonify(error="not found"), 404
    rows = Expense.query.filter_by(project_id=pid).order_by(Expense.expense_date.desc(), Expense.id.desc()).all()
    return jsonify(expenses=[exp_json(e) for e in rows])

@bp.post("/projects/<int:pid>/expenses")
@require_auth
def create_expense(pid: int):
    p = Project.query.get(pid)
    if not p or p.deleted_at is not None:
        return jsonify(error="not found"), 404

    data = request.get_json(silent=True) or {}
    e = Expense(
        project_id=pid,
        expense_date=_parse_date(data.get("expense_date")) or dt_date.today(),
        vendor=(data.get("vendor") or "").strip() or None,
        reference_no=(data.get("reference_no") or "").strip() or None,
        note=(data.get("note") or "").strip() or None,
    )

    for ln in data.get("lines") or []:
        cid = ln.get("category_id")
        if not cid or not Category.query.get(cid):
            return jsonify(error=f"invalid category_id: {cid}"), 400
        qty = float(ln.get("quantity") or 1.0)
        unit = float(ln.get("unit_price_usd") or 0.0)
        e.lines.append(ExpenseLine(
            category_id=cid,
            description=(ln.get("description") or "").strip() or None,
            quantity=qty,
            unit_price_usd=unit,
            line_total_usd=round(qty * unit, 2),
        ))

    _recalc(e, p.tax_rate)
    db.session.add(e)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify(error="could not save expense"), 400
    return jsonify(exp_json(e)), 201

@bp.get("/expenses/<int:eid>")
@require_auth
def get_expense(eid: int):
    e = Expense.query.get(eid)
    if not e:
        return jsonify(error="not found"), 404
    return jsonify(exp_json(e))

@bp.patch("/expenses/<int:eid>")
@require_auth
def update_expense(eid: int):
    e = Expense.query.get(eid)
    if not e:
        return jsonify(error="not found"), 404
    p = Project.query.get(e.project_id)

    data = request.get_json(silent=True) or {}
    if "expense_date" in data:
        e.expense_date = _parse_date(data.get("expense_date")) or e.expense_date
    for f in ("vendor", "reference_no", "note"):
        if f in data:
            val = (data.get(f) or "").strip()
            setattr(e, f, val or None)

    if "lines" in data:
        e.lines.clear()
        for ln in data.get("lines") or []:
            cid = ln.get("category_id")
            if not cid or not Category.query.get(cid):
                return jsonify(error=f"invalid category_id: {cid}"), 400
            qty = float(ln.get("quantity") or 1.0)
            unit = float(ln.get("unit_price_usd") or 0.0)
            e.lines.append(ExpenseLine(
                category_id=cid,
                description=(ln.get("description") or "").strip() or None,
                quantity=qty,
                unit_price_usd=unit,
                line_total_usd=round(qty * unit, 2),
            ))

    _recalc(e, p.tax_rate if p else 0.0)
    db.session.commit()
    return jsonify(exp_json(e))

@bp.delete("/expenses/<int:eid>")
@require_auth
def delete_expense(eid: int):
    e = Expense.query.get(eid)
    if not e:
        return jsonify(error="not found"), 404
    db.session.delete(e)
    db.session.commit()
    return ("", 204)
