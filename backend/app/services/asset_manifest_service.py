"""Loads, validates, and saves the wall-plate asset manifest.

The JSON file at ``config/wall_plates/asset_manifest.json`` is the source of
truth for geometry asset records. Assembly resolution ignores inactive entries
and looks up assets by structured fields (not key/filename parsing alone).
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import settings
from ..errors import AssetManifestError, ConflictError, MissingAssetError, ValidationError
from ..models import ModuleType

ASSET_TYPES = frozenset({"plate", "hardware", "slot_module"})
SUPPORTED_GANG_COUNTS = frozenset({1, 2, 3, 4})
HARDWARE_TYPES = frozenset({"plate_screws"})
WALL_PLATES_PREFIX = "/assets/wall_plates/"
LEGACY_GLB_PREFIX = "/assets/glb/"

_GANG_FROM_KEY_RE = re.compile(r"(?:^|\.)(\d)gang(?:\.|$)")
_DANGEROUS_PATH_RE = re.compile(r"(?:\.\.|:\\|/etc/|/usr/|file://)", re.IGNORECASE)


@dataclass
class ManifestIssue:
    level: str  # "error" | "warning"
    message: str
    asset_key: str | None = None


@dataclass
class ManifestValidationResult:
    errors: list[ManifestIssue] = field(default_factory=list)
    warnings: list[ManifestIssue] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


class AssetManifest:
    """In-memory view of the wall-plate asset manifest."""

    def __init__(self, assets: dict[str, dict]) -> None:
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

    def find_active(
        self,
        *,
        asset_type: str,
        gang_count: int,
        hardware_type: str | None = None,
        slot_position: int | None = None,
        module_type: str | None = None,
    ) -> tuple[str, dict] | None:
        """Return ``(key, entry)`` for the first active match, else ``None``."""
        for key, entry in self.assets.items():
            if not _is_active(entry):
                continue
            if entry.get("asset_type") != asset_type:
                continue
            if int(entry.get("gang_count", -1)) != gang_count:
                continue
            if asset_type == "hardware":
                if entry.get("hardware_type") != hardware_type:
                    continue
            elif asset_type == "slot_module":
                if int(entry.get("slot_position", -1)) != slot_position:
                    continue
                if entry.get("module_type") != module_type:
                    continue
            return key, entry
        return None


def _is_active(entry: dict) -> bool:
    if "is_active" not in entry:
        return True
    return bool(entry["is_active"])


def _derive_gang_count(key: str, entry: dict) -> int | None:
    if "gang_count" in entry:
        try:
            return int(entry["gang_count"])
        except (TypeError, ValueError):
            return None
    match = _GANG_FROM_KEY_RE.search(key)
    if match:
        return int(match.group(1))
    file_path = str(entry.get("file", ""))
    match = re.search(r"(\d)gang", file_path)
    if match:
        return int(match.group(1))
    return None


def migrate_entry(key: str, raw: dict[str, Any]) -> dict[str, Any]:
    """Normalize a single legacy or partial entry into the current shape."""
    entry = dict(raw)
    entry.pop("schema_version", None)
    entry.pop("coordinate_space", None)

    asset_type = entry.get("asset_type")
    gang_count = _derive_gang_count(key, entry)
    if gang_count is not None:
        entry["gang_count"] = gang_count

    file_path = entry.get("file")
    if isinstance(file_path, str) and file_path.startswith(LEGACY_GLB_PREFIX):
        entry["file"] = WALL_PLATES_PREFIX + file_path[len(LEGACY_GLB_PREFIX) :]

    if "is_active" not in entry:
        entry["is_active"] = True
    else:
        entry["is_active"] = bool(entry["is_active"])

    if asset_type == "hardware" and "hardware_type" not in entry:
        entry["hardware_type"] = "plate_screws"

    return entry


def migrate_manifest(raw: dict[str, Any]) -> dict[str, dict]:
    """Migrate a full raw JSON document to the current parts map.

    Accepts the current ``parts`` key and the legacy ``assets`` key.
    """
    parts_raw = raw.get("parts")
    if parts_raw is None:
        parts_raw = raw.get("assets")
    if not isinstance(parts_raw, dict):
        raise AssetManifestError("Asset manifest has no 'parts' section.")

    migrated: dict[str, dict] = {}
    for key, value in parts_raw.items():
        if not isinstance(value, dict):
            raise AssetManifestError(f"Asset entry '{key}' must be an object.")
        migrated[str(key)] = migrate_entry(str(key), value)
    return migrated


def compute_revision(assets: dict[str, dict]) -> str:
    """Stable content hash used as an optimistic-concurrency token."""
    normalized = normalize_manifest_assets(assets)
    payload = json.dumps({"parts": normalized}, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return f"sha256-{digest}"


def _ordered_entry_fields(entry: dict) -> dict[str, Any]:
    asset_type = entry.get("asset_type")
    ordered: dict[str, Any] = {}
    if asset_type == "plate":
        for key in ("asset_type", "gang_count", "file", "is_active"):
            if key in entry:
                ordered[key] = entry[key]
    elif asset_type == "hardware":
        for key in ("asset_type", "hardware_type", "gang_count", "file", "is_active"):
            if key in entry:
                ordered[key] = entry[key]
    elif asset_type == "slot_module":
        for key in (
            "asset_type",
            "gang_count",
            "module_type",
            "slot_position",
            "file",
            "is_active",
        ):
            if key in entry:
                ordered[key] = entry[key]
    else:
        ordered = dict(entry)
    # Preserve any unexpected leftover fields after the preferred order.
    for key, value in entry.items():
        if key not in ordered:
            ordered[key] = value
    return ordered


def _sort_key_for_entry(
    key: str,
    entry: dict,
    module_type_order: dict[str, int] | None = None,
) -> tuple:
    asset_type = entry.get("asset_type")
    type_rank = {"plate": 0, "hardware": 1, "slot_module": 2}.get(
        str(asset_type), 99
    )
    gang = entry.get("gang_count", 99)
    try:
        gang_i = int(gang)
    except (TypeError, ValueError):
        gang_i = 99
    slot = entry.get("slot_position", 0)
    try:
        slot_i = int(slot)
    except (TypeError, ValueError):
        slot_i = 0
    module_code = str(entry.get("module_type") or "")
    module_rank = 9999
    if module_type_order and module_code in module_type_order:
        module_rank = module_type_order[module_code]
    return (type_rank, gang_i, slot_i, module_rank, module_code, key)


def normalize_manifest_assets(
    assets: dict[str, dict],
    *,
    module_type_order: dict[str, int] | None = None,
) -> dict[str, dict]:
    """Return deterministically ordered assets with stable field order."""
    items = sorted(
        assets.items(),
        key=lambda item: _sort_key_for_entry(item[0], item[1], module_type_order),
    )
    return {key: _ordered_entry_fields(dict(entry)) for key, entry in items}


def serialize_manifest(
    assets: dict[str, dict],
    *,
    module_type_order: dict[str, int] | None = None,
) -> str:
    normalized = normalize_manifest_assets(assets, module_type_order=module_type_order)
    return json.dumps({"parts": normalized}, indent=2, ensure_ascii=False) + "\n"


def _load_raw_from_disk(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise AssetManifestError(f"Asset manifest not found at: {path}")
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise AssetManifestError(f"Asset manifest is not valid JSON: {exc}") from exc
    if not isinstance(raw, dict):
        raise AssetManifestError("Asset manifest root must be an object.")
    return raw


def _load_manifest_from_disk(path: Path) -> AssetManifest:
    raw = _load_raw_from_disk(path)
    assets = migrate_manifest(raw)
    if not assets:
        raise AssetManifestError("Asset manifest has no 'parts' section.")
    return AssetManifest(assets=assets)


@lru_cache(maxsize=1)
def _cached_manifest(path_str: str) -> AssetManifest:
    return _load_manifest_from_disk(Path(path_str))


def get_asset_manifest() -> AssetManifest:
    """Return the cached asset manifest, loading it on first use."""
    return _cached_manifest(str(settings.asset_manifest_path))


def clear_manifest_cache() -> None:
    """Clear the cache (used after saves and by tests)."""
    _cached_manifest.cache_clear()


def get_manifest_document() -> tuple[dict[str, dict], str]:
    """Return ``(assets, revision)`` for the Geometry editor GET endpoint."""
    clear_manifest_cache()
    manifest = get_asset_manifest()
    assets = normalize_manifest_assets(manifest.assets)
    return assets, compute_revision(assets)


def _module_type_codes(session: Session) -> dict[str, ModuleType]:
    rows = session.scalars(select(ModuleType)).all()
    return {row.code: row for row in rows}


def _module_type_sort_order(session: Session) -> dict[str, int]:
    rows = session.scalars(select(ModuleType)).all()
    return {row.code: row.sort_order for row in rows}


def _resolver_identity(key: str, entry: dict) -> tuple | None:
    asset_type = entry.get("asset_type")
    try:
        gang = int(entry.get("gang_count"))  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    if asset_type == "plate":
        return ("plate", gang)
    if asset_type == "hardware":
        return ("hardware", entry.get("hardware_type"), gang)
    if asset_type == "slot_module":
        try:
            slot = int(entry.get("slot_position"))  # type: ignore[arg-type]
        except (TypeError, ValueError):
            return None
        return ("slot_module", gang, slot, entry.get("module_type"))
    return None


def _validate_file_path(key: str, file_path: Any, result: ManifestValidationResult) -> None:
    if not isinstance(file_path, str) or not file_path.strip():
        result.errors.append(
            ManifestIssue("error", "File path is required.", asset_key=key)
        )
        return
    path = file_path.strip()
    if _DANGEROUS_PATH_RE.search(path) or "\\" in path:
        result.errors.append(
            ManifestIssue(
                "error",
                "File path contains unsupported or dangerous path characters.",
                asset_key=key,
            )
        )
        return
    if not path.startswith(WALL_PLATES_PREFIX):
        result.errors.append(
            ManifestIssue(
                "error",
                f"File path must begin with {WALL_PLATES_PREFIX}.",
                asset_key=key,
            )
        )
    if not path.lower().endswith(".glb"):
        result.errors.append(
            ManifestIssue("error", "File path must end with .glb.", asset_key=key)
        )


def validate_manifest(
    assets: dict[str, dict],
    *,
    module_types: dict[str, ModuleType] | None = None,
) -> ManifestValidationResult:
    """Validate a complete working manifest. Does not check GLB existence."""
    result = ManifestValidationResult()

    if not isinstance(assets, dict):
        result.errors.append(ManifestIssue("error", "assets must be an object."))
        return result

    seen_keys: set[str] = set()
    active_identities: dict[tuple, str] = {}
    inactive_identities: dict[tuple, str] = {}

    for key, entry in assets.items():
        if not isinstance(key, str) or not key.strip():
            result.errors.append(
                ManifestIssue("error", "Manifest key is empty.", asset_key=str(key))
            )
            continue
        if "\x00" in key or any(ord(ch) < 32 for ch in key):
            result.errors.append(
                ManifestIssue(
                    "error",
                    "Manifest key contains unsupported control characters.",
                    asset_key=key,
                )
            )
        if key in seen_keys:
            result.errors.append(
                ManifestIssue("error", "Duplicate manifest key.", asset_key=key)
            )
        seen_keys.add(key)

        if not isinstance(entry, dict):
            result.errors.append(
                ManifestIssue("error", "Asset entry must be an object.", asset_key=key)
            )
            continue

        asset_type = entry.get("asset_type")
        if asset_type not in ASSET_TYPES:
            result.errors.append(
                ManifestIssue(
                    "error",
                    f"Unrecognized asset_type: {asset_type!r}.",
                    asset_key=key,
                )
            )

        try:
            gang_count = int(entry.get("gang_count"))  # type: ignore[arg-type]
        except (TypeError, ValueError):
            result.errors.append(
                ManifestIssue(
                    "error",
                    "Gang count must be between 1 and 4.",
                    asset_key=key,
                )
            )
            gang_count = -1
        else:
            if gang_count not in SUPPORTED_GANG_COUNTS:
                result.errors.append(
                    ManifestIssue(
                        "error",
                        "Gang count must be between 1 and 4.",
                        asset_key=key,
                    )
                )

        if "is_active" not in entry or not isinstance(entry["is_active"], bool):
            result.errors.append(
                ManifestIssue(
                    "error",
                    "is_active must be a boolean.",
                    asset_key=key,
                )
            )

        _validate_file_path(key, entry.get("file"), result)

        if asset_type == "plate":
            for forbidden in ("hardware_type", "module_type", "slot_position"):
                if forbidden in entry:
                    result.errors.append(
                        ManifestIssue(
                            "error",
                            f"Plate entries must not include {forbidden}.",
                            asset_key=key,
                        )
                    )
        elif asset_type == "hardware":
            hardware_type = entry.get("hardware_type")
            if hardware_type not in HARDWARE_TYPES:
                result.errors.append(
                    ManifestIssue(
                        "error",
                        "hardware_type must be plate_screws.",
                        asset_key=key,
                    )
                )
            for forbidden in ("module_type", "slot_position"):
                if forbidden in entry:
                    result.errors.append(
                        ManifestIssue(
                            "error",
                            f"Hardware entries must not include {forbidden}.",
                            asset_key=key,
                        )
                    )
        elif asset_type == "slot_module":
            if "hardware_type" in entry:
                result.errors.append(
                    ManifestIssue(
                        "error",
                        "Slot-module entries must not include hardware_type.",
                        asset_key=key,
                    )
                )
            module_code = entry.get("module_type")
            if not isinstance(module_code, str) or not module_code.strip():
                result.errors.append(
                    ManifestIssue(
                        "error",
                        "module_type is required for slot modules.",
                        asset_key=key,
                    )
                )
            elif module_types is not None and module_code not in module_types:
                result.errors.append(
                    ManifestIssue(
                        "error",
                        f'Module type "{module_code}" does not exist in the database.',
                        asset_key=key,
                    )
                )
            elif (
                module_types is not None
                and module_code in module_types
                and not module_types[module_code].is_active
            ):
                result.warnings.append(
                    ManifestIssue(
                        "warning",
                        f'Module type "{module_code}" is inactive.',
                        asset_key=key,
                    )
                )

            try:
                slot_position = int(entry.get("slot_position"))  # type: ignore[arg-type]
            except (TypeError, ValueError):
                result.errors.append(
                    ManifestIssue(
                        "error",
                        "slot_position must be an integer.",
                        asset_key=key,
                    )
                )
            else:
                if slot_position < 1 or (
                    gang_count in SUPPORTED_GANG_COUNTS and slot_position > gang_count
                ):
                    result.errors.append(
                        ManifestIssue(
                            "error",
                            f"Slot {slot_position} is invalid for a {gang_count}-gang asset.",
                            asset_key=key,
                        )
                    )

        identity = _resolver_identity(key, entry)
        if identity is None:
            continue
        if _is_active(entry):
            if identity in active_identities:
                other = active_identities[identity]
                result.errors.append(
                    ManifestIssue(
                        "error",
                        f"Two active entries resolve to the same assembly requirement "
                        f"({key} and {other}).",
                        asset_key=key,
                    )
                )
            else:
                active_identities[identity] = key
                if identity in inactive_identities:
                    result.warnings.append(
                        ManifestIssue(
                            "warning",
                            "An inactive entry duplicates this resolver identity.",
                            asset_key=key,
                        )
                    )
        else:
            if identity in active_identities or identity in inactive_identities:
                result.warnings.append(
                    ManifestIssue(
                        "warning",
                        "An inactive entry duplicates another resolver identity.",
                        asset_key=key,
                    )
                )
            inactive_identities.setdefault(identity, key)

    return result


def validate_and_raise(
    assets: dict[str, dict],
    *,
    session: Session,
) -> ManifestValidationResult:
    module_types = _module_type_codes(session)
    result = validate_manifest(assets, module_types=module_types)
    if not result.ok:
        messages = [issue.message for issue in result.errors]
        raise ValidationError("; ".join(messages))
    return result


def save_manifest(
    session: Session,
    *,
    assets: dict[str, dict],
    expected_revision: str | None,
) -> tuple[dict[str, dict], str, list[str]]:
    """Validate, atomically write, and return ``(assets, revision, warnings)``."""
    path = settings.asset_manifest_path
    if not path.parent.exists():
        path.parent.mkdir(parents=True, exist_ok=True)

    current_assets, current_revision = get_manifest_document()
    if expected_revision is not None and expected_revision != current_revision:
        raise ConflictError(
            "The manifest changed on disk after it was loaded. Reload it before saving."
        )

    # Work on a cleaned copy: drop forbidden fields by type after migrate-normalize.
    cleaned: dict[str, dict] = {}
    for key, raw_entry in assets.items():
        if not isinstance(raw_entry, dict):
            raise ValidationError(f"Asset entry '{key}' must be an object.")
        entry = migrate_entry(key, raw_entry)
        asset_type = entry.get("asset_type")
        if asset_type == "plate":
            entry.pop("hardware_type", None)
            entry.pop("module_type", None)
            entry.pop("slot_position", None)
        elif asset_type == "hardware":
            entry.pop("module_type", None)
            entry.pop("slot_position", None)
        elif asset_type == "slot_module":
            entry.pop("hardware_type", None)
        cleaned[key] = entry

    result = validate_and_raise(cleaned, session=session)
    module_order = _module_type_sort_order(session)
    text = serialize_manifest(cleaned, module_type_order=module_order)
    normalized = normalize_manifest_assets(cleaned, module_type_order=module_order)

    _atomic_write(path, text)
    clear_manifest_cache()

    revision = compute_revision(normalized)
    warnings = [issue.message for issue in result.warnings]
    return normalized, revision, warnings


def _atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(
        prefix=".asset_manifest_",
        suffix=".tmp",
        dir=str(path.parent),
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_name, path)
    except Exception:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


def check_glb_availability(file_paths: Iterable[str]) -> dict[str, bool]:
    """Map public URL paths to whether a matching file exists under frontend/public."""
    public_root = settings.repository_root / "frontend" / "public"
    availability: dict[str, bool] = {}
    for file_path in file_paths:
        if not isinstance(file_path, str) or not file_path.startswith("/"):
            availability[str(file_path)] = False
            continue
        relative = file_path.lstrip("/")
        availability[file_path] = (public_root / relative).is_file()
    return availability
