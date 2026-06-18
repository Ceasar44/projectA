"""initial schema

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-04-15
"""

from alembic import op
import sqlalchemy as sa

from app.infrastructure.db.base import Base
from app.infrastructure.db.models import *  # noqa: F403


revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)


def downgrade() -> None:
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)
