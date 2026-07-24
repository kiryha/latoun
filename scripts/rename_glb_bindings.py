"""One-time asset migration: rewrite GLB glTF material names to semantic bindings.

The v0.1 Houdini exports shipped with a single physical material name
(``brass_metal``) on every mesh. The semantic material assignment system
(see ``docs/material_assignment.md``) requires each geometry region to carry a
role-based *semantic binding* name instead, resolved at render time through the
finish-scheme + binding -> render-material tables.

Until the Houdini master scene is re-exported with these names natively, this
script performs the equivalent rename directly on the shipped GLB files. It is
idempotent: running it again after the rename is a no-op.

This is an offline asset-preparation step, NOT runtime GLB rewriting (which is
an explicit non-goal). Run it once from the repository root:

    python scripts/rename_glb_bindings.py
"""

from __future__ import annotations

import json
import struct
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
GLB_DIRECTORY = REPOSITORY_ROOT / "frontend" / "public" / "assets" / "glb"

_GLB_MAGIC = 0x46546C67  # 'glTF'
_JSON_CHUNK_TYPE = 0x4E4F534A  # 'JSON'
_BIN_CHUNK_TYPE = 0x004E4942  # 'BIN\0'

# Target semantic binding for the single material inside each GLB file.
# See docs/material_assignment.md section 24 (Stage 2 suggested first bindings).
BINDING_BY_FILENAME: dict[str, str] = {
    "1gang_plate.glb": "primary_metal",
    "1gang_plate_screws.glb": "hardware_metal",
    "1gang_slot1_dimmer.glb": "actuator_metal",
    "1gang_slot1_switch.glb": "actuator_metal",
}


def _read_chunks(data: bytes) -> tuple[dict, bytes | None]:
    """Parse a GLB byte string into (json_object, binary_chunk_bytes)."""
    magic, version, _length = struct.unpack_from("<III", data, 0)
    if magic != _GLB_MAGIC:
        raise ValueError("Not a GLB file (bad magic).")
    if version != 2:
        raise ValueError(f"Unsupported GLB version: {version}")

    offset = 12
    json_object: dict | None = None
    binary_chunk: bytes | None = None
    while offset < len(data):
        chunk_length, chunk_type = struct.unpack_from("<II", data, offset)
        offset += 8
        chunk_data = data[offset : offset + chunk_length]
        offset += chunk_length
        if chunk_type == _JSON_CHUNK_TYPE:
            json_object = json.loads(chunk_data.decode("utf-8"))
        elif chunk_type == _BIN_CHUNK_TYPE:
            binary_chunk = chunk_data

    if json_object is None:
        raise ValueError("GLB has no JSON chunk.")
    return json_object, binary_chunk


def _pad(chunk: bytes, pad_byte: bytes) -> bytes:
    remainder = len(chunk) % 4
    if remainder == 0:
        return chunk
    return chunk + pad_byte * (4 - remainder)


def _write_glb(json_object: dict, binary_chunk: bytes | None) -> bytes:
    json_bytes = _pad(
        json.dumps(json_object, separators=(",", ":")).encode("utf-8"), b"\x20"
    )
    parts = [struct.pack("<II", len(json_bytes), _JSON_CHUNK_TYPE), json_bytes]

    if binary_chunk is not None:
        bin_bytes = _pad(binary_chunk, b"\x00")
        parts.append(struct.pack("<II", len(bin_bytes), _BIN_CHUNK_TYPE))
        parts.append(bin_bytes)

    body = b"".join(parts)
    total_length = 12 + len(body)
    header = struct.pack("<III", _GLB_MAGIC, 2, total_length)
    return header + body


def rename_bindings() -> None:
    for filename, binding_name in BINDING_BY_FILENAME.items():
        path = GLB_DIRECTORY / filename
        if not path.exists():
            print(f"  SKIP (missing): {filename}")
            continue

        json_object, binary_chunk = _read_chunks(path.read_bytes())
        materials = json_object.get("materials", [])
        if not materials:
            print(f"  SKIP (no materials): {filename}")
            continue

        current_names = [material.get("name") for material in materials]
        if current_names == [binding_name] * len(materials):
            print(f"  OK (already '{binding_name}'): {filename}")
            continue

        # Each shipped GLB has exactly one material region; assign it the
        # semantic binding. If a file ever has multiple, they all take the
        # same role here (single visible metal region per part in v0.1).
        for material in materials:
            material["name"] = binding_name

        path.write_bytes(_write_glb(json_object, binary_chunk))
        print(f"  RENAMED {current_names} -> '{binding_name}': {filename}")


if __name__ == "__main__":
    print(f"Renaming GLB material names to semantic bindings in: {GLB_DIRECTORY}")
    rename_bindings()
    print("Done.")
