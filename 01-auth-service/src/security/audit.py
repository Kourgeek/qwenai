"""Security audit logging for HyperScale Marketplace.

Provides structured audit logging for:
- Login attempts (success / failure)
- Password changes
- Permission / role changes
- Data access patterns
- Configuration changes

All audit events are written to the application logger with a dedicated
``audit`` logger namespace and include correlation/request IDs for
tracing.
"""

from __future__ import annotations

import enum
import json
import logging
import time
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

logger = logging.getLogger("hypersec.audit")


# ------------------------------------------------------------------
# Event types
# ------------------------------------------------------------------

class AuditEventType(str, enum.Enum):
    """Types of security-relevant events."""

    # Authentication
    LOGIN_SUCCESS = "LOGIN_SUCCESS"
    LOGIN_FAILURE = "LOGIN_FAILURE"
    LOGIN_LOCKED = "LOGIN_LOCKED"
    LOGOUT = "LOGOUT"

    # Password
    PASSWORD_CHANGE_SUCCESS = "PASSWORD_CHANGE_SUCCESS"
    PASSWORD_CHANGE_FAILED = "PASSWORD_CHANGE_FAILED"
    PASSWORD_RESET_REQUEST = "PASSWORD_RESET_REQUEST"
    PASSWORD_RESET_COMPLETE = "PASSWORD_RESET_COMPLETE"

    # Authorization
    PERMISSION_GRANT = "PERMISSION_GRANT"
    PERMISSION_REVOKE = "PERMISSION_REVOKE"
    ROLE_ASSIGN = "ROLE_ASSIGN"
    ROLE_REMOVE = "ROLE_REMOVE"

    # Data access
    DATA_READ = "DATA_READ"
    DATA_WRITE = "DATA_WRITE"
    DATA_DELETE = "DATA_DELETE"
    DATA_EXPORT = "DATA_EXPORT"

    # Configuration
    CONFIG_CHANGE = "CONFIG_CHANGE"
    CONFIG_CREATE = "CONFIG_CREATE"
    CONFIG_DELETE = "CONFIG_DELETE"

    # Token
    TOKEN_ISSUED = "TOKEN_ISSUED"
    TOKEN_REVOKED = "TOKEN_REVOKED"
    TOKEN_ROTATED = "TOKEN_ROTATED"

    # Admin
    ADMIN_ACTION = "ADMIN_ACTION"


# ------------------------------------------------------------------
# Data classes
# ------------------------------------------------------------------

