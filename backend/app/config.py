"""Application configuration.

All paths and tunables live here so nothing is hardcoded deep inside services.
Values can be overridden with environment variables (see ``.env.example``).
"""

from __future__ import annotations

import os
from pathlib import Path

# backend/app/config.py -> repository root is three levels up.
REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def _resolve_path(env_var: str, default_relative: str) -> Path:
    """Resolve a path from an environment variable or a repo-relative default."""
    raw_value = os.environ.get(env_var)
    if raw_value:
        return Path(raw_value).expanduser().resolve()
    return (REPOSITORY_ROOT / default_relative).resolve()


def _resolve_absolute_path(env_var: str, default: str) -> Path:
    """Resolve an absolute-path setting while still accepting relative overrides."""
    raw_value = os.environ.get(env_var, default)
    path = Path(raw_value).expanduser()
    if not path.is_absolute():
        path = REPOSITORY_ROOT / path
    return path.resolve()


class Settings:
    """Runtime settings for the Latoun configurator backend."""

    def __init__(self) -> None:
        self.repository_root: Path = REPOSITORY_ROOT
        self.database_path: Path = _resolve_path(
            "LATOUN_DATABASE_PATH", "data/latoun.sqlite"
        )
        self.asset_manifest_path: Path = _resolve_path(
            "LATOUN_ASSET_MANIFEST_PATH", "config/wall_plates/asset_manifest.json"
        )
        self.blender_executable: Path = _resolve_absolute_path(
            "LATOUN_BLENDER_EXECUTABLE",
            r"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe",
        )
        self.parts_obj_directory: Path = _resolve_absolute_path(
            "LATOUN_PARTS_OBJ_DIRECTORY",
            r"C:\Users\kko8\OneDrive\projects\latoun\prod\3d\caches\assets\OBJ",
        )
        self.parts_glb_directory: Path = _resolve_absolute_path(
            "LATOUN_PARTS_GLB_DIRECTORY",
            "frontend/public/assets/wall_plates",
        )
        self.blender_timeout_seconds: int = int(
            os.environ.get("LATOUN_BLENDER_TIMEOUT_SECONDS", "1800")
        )
        # Comma separated list of allowed CORS origins for the Vite dev server.
        raw_origins = os.environ.get(
            "LATOUN_CORS_ORIGINS",
            "http://localhost:5173,http://127.0.0.1:5173",
        )
        self.cors_origins: list[str] = [
            origin.strip() for origin in raw_origins.split(",") if origin.strip()
        ]

    @property
    def database_url(self) -> str:
        # SQLAlchemy expects forward slashes even on Windows.
        return f"sqlite:///{self.database_path.as_posix()}"


settings = Settings()
