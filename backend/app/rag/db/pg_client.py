"""Deprecated RAG raw-SQL client.

RAG database access now follows the Owly backend style:

- SQLAlchemy models live in app.infrastructure.db.models.rag
- Alembic owns schema creation
- repositories use AsyncSession from app.core.database

The old cursor/executemany helpers intentionally fail fast so new code does not
silently reintroduce a second database access stack.
"""


def _raise_deprecated():
    raise RuntimeError(
        "app.rag.db.pg_client is deprecated. Use app.rag.db repositories with an AsyncSession."
    )


def execute_sql(*args, **kwargs):
    _raise_deprecated()


def execute_select(*args, **kwargs):
    _raise_deprecated()


def execute_returning(*args, **kwargs):
    _raise_deprecated()


def execute_many(*args, **kwargs):
    _raise_deprecated()
