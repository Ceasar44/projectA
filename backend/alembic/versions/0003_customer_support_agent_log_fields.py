"""add customer support agent log fields

Revision ID: 0003_customer_support_agent_log_fields
Revises: 0002_rag_schema
Create Date: 2026-06-17
"""

from alembic import op
import sqlalchemy as sa


revision = "0003_customer_support_agent_log_fields"
down_revision = "0002_rag_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("ai_auto_reply_log") as batch_op:
        batch_op.add_column(sa.Column("intent", sa.String(length=100), nullable=False, server_default=""))
        batch_op.add_column(sa.Column("sentiment", sa.String(length=50), nullable=False, server_default=""))
        batch_op.add_column(sa.Column("confidence", sa.Float(), nullable=False, server_default="0"))
        batch_op.add_column(sa.Column("tool_calls", sa.JSON(), nullable=False, server_default="[]"))
        batch_op.add_column(sa.Column("sources", sa.JSON(), nullable=False, server_default="[]"))
        batch_op.add_column(sa.Column("agent_status", sa.String(length=50), nullable=False, server_default=""))


def downgrade() -> None:
    with op.batch_alter_table("ai_auto_reply_log") as batch_op:
        batch_op.drop_column("agent_status")
        batch_op.drop_column("sources")
        batch_op.drop_column("tool_calls")
        batch_op.drop_column("confidence")
        batch_op.drop_column("sentiment")
        batch_op.drop_column("intent")
