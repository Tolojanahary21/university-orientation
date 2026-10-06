from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import select

from app.models.audit_event import AuditEvent
from app.models.enums import (
    Environment,
    ModelStatus,
    RecommendationSource,
    TrainingType,
    UserRole,
)
from app.models.field import Field
from app.models.model_version import ModelVersion
from app.models.recommendation import Recommendation
from app.models.student_profile import StudentProfile
from app.models.user import User
from app.schemas.field import FieldCreate, FieldUpdate
from app.schemas.profile import StudentProfileCreate, StudentProfileUpdate
from app.services import auth_service, field_service
from app.services.auth_service import (
    EmailNotVerifiedError,
    InvalidCredentialsError,
    authenticate_user,
)
from app.services.email_service import EmailDeliveryError
from app.services.field_service import create_catalog_field
from app.services.otp_service import (
    OTPBlockedError,
    OTPCooldownError,
    OTPExpiredError,
    OTPInvalidError,
    create_email_verification_otp,
    verify_email_otp,
)
from app.services.profile_service import (
    create_student_profile,
    update_student_profile,
)
from app.services.token_service import create_access_token


def make_user(db, email, role=UserRole.STUDENT, verified=True):
    user = User(
        email=email,
        password_hash="$argon2id$test-placeholder",
        role=role,
        is_active=True,
        email_verified_at=datetime.now(UTC) if verified else None,
    )
    db.add(user)
    db.flush()
    return user


def make_model(db, status=ModelStatus.CANDIDATE):
    model = ModelVersion(
        name="Integration model",
        version=f"t-{uuid4().hex[:20]}",
        status=status,
        training_type=TrainingType.INITIAL,
        environment=Environment.DEVELOPMENT,
    )
    db.add(model)
    db.flush()
    return model


def test_register_and_login_audit_and_public_role(client, db_session, monkeypatch):
    delivered = []
    monkeypatch.setattr(
        auth_service,
        "send_verification_email",
        lambda email, otp, first_name=None: delivered.append(otp),
    )
    response = client.post(
        "/auth/register",
        json={"email": "New.User@example.com", "password": "CorrectPass9"},
    )
    assert response.status_code == 201
    created = db_session.scalar(
        select(User).where(User.email == "new.user@example.com")
    )
    assert created.role == UserRole.STUDENT
    assert len(delivered) == 1
    assert db_session.scalar(
        select(AuditEvent).where(AuditEvent.event_type == "USER_CREATED")
    )

    with pytest.raises(EmailNotVerifiedError):
        authenticate_user(db_session, created.email, "CorrectPass9")

    otp = delivered[0]
    verify_email_otp(created, otp)
    db_session.commit()
    authenticated = authenticate_user(db_session, created.email, "CorrectPass9")
    assert authenticated.id == created.id
    assert db_session.scalar(
        select(AuditEvent).where(AuditEvent.event_type == "USER_LOGIN")
    )
    with pytest.raises(InvalidCredentialsError):
        authenticate_user(db_session, created.email, "WrongPass9")
    assert db_session.scalar(
        select(AuditEvent).where(AuditEvent.event_type == "LOGIN_FAILED")
    )


def test_registration_email_failure_is_audited_without_secrets(
    client, db_session, monkeypatch
):
    monkeypatch.setattr(
        auth_service,
        "send_verification_email",
        lambda *args, **kwargs: (_ for _ in ()).throw(EmailDeliveryError()),
    )
    response = client.post(
        "/auth/register",
        json={"email": "email.fail@example.com", "password": "CorrectPass9"},
    )
    assert response.status_code == 503
    event = db_session.scalar(
        select(AuditEvent).where(AuditEvent.event_type == "USER_CREATED")
    )
    assert event is not None
    events = db_session.scalars(select(AuditEvent)).all()
    assert any(item.event_type == "EMAIL_VERIFICATION_SEND_FAILED" for item in events)
    assert all("otp" not in str(item.new_values).lower() for item in events)


