"""
Sends admin emails (EmailCampaign) one recipient at a time over one SMTP connection.

Bulk sends run in a background thread so the admin page returns straight away.
Progress is saved per recipient, so if the server restarts mid-send the
campaign can be resumed from admin without emailing anyone twice.
"""
import logging
import threading
import time
from datetime import timedelta
from email.utils import formataddr

from django.conf import settings
from django.core import signing
from django.core.mail import EmailMultiAlternatives, get_connection
from django.db import close_old_connections, transaction
from django.db.models import F
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.utils.html import escape, urlize

from api.models import EmailCampaign, EmailRecipient, EmailUnsubscribe

logger = logging.getLogger(__name__)

FROM_NAME = 'JeroPay'
UNSUBSCRIBE_SALT = 'jeropay-email-unsubscribe'

# pause between emails so the mail server doesn't flag us as spam or hit its hourly limit
SEND_DELAY_SECONDS = 1.0
# open a fresh SMTP connection every N emails (servers drop long-lived ones)
RECONNECT_EVERY = 50
# a 'sending' campaign with no progress for this long is treated as stopped (e.g. server restart)
STALE_AFTER = timedelta(minutes=10)
# at most this many recipients are sent inside the request; bigger sends go to the background
INLINE_SEND_LIMIT = 5
# after this many failures in a row the mail server is probably down: pause instead of failing everyone
PAUSE_AFTER_CONSECUTIVE_FAILURES = 10

PLACEHOLDERS = ('name', 'first_name', 'username', 'email')


def from_address():
    return formataddr((FROM_NAME, settings.DEFAULT_FROM_EMAIL))


def unsubscribe_token(email):
    return signing.dumps(email.strip().lower(), salt=UNSUBSCRIBE_SALT)


def email_from_unsubscribe_token(token):
    try:
        return signing.loads(token, salt=UNSUBSCRIBE_SALT)
    except signing.BadSignature:
        return None


def is_unsubscribed(email):
    return EmailUnsubscribe.objects.filter(email__iexact=email.strip()).exists()


def fill_placeholders(text, recipient):
    """Replace {name} etc. Plain str.replace so other braces in the message are left alone."""
    name = recipient.name or recipient.username or 'there'
    values = {
        'name': name,
        'first_name': name.split(' ')[0],
        'username': recipient.username or '',
        'email': recipient.email,
    }
    for key in PLACEHOLDERS:
        text = text.replace('{' + key + '}', values[key])
    return text


def build_message(campaign, recipient, connection=None):
    subject = fill_placeholders(campaign.subject, recipient).replace('\n', ' ').strip()
    body = fill_placeholders(campaign.body, recipient)

    unsubscribe_url = ''
    headers = {}
    if campaign.is_bulk and campaign.site_url:
        unsubscribe_url = campaign.site_url.rstrip('/') + reverse(
            'api:email-unsubscribe', args=[unsubscribe_token(recipient.email)]
        )
        headers['List-Unsubscribe'] = f'<{unsubscribe_url}>'
        headers['List-Unsubscribe-Post'] = 'List-Unsubscribe=One-Click'

    text = body
    if unsubscribe_url:
        text += f'\n\n--\nYou received this because you have a JeroPay account.\nUnsubscribe: {unsubscribe_url}'

    # message is admin-written plain text: escape it, keep line breaks, make links clickable
    html_body = urlize(escape(body)).replace('\n', '<br>\n')
    html = render_to_string('emails/admin_email.html', {
        'subject': subject,
        'body_html': html_body,
        'unsubscribe_url': unsubscribe_url,
    })

    message = EmailMultiAlternatives(
        subject=subject,
        body=text,
        from_email=from_address(),
        to=[recipient.email],
        headers=headers,
        connection=connection,
    )
    message.attach_alternative(html, 'text/html')
    return message


def send_test_email(subject, body, to_email, is_bulk, site_url):
    """Sends one preview to the admin. Raises on failure so the page can show the error."""
    campaign = EmailCampaign(subject=subject, body=body, is_bulk=is_bulk, site_url=site_url)
    recipient = EmailRecipient(email=to_email, name='Test Customer', username='testcustomer')
    message = build_message(campaign, recipient)
    message.subject = f'[TEST] {message.subject}'
    message.send(fail_silently=False)


