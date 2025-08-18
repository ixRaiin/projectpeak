# backend/tasks.py
from datetime import date
from flask import Blueprint, request, jsonify, abort, g
from functools import wraps
from sqlalchemy import func
from .extensions import db
from .models import Project, Task, TaskComment
from .auth import _get_token_from_request, _verify_token

bp = Blueprint("tasks", __name__, url_prefix="/api")
MAX_COMMENT_LEN = 4000

def _extract_user_id(user):
    # Accepts many shapes: ORM user, dict, tuple like (ok, id), plain int/str
    if user is None:
        return None
    # ORM-like
    uid = getattr(user, "id", None)
    if isinstance(uid, int):
        return uid
    # dict-like
    if isinstance(user, dict):
        for k in ("id", "user_id", "uid"):
            v = user.get(k)
            if isinstance(v, int):
                return v
            if isinstance(v, str) and v.isdigit():
                return int(v)
    # tuple/list-like: pick the first int inside (handles (True, 2))
    if isinstance(user, (list, tuple)):
        for v in user:
            if isinstance(v, int):
                return v
            if isinstance(v, str) and v.isdigit():
                return int(v)
    # plain str/int
    if isinstance(user, int):
        return user
    if isinstance(user, str) and user.isdigit():
        return int(user)
    return None

def auth_required(fn):
    @wraps(fn)
    def inner(*args, **kwargs):
        try:
            token = _get_token_from_request()
            if not token:
                return jsonify({"error": "UNAUTHORIZED", "detail": "missing token"}), 401
            user = _verify_token(token)
            uid = _extract_user_id(user)
            if uid is None:
                return jsonify({"error": "UNAUTHORIZED", "detail": "invalid token"}), 401
            g.current_user = user
            g.user_id = uid  # <- always an int now
        except Exception as e:
            return jsonify({"error": "UNAUTHORIZED", "detail": str(e)}), 401
        return fn(*args, **kwargs)
    return inner

# Ensure the project exists or return 404
def _project_or_404(pid: int) -> Project:
    p = Project.query.get(pid)
    if not p:
        abort(404, description="Project not found")
    return p

def _task_in_project_or_404(pid: int, tid: int) -> Task:
    t = Task.query.filter_by(project_id=pid, id=tid).first()
    if not t:
        abort(404, description="Task not found")
    return t

# GET
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

# POST
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

# PATCH
@bp.route("/projects/<int:pid>/tasks/<int:tid>", methods=["PATCH"])
@auth_required
def update_task(pid, tid):
    t = Task.query.filter_by(project_id=pid, id=tid).first()
    if not t:
        return jsonify({"error": "Task not found"}), 404
    data = request.get_json(silent=True) or {}
    if "title" in data:
        title = (data["title"] or "").strip()
        if not title:
            return jsonify({"error": "title cannot be empty"}), 400
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
        if not v:
            t.due_date = None
        else:
            try:
                t.due_date = date.fromisoformat(v)
            except Exception:
                return jsonify({"error": "Invalid due_date, expected YYYY-MM-DD"}), 400
    db.session.commit()
    return jsonify(t.to_dict())

# DELETE
@bp.route("/projects/<int:pid>/tasks/<int:tid>", methods=["DELETE"])
@auth_required
def delete_task(pid, tid):
    t = Task.query.filter_by(project_id=pid, id=tid).first()
    if not t:
        return jsonify({"error": "Task not found"}), 404
    db.session.delete(t)
    db.session.commit()
    return jsonify({"ok": True})
    

@bp.route("/projects/<int:pid>/tasks/<int:tid>/comments", methods=["GET"])
@auth_required
def list_task_comments(pid, tid):
    _project_or_404(pid)
    t = _task_in_project_or_404(pid, tid)
    # Use relationship ordering by created_at
    return jsonify({"comments": [c.to_dict() for c in t.comments]})

@bp.route("/projects/<int:pid>/tasks/<int:tid>/comments", methods=["POST"])
@auth_required
def create_task_comment(pid, tid):
    _project_or_404(pid)
    _task_in_project_or_404(pid, tid)

    data = request.get_json(silent=True) or {}
    body = (data.get("body") or "").strip()
    if not body:
        return jsonify({"error": "body is required"}), 400
    if len(body) > MAX_COMMENT_LEN:
        return jsonify({"error": f"body too long (max {MAX_COMMENT_LEN})"}), 400

    c = TaskComment(task_id=tid, user_id=g.user_id, body=body)
    db.session.add(c)
    db.session.commit()
    return jsonify(c.to_dict()), 201

@bp.route("/projects/<int:pid>/tasks/<int:tid>/comments/<int:cid>", methods=["DELETE"])
@auth_required
def delete_task_comment(pid, tid, cid):
    _project_or_404(pid)
    _task_in_project_or_404(pid, tid)

    c = TaskComment.query.filter_by(id=cid, task_id=tid).first()
    if not c:
        return jsonify({"error": "Comment not found"}), 404

    # simple permission: author can delete (extend later for admins)
    if c.user_id != g.user_id:
        return jsonify({"error": "Forbidden"}), 403

    db.session.delete(c)
    db.session.commit()
    return jsonify({"ok": True})
