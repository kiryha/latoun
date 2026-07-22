"""Material assignment CRUD plus the single authoritative assignment resolver.

The resolver here is the one place that combines ``init`` with a selected
finish scheme. The render-state service, the resolved-assignments endpoint, and
the Assignments-tab preview all go through it so there is exactly one
resolution implementation.
"""

from __future__ import annotations

import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..errors import ConflictError, NotFoundError, ValidationError
from ..models import FinishScheme, Material, MaterialAssignment
from ..schemas import (
    BINDING_NAME_PATTERN,
    BulkAssignmentItem,
    FinishSchemeRef,
    MaterialAssignmentCreate,
    MaterialAssignmentOut,
    MaterialAssignmentUpdate,
    MaterialOut,
    MaterialUsageOut,
    ResolvedAssignmentsOut,
)
from .finish_scheme_service import (
    INIT_SCHEME_CODE,
    get_finish_scheme,
    get_finish_scheme_by_code,
)

_BINDING_NAME_RE = re.compile(BINDING_NAME_PATTERN)


def normalize_binding_name(raw_binding_name: str) -> str:
    """Normalize and validate a semantic binding name.

    Rules (see docs/material_assignment.md 14.5): trim, lowercase, spaces ->
    underscores, reject empty, and require the pattern ``^[a-z][a-z0-9_]*$``.
    """
    normalized = raw_binding_name.strip().lower().replace(" ", "_")
    if not normalized:
        raise ValidationError("Binding name must not be empty.")
    if not _BINDING_NAME_RE.match(normalized):
        raise ValidationError(
            f"Invalid binding name '{raw_binding_name}'. Use lowercase letters, "
            "digits and underscores, starting with a letter "
            "(e.g. 'primary_metal')."
        )
    return normalized


def _resolve_material_by_code(session: Session, material_code: str) -> Material:
    material = session.scalar(select(Material).where(Material.code == material_code))
    if material is None:
        raise ValidationError(f"Render material does not exist: {material_code}")
    return material


def _to_out(assignment: MaterialAssignment) -> MaterialAssignmentOut:
    return MaterialAssignmentOut(
        material_assignment_id=assignment.material_assignment_id,
        finish_scheme_id=assignment.finish_scheme_id,
        finish_scheme_code=assignment.finish_scheme.code,
        binding_name=assignment.binding_name,
        material_code=assignment.material.code,
        material_display_name=assignment.material.display_name,
    )


def list_assignments(
    session: Session, finish_scheme_id: int
) -> list[MaterialAssignmentOut]:
    finish_scheme = get_finish_scheme(session, finish_scheme_id)
    assignments = session.scalars(
        select(MaterialAssignment)
        .where(MaterialAssignment.finish_scheme_id == finish_scheme.finish_scheme_id)
        .order_by(MaterialAssignment.binding_name)
    ).all()
    return [_to_out(assignment) for assignment in assignments]


def create_assignment(
    session: Session, finish_scheme_id: int, data: MaterialAssignmentCreate
) -> MaterialAssignmentOut:
    finish_scheme = get_finish_scheme(session, finish_scheme_id)
    binding_name = normalize_binding_name(data.binding_name)
    material = _resolve_material_by_code(session, data.material_code)

    existing = session.scalar(
        select(MaterialAssignment).where(
            MaterialAssignment.finish_scheme_id == finish_scheme.finish_scheme_id,
            MaterialAssignment.binding_name == binding_name,
        )
    )
    if existing is not None:
        raise ConflictError(
            f"An assignment for binding '{binding_name}' already exists in "
            f"finish scheme '{finish_scheme.code}'."
        )

    assignment = MaterialAssignment(
        finish_scheme_id=finish_scheme.finish_scheme_id,
        binding_name=binding_name,
        material_id=material.material_id,
    )
    session.add(assignment)
    session.commit()
    session.refresh(assignment)
    return _to_out(assignment)


def _get_assignment(session: Session, material_assignment_id: int) -> MaterialAssignment:
    assignment = session.get(MaterialAssignment, material_assignment_id)
    if assignment is None:
        raise NotFoundError(
            f"Material assignment not found: {material_assignment_id}"
        )
    return assignment


def update_assignment(
    session: Session, material_assignment_id: int, data: MaterialAssignmentUpdate
) -> MaterialAssignmentOut:
    assignment = _get_assignment(session, material_assignment_id)

    if data.binding_name is not None:
        binding_name = normalize_binding_name(data.binding_name)
        if binding_name != assignment.binding_name:
            clash = session.scalar(
                select(MaterialAssignment).where(
                    MaterialAssignment.finish_scheme_id == assignment.finish_scheme_id,
                    MaterialAssignment.binding_name == binding_name,
                )
            )
            if clash is not None:
                raise ConflictError(
                    f"An assignment for binding '{binding_name}' already exists "
                    "in this finish scheme."
                )
            assignment.binding_name = binding_name

    if data.material_code is not None:
        material = _resolve_material_by_code(session, data.material_code)
        assignment.material_id = material.material_id

    session.commit()
    session.refresh(assignment)
    return _to_out(assignment)


def delete_assignment(
    session: Session, material_assignment_id: int
) -> MaterialAssignmentOut:
    assignment = _get_assignment(session, material_assignment_id)
    result = _to_out(assignment)
    session.delete(assignment)
    session.commit()
    return result


