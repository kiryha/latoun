"""Loads and queries the asset manifest.

The manifest is the single registry that maps stable semantic asset keys to
physical GLB paths. Nothing else in the codebase should hardcode GLB paths.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from ..config import settings
from ..errors import AssetManifestError, MissingAssetError


class AssetManifest:
    """In-memory view of ``config/asset_manifest.json``."""

    def __init__(self, schema_version: int, assets: dict[str, dict]) -> None:
        self.schema_version = schema_version
        self.assets = assets

    def get(self, asset_key: str) -> dict:
        try:
            return self.assets[asset_key]
        except KeyError as exc:
            raise MissingAssetError(
                f"Missing asset key in manifest: {asset_key}"
            ) from exc

    def try_get(self, asset_key: str) -> dict | None:
        """Return the asset entry, or ``None`` when the key is unregistered."""
        return self.assets.get(asset_key)

    def file_for(self, asset_key: str) -> str:
        return self.get(asset_key)["file"]


def _load_manifest_from_disk(path: Path) -> AssetManifest:
    if not path.exists():
        raise AssetManifestError(f"Asset manifest not found at: {path}")
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise AssetManifestError(f"Asset manifest is not valid JSON: {exc}") from exc

    assets = raw.get("assets")
    if not isinstance(assets, dict) or not assets:
        raise AssetManifestError("Asset manifest has no 'assets' section.")

    return AssetManifest(
        schema_version=int(raw.get("schema_version", 1)),
        assets=assets,
    )


@lru_cache(maxsize=1)
def _cached_manifest(path_str: str) -> AssetManifest:
    return _load_manifest_from_disk(Path(path_str))


def get_asset_manifest() -> AssetManifest:
    """Return the cached asset manifest, loading it on first use."""
    return _cached_manifest(str(settings.asset_manifest_path))


def clear_manifest_cache() -> None:
    """Clear the cache (used by tests that point at different manifests)."""
    _cached_manifest.cache_clear()
