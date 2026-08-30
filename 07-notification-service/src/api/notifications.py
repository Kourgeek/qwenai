"""FastAPI router for the Notification Service HTTP API."""

import logging
from typing import Any

from fastapi import APIRouter, HTTPException

from src.services.email_service import EmailService
from src.services.sms_service import SmsService
from src.services.push_service import PushService
from src.grpc_server.notification_pb2_service import grpc_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/notifications", tags=["notifications"])

# Shared service instances
email_service = EmailService()
sms_service = SmsService()
push_service = PushService()


# ------------------------------------------------------------------
# Email endpoints
# ------------------------------------------------------------------
@router.post("/email")
async def send_email(to: str, subject: str, body: str) -> dict[str, Any]:
    """Send an email notification via the EmailService."""
    try:
        # Parse comma-separated recipients
        recipients = [r.strip() for r in to.split(",") if r.strip()]
        for recipient in recipients:
            await email_service._send_email(recipient, subject, body)
        return {
            "status": "sent",
            "recipients": recipients,
            "subject": subject,
        }
    except Exception as exc:
        logger.exception("Failed to send email: %s", exc)
        raise HTTPException(status_code=502, detail=str(exc))


# ------------------------------------------------------------------
# SMS endpoints
# ------------------------------------------------------------------
@router.post("/sms")
async def send_sms(phone: str, body: str) -> dict[str, Any]:
    """Send an SMS notification via the SmsService."""
    try:
        result = await sms_service.send_order_status_sms(phone, "N/A", body)
        return {
            "status": "sent",
            "to": phone,
            "message_id": f"sms-{id(phone)}",
        }
    except Exception as exc:
        logger.exception("Failed to send SMS: %s", exc)
        raise HTTPException(status_code=502, detail=str(exc))


# ------------------------------------------------------------------
# Push endpoints
# ------------------------------------------------------------------
@router.post("/push")
async def send_push(device_token: str, title: str, body: str) -> dict[str, Any]:
    """Send a push notification via the PushService."""
    try:
        result = await push_service.send_order_update(device_token, "N/A", title)
        return {
            "status": "sent",
            "device_token": device_token,
            "message_id": f"push-{id(device_token)}",
        }
    except Exception as exc:
        logger.exception("Failed to send push: %s", exc)
        raise HTTPException(status_code=502, detail=str(exc))


# ------------------------------------------------------------------
# History & stats endpoints
# ------------------------------------------------------------------
@router.get("/history")
async def get_notification_history(limit: int = 50) -> dict[str, Any]:
    """Retrieve the recent notification history (gRPC servicer state)."""
    servicer = grpc_manager.servicer
    if servicer is None:
        return {"notifications": [], "count": 0}
    history = servicer._history[-limit:]
    return {"notifications": history, "count": len(history)}


@router.get("/stats")
async def get_notification_stats() -> dict[str, Any]:
    """Retrieve notification statistics (gRPC servicer state)."""
    servicer = grpc_manager.servicer
    if servicer is None:
        return {
            "email_sent": 0,
            "sms_sent": 0,
            "push_sent": 0,
            "email_failed": 0,
            "sms_failed": 0,
            "push_failed": 0,
        }
    return {
        "email_sent": servicer._stats["email_sent"],
        "sms_sent": servicer._stats["sms_sent"],
        "push_sent": servicer._stats["push_sent"],
        "email_failed": servicer._stats["email_failed"],
        "sms_failed": servicer._stats["sms_failed"],
        "push_failed": servicer._stats["push_failed"],
    }
