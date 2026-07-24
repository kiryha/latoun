"""Run Blender headlessly to convert the wall-plate OBJ source files to GLB."""

from __future__ import annotations

import json
import subprocess
import threading
from pathlib import Path
from typing import Any

from ..config import settings
from ..errors import ConflictError, GeometryConversionError


RESULT_PREFIX = "LATOUN_CONVERSION_RESULT="
BLENDER_SCRIPT = Path(__file__).with_name("blender_convert_parts.py")
_conversion_lock = threading.Lock()


def list_parts() -> dict[str, Any]:
    """Return the top-level OBJ inventory and matching GLB availability."""
    source_directory = settings.parts_obj_directory
    output_directory = settings.parts_glb_directory
    if not source_directory.is_dir():
        raise GeometryConversionError(
            f"OBJ source directory was not found: {source_directory}"
        )

    parts = []
    for source in sorted(
        source_directory.glob("*.obj"),
        key=lambda path: path.name.casefold(),
    ):
        output = output_directory / f"{source.stem}.glb"
        parts.append(
            {
                "source": source.name,
                "output": output.name,
                "glb_exists": output.is_file(),
                "source_size": source.stat().st_size,
                "output_size": output.stat().st_size if output.is_file() else None,
            }
        )
    return {
        "source_directory": str(source_directory),
        "output_directory": str(output_directory),
        "blender_executable": str(settings.blender_executable),
        "blender_available": settings.blender_executable.is_file(),
        "parts": parts,
    }


def _result_from_stdout(stdout: str) -> dict[str, Any]:
    for line in reversed(stdout.splitlines()):
        if line.startswith(RESULT_PREFIX):
            try:
                result = json.loads(line.removeprefix(RESULT_PREFIX))
            except json.JSONDecodeError as exc:
                raise GeometryConversionError(
                    "Blender returned an invalid conversion result."
                ) from exc
            if not isinstance(result, dict):
                break
            return result
    raise GeometryConversionError(
        "Blender finished without returning a conversion result."
    )


def convert_all_parts(*, skip_existing: bool = True) -> dict[str, Any]:
    """Convert top-level OBJs, optionally preserving same-named existing GLBs."""
    if not _conversion_lock.acquire(blocking=False):
        raise ConflictError("A parts conversion is already running.")

    try:
        blender = settings.blender_executable
        source_directory = settings.parts_obj_directory
        output_directory = settings.parts_glb_directory

        if not blender.is_file():
            raise GeometryConversionError(
                f"Blender executable was not found: {blender}"
            )
        if not source_directory.is_dir():
            raise GeometryConversionError(
                f"OBJ source directory was not found: {source_directory}"
            )

        sources = sorted(
            source_directory.glob("*.obj"),
            key=lambda path: path.name.casefold(),
        )
        if not sources:
            return {
                "total": 0,
                "converted": 0,
                "skipped": 0,
                "failed": 0,
                "files": [],
            }

        output_directory.mkdir(parents=True, exist_ok=True)
        if skip_existing and all(
            (output_directory / f"{source.stem}.glb").is_file()
            for source in sources
        ):
            return {
                "total": len(sources),
                "converted": 0,
                "skipped": len(sources),
                "failed": 0,
                "files": [
                    {
                        "source": source.name,
                        "output": f"{source.stem}.glb",
                        "success": True,
                        "skipped": True,
                        "error": None,
                    }
                    for source in sources
                ],
            }

        command = [
            str(blender),
            "--factory-startup",
            "--background",
            "--python",
            str(BLENDER_SCRIPT),
            "--",
            str(source_directory),
            str(output_directory),
            "1" if skip_existing else "0",
        ]
        try:
            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=settings.blender_timeout_seconds,
                check=False,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
        except subprocess.TimeoutExpired as exc:
            raise GeometryConversionError(
                f"Blender conversion exceeded {settings.blender_timeout_seconds} seconds."
            ) from exc
        except OSError as exc:
            raise GeometryConversionError(
                f"Blender could not be started: {exc}"
            ) from exc

        if completed.returncode != 0:
            details = (completed.stderr or completed.stdout).strip()
            if len(details) > 1200:
                details = details[-1200:]
            message = f"Blender exited with code {completed.returncode}."
            if details:
                message = f"{message} {details}"
            raise GeometryConversionError(message)

        return _result_from_stdout(completed.stdout)
    finally:
        _conversion_lock.release()
