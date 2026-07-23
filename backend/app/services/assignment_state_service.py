"""CRUD for admin Assignment States and their per-slot modules."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from ..errors import NotFoundError, ValidationError
from ..models import AssignmentState, AssignmentStateModule, FinishScheme, ModuleType
from ..schemas import (
    AssignmentStateCreate,
    AssignmentStateModuleIn,
    AssignmentStateModuleOut,
    AssignmentStateOut,
    AssignmentStateUpdate,
)
from .render_state_service import SUPPORTED_GANG_COUNTS, resolve_render_state


def _next_assignment_state_code(session: Session) -> str:
    count = (
        session.scalar(select(func.count(AssignmentState.assignment_state_id))) or 0
    )
    return f"LAT-ASG-{count + 1:06d}"


def _module_type_by_id(session: Session, module_type_id: int) -> ModuleType:
    module_type = session.get(ModuleType, module_type_id)
    if module_type is None:
        raise ValidationError(f"Module type not found: {module_type_id}")
    if not module_type.is_active:
        raise ValidationError(
            f"Module type '{module_type.code}' is inactive and cannot be used."
        )
    return module_type


def _validate_modules(
    session: Session, gang_count: int, modules: list[AssignmentStateModuleIn]
) -> list[tuple[int, ModuleType]]:
    if gang_count not in SUPPORTED_GANG_COUNTS:
        raise ValidationError(
            f"Unsupported gang_count: {gang_count}. "
            f"Supported: {list(SUPPORTED_GANG_COUNTS)}"
        )
    if len(modules) != gang_count:
        raise ValidationError(
            f"Expected exactly {gang_count} module row(s) for gang_count="
            f"{gang_count}; got {len(modules)}."
        )

    slot_numbers = [row.slot_number for row in modules]
    if len(slot_numbers) != len(set(slot_numbers)):
        raise ValidationError("Duplicate slot numbers are not allowed.")

    expected = set(range(1, gang_count + 1))
    actual = set(slot_numbers)
    if actual != expected:
        raise ValidationError(
            f"Modules must cover slots {sorted(expected)} exactly; "
            f"got {sorted(actual)}."
        )

    resolved: list[tuple[int, ModuleType]] = []
    for row in sorted(modules, key=lambda item: item.slot_number):
        module_type = _module_type_by_id(session, row.module_type_id)
        resolved.append((row.slot_number, module_type))
    return resolved


def _validate_default_finish(
    session: Session, finish_scheme_id: int | None
) -> FinishScheme | None:
    if finish_scheme_id is None:
        return None
    finish_scheme = session.get(FinishScheme, finish_scheme_id)
    if finish_scheme is None:
        raise ValidationError(f"Finish scheme not found: {finish_scheme_id}")
    return finish_scheme


def _to_out(state: AssignmentState) -> AssignmentStateOut:
    return AssignmentStateOut(
        assignment_state_id=state.assignment_state_id,
        assignment_state_code=state.assignment_state_code,
        display_name=state.display_name,
        gang_count=state.gang_count,
        default_finish_scheme_id=state.default_finish_scheme_id,
        default_finish_scheme_code=(
            state.default_finish_scheme.code if state.default_finish_scheme else None
        ),
        notes=state.notes,
        is_active=state.is_active,
        sort_order=state.sort_order,
        modules=[
            AssignmentStateModuleOut(
                assignment_state_module_id=row.assignment_state_module_id,
                slot_number=row.slot_number,
                module_type_id=row.module_type_id,
                module_type_code=row.module_type.code,
                module_type_display_name=row.module_type.display_name,
            )
            for row in sorted(state.modules, key=lambda item: item.slot_number)
        ],
        created_at=state.created_at,
        updated_at=state.updated_at,
    )


def _load_state(session: Session, assignment_state_id: int) -> AssignmentState:
    state = session.scalar(
        select(AssignmentState)
        .options(
            selectinload(AssignmentState.modules).selectinload(
                AssignmentStateModule.module_type
            ),
            selectinload(AssignmentState.default_finish_scheme),
        )
        .where(AssignmentState.assignment_state_id == assignment_state_id)
    )
    if state is None:
        raise NotFoundError(f"Assignment state not found: {assignment_state_id}")
    return state


def list_assignment_states(
    session: Session, *, is_active: bool | None = None
) -> list[AssignmentStateOut]:
    statement = (
        select(AssignmentState)
        .options(
            selectinload(AssignmentState.modules).selectinload(
                AssignmentStateModule.module_type
            ),
            selectinload(AssignmentState.default_finish_scheme),
        )
        .order_by(AssignmentState.sort_order, AssignmentState.assignment_state_code)
    )
    if is_active is not None:
        statement = statement.where(AssignmentState.is_active.is_(is_active))
    return [_to_out(state) for state in session.scalars(statement)]


def get_assignment_state(
    session: Session, assignment_state_id: int
) -> AssignmentStateOut:
    return _to_out(_load_state(session, assignment_state_id))


def create_assignment_state(
    session: Session, data: AssignmentStateCreate
) -> AssignmentStateOut:
    modules = _validate_modules(session, data.gang_count, data.modules)
    _validate_default_finish(session, data.default_finish_scheme_id)

    state = AssignmentState(
        assignment_state_code=_next_assignment_state_code(session),
        display_name=data.display_name,
        gang_count=data.gang_count,
        default_finish_scheme_id=data.default_finish_scheme_id,
        notes=data.notes,
        is_active=data.is_active,
        sort_order=data.sort_order,
    )
    session.add(state)
    session.flush()

    for slot_number, module_type in modules:
        session.add(
            AssignmentStateModule(
                assignment_state_id=state.assignment_state_id,
                slot_number=slot_number,
                module_type_id=module_type.module_type_id,
            )
        )
    session.commit()
    return _to_out(_load_state(session, state.assignment_state_id))


def update_assignment_state(
    session: Session, assignment_state_id: int, data: AssignmentStateUpdate
) -> AssignmentStateOut:
    state = _load_state(session, assignment_state_id)
    payload = data.model_dump(exclude_unset=True)
    modules_payload = payload.pop("modules", None)

    if "default_finish_scheme_id" in payload:
        _validate_default_finish(session, payload["default_finish_scheme_id"])

    for key, value in payload.items():
        setattr(state, key, value)

    gang_count = state.gang_count
    if modules_payload is not None:
        module_inputs = [AssignmentStateModuleIn(**row) for row in modules_payload]
        modules = _validate_modules(session, gang_count, module_inputs)
        state.modules.clear()
        session.flush()
        for slot_number, module_type in modules:
            session.add(
                AssignmentStateModule(
                    assignment_state_id=state.assignment_state_id,
                    slot_number=slot_number,
                    module_type_id=module_type.module_type_id,
                )
            )
    elif "gang_count" in payload:
        # Gang changed without modules — require modules in the same request.
        raise ValidationError(
            "When changing gang_count, submit a complete modules list covering "
            "every slot."
        )

    session.commit()
    return _to_out(_load_state(session, assignment_state_id))


def delete_assignment_state(
    session: Session, assignment_state_id: int
) -> AssignmentStateOut:
    state = _load_state(session, assignment_state_id)
    result = _to_out(state)
    session.delete(state)
    session.commit()
    return result


def resolve_assignment_state_render(
    session: Session,
    assignment_state_id: int,
    *,
    finish_scheme_code: str | None = None,
):
    """Resolve viewport geometry from an assignment state + finish scheme."""
    state = _load_state(session, assignment_state_id)
    if not state.is_active:
        raise ValidationError(
            f"Assignment state '{state.assignment_state_code}' is inactive."
        )

    finish_code = finish_scheme_code
    if not finish_code:
        if state.default_finish_scheme is None:
            raise ValidationError(
                f"Assignment state '{state.assignment_state_code}' has no default "
                "finish scheme; provide finish_scheme explicitly."
            )
        finish_code = state.default_finish_scheme.code

    modules = [
        (row.slot_number, row.module_type.code)
        for row in sorted(state.modules, key=lambda item: item.slot_number)
    ]
    return resolve_render_state(
        session,
        gang_count=state.gang_count,
        modules=modules,
        finish_scheme_code=finish_code,
        assignment_state_code=state.assignment_state_code,
        assignment_state_display_name=state.display_name,
    )
