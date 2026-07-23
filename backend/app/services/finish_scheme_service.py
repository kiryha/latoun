"""CRUD for finish schemes.

Finish schemes are the customer-visible finish choices (brass, steel, …) plus
the hidden internal ``init`` scheme. Deletion rules protect ``init`` and any
scheme referenced as an assignment state's default finish.
"""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..errors import ConflictError, NotFoundError
from ..models import AssignmentState, FinishScheme
from ..schemas import FinishSchemeCreate, FinishSchemeUpdate

INIT_SCHEME_CODE = "init"


def list_finish_schemes(
    session: Session,
    *,
    is_active: bool | None = None,
    is_customer_visible: bool | None = None,
) -> list[FinishScheme]:
    """Return finish schemes ordered by sort order then code, with optional filters."""
    statement = select(FinishScheme)
    if is_active is not None:
        statement = statement.where(FinishScheme.is_active.is_(is_active))
    if is_customer_visible is not None:
        statement = statement.where(
            FinishScheme.is_customer_visible.is_(is_customer_visible)
        )
    statement = statement.order_by(FinishScheme.sort_order, FinishScheme.code)
    return list(session.scalars(statement))


def get_finish_scheme(session: Session, finish_scheme_id: int) -> FinishScheme:
    finish_scheme = session.get(FinishScheme, finish_scheme_id)
    if finish_scheme is None:
        raise NotFoundError(f"Finish scheme not found: {finish_scheme_id}")
    return finish_scheme


def get_finish_scheme_by_code(session: Session, code: str) -> FinishScheme:
    finish_scheme = session.scalar(
        select(FinishScheme).where(FinishScheme.code == code)
    )
    if finish_scheme is None:
        raise NotFoundError(f"Finish scheme not found: {code}")
    return finish_scheme


def create_finish_scheme(session: Session, data: FinishSchemeCreate) -> FinishScheme:
    existing = session.scalar(
        select(FinishScheme).where(FinishScheme.code == data.code)
    )
    if existing is not None:
        raise ConflictError(f"Finish scheme code already exists: {data.code}")

    finish_scheme = FinishScheme(**data.model_dump())
    session.add(finish_scheme)
    session.commit()
    session.refresh(finish_scheme)
    return finish_scheme


def update_finish_scheme(
    session: Session, finish_scheme_id: int, data: FinishSchemeUpdate
) -> FinishScheme:
    finish_scheme = get_finish_scheme(session, finish_scheme_id)
    # ``code`` is a stable identifier and is intentionally not updatable here.
    payload = data.model_dump(exclude_unset=True)
    for key, value in payload.items():
        setattr(finish_scheme, key, value)
    session.commit()
    session.refresh(finish_scheme)
    return finish_scheme


def delete_finish_scheme(session: Session, finish_scheme_id: int) -> FinishScheme:
    finish_scheme = get_finish_scheme(session, finish_scheme_id)

    if finish_scheme.code == INIT_SCHEME_CODE:
        raise ConflictError(
            "The 'init' scheme holds static assignments shared by all "
            "assemblies and cannot be deleted."
        )

    reference_count = (
        session.scalar(
            select(func.count(AssignmentState.assignment_state_id)).where(
                AssignmentState.default_finish_scheme_id
                == finish_scheme.finish_scheme_id
            )
        )
        or 0
    )
    if reference_count > 0:
        raise ConflictError(
            f"Cannot delete finish scheme '{finish_scheme.code}': it is "
            f"referenced by {reference_count} assembly state(s) as the "
            "default finish."
        )

    # Assignment rows cascade-delete via the relationship / FK.
    session.delete(finish_scheme)
    session.commit()
    return finish_scheme
