from uuid import UUID, uuid4

from fastapi import FastAPI, Request

from app.api.routes.admin_audit_events import (
    router as admin_audit_events_router,
)
from app.api.routes.admin_models import (
    router as admin_models_router,
)
from app.api.routes.admin_monitoring import (
    router as admin_monitoring_router,
)
from app.api.routes.admin_stats import router as admin_stats_router
from app.api.routes.admin_users import router as admin_users_router
from app.api.routes.auth import router as auth_router
from app.api.routes.fields import router as fields_router
from app.api.routes.model_info import router as model_info_router
from app.api.routes.profiles import router as profiles_router
from app.api.routes.recommendations import (
    router as recommendations_router,
)
from app.core.trace import (
    bind_trace_id,
    reset_trace_id,
)

app = FastAPI(
    title="Orientation API",
    version="1.0.0",
)


@app.middleware("http")
async def trace_id_middleware(
    request: Request,
    call_next,
):
    incoming_trace_id = request.headers.get("X-Trace-Id")

    try:
        trace_id = UUID(incoming_trace_id) if incoming_trace_id else uuid4()
    except ValueError:
        trace_id = uuid4()

    token = bind_trace_id(trace_id)

    try:
        response = await call_next(request)

        response.headers["X-Trace-Id"] = str(trace_id)

        return response

    finally:
        reset_trace_id(token)


# routes
app.include_router(auth_router)
app.include_router(profiles_router)
app.include_router(fields_router)
app.include_router(admin_users_router)
app.include_router(admin_models_router)
app.include_router(recommendations_router)
app.include_router(admin_monitoring_router)
app.include_router(admin_audit_events_router)
app.include_router(admin_stats_router)
app.include_router(model_info_router)


@app.get("/health")
def health():
    return {"status": "ok"}
