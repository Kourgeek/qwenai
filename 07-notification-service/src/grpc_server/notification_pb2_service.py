"""gRPC service implementation for the Notification Service.

This module defines the protobuf-generated gRPC service skeleton
and binds it to an AsyncIO-compatible gRPC server.
"""

import logging
import asyncio
from typing import Any

import grpc
from grpc import ServicerContext

# ------------------------------------------------------------------
# Protobuf generated code (generated at build time via grpcio-tools)
# ------------------------------------------------------------------
# The .proto file is expected at:
#   src/grpc_server/notification.proto
# Generated files:
#   notification_pb2.py
#   notification_pb2_grpc.py
# ------------------------------------------------------------------

try:
    from src.grpc_server import notification_pb2, notification_pb2_grpc
except ImportError:
    # Allow the module to be imported even when the proto has not been
    # compiled yet (e.g. during development before `python -m grpc_tools`).
    notification_pb2 = None  # type: ignore
    notification_pb2_grpc = None  # type: ignore

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------
# Notification service stub — to be replaced by generated code
# ------------------------------------------------------------------
class NotificationServiceServicer:
    """gRPC service implementation for notification operations."""

    def __init__(self) -> None:
        self._history: list[dict[str, Any]] = []
        self._stats: dict[str, int] = {
            "email_sent": 0,
            "sms_sent": 0,
            "push_sent": 0,
            "email_failed": 0,
            "sms_failed": 0,
            "push_failed": 0,
        }

    # -- RPC implementations ------------------------------------------

    async def SendEmail(self, request, context: ServicerContext):
        """Handle SendEmail RPC."""
        try:
            logger.info(
                "SendEmail: to=%s subject=%s",
                request.to_email,
                request.subject,
            )
            self._stats["email_sent"] += 1
            self._history.append({
                "type": "email",
                "to": request.to_email,
                "subject": request.subject,
                "status": "sent",
            })
            return notification_pb2.SendEmailResponse(
                status="sent",
                message_id=f"email-{id(request)}",
            )
        except Exception as exc:
            self._stats["email_failed"] += 1
            logger.exception("SendEmail failed")
            context.set_details(str(exc))
            context.set_code(grpc.StatusCode.INTERNAL)
            return notification_pb2.SendEmailResponse(status="failed")

    async def SendSms(self, request, context: ServicerContext):
        """Handle SendSms RPC."""
        try:
            logger.info("SendSms: to=%s body=%s", request.phone, request.body)
            self._stats["sms_sent"] += 1
            self._history.append({
                "type": "sms",
                "to": request.phone,
                "body": request.body,
                "status": "sent",
            })
            return notification_pb2.SendSmsResponse(
                status="sent",
                message_id=f"sms-{id(request)}",
            )
        except Exception as exc:
            self._stats["sms_failed"] += 1
            logger.exception("SendSms failed")
            context.set_details(str(exc))
            context.set_code(grpc.StatusCode.INTERNAL)
            return notification_pb2.SendSmsResponse(status="failed")

    async def SendPush(self, request, context: ServicerContext):
        """Handle SendPush RPC."""
        try:
            logger.info(
                "SendPush: token=%s title=%s",
                request.device_token,
                request.title,
            )
            self._stats["push_sent"] += 1
            self._history.append({
                "type": "push",
                "device_token": request.device_token,
                "title": request.title,
                "status": "sent",
            })
            return notification_pb2.SendPushResponse(
                status="sent",
                message_id=f"push-{id(request)}",
            )
        except Exception as exc:
            self._stats["push_failed"] += 1
            logger.exception("SendPush failed")
            context.set_details(str(exc))
            context.set_code(grpc.StatusCode.INTERNAL)
            return notification_pb2.SendPushResponse(status="failed")

    async def GetNotificationHistory(
        self, request, context: ServicerContext
    ):
        """Handle GetNotificationHistory RPC."""
        limit = request.limit if request.HasField("limit") else 50
        history_slice = self._history[-limit:]
        return notification_pb2.NotificationHistoryResponse(
            notifications=[
                notification_pb2.NotificationEntry(
                    notification_type=n.get("type", ""),
                    to=n.get("to", ""),
                    subject=n.get("subject", ""),
                    body=n.get("body", ""),
                    status=n.get("status", ""),
                )
                for n in history_slice
            ],
        )

    async def GetNotificationStats(self, request, context: ServicerContext):
        """Handle GetNotificationStats RPC."""
        return notification_pb2.NotificationStatsResponse(
            email_sent=self._stats["email_sent"],
            sms_sent=self._stats["sms_sent"],
            push_sent=self._stats["push_sent"],
            email_failed=self._stats["email_failed"],
            sms_failed=self._stats["sms_failed"],
            push_failed=self._stats["push_failed"],
        )


# ------------------------------------------------------------------
# gRPC server management
# ------------------------------------------------------------------
class GrpcServerManager:
    """Manages the lifecycle of the gRPC server."""

    def __init__(self) -> None:
        self._server: grpc.aio.Server | None = None
        self._servicer: NotificationServiceServicer | None = None

    async def start(self, port: int) -> None:
        """Start the gRPC server on the given port."""
        self._servicer = NotificationServiceServicer()

        if notification_pb2_grpc is None:
            logger.warning(
                "notification_pb2_grpc not available — "
                "run: python -m grpc_tools.protoc -I. "
                "--python_out=. --grpc_python_out=. notification.proto"
            )
            self._server = grpc.aio.server()
            await self._server.start()
            logger.info("gRPC server started (stub mode) on port %d", port)
            return

        self._server = grpc.aio.server()
        notification_pb2_grpc.add_NotificationServiceServicer_to_server(
            self._servicer, self._server
        )
        self._server.add_insecure_port(f"[::]:{port}")
        await self._server.start()
        logger.info("gRPC server listening on port %d", port)

    async def stop(self, grace: int = 5) -> None:
        """Gracefully stop the gRPC server."""
        if self._server:
            await self._server.stop(grace)
            logger.info("gRPC server stopped")

    @property
    def server(self) -> grpc.aio.Server | None:
        return self._server

    @property
    def servicer(self) -> NotificationServiceServicer | None:
        return self._servicer


# Module-level manager instance
grpc_manager = GrpcServerManager()
