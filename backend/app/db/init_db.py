import sys

from sqlalchemy import text

from backend.app.db.models import Base
from backend.app.db.session import engine


def init_db() -> bool:
    # Lightweight helper for local bootstrapping without Alembic
    print("Testing database connection...")

    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            print(f"Connected: {result.scalar()}")

        print("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        print("Database initialization complete.")
        return True
    except Exception as exc:
        print(f"Error: {exc}")
        return False


if __name__ == "__main__":
    success = init_db()
    sys.exit(0 if success else 1)
