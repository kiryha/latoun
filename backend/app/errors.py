"""Domain-specific exceptions with clear, surfaceable messages."""

from __future__ import annotations


class ConfiguratorError(Exception):
    """Base class for configurator errors.

    ``status_code`` maps to an HTTP status when raised inside a request.
    """

    status_code: int = 400

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class ValidationError(ConfiguratorError):
    """Invalid material code, module type, or gang count."""

    status_code = 422


class AssetManifestError(ConfiguratorError):
    """The asset manifest is missing or malformed."""

    status_code = 500


class GeometryConversionError(ConfiguratorError):
    """Blender could not start or did not return a usable conversion result."""

    status_code = 500


class MissingAssetError(ConfiguratorError):
    """A required asset key is not present in the manifest."""

    status_code = 500


class NotFoundError(ConfiguratorError):
    """A requested resource (e.g. saved configuration) does not exist."""

    status_code = 404


class ConflictError(ConfiguratorError):
    """The request conflicts with current state (e.g. duplicate code, or
    deleting a material still referenced by a saved configuration)."""

    status_code = 409
