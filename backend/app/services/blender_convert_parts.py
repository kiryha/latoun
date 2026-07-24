"""Blender-side OBJ-to-GLB batch conversion.

This file is executed by Blender, not imported by the FastAPI process.
Arguments after ``--`` are the source OBJ directory, destination GLB
directory, and whether existing outputs should be skipped. A machine-readable
result is emitted on stdout for the caller.
"""

from __future__ import annotations

import json
import sys
import traceback
from pathlib import Path

import bpy


RESULT_PREFIX = "LATOUN_CONVERSION_RESULT="


def _script_arguments() -> tuple[Path, Path, bool]:
    try:
        separator = sys.argv.index("--")
        source_arg, output_arg, skip_arg = sys.argv[separator + 1 : separator + 4]
    except (ValueError, IndexError):
        raise RuntimeError(
            "Expected source directory, output directory, and skip flag after '--'"
        )
    return Path(source_arg), Path(output_arg), skip_arg == "1"


def _convert_file(
    source: Path,
    output_directory: Path,
    skip_existing: bool,
) -> dict[str, object]:
    output = output_directory / f"{source.stem}.glb"
    temporary_output = output_directory / f"{source.stem}.tmp.glb"
    if skip_existing and output.is_file():
        return {
            "source": source.name,
            "output": output.name,
            "success": True,
            "skipped": True,
            "error": None,
        }

    try:
        bpy.ops.wm.read_factory_settings(use_empty=True)
        imported = bpy.ops.wm.obj_import(
            filepath=str(source),
            use_split_groups=True,
        )
        if "FINISHED" not in imported:
            raise RuntimeError(f"OBJ import returned {sorted(imported)}")

        exported = bpy.ops.export_scene.gltf(
            filepath=str(temporary_output),
            export_format="GLB",
        )
        if "FINISHED" not in exported:
            raise RuntimeError(f"GLB export returned {sorted(exported)}")

        temporary_output.replace(output)
        return {
            "source": source.name,
            "output": output.name,
            "success": True,
            "skipped": False,
            "error": None,
        }
    except Exception as exc:
        temporary_output.unlink(missing_ok=True)
        return {
            "source": source.name,
            "output": output.name,
            "success": False,
            "skipped": False,
            "error": f"{type(exc).__name__}: {exc}",
        }


def main() -> None:
    source_directory, output_directory, skip_existing = _script_arguments()
    output_directory.mkdir(parents=True, exist_ok=True)
    sources = sorted(
        source_directory.glob("*.obj"),
        key=lambda path: path.name.casefold(),
    )
    files = [
        _convert_file(source, output_directory, skip_existing)
        for source in sources
    ]
    result = {
        "total": len(files),
        "converted": sum(
            bool(item["success"]) and not bool(item["skipped"]) for item in files
        ),
        "skipped": sum(bool(item["skipped"]) for item in files),
        "failed": sum(not bool(item["success"]) for item in files),
        "files": files,
    }
    print(f"{RESULT_PREFIX}{json.dumps(result, ensure_ascii=False)}", flush=True)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        raise
