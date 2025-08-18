from __future__ import annotations
import re
from datetime import datetime, date as dt_date
from sqlalchemy import UniqueConstraint, Index, event, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column
from .extensions import db


# ----- helpers -----
def utcnow() -> datetime:
    return datetime.utcnow()
# ----- mixins -----
class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        default=utcnow, onupdate=utcnow, nullable=False
    )
    deleted_at: Mapped[datetime | None] = mapped_column(default=None)


class PKMixin:
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)


# ----- users -----
class User(db.Model, PKMixin, TimestampMixin):
    __tablename__ = "users"
    name: Mapped[str] = mapped_column(db.String(120), nullable=False)
    email: Mapped[str] = mapped_column(
        db.String(255), unique=True, index=True, nullable=False
    )
    password_hash: Mapped[str] = mapped_column(db.String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(db.Boolean, default=True, nullable=False)


# ----- clients -----
class Client(db.Model, PKMixin, TimestampMixin):
    __tablename__ = "clients"
    name: Mapped[str] = mapped_column(db.String(200), nullable=False)
    contact_name: Mapped[str | None] = mapped_column(db.String(120))
    email: Mapped[str | None] = mapped_column(db.String(255))
    phone: Mapped[str | None] = mapped_column(db.String(50))
    address: Mapped[str | None] = mapped_column(db.Text)
    notes: Mapped[str | None] = mapped_column(db.Text)

    projects = relationship(
        "Project", back_populates="client", cascade="all, delete-orphan"
    )


# ----- categories (global master) -----
class Category(db.Model, PKMixin, TimestampMixin):
    __tablename__ = "categories"
    name: Mapped[str] = mapped_column(db.String(120), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(db.Text)

    components = relationship(
        "Component", back_populates="category", cascade="all, delete-orphan"
    )


# ----- components (global master) -----
class Component(db.Model, PKMixin, TimestampMixin):
    __tablename__ = "components"
    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(db.String(200), nullable=False)
    default_unit_price_usd: Mapped[float | None] = mapped_column(db.Float)
    uom: Mapped[str | None] = mapped_column(db.String(40))  # piece, meter, hour, etc.

    category = relationship("Category", back_populates="components")

    __table_args__ = (
        UniqueConstraint("category_id", "name", name="uq_components_category_name"),
    )


# ----- projects -----
class Project(db.Model, PKMixin, TimestampMixin):
    __tablename__ = "projects"
    client_id: Mapped[int] = mapped_column(
        ForeignKey("clients.id"), nullable=False, index=True
    )
    code: Mapped[str] = mapped_column(
        db.String(20), unique=True, index=True
    )  # PP-####-YYYYMM
    name: Mapped[str] = mapped_column(db.String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(db.Text)
    project_type: Mapped[str | None] = mapped_column(db.String(120))
    status: Mapped[str] = mapped_column(
        db.String(20), default="planned"
    )  # planned/active/on_hold/completed
    start_date: Mapped[dt_date | None]
    end_date: Mapped[dt_date | None]
    budget_amount_usd: Mapped[float | None] = mapped_column(db.Float)
    tax_rate: Mapped[float | None] = mapped_column(db.Float)  # 0.0 - 0.25 etc.
    currency: Mapped[str] = mapped_column(db.String(3), default="USD", nullable=False)

    client = relationship("Client", back_populates="projects")
    categories = relationship(
        "ProjectCategory", back_populates="project", cascade="all, delete-orphan"
    )
    components = relationship(
        "ProjectComponent", back_populates="project", cascade="all, delete-orphan"
    )
    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")
    expenses: Mapped[list["Expense"]] = relationship(
        "Expense",
        back_populates="project",
        cascade="all, delete-orphan",
    )


@event.listens_for(Project, "before_insert")
def assign_project_code(mapper, connection, target: Project):
    if target.code:
        return
    yyyymm = (target.start_date or datetime.utcnow().date()).strftime("%Y%m")
    pattern = f"PP-%-{yyyymm}"
    result = db.session.query(Project.code).filter(Project.code.like(pattern)).all()
    seqs: list[int] = []
    for (code,) in result:
        m = re.match(rf"PP-(\d{{4}})-{yyyymm}$", code or "")
        if m:
            seqs.append(int(m.group(1)))
    next_seq = (max(seqs) + 1) if seqs else 1
    target.code = f"PP-{next_seq:04d}-{yyyymm}"


# ----- project -> categories (with base cost) -----
class ProjectCategory(db.Model, PKMixin, TimestampMixin):
    __tablename__ = "project_categories"
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id"), nullable=False, index=True
    )
    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id"), nullable=False, index=True
    )
    base_cost_usd: Mapped[float] = mapped_column(db.Float, default=0.0, nullable=False)
    project = relationship("Project", back_populates="categories")
    category = relationship("Category")
    __table_args__ = (
        UniqueConstraint(
            "project_id", "category_id", name="uq_project_categories_proj_cat"
        ),
        Index("ix_pc_proj_cat", "project_id", "category_id"),
    )


# ----- project -> components (BOM) -----
class ProjectComponent(db.Model, PKMixin, TimestampMixin):
    __tablename__ = "project_components"
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id"), nullable=False, index=True
    )
    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id"), nullable=False, index=True
    )
    component_id: Mapped[int] = mapped_column(
        ForeignKey("components.id"), nullable=False, index=True
    )
    quantity: Mapped[float] = mapped_column(db.Float, default=1.0, nullable=False)
    unit_price_usd: Mapped[float | None] = mapped_column(
        db.Float
    )  # overrides component default
    note: Mapped[str | None] = mapped_column(db.Text)
    project = relationship("Project", back_populates="components")
    category = relationship("Category")
    component = relationship("Component")
    __table_args__ = (
        UniqueConstraint(
            "project_id", "component_id", name="uq_project_component_unique"
        ),
        Index("ix_proj_comp_proj_cat", "project_id", "category_id"),
    )


