from pathlib import Path
import sys

from alembic import command
from alembic.config import Config


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.db.session import engine


def main() -> None:
    alembic_config = Config(str(PROJECT_ROOT / "alembic.ini"))
    command.upgrade(alembic_config, "head")
    print(f"Initialized local database: {engine.url}")


if __name__ == "__main__":
    main()
