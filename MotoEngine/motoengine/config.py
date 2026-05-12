from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Settings:
    base_dir: Path = BASE_DIR
    env_path: Path = BASE_DIR / "motoengine" / ".env"
    data_dir: Path = BASE_DIR / "data"
    vector_db_dir: Path = BASE_DIR / "data" / "vector_db"
    uploads_dir: Path = BASE_DIR / "uploads"
    app_name: str = "MotoEngine"
    app_version: str = "0.1.0"
    extra: dict[str, Any] = field(default_factory=dict)


settings = Settings()
