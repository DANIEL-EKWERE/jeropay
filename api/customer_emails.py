"""
Admin page for copying / downloading customer emails.

Lives at /admin/database/customer-emails/ (registered in api/admin.py).
Staff with the "Can view user" permission can filter customers, copy every
email in one click, or download them as CSV, Excel, TXT, JSON, vCard or a
Mailchimp/Brevo import file.
"""
import csv
import io
import json
import re
import zipfile
from datetime import datetime, time, timedelta
from xml.sax.saxutils import escape as xml_escape

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse, HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils import timezone

from api.dashboard import PURCHASE_TYPES, WAT, period_range
from api.models import Transaction

User = get_user_model()

EMAIL_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')
SELECTION_SESSION_KEY = 'customer_email_selection'

AUDIENCES = [
    ('all', 'All customers'),
    ('buyers', 'Customers who have bought something'),
    ('non_buyers', 'Customers who have never bought anything'),
    ('resellers', 'Resellers only'),
    ('regular', 'Non-resellers only'),
]
JOINED = [
    ('any', 'Any time'),
    ('today', 'Today'),
    ('7d', 'Last 7 days'),
    ('30d', 'Last 30 days'),
    ('custom', 'Custom dates'),
]
COPY_STYLES = [
    ('comma', 'Comma separated (Gmail, most apps)'),
    ('semicolon', 'Semicolon separated (Outlook)'),
    ('newline', 'One per line'),
    ('named', 'With names: Name <email>'),
]
DOWNLOAD_FORMATS = [
    ('csv', 'CSV (all details)', 'csv', 'text/csv; charset=utf-8'),
    ('xlsx', 'Excel (.xlsx)', 'xlsx', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
    ('mailchimp', 'Mailchimp / Brevo import (CSV)', 'csv', 'text/csv; charset=utf-8'),
    ('txt', 'Text, one email per line', 'txt', 'text/plain; charset=utf-8'),
    ('json', 'JSON', 'json', 'application/json'),
    ('vcf', 'Contacts (vCard .vcf)', 'vcf', 'text/vcard; charset=utf-8'),
]
COLUMNS = ['Email', 'Full name', 'First name', 'Last name', 'Username', 'Phone', 'Reseller', 'Joined']


# ── filtering ────────────────────────────────────────────────────────────────

def _parse_date(value):
    try:
        return datetime.strptime(value, '%Y-%m-%d').date()
    except (TypeError, ValueError):
        return None


def read_filters(params):
    def pick(name, choices, default):
        value = params.get(name, default)
        return value if value in dict(choices) else default

    return {
        'audience': pick('audience', AUDIENCES, 'all'),
        'joined': pick('joined', JOINED, 'any'),
        'start': params.get('start', ''),
        'end': params.get('end', ''),
        'include_staff': params.get('include_staff') == '1',
        'include_inactive': params.get('include_inactive') == '1',
        'style': pick('style', COPY_STYLES, 'comma'),
        'selection': params.get('selection') == '1',
    }


def filtered_users(filters, selected_ids=None):
    qs = User.objects.select_related('profile').order_by('-date_joined', '-pk')

    if selected_ids is not None:
        qs = qs.filter(pk__in=selected_ids)
    if not filters['include_staff']:
        qs = qs.filter(is_staff=False, is_superuser=False)
    if not filters['include_inactive']:
        qs = qs.filter(is_active=True)

    audience = filters['audience']
    if audience in ('buyers', 'non_buyers'):
        buyer_ids = (
            Transaction.objects.filter(type__in=PURCHASE_TYPES, status__iexact='success')
            .values_list('user_id', flat=True)
        )
        qs = qs.filter(pk__in=buyer_ids) if audience == 'buyers' else qs.exclude(pk__in=buyer_ids)
    elif audience == 'resellers':
        qs = qs.filter(profile__reseller=True)
    elif audience == 'regular':
        qs = qs.exclude(profile__reseller=True)

    joined = filters['joined']
    if joined in ('today', '7d', '30d'):
        start, _ = period_range(joined)
        qs = qs.filter(date_joined__gte=start)
    elif joined == 'custom':
        start, end = _parse_date(filters['start']), _parse_date(filters['end'])
        if start:
            qs = qs.filter(date_joined__gte=datetime.combine(start, time.min, tzinfo=WAT))
        if end:
            qs = qs.filter(date_joined__lt=datetime.combine(end + timedelta(days=1), time.min, tzinfo=WAT))
    return qs


def customer_rows(users):
    """One row per unique, valid email. Returns (rows, skipped_counts)."""
    rows, seen = [], set()
    skipped = {'blank': 0, 'invalid': 0, 'duplicate': 0}
    for user in users.iterator() if hasattr(users, 'iterator') else users:
        email = (user.email or '').strip()
        if not email:
            skipped['blank'] += 1
            continue
        if not EMAIL_RE.match(email):
            skipped['invalid'] += 1
            continue
        if email.lower() in seen:
            skipped['duplicate'] += 1
            continue
        seen.add(email.lower())

        profile = getattr(user, 'profile', None) if _has_profile(user) else None
        full_name = (profile.fullName if profile and profile.fullName not in ('', 'N/A') else '') \
            or f'{user.first_name} {user.last_name}'.strip()
        first, _, last = full_name.partition(' ')
        rows.append({
            'email': email,
            'full_name': full_name,
            'first_name': user.first_name or first,
            'last_name': user.last_name or last,
            'username': user.username,
            'phone': profile.phone if profile else '',
            'reseller': 'Yes' if profile and profile.reseller else 'No',
            'joined': timezone.localtime(user.date_joined, WAT).strftime('%Y-%m-%d %H:%M'),
        })
    return rows, skipped


def _has_profile(user):
    try:
        return user.profile is not None
    except Exception:
        return False


# ── output formats ───────────────────────────────────────────────────────────

def _safe_cell(value):
    """Stop spreadsheet apps treating user-entered text as a formula."""
    value = '' if value is None else str(value)
    return "'" + value if value[:1] in ('=', '+', '-', '@', '\t', '\r') else value


def _row_values(row):
    return [row['email'], row['full_name'], row['first_name'], row['last_name'],
            row['username'], row['phone'], row['reseller'], row['joined']]


def copy_text(rows, style):
    if style == 'semicolon':
        return '; '.join(r['email'] for r in rows)
    if style == 'newline':
        return '\n'.join(r['email'] for r in rows)
    if style == 'named':
        def named(r):
            name = r['full_name'].replace('"', "'").replace('<', '').replace('>', '')
            return f'"{name}" <{r["email"]}>' if name else r['email']
        return ', '.join(named(r) for r in rows)
    return ', '.join(r['email'] for r in rows)


def build_csv(rows, mailchimp=False):
    out = io.StringIO()
    out.write('\ufeff')  # BOM so Excel reads names with accents correctly
    writer = csv.writer(out)
    if mailchimp:
        writer.writerow(['Email Address', 'First Name', 'Last Name'])
        for r in rows:
            writer.writerow([_safe_cell(r['email']), _safe_cell(r['first_name']), _safe_cell(r['last_name'])])
    else:
        writer.writerow(COLUMNS)
        for r in rows:
            writer.writerow([_safe_cell(v) for v in _row_values(r)])
    return out.getvalue().encode('utf-8')


_XML_ILLEGAL = re.compile('[\x00-\x08\x0b\x0c\x0e-\x1f]')


def _xlsx_cell(ref, value):
    text = xml_escape(_XML_ILLEGAL.sub('', _safe_cell(value)))
    return f'<c r="{ref}" t="inlineStr"><is><t xml:space="preserve">{text}</t></is></c>'


def _col_letter(index):
    letters = ''
    index += 1
    while index:
        index, rem = divmod(index - 1, 26)
        letters = chr(65 + rem) + letters
    return letters


def build_xlsx(rows):
    """Minimal valid .xlsx using only the standard library (no openpyxl needed)."""
    sheet_rows = []
    for r_index, values in enumerate([COLUMNS] + [_row_values(r) for r in rows], start=1):
        cells = ''.join(_xlsx_cell(f'{_col_letter(c)}{r_index}', v) for c, v in enumerate(values))
        sheet_rows.append(f'<row r="{r_index}">{cells}</row>')
    widths = [34, 26, 16, 16, 18, 14, 9, 17]
    cols = ''.join(f'<col min="{i}" max="{i}" width="{w}" customWidth="1"/>' for i, w in enumerate(widths, start=1))

    files = {
        '[Content_Types].xml': (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
            '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
            '</Types>'
        ),
        '_rels/.rels': (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
            '</Relationships>'
        ),
        'xl/workbook.xml': (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
            'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
            '<sheets><sheet name="Customers" sheetId="1" r:id="rId1"/></sheets></workbook>'
        ),
        'xl/_rels/workbook.xml.rels': (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>'
            '</Relationships>'
        ),
        'xl/worksheets/sheet1.xml': (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
            '<sheetViews><sheetView workbookViewId="0"><pane ySplit="1" topLeftCell="A2" activePane="bottomLeft" state="frozen"/></sheetView></sheetViews>'
            f'<cols>{cols}</cols><sheetData>{"".join(sheet_rows)}</sheetData></worksheet>'
        ),
    }
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as archive:
        for name, content in files.items():
            archive.writestr(name, content)
    return buffer.getvalue()


def _vcard_escape(value):
    return str(value or '').replace('\\', '\\\\').replace(',', '\\,').replace(';', '\\;').replace('\n', ' ')


def build_vcf(rows):
    cards = []
    for r in rows:
        name = r['full_name'] or r['username'] or r['email']
        lines = [
            'BEGIN:VCARD', 'VERSION:3.0',
            f'N:{_vcard_escape(r["last_name"])};{_vcard_escape(r["first_name"])};;;',
            f'FN:{_vcard_escape(name)}',
            f'EMAIL;TYPE=INTERNET:{_vcard_escape(r["email"])}',
        ]
        if r['phone']:
            lines.append(f'TEL;TYPE=CELL:{_vcard_escape(r["phone"])}')
        lines += ['ORG:JeroPay customer', 'END:VCARD']
        cards.append('\r\n'.join(lines))
    return ('\r\n'.join(cards) + '\r\n').encode('utf-8')


def build_download(rows, fmt):
    if fmt == 'xlsx':
        return build_xlsx(rows)
    if fmt == 'mailchimp':
        return build_csv(rows, mailchimp=True)
    if fmt == 'txt':
        return ('\n'.join(r['email'] for r in rows) + '\n').encode('utf-8')
    if fmt == 'json':
        return json.dumps(rows, indent=2, ensure_ascii=False).encode('utf-8')
    if fmt == 'vcf':
        return build_vcf(rows)
    return build_csv(rows)


# ── admin views ──────────────────────────────────────────────────────────────

def _check_permission(request):
    if not request.user.has_perm(f'{User._meta.app_label}.view_user'):
        raise PermissionDenied


def customer_emails_view(request, admin_site):
    _check_permission(request)
    filters = read_filters(request.GET)

    selected_ids = None
    if filters['selection']:
        selected_ids = request.session.get(SELECTION_SESSION_KEY)
        if selected_ids is None:
            messages.warning(request, 'Your selection expired. Showing all customers instead.')
            filters['selection'] = False

    rows, skipped = customer_rows(filtered_users(filters, selected_ids))

    fmt = request.GET.get('download')
    formats = {key: (ext, content_type) for key, _label, ext, content_type in DOWNLOAD_FORMATS}
    if fmt in formats:
        ext, content_type = formats[fmt]
        stamp = timezone.now().astimezone(WAT).strftime('%Y%m%d-%H%M')
        suffix = '-mailchimp' if fmt == 'mailchimp' else ''
        response = HttpResponse(build_download(rows, fmt), content_type=content_type)
        response['Content-Disposition'] = f'attachment; filename="jeropay-customer-emails{suffix}-{stamp}.{ext}"'
        return response

    base_params = request.GET.copy()
    base_params.pop('download', None)
    context = {
        **admin_site.each_context(request),
        'title': 'Customer emails',
        'filters': filters,
        'audiences': AUDIENCES,
        'joined_choices': JOINED,
        'copy_styles': COPY_STYLES,
        'download_formats': [(key, label) for key, label, _ext, _ct in DOWNLOAD_FORMATS],
        'rows_preview': rows[:10],
        'email_count': len(rows),
        'skipped': skipped,
        'skipped_total': sum(skipped.values()),
        'copy_text': copy_text(rows, filters['style']),
        'query_prefix': base_params.urlencode(),
        'selection_count': len(selected_ids) if selected_ids is not None else None,
        'clear_selection_url': reverse('admin:customer-emails'),
    }
    return TemplateResponse(request, 'admin/customer_emails.html', context)


def export_emails_action(modeladmin, request, queryset):
    """Admin action on Users / Profiles: open the email page for just the ticked rows."""
    _check_permission(request)
    model = queryset.model
    if model is User:
        user_ids = list(queryset.values_list('pk', flat=True))
    else:
        user_ids = list(queryset.values_list('user_id', flat=True))
    request.session[SELECTION_SESSION_KEY] = user_ids
    return HttpResponseRedirect(reverse('admin:customer-emails') + '?selection=1&include_staff=1&include_inactive=1')


export_emails_action.short_description = 'Copy / download emails of selected customers'
