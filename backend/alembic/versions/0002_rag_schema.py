"""add rag schema

Revision ID: 0002_rag_schema
Revises: 0001_initial_schema
Create Date: 2026-05-06
"""

from alembic import op

from app.infrastructure.db.models.rag import (
    RagConversationMessage,
    RagConversationSession,
    RagKnowledgeBase,
    RagKnowledgeCategory,
    RagKnowledgeCategoryFile,
    RagKnowledgeChunk,
    RagKnowledgeChunkImage,
    RagKnowledgeChunkOrigin,
    RagKnowledgeFile,
    RagKnowledgeJob,
)

revision = "0002_rag_schema"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None

_tables = [
    RagKnowledgeBase.__table__,
    RagKnowledgeCategory.__table__,
    RagKnowledgeCategoryFile.__table__,
    RagKnowledgeFile.__table__,
    RagKnowledgeJob.__table__,
    RagKnowledgeChunk.__table__,
    RagKnowledgeChunkOrigin.__table__,
    RagKnowledgeChunkImage.__table__,
    RagConversationSession.__table__,
    RagConversationMessage.__table__,
]


def upgrade() -> None:
    bind = op.get_bind()
    for table in _tables:
        table.create(bind=bind, checkfirst=True)


def downgrade() -> None:
    bind = op.get_bind()
    for table in reversed(_tables):
        table.drop(bind=bind, checkfirst=True)