# ----- tasks / comments -----
class Task(db.Model, PKMixin, TimestampMixin):
    __tablename__ = "tasks"
    project_id = mapped_column(ForeignKey("projects.id"), nullable=False, index=True)
    parent_task_id = db.Column(db.Integer, db.ForeignKey("tasks.id", name="fk_tasks_parent"), nullable=True, index=True)
    title = mapped_column(db.String(200), nullable=False)
    description = mapped_column(db.Text)
    status = mapped_column(db.String(20), nullable=False, default="todo")
    assignee_user_id = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    due_date = mapped_column(db.Date)
    order_index = mapped_column(db.Integer, nullable=False, default=0)
    project = relationship("Project", back_populates="tasks")
    parent = relationship(
        "Task",
        remote_side="Task.id",
        back_populates="children",
    )
    children = relationship(
        "Task",
        back_populates="parent",
        cascade="all, delete-orphan",
    )
    comments = db.relationship(
        "TaskComment",
        back_populates="task",
        cascade="all, delete-orphan",
        order_by="TaskComment.created_at"
    )
    assignee = relationship("User")
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "project_id": self.project_id,
            "parent_task_id": self.parent_task_id,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "assignee_user_id": self.assignee_user_id,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "order_index": self.order_index,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class TaskComment(db.Model):
    __tablename__ = "task_comments"
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey("tasks.id", name="fk_task_comments_task"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", name="fk_task_comments_user"), nullable=False, index=True)
    body = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    task = db.relationship("Task", back_populates="comments")
    def to_dict(self):
        return {
            "id": self.id,
            "task_id": self.task_id,
            "user_id": self.user_id,
            "body": self.body,
            "created_at": self.created_at.isoformat() + "Z" if self.created_at else None,
        }


# ----- expenses (header) -----
class Expense(db.Model, PKMixin, TimestampMixin):
    __tablename__ = "expenses"
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False, index=True)
    reference_no: Mapped[str | None] = mapped_column(db.String(50))
    expense_date: Mapped[dt_date] = mapped_column(db.Date, nullable=False)
    vendor: Mapped[str | None] = mapped_column(db.String(120))
    memo: Mapped[str | None] = mapped_column(db.Text)
    project: Mapped["Project"] = relationship("Project", back_populates="expenses")
    lines: Mapped[list["ExpenseLine"]] = relationship(
        "ExpenseLine",
        back_populates="expense",
        cascade="all, delete-orphan",
    )


# ----- expense lines (detail, tax-exclusive) -----
class ExpenseLine(db.Model, PKMixin, TimestampMixin):
    __tablename__ = "expense_lines"
    expense_id: Mapped[int] = mapped_column(ForeignKey("expenses.id"), nullable=False, index=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"), nullable=False, index=True)
    qty: Mapped[float] = mapped_column(db.Numeric(12, 2), default=1)
    unit_price_usd: Mapped[float] = mapped_column(db.Numeric(12, 2), default=0)
    line_total_usd: Mapped[float] = mapped_column(db.Numeric(12, 2))
    expense: Mapped["Expense"] = relationship("Expense", back_populates="lines")
    category: Mapped["Category"] = relationship("Category")


# ----- attachments (polymorphic) -----
class Attachment(db.Model, PKMixin, TimestampMixin):
    __tablename__ = "attachments"
    owner_type: Mapped[str] = mapped_column(
        db.String(20), nullable=False
    )  # 'project' | 'task' | 'expense'
    owner_id: Mapped[int] = mapped_column(db.Integer, nullable=False, index=True)
    file_path: Mapped[str] = mapped_column(db.String(400), nullable=False)
    original_name: Mapped[str] = mapped_column(db.String(255), nullable=False)
    mime_type: Mapped[str | None] = mapped_column(db.String(120))
    size_bytes: Mapped[int | None] = mapped_column(db.Integer)
    uploaded_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