def bulk_save_assignments(
    session: Session, finish_scheme_id: int, items: list[BulkAssignmentItem]
) -> list[MaterialAssignmentOut]:
    """Replace the finish scheme's assignments with the submitted complete set.

    Creates new rows, updates existing rows for matching binding names, and
    removes rows omitted from the submission — all in one transaction.
    """
    finish_scheme = get_finish_scheme(session, finish_scheme_id)

    # Normalize and validate every item first so we fail before mutating.
    normalized: dict[str, int] = {}  # binding_name -> material_id
    for item in items:
        binding_name = normalize_binding_name(item.binding_name)
        if binding_name in normalized:
            raise ValidationError(
                f"Duplicate binding '{binding_name}' in the submitted set."
            )
        material = _resolve_material_by_code(session, item.material_code)
        normalized[binding_name] = material.material_id

    existing_rows = session.scalars(
        select(MaterialAssignment).where(
            MaterialAssignment.finish_scheme_id == finish_scheme.finish_scheme_id
        )
    ).all()
    existing_by_binding = {row.binding_name: row for row in existing_rows}

    # Remove rows omitted from the submission.
    for binding_name, row in existing_by_binding.items():
        if binding_name not in normalized:
            session.delete(row)

    # Create or update.
    for binding_name, material_id in normalized.items():
        row = existing_by_binding.get(binding_name)
        if row is None:
            session.add(
                MaterialAssignment(
                    finish_scheme_id=finish_scheme.finish_scheme_id,
                    binding_name=binding_name,
                    material_id=material_id,
                )
            )
        else:
            row.material_id = material_id

    session.commit()
    return list_assignments(session, finish_scheme.finish_scheme_id)


def material_usages(session: Session, material_code: str) -> list[MaterialUsageOut]:
    """Return the assignments that reference a material, for delete-block messages."""
    rows = session.scalars(
        select(MaterialAssignment)
        .join(Material, MaterialAssignment.material_id == Material.material_id)
        .where(Material.code == material_code)
        .order_by(MaterialAssignment.binding_name)
    ).all()
    return [
        MaterialUsageOut(
            finish_scheme_code=row.finish_scheme.code,
            finish_scheme_display_name=row.finish_scheme.display_name,
            binding_name=row.binding_name,
        )
        for row in rows
    ]


# --------------------------------------------------------------------------- #
# Resolution
# --------------------------------------------------------------------------- #
def _assignment_map_for(
    session: Session, finish_scheme: FinishScheme
) -> dict[str, str]:
    """Return ``{binding_name: material_code}`` for one finish scheme."""
    rows = session.scalars(
        select(MaterialAssignment).where(
            MaterialAssignment.finish_scheme_id == finish_scheme.finish_scheme_id
        )
    ).all()
    return {row.binding_name: row.material.code for row in rows}


def resolve_assignment_mapping(
    session: Session, finish_scheme_code: str
) -> tuple[FinishScheme, list[str], dict[str, str], dict[str, Material]]:
    """Combine ``init`` with the selected finish scheme.

    Precedence is explicit: ``init < selected finish scheme`` (selected scheme
    overrides init for matching binding names). Returns the selected scheme, the
    active source codes, the flattened ``binding -> material_code`` mapping, and
    the ``material_code -> Material`` objects referenced by that mapping.
    """
    init_scheme = session.scalar(
        select(FinishScheme).where(FinishScheme.code == INIT_SCHEME_CODE)
    )
    if init_scheme is None:
        raise ValidationError(
            "The 'init' finish scheme is missing. Seed the database before "
            "resolving configurations."
        )
    if not init_scheme.is_active:
        raise ValidationError("The 'init' finish scheme is inactive.")

    selected_scheme = get_finish_scheme_by_code(session, finish_scheme_code)
    if not selected_scheme.is_active:
        raise ValidationError(
            f"Finish scheme '{finish_scheme_code}' is inactive and cannot be selected."
        )

    mapping: dict[str, str] = {}
    active_sources: list[str] = [INIT_SCHEME_CODE]
    # 1. init assignments form the base layer.
    mapping.update(_assignment_map_for(session, init_scheme))
    # 2. selected scheme overlays init (unless the selection *is* init).
    if selected_scheme.code != INIT_SCHEME_CODE:
        active_sources.append(selected_scheme.code)
        mapping.update(_assignment_map_for(session, selected_scheme))

    material_codes = set(mapping.values())
    materials: dict[str, Material] = {}
    if material_codes:
        rows = session.scalars(
            select(Material).where(Material.code.in_(material_codes))
        ).all()
        materials = {material.code: material for material in rows}

    return selected_scheme, active_sources, mapping, materials


def resolve_assignments(
    session: Session, finish_scheme_code: str
) -> ResolvedAssignmentsOut:
    """Flattened resolved assignments for a finish scheme (API response)."""
    selected_scheme, active_sources, mapping, materials = resolve_assignment_mapping(
        session, finish_scheme_code
    )
    return ResolvedAssignmentsOut(
        finish_scheme=FinishSchemeRef(
            code=selected_scheme.code, display_name=selected_scheme.display_name
        ),
        active_sources=active_sources,
        material_assignments=mapping,
        materials={
            code: MaterialOut.model_validate(material)
            for code, material in materials.items()
        },
    )
