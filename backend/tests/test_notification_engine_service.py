from __future__ import annotations

import pytest
from pydantic import ValidationError

from backend.engines.notification_engine.public import notification_service
from backend.engines.notification_engine.schemas import NotificationCreateInput, NotificationEventInput, NotificationFilters


@pytest.mark.asyncio
async def test_notification_service_creates_in_app_notification_without_db() -> None:
    notification = await notification_service.create_notification(
        None,
        user_id="user_notif_test",
        input_data=NotificationCreateInput(
            type="deployment_success",
            title="Deployment completed",
            message="Your deployment completed successfully.",
            severity="success",
            related_resource_type="deployment",
            related_resource_id="dep_test",
        ),
    )
    assert notification.id.startswith("notif_")
    assert notification.status == "unread"
    assert notification.channel == "in_app"
    assert notification.related_resource_id == "dep_test"


@pytest.mark.asyncio
async def test_notification_service_event_creation_is_secret_safe() -> None:
    notification = await notification_service.create_from_event(
        None,
        event=NotificationEventInput(
            event_name="deployment.failed",
            recipient_user_id="user_notif_test",
            type="deployment_failure",
            title="Deployment failed",
            message="Deployment failed. Open deployment logs for details.",
            severity="error",
            related_resource_type="deployment",
            related_resource_id="dep_failed",
            metadata={"failure_code": "DEPLOY_PIPELINE_CLOUDFLARE_FAILED"},
        ),
    )
    assert notification.metadata["source_event"] == "deployment.failed"
    assert "token" not in notification.model_dump_json().lower()


@pytest.mark.asyncio
async def test_notification_service_empty_list_and_count_without_db() -> None:
    page = await notification_service.list_notifications(None, user_id="user_notif_test", filters=NotificationFilters())
    count = await notification_service.get_unread_count(None, user_id="user_notif_test")
    assert page.items == []
    assert page.total_items == 0
    assert count.unread_count == 0


@pytest.mark.asyncio
async def test_notification_service_mark_read_contract_without_db() -> None:
    notification = await notification_service.mark_notification_read(
        None,
        user_id="user_notif_test",
        notification_id="notif_contract",
    )
    assert notification.status == "read"
    assert notification.id == "notif_contract"


def test_notification_metadata_rejects_secrets() -> None:
    with pytest.raises(ValidationError):
        NotificationCreateInput(
            type="system_notice",
            title="Invalid",
            message="Invalid metadata.",
            metadata={"access_token": "secret"},
        )
