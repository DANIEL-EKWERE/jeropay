"""
Admin: compose and send email to one customer, a list of addresses, or a filtered group.
Public: unsubscribe page for bulk emails.
"""
import re
import uuid

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.validators import validate_email
from django.db import IntegrityError
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

from api import mailer
from api.customer_emails import (
    AUDIENCES, JOINED, SELECTION_SESSION_KEY, customer_rows, filtered_users, read_filters,
)
from api.models import EmailCampaign, EmailRecipient, EmailUnsubscribe

User = get_user_model()

COMPOSE_TOKENS_SESSION_KEY = 'email_compose_tokens'
MAX_INDIVIDUAL_RECIPIENTS = 50
ADDRESS_SPLIT_RE = re.compile(r'[,;\n\r\t]+')
NAMED_ADDRESS_RE = re.compile(r'^\s*"?([^"<]*)"?\s*<([^>]+)>\s*$')


def _check_permission(request, bulk):
    if not request.user.has_perm('api.add_emailcampaign'):
        raise PermissionDenied
    if bulk and not request.user.has_perm(f'{User._meta.app_label}.view_user'):
        raise PermissionDenied


def parse_addresses(raw):
    """'a@x.com; "Ada" <ada@x.com>' -> (valid [(email, name)], invalid [str]). Deduped, order kept."""
    valid, invalid, seen = [], [], set()
    for part in ADDRESS_SPLIT_RE.split(raw or ''):
        part = part.strip()
        if not part:
            continue
        name = ''
        match = NAMED_ADDRESS_RE.match(part)
        if match:
            name, part = match.group(1).strip(), match.group(2).strip()
        try:
            validate_email(part)
        except ValidationError:
            invalid.append(part)
            continue
        if part.lower() in seen:
            continue
        seen.add(part.lower())
        valid.append((part, name))
    return valid, invalid


def _individual_recipients(addresses):
    """Match typed addresses to accounts so {name} works for known customers."""
    rows = []
    for email, typed_name in addresses:
        user = User.objects.filter(email__iexact=email).select_related('profile').first()
        name, username, user_id = typed_name, '', None
        if user:
            user_id, username = user.pk, user.username
            profile = getattr(user, 'profile', None) if _has_profile(user) else None
            name = name or (profile.fullName if profile and profile.fullName not in ('', 'N/A') else '') \
                or f'{user.first_name} {user.last_name}'.strip()
        rows.append({'email': email, 'full_name': name, 'username': username, 'user_id': user_id})
    return rows


def _has_profile(user):
    try:
        return user.profile is not None
    except Exception:
        return False


def _audience_label(filters, selection_count):
    if filters['selection']:
        return f'{selection_count} selected customer{"s" if selection_count != 1 else ""}'
    parts = [dict(AUDIENCES)[filters['audience']]]
    if filters['joined'] == 'custom':
        parts.append(f'joined {filters["start"] or "…"} to {filters["end"] or "…"}')
    elif filters['joined'] != 'any':
        parts.append(f'joined {dict(JOINED)[filters["joined"]].lower()}')
    if filters['include_staff']:
        parts.append('including staff')
    if filters['include_inactive']:
        parts.append('including deactivated')
    return ' · '.join(parts)


def _new_token(request):
    token = uuid.uuid4().hex
    tokens = request.session.get(COMPOSE_TOKENS_SESSION_KEY, [])[-19:]
    request.session[COMPOSE_TOKENS_SESSION_KEY] = tokens + [token]
    return token


def _use_token(request, token):
    tokens = request.session.get(COMPOSE_TOKENS_SESSION_KEY, [])
    if token not in tokens:
        return False
    tokens.remove(token)
    request.session[COMPOSE_TOKENS_SESSION_KEY] = tokens
    return True


