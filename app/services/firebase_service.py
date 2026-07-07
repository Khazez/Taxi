import json
import logging
import os

import firebase_admin
from firebase_admin import credentials, messaging
from app.core.config import settings

logger = logging.getLogger(__name__)

_firebase_enabled = False

if settings.FIREBASE_CREDENTIALS_JSON:
    cred = credentials.Certificate(json.loads(settings.FIREBASE_CREDENTIALS_JSON))
    firebase_admin.initialize_app(cred)
    _firebase_enabled = True
elif os.path.exists(settings.FIREBASE_CREDENTIALS_PATH):
    cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
    firebase_admin.initialize_app(cred)
    _firebase_enabled = True
else:
    logger.warning(
        "Firebase credentials not found — push-уведомления отключены "
        "(укажите FIREBASE_CREDENTIALS_JSON или FIREBASE_CREDENTIALS_PATH)"
    )


def send_push(token: str, title: str, body: str) -> None:
    """Отправляет push-уведомление на устройство по токену."""
    if not _firebase_enabled:
        return
    message = messaging.Message(
        notification=messaging.Notification(
            title=title,
            body=body,
        ),
        token=token,
    )
    messaging.send(message)


def send_push_multicast(tokens: list[str], title: str, body: str) -> None:
    """Отправляет push-уведомление сразу нескольким устройствам."""
    if not _firebase_enabled:
        return
    message = messaging.MulticastMessage(
        notification=messaging.Notification(
            title=title,
            body=body,
        ),
        tokens=tokens,
    )
    messaging.send_multicast(message)
