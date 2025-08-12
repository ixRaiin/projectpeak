from __future__ import annotations
from datetime import date as dt_date
from functools import wraps
from flask import Blueprint, jsonify, request, g, current_app
from sqlalchemy.exc import IntegrityError
from .extensions import db
from .models import Expense, ExpenseLine, Project, Category
from .auth import _get_token_from_request, _verify_token

bp = Blueprint("expenses", __name__, url_prefix="/api/projects")

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
    if not s:
        return None
    try:
        return dt_date.fromisoformat(s)
    except Exception:
        return None

@bp.post("/<int:pid>/expenses")
@require_auth
def create_expense(pid: int):
    # ensure project exists
    project = Project.query.get(pid)
    if not project or project.deleted_at is not None:
        return jsonify(error="not found"), 404

    data = request.get_json(silent=True) or {}

    e = Expense(
        project_id=pid,
        reference_no=(data.get("reference_no") or None),
        expense_date=_parse_date(data.get("expense_date")) or dt_date.today(),
        vendor=(data.get("vendor") or None),
        memo=(data.get("memo") or None),
    )
    db.session.add(e)
    db.session.flush()  # get e.id

    lines = data.get("lines") or []
    for ln in lines:
        cid = ln.get("category_id")
        if not cid or not Category.query.get(cid):
            db.session.rollback()
            return jsonify(error="invalid category_id in lines"), 400
        qty = float(ln.get("qty") or 1)
        unit = float(ln.get("unit_price_usd") or 0)
        db.session.add(ExpenseLine(
            expense_id=e.id,
            category_id=cid,
            qty=qty,
            unit_price_usd=unit,
            line_total_usd=qty * unit,
        ))

    db.session.commit()
    return jsonify(id=e.id), 201


@bp.get("/<int:pid>/expenses")
@require_auth
def list_expenses(pid: int):
    project = Project.query.get(pid)
    if not project or project.deleted_at is not None:
        return jsonify(error="not found"), 404

    items = []
    for e in Expense.query.filter_by(project_id=pid).order_by(Expense.expense_date.desc()).all():
        items.append({
            "id": e.id,
            "reference_no": e.reference_no,
            "expense_date": e.expense_date.isoformat(),
            "vendor": e.vendor,
            "memo": e.memo,
            "lines": [
                {
                    "id": l.id,
                    "category_id": l.category_id,
                    "qty": float(l.qty),
                    "unit_price_usd": float(l.unit_price_usd),
                    "line_total_usd": float(l.line_total_usd),
                } for l in e.lines
            ],
        })
    return jsonify(expenses=items)
