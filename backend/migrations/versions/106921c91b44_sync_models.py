from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '106921c91b44'
down_revision = 'cb3fec638ac2'
branch_labels = None
depends_on = None


def upgrade():
    # Only add what we need; do NOT attempt to drop/recreate the existing project_id FK in SQLite
    with op.batch_alter_table('tasks', schema=None) as batch_op:
        # add parent_task_id
        batch_op.add_column(sa.Column('parent_task_id', sa.Integer(), nullable=True))

        # index on assignee_user_id (as autogenerate suggested)
        batch_op.create_index('ix_tasks_assignee_user_id', ['assignee_user_id'], unique=False)

        # self-referencing FK (name it explicitly; SQLite needs a name for Alembic to manage later)
        batch_op.create_foreign_key(
            'fk_tasks_parent_task_id_tasks',
            'tasks',
            ['parent_task_id'],
            ['id'],
            ondelete='SET NULL'
        )

    # IMPORTANT: Do NOT drop any existing constraint on project_id in SQLite.
    # If autogenerate added a drop_constraint for project_id, remove it.


def downgrade():
    with op.batch_alter_table('tasks', schema=None) as batch_op:
        # drop the self-referencing FK and the index, then the column
        batch_op.drop_constraint('fk_tasks_parent_task_id_tasks', type_='foreignkey')
        batch_op.drop_index('ix_tasks_assignee_user_id')
        batch_op.drop_column('parent_task_id')
