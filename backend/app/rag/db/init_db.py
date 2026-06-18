"""RAG schema initialization is managed by Alembic.

This module is kept only for backward-compatible imports from the portable RAG
code. Do not create RAG tables at application startup; run Alembic migrations
instead:

    cd backend
    alembic upgrade head
"""


def init_db() -> None:
    return None


if __name__ == "__main__":
    print("RAG tables are managed by Alembic. Run: alembic upgrade head")
