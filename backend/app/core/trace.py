from contextvars import ContextVar, Token
from uuid import UUID

_trace_id: ContextVar[UUID | None] = ContextVar(
    "trace_id",
    default=None,
)


def bind_trace_id(
    trace_id: UUID,
) -> Token:
    return _trace_id.set(trace_id)


def get_trace_id() -> UUID | None:
    return _trace_id.get()


def reset_trace_id(
    token: Token,
) -> None:
    _trace_id.reset(token)
