from sqlalchemy.orm import Session

from app.core.audit_events import AuditEventType
from app.core.audit_sanitizer import sanitize_audit_value
from app.models.audit_event import AuditEvent
from app.services.audit_event_service import record_audit_event


def test_sanitizer_removes_secrets_recursively():
    sanitized = sanitize_audit_value(
        {
            "email": "student@example.test",
            "password": "clear",
            "nested": {"otp_hash": "hash", "name": "Ada"},
            "items": [{"access_token": "jwt", "ok": True}],
            "authorization": "Bearer eyJabc.eyJdef.sig",
            "note": "token=eyJabc.eyJdef.sig",
        }
    )
    assert sanitized == {
        "email": "student@example.test",
        "nested": {"name": "Ada"},
        "items": [{"ok": True}],
        "authorization": "[REDACTED]",
        "note": "token=[REDACTED]",
    }


def test_record_audit_event_flushes_without_commit(monkeypatch):
    db = Session()
    calls = []
    monkeypatch.setattr(db, "add", lambda event: calls.append(("add", event)))
    monkeypatch.setattr(db, "flush", lambda: calls.append(("flush", None)))
    monkeypatch.setattr(db, "commit", lambda: calls.append(("commit", None)))

    event = record_audit_event(
        db,
        event_type=AuditEventType.FIELD_CREATED,
        new_values={"password": "secret", "name": "Math"},
    )

    assert isinstance(event, AuditEvent)
    assert calls[0][0] == "add"
    assert calls[1][0] == "flush"
    assert all(kind != "commit" for kind, _ in calls)
    assert event.new_values == {"name": "Math"}


def test_audit_event_metadata_keeps_database_column_name():
    assert AuditEvent.__table__.c.metadata.name == "metadata"
    assert "event_metadata" not in AuditEvent.__table__.c