def compose_email_view(request, admin_site):
    params = request.POST if request.method == 'POST' else request.GET
    bulk = params.get('mode') == 'bulk'
    _check_permission(request, bulk)

    filters = read_filters(params)
    selected_ids = request.session.get(SELECTION_SESSION_KEY) if filters['selection'] else None
    if filters['selection'] and selected_ids is None:
        messages.warning(request, 'Your selection expired. Please select the customers again.')
        return HttpResponseRedirect(reverse('admin:customer-emails'))

    subject = params.get('subject', '').strip()
    body = params.get('body', '').strip()
    to_raw = params.get('to', '')
    errors = []

    if bulk:
        rows, skipped = customer_rows(filtered_users(filters, selected_ids))
        unsubscribed = EmailUnsubscribe.objects.filter(email__in=[r['email'].lower() for r in rows]).count() if rows else 0
        invalid = []
    else:
        addresses, invalid = parse_addresses(to_raw)
        rows = _individual_recipients(addresses)
        skipped, unsubscribed = {}, 0

    if request.method == 'POST':
        action = request.POST.get('action')
        if not subject:
            errors.append('Please enter a subject.')
        if not body:
            errors.append('Please write a message.')
        if not bulk and invalid:
            errors.append(f'These addresses are not valid: {", ".join(invalid)}')
        if not rows:
            errors.append('There is nobody to send to.')
        if not bulk and len(rows) > MAX_INDIVIDUAL_RECIPIENTS:
            errors.append(
                f'That is more than {MAX_INDIVIDUAL_RECIPIENTS} addresses. '
                'Use Customer emails → "Email these customers" for bulk sends.'
            )

        if action == 'test':
            test_errors = [e for e in errors if 'nobody' not in e and 'not valid' not in e and 'more than' not in e]
            if not request.user.email:
                test_errors.append('Your admin account has no email address to send the test to.')
            if not test_errors:
                try:
                    mailer.send_test_email(subject, body, request.user.email, bulk, request.build_absolute_uri('/'))
                    messages.success(request, f'Test email sent to {request.user.email}. Check your inbox (and spam folder).')
                except Exception as e:
                    messages.error(request, f'Test email failed: {e}')
            errors = test_errors

        elif action == 'send':
            if bulk and request.POST.get('confirm') != 'yes':
                errors.append(f'Tick the box to confirm you want to email {len(rows)} customers.')
            if not errors:
                if not _use_token(request, request.POST.get('token', '')):
                    messages.warning(request, 'This email was already sent. Here is the list of sent emails.')
                    return HttpResponseRedirect(reverse('admin:api_emailcampaign_changelist'))
                campaign = _create_campaign(request, subject, body, bulk, rows, filters, selected_ids, to_raw)
                in_background = mailer.start_campaign(campaign.pk)
                if in_background:
                    messages.success(request, f'Sending to {len(rows)} recipients in the background. This page updates as it goes.')
                else:
                    campaign.refresh_from_db()
                    if campaign.failed_count:
                        messages.error(request, f'{campaign.sent_count} sent, {campaign.failed_count} failed. See the error below.')
                    else:
                        messages.success(request, f'Email sent to {campaign.sent_count} recipient{"s" if campaign.sent_count != 1 else ""}.')
                if filters['selection']:
                    request.session.pop(SELECTION_SESSION_KEY, None)
                return HttpResponseRedirect(reverse('admin:api_emailcampaign_change', args=[campaign.pk]))

    back_params = request.GET.copy() if request.method == 'GET' else request.POST.copy()
    for key in ('mode', 'subject', 'body', 'to', 'action', 'confirm', 'token', 'csrfmiddlewaretoken'):
        back_params.pop(key, None)

    context = {
        **admin_site.each_context(request),
        'title': 'Send email to customers' if bulk else 'Send email',
        'bulk': bulk,
        'subject': subject,
        'body': body,
        'to_raw': to_raw,
        'errors': errors,
        'recipient_count': len(rows),
        'recipients_preview': rows[:8],
        'invalid': invalid,
        'unsubscribed_count': unsubscribed,
        'skipped_total': sum(skipped.values()) if skipped else 0,
        'audience_label': _audience_label(filters, len(selected_ids or [])) if bulk else '',
        'filter_fields': [(k, v) for k, v in back_params.items() if k in (
            'audience', 'joined', 'start', 'end', 'include_staff', 'include_inactive', 'selection')],
        'back_url': reverse('admin:customer-emails') + (f'?{back_params.urlencode()}' if back_params else ''),
        'token': _new_token(request),
        'placeholders': ['{' + p + '}' for p in mailer.PLACEHOLDERS],
        'max_individual': MAX_INDIVIDUAL_RECIPIENTS,
        'send_delay': mailer.SEND_DELAY_SECONDS,
        'from_address': mailer.from_address(),
    }
    return TemplateResponse(request, 'admin/email_compose.html', context)


def _create_campaign(request, subject, body, bulk, rows, filters, selected_ids, to_raw):
    audience = _audience_label(filters, len(selected_ids or [])) if bulk else ', '.join(r['email'] for r in rows)
    campaign = EmailCampaign.objects.create(
        subject=subject,
        body=body,
        is_bulk=bulk,
        audience=audience[:300],
        site_url=request.build_absolute_uri('/'),
        total_recipients=len(rows),
        created_by=request.user,
    )
    recipients = [
        EmailRecipient(
            campaign=campaign,
            user_id=row.get('user_id'),
            email=row['email'][:254],
            name=(row.get('full_name') or '')[:150],
            username=(row.get('username') or '')[:150],
        )
        for row in rows
    ]
    try:
        EmailRecipient.objects.bulk_create(recipients, batch_size=500)
    except IntegrityError:
        # emails differing only by case: keep the first of each
        seen = set()
        for r in recipients:
            if r.email.lower() not in seen:
                seen.add(r.email.lower())
                EmailRecipient.objects.get_or_create(campaign=campaign, email=r.email, defaults={
                    'user_id': r.user_id, 'name': r.name, 'username': r.username})
        EmailCampaign.objects.filter(pk=campaign.pk).update(total_recipients=len(seen))
    return campaign


@csrf_exempt  # mail apps send one-click unsubscribe as a plain POST with no CSRF token
def unsubscribe_view(request, token):
    email = mailer.email_from_unsubscribe_token(token)
    if email is None:
        return TemplateResponse(request, 'emails/unsubscribe.html', {'invalid': True}, status=400)

    done = False
    if request.method == 'POST':
        EmailUnsubscribe.objects.get_or_create(email=email)
        done = True
    return TemplateResponse(request, 'emails/unsubscribe.html', {
        'email': email,
        'done': done or EmailUnsubscribe.objects.filter(email__iexact=email).exists(),
    })
