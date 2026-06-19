import firebase_admin
from firebase_admin import credentials, messaging
from app.core.config import settings

cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
firebase_admin.initialize_app(cred)


def send_push(token: str, title: str, body: str) -> None:
    """Отправляет push-уведомление на устройство по токену."""
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
    message = messaging.MulticastMessage(
        notification=messaging.Notification(
            title=title,
            body=body,
        ),
        tokens=tokens,
    )
    messaging.send_multicast(message)