def test_otp_invalid_expired_blocked_and_cooldown(db_session):
    user = make_user(db_session, f"otp-{uuid4()}@example.com", verified=False)
    otp = create_email_verification_otp(user)
    with pytest.raises(OTPInvalidError):
        verify_email_otp(user, "000000" if otp != "000000" else "000001")
    with pytest.raises(OTPCooldownError):
        create_email_verification_otp(user)

    user.otp_expires_at = datetime.now(UTC) - timedelta(seconds=1)
    with pytest.raises(OTPExpiredError):
        verify_email_otp(user, otp)

    user.otp_hash = "invalid"
    user.otp_expires_at = datetime.now(UTC) + timedelta(minutes=1)
    from app.core.config import OTP_MAX_ATTEMPTS

    user.otp_attempts = OTP_MAX_ATTEMPTS - 1
    with pytest.raises(OTPBlockedError):
        verify_email_otp(user, "000000" if otp != "000000" else "000001")


def test_auth_me_and_admin_stats_role(client, db_session):
    student = make_user(db_session, f"http-student-{uuid4()}@example.com")
    response = client.get("/auth/me")
    assert response.status_code == 401
    token = create_access_token(student.id)
    assert (
        client.get("/auth/me", headers={"Authorization": f"Bearer {token}"}).status_code
        == 200
    )
    assert (
        client.get(
            "/admin/stats", headers={"Authorization": f"Bearer {token}"}
        ).status_code
        == 403
    )

    admin = make_user(
        db_session, f"http-admin-{uuid4()}@example.com", role=UserRole.ADMIN
    )
    admin_token = create_access_token(admin.id)
    stats = client.get(
        "/admin/stats", headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert stats.status_code == 200
    assert "users_count" in stats.json()


def test_field_crud_audit_and_atomicity(db_session, monkeypatch):
    admin = make_user(
        db_session, f"field-admin-{uuid4()}@example.com", role=UserRole.ADMIN
    )
    create_data = FieldCreate(code=f"C{uuid4().hex[:12]}", name="Mathematics")
    field = create_catalog_field(db_session, create_data, actor=admin)
    assert db_session.scalar(
        select(AuditEvent).where(
            AuditEvent.entity_id == field.id, AuditEvent.event_type == "FIELD_CREATED"
        )
    )

    field = field_service.update_catalog_field(
        db_session, field.id, FieldUpdate(name="Applied Mathematics"), actor=admin
    )
    assert field.name == "Applied Mathematics"
    assert db_session.scalar(
        select(AuditEvent).where(
            AuditEvent.entity_id == field.id, AuditEvent.event_type == "FIELD_UPDATED"
        )
    )
    field = field_service.deactivate_catalog_field(db_session, field.id)
    assert not field.is_active
    assert db_session.scalar(
        select(AuditEvent).where(
            AuditEvent.entity_id == field.id, AuditEvent.event_type == "FIELD_DISABLED"
        )
    )

    monkeypatch.setattr(
        field_service,
        "record_audit_event",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("audit failed")),
    )
    code = f"X{uuid4().hex[:12]}"
    with pytest.raises(RuntimeError):
        create_catalog_field(
            db_session, FieldCreate(code=code, name="Rollback"), actor=admin
        )
    db_session.rollback()
    assert db_session.scalar(select(Field).where(Field.code == code)) is None


def test_profile_version_and_audit(db_session):
    user = make_user(db_session, f"profile-{uuid4()}@example.com")
    profile = create_student_profile(
        db_session, user, StudentProfileCreate(bac_series="S", scores=None)
    )
    assert profile.scores is None
    unchanged = update_student_profile(
        db_session, user, StudentProfileUpdate(bac_series="S")
    )
    assert unchanged.profile_version == 1
    updated = update_student_profile(
        db_session, user, StudentProfileUpdate(bac_series="L", scores=None)
    )
    assert updated.profile_version == 2
    assert db_session.scalar(
        select(AuditEvent).where(
            AuditEvent.entity_id == profile.id,
            AuditEvent.event_type == "PROFILE_UPDATED",
        )
    )


