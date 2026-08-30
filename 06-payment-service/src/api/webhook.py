"""
FastAPI router for HTTP webhook endpoints.

Provides ``POST /webhook/stripe`` (and optionally YooMoney) that
verifies signatures and dispatches to ``PaymentService``.
"""

import logging

from fastapi import APIRouter, Header, HTTPException, Request

from src.services.payment_service import PaymentService
from src.database import async_session_factory

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhook", tags=["webhooks"])


@router.post("/stripe")
async def webhook_stripe(request: Request) -> dict:
    """
    Stripe webhook endpoint.

    Verifies the Stripe signature and processes the event.
    Returns 200 on success regardless of event processing result
    (Stripe expects this).
    """
    body = await request.body()
    signature = request.headers.get("stripe-signature", "")

    if not signature:
        raise HTTPException(status_code=400, detail="Missing stripe-signature header")

    async with async_session_factory() as session:
        service = PaymentService(session=session)
        try:
            result = await service.handle_webhook(provider="stripe", payload=body, signature=signature)
            return result
        except ValueError as exc:
            logger.warning("Stripe webhook verification failed: %s", exc)
            raise HTTPException(status_code=400, detail=str(exc))
        except Exception as exc:
            logger.error("Stripe webhook processing error: %s", exc)
            raise HTTPException(status_code=500, detail="Webhook processing failed")


@router.post("/yoomoney")
async def webhook_yoomoney(request: Request) -> dict:
    """
    YooMoney webhook endpoint.

    Verifies the YooMoney HMAC signature and processes the event.
    """
    body = await request.body()
    signature = request.headers.get("x-notification-checksum", "")

    if not signature:
        raise HTTPException(status_code=400, detail="Missing X-Notification-Checksum header")

    async with async_session_factory() as session:
        service = PaymentService(session=session)
        try:
            result = await service.handle_webhook(provider="yoomoney", payload=body, signature=signature)
            return result
        except ValueError as exc:
            logger.warning("YooMoney webhook verification failed: %s", exc)
            raise HTTPException(status_code=400, detail=str(exc))
        except Exception as exc:
            logger.error("YooMoney webhook processing error: %s", exc)
            raise HTTPException(status_code=500, detail="Webhook processing failed")
