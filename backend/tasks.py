# backend/tasks.py
from datetime import date
from flask import Blueprint, request, jsonify, abort, g
from functools import wraps
from sqlalchemy import func
from .extensions import db
from .models import Project, Task
from .auth import _get_token_from_request, _verify_token

bp = Blueprint("tasks", __name__, url_prefix="/api")

def auth_required(fn):
    """Guards a route using your token helpers."""
    @wraps(fn)
    def inner(*args, **kwargs):
        try:
            token = _get_token_from_request()
            if not token:
                return jsonify({"error": "UNAUTHORIZED", "detail": "missing token"}), 401
            user = _verify_token(token)
            if not user:
                return jsonify({"error": "UNAUTHORIZED", "detail": "invalid token"}), 401
            # normalize for downstream use
            g.current_user = user
            g.user_id = getattr(user, "id", None) or (user.get("id") if isinstance(user, dict) else user)
        except Exception as e:
            # keep this 401 to avoid leaking internals
            return jsonify({"error": "UNAUTHORIZED", "detail": str(e)}), 401
        return fn(*args, **kwargs)
    return inner

def _project_or_404(pid: int) -> Project:
    p = Project.query.get(pid)
    if not p:
        abort(404, description="Project not found")
    return p

@bp.route("/projects/<int:pid>/tasks", methods=["GET"])
@auth_required
def list_tasks(pid):
    _project_or_404(pid)
    rows = (
        Task.query.filter_by(project_id=pid)
        .order_by(Task.parent_task_id.is_(None).desc(), Task.parent_task_id, Task.order_index, Task.id)
        .all()
    )
    return jsonify({"tasks": [t.to_dict() for t in rows]})

@bp.route("/projects/<int:pid>/tasks", methods=["POST"])
@auth_required
def create_task(pid):
    _project_or_404(pid)
    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()
    if not title:
        abort(400, description="title is required")
    def _parse_date(v):
        if not v:
            return None
        try:
            return date.fromisoformat(v)
        except Exception:
            abort(400, description="Invalid due_date")
    t = Task(
        project_id=pid,
        parent_task_id=data.get("parent_task_id"),
        title=title,
        description=(data.get("description") or None),
        status=(data.get("status") or "todo"),
        assignee_user_id=data.get("assignee_user_id"),
        due_date=_parse_date(data.get("due_date")),
        order_index=int(data.get("order_index") or 0),
    )
    db.session.add(t)
    db.session.commit()
    return jsonify(t.to_dict()), 201

@bp.route("/projects/<int:pid>/tasks/<int:tid>", methods=["PATCH"])
@auth_required
def update_task(pid, tid):
    _project_or_404(pid)
    t = Task.query.get_or_404(tid)
    if t.project_id != pid:
        abort(404)
    data = request.get_json(silent=True) or {}
    if "title" in data:
        title = (data["title"] or "").strip()
        if not title:
            abort(400, description="title cannot be empty")
        t.title = title
    if "description" in data:
        t.description = data["description"] or None
    if "status" in data:
        t.status = data["status"] or "todo"
    if "assignee_user_id" in data:
        t.assignee_user_id = data["assignee_user_id"]
    if "parent_task_id" in data:
        t.parent_task_id = data["parent_task_id"]
    if "order_index" in data:
        t.order_index = int(data["order_index"] or 0)
    if "due_date" in data:
        v = data["due_date"]
        t.due_date = date.fromisoformat(v) if v else None
    db.session.commit()
    return jsonify(t.to_dict())

@bp.route("/projects/<int:pid>/tasks/<int:tid>", methods=["DELETE"])
@auth_required
def delete_task(pid, tid):
    _project_or_404(pid)
    t = Task.query.get_or_404(tid)
    if t.project_id != pid:
        abort(404)
    db.session.delete(t)
    db.session.commit()
    return jsonify({"ok": True})

@bp.get("/projects/<int:pid>/tasks/progress")
@auth_required
def task_progress(pid):
    total = Task.query.filter_by(project_id=pid).count()
    done = Task.query.filter_by(project_id=pid, status="done").count()
    percent = 0 if total == 0 else round(done * 100 / total)
    return jsonify({"total": total, "done": done, "percent": percent})