def start_campaign(campaign_id):
    """Send small campaigns now; send big ones in a background thread."""
    pending = EmailRecipient.objects.filter(campaign_id=campaign_id, status='pending').count()
    if pending <= INLINE_SEND_LIMIT:
        send_campaign(campaign_id, delay=0)
        return False
    thread = threading.Thread(target=_send_in_thread, args=(campaign_id,), name=f'email-campaign-{campaign_id}', daemon=True)
    thread.start()
    return True


def _send_in_thread(campaign_id):
    close_old_connections()
    try:
        send_campaign(campaign_id)
    except Exception:
        logger.exception('Email campaign %s crashed', campaign_id)
    finally:
        close_old_connections()


def can_resume(campaign):
    if campaign.status == 'queued':
        return True
    if campaign.status == 'sending':
        last = campaign.last_activity_at or campaign.started_at
        return last is None or timezone.now() - last > STALE_AFTER
    return False


def _claim(campaign_id):
    """Mark the campaign as sending unless another worker is already on it."""
    now = timezone.now()
    with transaction.atomic():
        campaign = EmailCampaign.objects.select_for_update().get(pk=campaign_id)
        if not can_resume(campaign):
            return None
        campaign.status = 'sending'
        campaign.started_at = campaign.started_at or now
        campaign.last_activity_at = now
        campaign.save(update_fields=['status', 'started_at', 'last_activity_at'])
        return campaign


def send_campaign(campaign_id, delay=SEND_DELAY_SECONDS):
    campaign = _claim(campaign_id)
    if campaign is None:
        logger.info('Email campaign %s is already being sent or is finished', campaign_id)
        return

    connection = None
    sent_since_connect = 0
    consecutive_failures = 0
    try:
        while True:
            recipient = EmailRecipient.objects.filter(campaign_id=campaign_id, status='pending').order_by('id').first()
            if recipient is None:
                break

            # stop promptly if an admin cancelled
            if EmailCampaign.objects.filter(pk=campaign_id, status='cancelled').exists():
                logger.info('Email campaign %s cancelled', campaign_id)
                return

            if campaign.is_bulk and is_unsubscribed(recipient.email):
                _mark(recipient, 'skipped', 'Unsubscribed', 'skipped_count')
                continue

            try:
                if connection is None or sent_since_connect >= RECONNECT_EVERY:
                    _close(connection)
                    connection = get_connection(fail_silently=False)
                    connection.open()
                    sent_since_connect = 0
                build_message(campaign, recipient, connection=connection).send(fail_silently=False)
                _mark(recipient, 'sent', '', 'sent_count')
                sent_since_connect += 1
                consecutive_failures = 0
            except Exception as e:
                logger.warning('Email to %s failed (campaign %s): %s', recipient.email, campaign_id, e)
                _mark(recipient, 'failed', str(e)[:500], 'failed_count')
                # a broken connection would fail every following email too
                _close(connection)
                connection = None
                consecutive_failures += 1
                if consecutive_failures >= PAUSE_AFTER_CONSECUTIVE_FAILURES:
                    logger.error('Email campaign %s paused after %s failures in a row', campaign_id, consecutive_failures)
                    EmailCampaign.objects.filter(pk=campaign_id, status='sending').update(status='queued')
                    return

            if delay:
                time.sleep(delay)
    finally:
        _close(connection)

    EmailCampaign.objects.filter(pk=campaign_id, status='sending').update(
        status='sent', finished_at=timezone.now(), last_activity_at=timezone.now()
    )


def _mark(recipient, status, error, counter):
    now = timezone.now()
    with transaction.atomic():
        updated = EmailRecipient.objects.filter(pk=recipient.pk, status='pending').update(
            status=status, error=error, sent_at=now if status == 'sent' else None
        )
        if updated:
            EmailCampaign.objects.filter(pk=recipient.campaign_id).update(
                **{counter: F(counter) + 1}, last_activity_at=now
            )


def _close(connection):
    if connection is None:
        return
    try:
        connection.close()
    except Exception:
        pass


def retry_failed(campaign):
    """Put failed recipients back in the queue. Returns how many."""
    with transaction.atomic():
        count = EmailRecipient.objects.filter(campaign=campaign, status='failed').update(status='pending', error='')
        if count:
            EmailCampaign.objects.filter(pk=campaign.pk).update(
                failed_count=F('failed_count') - count, status='queued', finished_at=None
            )
    return count
