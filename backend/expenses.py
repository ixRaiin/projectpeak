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
    
def _coerce_num(v, default=0.0) -> float:
    try:
        return float(v)
    except Exception:
        return float(default)

def _recalculate_expense(exp: Expense) -> None:
    """Recompute per-line totals and (if columns exist) subtotal/tax/total."""
    subtotal = 0.0
    for ln in exp.lines:
        ln.qty = _coerce_num(getattr(ln, "qty", 0))
        ln.unit_price_usd = _coerce_num(getattr(ln, "unit_price_usd", 0))
        ln.line_total_usd = round(ln.qty * ln.unit_price_usd, 2)
        subtotal += ln.line_total_usd
    tax_rate = _coerce_num(getattr(exp.project, "tax_rate", 0.0))
    tax = round(subtotal * tax_rate, 2)
    total = round(subtotal + tax, 2)
    if hasattr(exp, "subtotal_usd"):
        exp.subtotal_usd = subtotal
    if hasattr(exp, "tax_usd"):
        exp.tax_usd = tax
    if hasattr(exp, "total_usd"):
        exp.total_usd = total


def _expense_to_dict(e: Expense) -> dict:
    return {
        "id": e.id,
        "reference_no": e.reference_no,
        "expense_date": e.expense_date.isoformat() if e.expense_date else None,
        "vendor": e.vendor,
        "memo": e.memo,
        "lines": [
            {
                "id": ln.id,
                "category_id": ln.category_id,
                "qty": float(ln.qty),
                "unit_price_usd": float(ln.unit_price_usd),
                "line_total_usd": float(ln.line_total_usd),
            }
            for ln in getattr(e, "lines", [])
        ],
    }

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

@bp.route("/<int:pid>/expenses/<int:eid>", methods=["PATCH"])
@require_auth
def patch_expense(pid: int, eid: int):
    project = Project.query.get(pid)
    if not project or getattr(project, "deleted_at", None) is not None:
        return jsonify(error="not found"), 404
    exp = Expense.query.filter_by(id=eid, project_id=pid).first()
    if not exp:
        return jsonify(error="not found"), 404
    data = request.get_json(silent=True) or {}
    if "expense_date" in data:
        exp.expense_date = _parse_date(data["expense_date"]) or exp.expense_date
    if "vendor" in data:
        exp.vendor = data["vendor"] or None
    if "reference_no" in data:
        exp.reference_no = data["reference_no"] or None
    if "memo" in data:
        exp.memo = data["memo"] or None
    db.session.commit()
    return jsonify(_expense_to_dict(exp))

@bp.post("/<int:pid>/expenses/<int:eid>/lines")
@require_auth
def add_expense_line(pid: int, eid: int):
    project = Project.query.get(pid)
    if not project or getattr(project, "deleted_at", None) is not None:
        return jsonify(error="not found"), 404
    exp = Expense.query.filter_by(id=eid, project_id=pid).first()
    if not exp:
        return jsonify(error="not found"), 404
    data = request.get_json(silent=True) or {}
    cid = data.get("category_id")
    if not cid or not Category.query.get(cid):
        return jsonify(error="invalid category_id"), 400
    qty = _coerce_num(data.get("qty") if "qty" in data else data.get("quantity"), 0)
    unit = _coerce_num(data.get("unit_price_usd"), 0)
    if qty < 0 or unit < 0:
        return jsonify(error="negative qty or unit_price_usd"), 400
    ln = ExpenseLine(
        expense_id=eid,
        category_id=cid,
        qty=qty,
        unit_price_usd=unit,
        line_total_usd=round(qty * unit, 2),
    )
    db.session.add(ln)
    _recalculate_expense(exp)
    db.session.commit()
    return jsonify({
        "id": ln.id,
        "expense_id": eid,
        "category_id": ln.category_id,
        "qty": float(ln.qty),
        "unit_price_usd": float(ln.unit_price_usd),
        "line_total_usd": float(ln.line_total_usd),
    }), 201


@bp.patch("/<int:pid>/expenses/<int:eid>/lines/<int:lid>")
@require_auth
def patch_expense_line(pid: int, eid: int, lid: int):
    project = Project.query.get(pid)
    if not project or getattr(project, "deleted_at", None) is not None:
        return jsonify(error="not found"), 404
    exp = Expense.query.filter_by(id=eid, project_id=pid).first()
    if not exp:
        return jsonify(error="not found"), 404
    ln = ExpenseLine.query.filter_by(id=lid, expense_id=eid).first()
    if not ln:
        return jsonify(error="line not found"), 404
    data = request.get_json(silent=True) or {}
    if "category_id" in data:
        cid = data.get("category_id")
        if not cid or not Category.query.get(cid):
            return jsonify(error="invalid category_id"), 400
        ln.category_id = cid
    if "qty" in data or "quantity" in data:
        qv = data.get("qty") if "qty" in data else data.get("quantity")
        qv = _coerce_num(qv, ln.qty)
        if qv < 0:
            return jsonify(error="qty cannot be negative"), 400
        ln.qty = qv
    if "unit_price_usd" in data:
        up = _coerce_num(data.get("unit_price_usd"), ln.unit_price_usd)
        if up < 0:
            return jsonify(error="unit_price_usd cannot be negative"), 400
        ln.unit_price_usd = up
    ln.qty = _coerce_num(ln.qty, ln.qty)
    ln.unit_price_usd = _coerce_num(ln.unit_price_usd, ln.unit_price_usd)
    _recalculate_expense(exp)
    db.session.commit()
    return jsonify({
        "id": ln.id,
        "expense_id": eid,
        "category_id": ln.category_id,
        "qty": float(ln.qty),
        "unit_price_usd": float(ln.unit_price_usd),
        "line_total_usd": float(ln.line_total_usd),
    })

@bp.delete("/<int:pid>/expenses/<int:eid>/lines/<int:lid>")
@require_auth
def delete_expense_line(pid: int, eid: int, lid: int):
    project = Project.query.get(pid)
    if not project or getattr(project, "deleted_at", None) is not None:
        return jsonify(error="not found"), 404
    exp = Expense.query.filter_by(id=eid, project_id=pid).first()
    if not exp:
        return jsonify(error="not found"), 404
    ln = ExpenseLine.query.filter_by(id=lid, expense_id=eid).first()
    if not ln:
        return jsonify(error="line not found"), 404
    db.session.delete(ln)
    _recalculate_expense(exp)
    db.session.commit()
    return jsonify(ok=True)
