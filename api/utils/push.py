from django.conf import settings
from fcm_django.models import FCMDevice
from firebase_admin.messaging import (
    Message, Notification, AndroidConfig, AndroidNotification,
)
from api.models import InAppNotification

CHANNEL_ID = 'jeropay_alerts_v2'


def make_message(title: str, body: str) -> Message:
    """Build an FCM Message with the correct Android notification channel."""
    return Message(
        notification=Notification(title=title, body=body),
        android=AndroidConfig(
            priority='high',
            notification=AndroidNotification(
                channel_id=CHANNEL_ID,
                sound='default',
                icon='ic_launcher',
            ),
        ),
    )


def send_push(user, title: str, body: str) -> None:
    """Send FCM push + persist an in-app notification for the user."""
    InAppNotification.objects.create(user=user, title=title, body=body)
    try:
        devices = FCMDevice.objects.filter(user=user, active=True)
        if devices.exists():
            response = devices.send_message(
                make_message(title, body),
                app=settings.FCM_DJANGO_SETTINGS['DEFAULT_FIREBASE_APP'],
            )
            failure = getattr(response, 'failure_count', 0)
            if failure:
                errors = [str(r.exception) for r in response.responses if not r.success and r.exception]
                print(f'FCM push partial failure [{user}]: {errors}')
    except Exception as e:
        print(f'FCM push failed [{user}]: {e}')


def send_push_to_all(title: str, body: str, queryset=None) -> int:
    """Broadcast to all active devices (or a filtered queryset). Returns device count."""
    try:
        devices = queryset if queryset is not None else FCMDevice.objects.filter(active=True)
        count = devices.count()
        if count:
            # Persist in-app notification for every targeted user
            user_ids = list(devices.values_list('user_id', flat=True).distinct())
            InAppNotification.objects.bulk_create([
                InAppNotification(user_id=uid, title=title, body=body)
                for uid in user_ids
            ])
            devices.send_message(
                make_message(title, body),
                app=settings.FCM_DJANGO_SETTINGS['DEFAULT_FIREBASE_APP'],
            )
        return count
    except Exception as e:
        print(f'FCM broadcast failed: {e}')
        return 0
