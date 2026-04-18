from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.db.init_db import init_db


if __name__ == "__main__":
    success = init_db()
    sys.exit(0 if success else 1)
