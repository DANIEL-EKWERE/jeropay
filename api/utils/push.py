from django.conf import settings
from fcm_django.models import FCMDevice
from firebase_admin.messaging import (
    Message, Notification, AndroidConfig, AndroidNotification,
)

CHANNEL_ID = 'jeropay_high_importance'


def make_message(title: str, body: str) -> Message:
    """Build an FCM Message with the correct Android notification channel."""
    return Message(
        notification=Notification(title=title, body=body),
        android=AndroidConfig(
            channel_id=CHANNEL_ID,
            priority='high',
            notification=AndroidNotification(
                channel_id=CHANNEL_ID,
                sound='default',
                icon='ic_launcher',
            ),
        ),
    )


def send_push(user, title: str, body: str) -> None:
    """Send a push notification to all active devices for a user. Silent on failure."""
    try:
        devices = FCMDevice.objects.filter(user=user, active=True)
        if devices.exists():
            devices.send_message(
                make_message(title, body),
                app=settings.FCM_DJANGO_SETTINGS['DEFAULT_FIREBASE_APP'],
            )
    except Exception as e:
        print(f'FCM push failed [{user}]: {e}')


def send_push_to_all(title: str, body: str, queryset=None) -> int:
    """Broadcast to all active devices (or a filtered queryset). Returns device count."""
    try:
        devices = queryset if queryset is not None else FCMDevice.objects.filter(active=True)
        count = devices.count()
        if count:
            devices.send_message(
                make_message(title, body),
                app=settings.FCM_DJANGO_SETTINGS['DEFAULT_FIREBASE_APP'],
            )
        return count
    except Exception as e:
        print(f'FCM broadcast failed: {e}')
        return 0