@dataclass
class AuditEvent:
    """Structured audit event."""

    event_id: str = field(default_factory=lambda: uuid.uuid4().hex[:16])
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    event_type: str = ""
    severity: str = "INFO"          # INFO, WARNING, ERROR, CRITICAL
    actor_id: str = ""               # user_id or service identity
    actor_ip: str = ""
    actor_agent: str = ""
    target_id: str = ""              # resource being acted upon
    target_type: str = ""            # user, config, permission, etc.
    resource: str = ""               # human-readable resource description
    action: str = ""                 # e.g. LOGIN, CHANGE, READ
    result: str = ""                 # SUCCESS, FAILURE
    details: dict[str, Any] = field(default_factory=dict)
    correlation_id: str = ""
    request_id: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a JSON-friendly dict."""
        return asdict(self)

    def to_json(self) -> str:
        """Serialize to a JSON string."""
        return json.dumps(self.to_dict(), default=str)


# ------------------------------------------------------------------
# Audit logger
# ------------------------------------------------------------------

class AuditLogger:
    """Central audit logging facility.

    Usage
    -----
    >>> audit = AuditLogger()
    >>> audit.login_failure(actor_id="user-42", ip="10.0.0.1", reason="invalid_password")
    >>> audit.login_success(actor_id="user-42", ip="10.0.0.1")
    >>> audit.permission_grant(actor_id="admin-1", target_id="user-42", permission="admin")
    """

    def __init__(
        self,
        logger: Optional[logging.Logger] = None,
        enabled: bool = True,
    ) -> None:
        self.logger = logger or logger  # type: ignore[arg-type]
        self.enabled = enabled

    # -- helpers -------------------------------------------------------

    def _emit(
        self,
        event_type: AuditEventType,
        *,
        severity: str = "INFO",
        actor_id: str = "",
        actor_ip: str = "",
        actor_agent: str = "",
        target_id: str = "",
        target_type: str = "",
        resource: str = "",
        action: str = "",
        result: str = "SUCCESS",
        details: Optional[dict[str, Any]] = None,
        correlation_id: str = "",
        request_id: str = "",
        metadata: Optional[dict[str, Any]] = None,
    ) -> AuditEvent:
        """Create and log an audit event."""
        if not self.enabled:
            return AuditEvent()

        event = AuditEvent(
            event_type=event_type.value,
            severity=severity,
            actor_id=actor_id,
            actor_ip=actor_ip,
            actor_agent=actor_agent,
            target_id=target_id,
            target_type=target_type,
            resource=resource,
            action=action,
            result=result,
            details=details or {},
            correlation_id=correlation_id,
            request_id=request_id,
            metadata=metadata or {},
        )

        log_msg = (
            f"AUDIT event_id={event.event_id} type={event.event_type} "
            f"severity={event.severity} actor={actor_id} "
            f"target={target_id} result={result}"
        )

        if severity in ("WARNING", "ERROR"):
            self.logger.warning(log_msg, extra={"audit": event.to_dict()})
        elif severity == "CRITICAL":
            self.logger.critical(log_msg, extra={"audit": event.to_dict()})
        else:
            self.logger.info(log_msg, extra={"audit": event.to_dict()})

        return event

    # -- authentication events ----------------------------------------

    def login_success(
        self,
        *,
        actor_id: str,
        ip: str = "",
        agent: str = "",
        correlation_id: str = "",
        request_id: str = "",
    ) -> AuditEvent:
        return self._emit(
            AuditEventType.LOGIN_SUCCESS,
            severity="INFO",
            actor_id=actor_id,
            actor_ip=ip,
            actor_agent=agent,
            action="LOGIN",
            result="SUCCESS",
            correlation_id=correlation_id,
            request_id=request_id,
        )

    def login_failure(
        self,
        *,
        actor_id: str,
        ip: str = "",
        agent: str = "",
        reason: str = "",
        correlation_id: str = "",
        request_id: str = "",
    ) -> AuditEvent:
        return self._emit(
            AuditEventType.LOGIN_FAILURE,
            severity="WARNING",
            actor_id=actor_id,
            actor_ip=ip,
            actor_agent=agent,
            action="LOGIN",
            result="FAILURE",
            details={"reason": reason},
            correlation_id=correlation_id,
            request_id=request_id,
        )

    def login_locked(
        self,
        *,
        actor_id: str,
        ip: str = "",
        attempts: int = 0,
        correlation_id: str = "",
        request_id: str = "",
    ) -> AuditEvent:
        return self._emit(
            AuditEventType.LOGIN_LOCKED,
            severity="ERROR",
            actor_id=actor_id,
            actor_ip=ip,
            action="LOGIN",
            result="LOCKED",
            details={"attempts": attempts},
            correlation_id=correlation_id,
            request_id=request_id,
        )

    def logout(
        self,
        *,
        actor_id: str,
        ip: str = "",
        correlation_id: str = "",
        request_id: str = "",
    ) -> AuditEvent:
        return self._emit(
            AuditEventType.LOGOUT,
            severity="INFO",
            actor_id=actor_id,
            actor_ip=ip,
            action="LOGOUT",
            result="SUCCESS",
            correlation_id=correlation_id,
            request_id=request_id,
        )

    # -- password events ----------------------------------------------

    def password_change_success(
        self,
        *,
        actor_id: str,
        ip: str = "",
        correlation_id: str = "",
        request_id: str = "",
    ) -> AuditEvent:
        return self._emit(
            AuditEventType.PASSWORD_CHANGE_SUCCESS,
            severity="INFO",
            actor_id=actor_id,
            actor_ip=ip,
            action="PASSWORD_CHANGE",
            result="SUCCESS",
            correlation_id=correlation_id,
            request_id=request_id,
        )

    def password_change_failed(
        self,
        *,
        actor_id: str,
        ip: str = "",
        reason: str = "",
        correlation_id: str = "",
        request_id: str = "",
    ) -> AuditEvent:
        return self._emit(
            AuditEventType.PASSWORD_CHANGE_FAILED,
            severity="WARNING",
            actor_id=actor_id,
            actor_ip=ip,
            action="PASSWORD_CHANGE",
            result="FAILURE",
            details={"reason": reason},
            correlation_id=correlation_id,
            request_id=request_id,
        )

    def password_reset_request(
        self,
        *,
        actor_id: str,
        ip: str = "",
        target_email: str = "",
        correlation_id: str = "",
        request_id: str = "",
    ) -> AuditEvent:
        return self._emit(
            AuditEventType.PASSWORD_RESET_REQUEST,
            severity="INFO",
            actor_id=actor_id,
            actor_ip=ip,
            target_id=target_email,
            action="PASSWORD_RESET",
            result="REQUESTED",
            correlation_id=correlation_id,
            request_id=request_id,
        )

    def password_reset_complete(
        self,
        *,
        actor_id: str,
        ip: str = "",
        target_email: str = "",
        correlation_id: str = "",
        request_id: str = "",
    ) -> AuditEvent:
        return self._emit(
            AuditEventType.PASSWORD_RESET_COMPLETE,
            severity="INFO",
            actor_id=actor_id,
            actor_ip=ip,
            target_id=target_email,
            action="PASSWORD_RESET",
            result="COMPLETE",
            correlation_id=correlation_id,
            request_id=request_id,
        )

    # -- permission / role events -------------------------------------

    def permission_grant(
        self,
        *,
        actor_id: str,
        target_id: str,
        permission: str = "",
        ip: str = "",
        correlation_id: str = "",
        request_id: str = "",
    ) -> AuditEvent:
        return self._emit(
            AuditEventType.PERMISSION_GRANT,
            severity="INFO",
            actor_id=actor_id,
            target_id=target_id,
            target_type="permission",
            resource=permission,
            action="GRANT",
            result="SUCCESS",
            details={"permission": permission},
            actor_ip=ip,
            correlation_id=correlation_id,
            request_id=request_id,
        )

    def permission_revoke(
        self,
        *,
        actor_id: str,
        target_id: str,
        permission: str = "",
        ip: str = "",
        correlation_id: str = "",
        request_id: str = "",
    ) -> AuditEvent:
        return self._emit(
            AuditEventType.PERMISSION_REVOKE,
            severity="WARNING",
            actor_id=actor_id,
            target_id=target_id,
            target_type="permission",
            resource=permission,
            action="REVOKE",
            result="SUCCESS",
            details={"permission": permission},
            actor_ip=ip,
            correlation_id=correlation_id,
            request_id=request_id,
        )

    def role_assign(
        self,
        *,
        actor_id: str,
        target_id: str,
        role: str = "",
        ip: str = "",
        correlation_id: str = "",
        request_id: str = "",
    ) -> AuditEvent:
        return self._emit(
            AuditEventType.ROLE_ASSIGN,
            severity="INFO",
            actor_id=actor_id,
            target_id=target_id,
            target_type="role",
            resource=role,
            action="ASSIGN",
            result="SUCCESS",
            details={"role": role},
            actor_ip=ip,
            correlation_id=correlation_id,
            request_id=request_id,
        )

    def role_remove(
        self,
        *,
        actor_id: str,
        target_id: str,
        role: str = "",
        ip: str = "",
        correlation_id: str = "",
        request_id: str = "",
    ) -> AuditEvent:
        return self._emit(
            AuditEventType.ROLE_REMOVE,
            severity="WARNING",
            actor_id=actor_id,
            target_id=target_id,
            target_type="role",
            resource=role,
            action="REMOVE",
            result="SUCCESS",
            details={"role": role},
            actor_ip=ip,
            correlation_id=correlation_id,
            request_id=request_id,
        )

    # -- data access events -------------------------------------------

    def data_read(
        self,
        *,
        actor_id: str,
        target_id: str,
        resource: str = "",
        ip: str = "",
        correlation_id: str = "",
        request_id: str = "",
        details: Optional[dict[str, Any]] = None,
    ) -> AuditEvent:
        return self._emit(
            AuditEventType.DATA_READ,
            severity="INFO",
            actor_id=actor_id,
            target_id=target_id,
            target_type="data",
            resource=resource,
            action="READ",
            result="SUCCESS",
            details=details or {},
            actor_ip=ip,
            correlation_id=correlation_id,
            request_id=request_id,
        )

    def data_write(
        self,
        *,
        actor_id: str,
        target_id: str,
        resource: str = "",
        ip: str = "",
        correlation_id: str = "",
        request_id: str = "",
        details: Optional[dict[str, Any]] = None,
    ) -> AuditEvent:
        return self._emit(
            AuditEventType.DATA_WRITE,
            severity="INFO",
            actor_id=actor_id,
            target_id=target_id,
            target_type="data",
            resource=resource,
            action="WRITE",
            result="SUCCESS",
            details=details or {},
            actor_ip=ip,
            correlation_id=correlation_id,
            request_id=request_id,
        )

    def data_delete(
        self,
        *,
        actor_id: str,
        target_id: str,
        resource: str = "",
        ip: str = "",
        correlation_id: str = "",
        request_id: str = "",
        details: Optional[dict[str, Any]] = None,
    ) -> AuditEvent:
        return self._emit(
            AuditEventType.DATA_DELETE,
            severity="WARNING",
            actor_id=actor_id,
            target_id=target_id,
            target_type="data",
            resource=resource,
            action="DELETE",
            result="SUCCESS",
            details=details or {},
            actor_ip=ip,
            correlation_id=correlation_id,
            request_id=request_id,
        )

    def data_export(
        self,
        *,
        actor_id: str,
        target_id: str,
        resource: str = "",
        ip: str = "",
        correlation_id: str = "",
        request_id: str = "",
        details: Optional[dict[str, Any]] = None,
    ) -> AuditEvent:
        return self._emit(
            AuditEventType.DATA_EXPORT,
            severity="INFO",
            actor_id=actor_id,
            target_id=target_id,
            target_type="data",
            resource=resource,
            action="EXPORT",
            result="SUCCESS",
            details=details or {},
            actor_ip=ip,
            correlation_id=correlation_id,
            request_id=request_id,
        )

    # -- configuration events -----------------------------------------

    def config_change(
        self,
        *,
        actor_id: str,
        target_id: str,
        resource: str = "",
        ip: str = "",
        old_value: Any = None,
        new_value: Any = None,
        correlation_id: str = "",
        request_id: str = "",
    ) -> AuditEvent:
        return self._emit(
            AuditEventType.CONFIG_CHANGE,
            severity="INFO",
            actor_id=actor_id,
            target_id=target_id,
            target_type="config",
            resource=resource,
            action="CHANGE",
            result="SUCCESS",
            details={
                "old_value": str(old_value) if old_value is not None else None,
                "new_value": str(new_value) if new_value is not None else None,
            },
            actor_ip=ip,
            correlation_id=correlation_id,
            request_id=request_id,
        )

    def config_create(
        self,
        *,
        actor_id: str,
        target_id: str,
        resource: str = "",
        ip: str = "",
        correlation_id: str = "",
        request_id: str = "",
    ) -> AuditEvent:
        return self._emit(
            AuditEventType.CONFIG_CREATE,
            severity="INFO",
            actor_id=actor_id,
            target_id=target_id,
            target_type="config",
            resource=resource,
            action="CREATE",
            result="SUCCESS",
            actor_ip=ip,
            correlation_id=correlation_id,
            request_id=request_id,
        )

    def config_delete(
        self,
        *,
        actor_id: str,
        target_id: str,
        resource: str = "",
        ip: str = "",
        correlation_id: str = "",
        request_id: str = "",
    ) -> AuditEvent:
        return self._emit(
            AuditEventType.CONFIG_DELETE,
            severity="WARNING",
            actor_id=actor_id,
            target_id=target_id,
            target_type="config",
            resource=resource,
            action="DELETE",
            result="SUCCESS",
            actor_ip=ip,
            correlation_id=correlation_id,
            request_id=request_id,
        )

    # -- token events -------------------------------------------------

    def token_issued(
        self,
        *,
        actor_id: str,
        target_id: str,
        token_type: str = "access",
        ip: str = "",
        correlation_id: str = "",
        request_id: str = "",
    ) -> AuditEvent:
        return self._emit(
            AuditEventType.TOKEN_ISSUED,
            severity="INFO",
            actor_id=actor_id,
            target_id=target_id,
            target_type="token",
            action="ISSUE",
            result="SUCCESS",
            details={"token_type": token_type},
            actor_ip=ip,
            correlation_id=correlation_id,
            request_id=request_id,
        )

    def token_revoked(
        self,
        *,
        actor_id: str,
        target_id: str,
        token_type: str = "refresh",
        ip: str = "",
        correlation_id: str = "",
        request_id: str = "",
    ) -> AuditEvent:
        return self._emit(
            AuditEventType.TOKEN_REVOKED,
            severity="INFO",
            actor_id=actor_id,
            target_id=target_id,
            target_type="token",
            action="REVOKE",
            result="SUCCESS",
            details={"token_type": token_type},
            actor_ip=ip,
            correlation_id=correlation_id,
            request_id=request_id,
        )

    def token_rotated(
        self,
        *,
        actor_id: str,
        target_id: str,
        ip: str = "",
        correlation_id: str = "",
        request_id: str = "",
    ) -> AuditEvent:
        return self._emit(
            AuditEventType.TOKEN_ROTATED,
            severity="INFO",
            actor_id=actor_id,
            target_id=target_id,
            target_type="token",
            action="ROTATE",
            result="SUCCESS",
            actor_ip=ip,
            correlation_id=correlation_id,
            request_id=request_id,
        )

    # -- admin events -------------------------------------------------

    def admin_action(
        self,
        *,
        actor_id: str,
        target_id: str = "",
        resource: str = "",
        action: str = "",
        ip: str = "",
        details: Optional[dict[str, Any]] = None,
        correlation_id: str = "",
        request_id: str = "",
    ) -> AuditEvent:
        return self._emit(
            AuditEventType.ADMIN_ACTION,
            severity="INFO",
            actor_id=actor_id,
            target_id=target_id,
            resource=resource,
            action=action,
            result="SUCCESS",
            details=details or {},
            actor_ip=ip,
            correlation_id=correlation_id,
            request_id=request_id,
        )


# ------------------------------------------------------------------
# Module-level singleton
# ------------------------------------------------------------------

_default_audit: Optional[AuditLogger] = None


def get_audit_logger() -> AuditLogger:
    """Return the module-level default audit logger singleton."""
    global _default_audit
    if _default_audit is None:
        _default_audit = AuditLogger()
    return _default_audit


# ------------------------------------------------------------------
# Convenience functions (use singleton)
# ------------------------------------------------------------------

def log_login_success(**kwargs: Any) -> AuditEvent:
    return get_audit_logger().login_success(**kwargs)


def log_login_failure(**kwargs: Any) -> AuditEvent:
    return get_audit_logger().login_failure(**kwargs)


def log_login_locked(**kwargs: Any) -> AuditEvent:
    return get_audit_logger().login_locked(**kwargs)


def log_password_change_success(**kwargs: Any) -> AuditEvent:
    return get_audit_logger().password_change_success(**kwargs)


def log_password_change_failed(**kwargs: Any) -> AuditEvent:
    return get_audit_logger().password_change_failed(**kwargs)


def log_permission_grant(**kwargs: Any) -> AuditEvent:
    return get_audit_logger().permission_grant(**kwargs)


def log_permission_revoke(**kwargs: Any) -> AuditEvent:
    return get_audit_logger().permission_revoke(**kwargs)


def log_data_read(**kwargs: Any) -> AuditEvent:
    return get_audit_logger().data_read(**kwargs)


def log_data_write(**kwargs: Any) -> AuditEvent:
    return get_audit_logger().data_write(**kwargs)


def log_data_delete(**kwargs: Any) -> AuditEvent:
    return get_audit_logger().data_delete(**kwargs)


def log_config_change(**kwargs: Any) -> AuditEvent:
    return get_audit_logger().config_change(**kwargs)


def log_config_create(**kwargs: Any) -> AuditEvent:
    return get_audit_logger().config_create(**kwargs)


def log_config_delete(**kwargs: Any) -> AuditEvent:
    return get_audit_logger().config_delete(**kwargs)


def log_token_issued(**kwargs: Any) -> AuditEvent:
    return get_audit_logger().token_issued(**kwargs)


def log_token_revoked(**kwargs: Any) -> AuditEvent:
    return get_audit_logger().token_revoked(**kwargs)


def log_token_rotated(**kwargs: Any) -> AuditEvent:
    return get_audit_logger().token_rotated(**kwargs)


def log_admin_action(**kwargs: Any) -> AuditEvent:
    return get_audit_logger().admin_action(**kwargs)
