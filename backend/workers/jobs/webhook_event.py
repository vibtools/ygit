from __future__ import annotations

JOB_TYPE = "webhook_event"


async def run(payload: dict[str, object]) -> None:
    """Webhook event job boundary.

    Webhook processing is contracted for future use. This skeleton validates
    dispatchability without implementing provider-specific business logic.
    """
    _ = payload