def test_trace_id_on_audit_matches_response(client, db_session):
    user = make_user(db_session, f"trace-{uuid4()}@example.com")
    token = create_access_token(user.id)
    response = client.post(
        "/profiles",
        json={"bac_series": "S"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    event = db_session.scalar(
        select(AuditEvent).where(AuditEvent.event_type == "PROFILE_CREATED")
    )
    assert str(event.trace_id) == response.headers["X-Trace-Id"]


def test_admin_stats_aggregation(client, db_session):
    admin = make_user(
        db_session, f"stats-admin-{uuid4()}@example.com", role=UserRole.ADMIN
    )
    db_session.add(Field(code=f"S{uuid4().hex[:12]}", name="Active", is_active=True))
    model = make_model(db_session, ModelStatus.PRODUCTION)
    profile_user = make_user(db_session, f"stats-profile-{uuid4()}@example.com")
    profile = StudentProfile(user_id=profile_user.id, bac_series="S", scores=None)
    db_session.add(profile)
    db_session.flush()
    db_session.add(
        Recommendation(
            student_profile_id=profile.id,
            model_version_id=model.id,
            input_snapshot={},
            status="success",
            source=RecommendationSource.WEB,
            latency_ms=42,
        )
    )
    db_session.flush()
    token = create_access_token(admin.id)
    body = client.get(
        "/admin/stats", headers={"Authorization": f"Bearer {token}"}
    ).json()
    assert body["users_count"] >= 2
    assert body["active_fields_count"] >= 1
    assert body["recommendations"]["success"] >= 1
    assert body["recommendations"]["average_latency_ms"] is not None
    assert body["production_model"]["id"] == str(model.id)


def test_model_info_uses_production_version(client, db_session):
    model = make_model(db_session, ModelStatus.PRODUCTION)
    response = client.get("/model/info")
    assert response.status_code == 200
    assert response.json()["id"] == str(model.id)


def test_feedback_is_atomic_and_preserves_snapshot(db_session):
    from app.schemas.recommendation import RecommendationFeedbackRequest
    from app.services import recommendation_service
    from app.services.recommendation_service import add_recommendation_feedback

    user = make_user(db_session, f"feedback-{uuid4()}@example.com")
    profile = StudentProfile(user_id=user.id, bac_series="S", scores=None)
    model = make_model(db_session)
    db_session.add(profile)
    db_session.flush()
    snapshot = {"scores": {"math": 17}}
    recommendation = Recommendation(
        student_profile_id=profile.id,
        model_version_id=model.id,
        input_snapshot=snapshot,
        status="success",
        source=RecommendationSource.WEB,
    )
    db_session.add(recommendation)
    db_session.flush()
    recommendation_id = recommendation.id
    db_session.commit()
    recommendation = db_session.get(Recommendation, recommendation_id)
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(
        recommendation_service,
        "record_audit_event",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("audit failed")),
    )
    try:
        with pytest.raises(RuntimeError):
            add_recommendation_feedback(
                db_session,
                recommendation.id,
                user,
                RecommendationFeedbackRequest(rating=5),
            )
        db_session.rollback()
    finally:
        monkeypatch.undo()
    assert db_session.get(Recommendation, recommendation_id).input_snapshot == snapshot
    assert db_session.get(Recommendation, recommendation_id).feedback_rating is None


def test_model_status_transitions_and_audits(db_session):
    from app.schemas.model_version import ModelStatusUpdate
    from app.services.model_version_service import change_model_status

    admin = make_user(db_session, f"model-admin-{uuid4()}@example.com", UserRole.ADMIN)
    model = make_model(db_session)
    for status, event_type, timestamp in (
        (ModelStatus.VALIDATED, "MODEL_VALIDATED", "validated_at"),
        (ModelStatus.PRODUCTION, "MODEL_DEPLOYED", "deployed_at"),
        (ModelStatus.ARCHIVED, "MODEL_ARCHIVED", "archived_at"),
    ):
        model = change_model_status(
            db_session, model.id, ModelStatusUpdate(status=status), actor=admin
        )
        assert getattr(model, timestamp) is not None
        assert db_session.scalar(
            select(AuditEvent).where(
                AuditEvent.entity_id == model.id,
                AuditEvent.event_type == event_type,
            )
        )


def test_monitoring_admin_read_and_drift_audit(client, db_session):
    from app.schemas.monitoring_run import MonitoringRunCreate
    from app.services.monitoring_run_service import record_monitoring_run

    admin = make_user(
        db_session, f"monitor-admin-{uuid4()}@example.com", UserRole.ADMIN
    )
    student = make_user(db_session, f"monitor-student-{uuid4()}@example.com")
    model = make_model(db_session)
    now = datetime.now(UTC)
    payload = MonitoringRunCreate(
        model_version_id=model.id,
        environment=Environment.DEVELOPMENT,
        period_start=now - timedelta(hours=1),
        period_end=now,
        sample_count=3,
        data_drift_detected=True,
        prediction_drift_detected=False,
    )
    run = record_monitoring_run(db_session, payload)
    assert db_session.scalar(
        select(AuditEvent).where(
            AuditEvent.entity_id == run.id,
            AuditEvent.event_type == "DRIFT_DETECTED",
        )
    )
    admin_token = create_access_token(admin.id)
    student_token = create_access_token(student.id)
    assert (
        client.get(
            "/admin/monitoring", headers={"Authorization": f"Bearer {admin_token}"}
        ).status_code
        == 200
    )
    assert (
        client.get(
            "/admin/monitoring", headers={"Authorization": f"Bearer {student_token}"}
        ).status_code
        == 403
    )


def test_recommendation_feedback_http_and_input_snapshot(client, db_session):
    user = make_user(db_session, f"feedback-http-{uuid4()}@example.com")
    other = make_user(db_session, f"feedback-other-{uuid4()}@example.com")
    profile = StudentProfile(user_id=user.id, bac_series="S", scores=None)
    model = make_model(db_session)
    db_session.add(profile)
    db_session.flush()
    snapshot = {"bac_series": "S", "scores": {"math": 18}}
    recommendation = Recommendation(
        student_profile_id=profile.id,
        model_version_id=model.id,
        input_snapshot=snapshot,
        status="success",
        source=RecommendationSource.WEB,
    )
    db_session.add(recommendation)
    db_session.flush()
    own_token = create_access_token(user.id)
    other_token = create_access_token(other.id)
    path = f"/recommendations/{recommendation.id}/feedback"
    assert (
        client.post(
            path, json={"rating": 6}, headers={"Authorization": f"Bearer {own_token}"}
        ).status_code
        == 422
    )
    assert (
        client.post(
            path, json={"rating": 0}, headers={"Authorization": f"Bearer {own_token}"}
        ).status_code
        == 422
    )
    assert (
        client.post(
            path, json={"rating": 5}, headers={"Authorization": f"Bearer {other_token}"}
        ).status_code
        == 404
    )
    response = client.post(
        path, json={"rating": 5}, headers={"Authorization": f"Bearer {own_token}"}
    )
    assert response.status_code == 200
    assert db_session.get(Recommendation, recommendation.id).input_snapshot == snapshot
    assert (
        client.post(
            path, json={"rating": 4}, headers={"Authorization": f"Bearer {own_token}"}
        ).status_code
        == 409
    )
    assert db_session.scalar(
        select(AuditEvent).where(
            AuditEvent.entity_id == recommendation.id,
            AuditEvent.event_type == "RECOMMENDATION_FEEDBACK_ADDED",
        )
    )
