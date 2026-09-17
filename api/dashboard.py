"""
Numbers for the overview at the top of the Django admin home page.

Days are counted in Nigerian time (WAT, UTC+1, no daylight saving), not the
server's UTC, so "Today" starts at midnight in Lagos.
"""
import re
from collections import defaultdict
from datetime import timedelta, timezone as dt_timezone
from decimal import Decimal
from urllib.parse import urlencode

from django.contrib.auth import get_user_model
from django.db.models import Count, Q, Sum
from django.urls import NoReverseMatch, reverse
from django.utils import timezone

from api.models import DepositRecord, Transaction

WAT = dt_timezone(timedelta(hours=1), 'WAT')

PURCHASE_TYPES = ['Airtime', 'Data', 'Cable', 'Electricity', 'Exam']

PERIODS = [
    ('today', 'Today'),
    ('yesterday', 'Yesterday'),
    ('7d', 'Last 7 days'),
    ('30d', 'Last 30 days'),
    ('all', 'All time'),
]

# money added by an admin through the fund-account endpoint, not a customer deposit
ADMIN_DEPOSIT_GATEWAY = 'Wallet Deposit from Admin'

SUCCESS_Q = Q(status__iexact='success')
FAILED_Q = Q(status__iexact='failed') | Q(status__iexact='refunded')
PENDING_Q = Q(status__iexact='pending')

# "You have purchased 1.5GB Data from MTN"
DATA_DETAIL_RE = re.compile(r'(\d+(?:\.\d+)?)\s*(MB|GB|TB)\b.*?\bfrom\s+(\w+)', re.IGNORECASE)
MB_PER_UNIT = {'MB': Decimal('1'), 'GB': Decimal('1024'), 'TB': Decimal('1048576')}


def period_range(period, now=None):
    """(start, end) as aware datetimes; None means unbounded."""
    local_now = (now or timezone.now()).astimezone(WAT)
    today = local_now.replace(hour=0, minute=0, second=0, microsecond=0)
    if period == 'yesterday':
        return today - timedelta(days=1), today
    if period == '7d':
        return today - timedelta(days=6), None
    if period == '30d':
        return today - timedelta(days=29), None
    if period == 'all':
        return None, None
    return today, None


def _in_range(qs, field, start, end):
    if start is not None:
        qs = qs.filter(**{f'{field}__gte': start})
    if end is not None:
        qs = qs.filter(**{f'{field}__lt': end})
    return qs


def _range_params(field, start, end):
    params = {}
    if start is not None:
        params[f'{field}__gte'] = start.isoformat()
    if end is not None:
        params[f'{field}__lt'] = end.isoformat()
    return params


def _admin_url(name, params):
    try:
        url = reverse(name)
    except NoReverseMatch:
        return ''
    return f'{url}?{urlencode(params)}' if params else url


def format_volume(megabytes):
    megabytes = Decimal(megabytes)
    if megabytes >= MB_PER_UNIT['TB']:
        return f'{megabytes / MB_PER_UNIT["TB"]:,.2f} TB'
    if megabytes >= MB_PER_UNIT['GB']:
        return f'{megabytes / MB_PER_UNIT["GB"]:,.2f} GB'
    return f'{megabytes:,.0f} MB'


def data_volume(transactions):
    """Total MB sold and MB per network, parsed from successful data transaction details."""
    total = Decimal('0')
    by_network = defaultdict(Decimal)
    unparsed = 0
    for detail, network in transactions.values_list('detail', 'network').iterator():
        match = DATA_DETAIL_RE.search(detail or '')
        if not match:
            unparsed += 1
            continue
        size, unit, detail_network = match.groups()
        megabytes = Decimal(size) * MB_PER_UNIT[unit.upper()]
        total += megabytes
        # the detail text names the plan's network; older rows have a wrong network column
        by_network[(detail_network or network or 'Other').upper()] += megabytes
    return total, dict(by_network), unparsed


def build_dashboard_stats(period='today'):
    if period not in dict(PERIODS):
        period = 'today'
    start, end = period_range(period)
    date_params = _range_params('date_and_time', start, end)

    purchases = _in_range(Transaction.objects.filter(type__in=PURCHASE_TYPES), 'date_and_time', start, end)
    totals = purchases.aggregate(
        total_count=Count('id'),
        total_amount=Sum('amount'),
        success_count=Count('id', filter=SUCCESS_Q),
        success_amount=Sum('amount', filter=SUCCESS_Q),
        failed_count=Count('id', filter=FAILED_Q),
        failed_amount=Sum('amount', filter=FAILED_Q),
        pending_count=Count('id', filter=PENDING_Q),
        pending_amount=Sum('amount', filter=PENDING_Q),
    )
    zero = Decimal('0')
    for key in ('total_amount', 'success_amount', 'failed_amount', 'pending_amount'):
        totals[key] = totals[key] or zero

    sales_by_type = {
        row['type']: row
        for row in purchases.filter(SUCCESS_Q).values('type').annotate(count=Count('id'), amount=Sum('amount'))
    }
    sales_breakdown = [
        {'type': t, 'count': sales_by_type.get(t, {}).get('count', 0), 'amount': sales_by_type.get(t, {}).get('amount') or zero}
        for t in PURCHASE_TYPES
    ]

    # pending purchases from any date still need someone to check them
    pending_all_time = Transaction.objects.filter(type__in=PURCHASE_TYPES).filter(PENDING_Q).count()

    deposits = _in_range(
        DepositRecord.objects.filter(status__iexact='successful').exclude(gateway=ADMIN_DEPOSIT_GATEWAY),
        'date_and_time', start, end,
    ).aggregate(count=Count('id'), amount=Sum('amount'))
    admin_credits = _in_range(Transaction.objects.filter(type='AdminCredit'), 'date_and_time', start, end).aggregate(
        count=Count('id'), amount=Sum('amount')
    )

    User = get_user_model()
    new_users = _in_range(User.objects.all(), 'date_joined', start, end).count()
    total_users = User.objects.count()

    volume_mb, volume_by_network, unparsed = data_volume(purchases.filter(type='Data').filter(SUCCESS_Q))

    purchase_types_param = {'type__in': ','.join(PURCHASE_TYPES)}
    transaction_list = 'admin:api_transaction_changelist'

    return {
        'period': period,
        'period_label': dict(PERIODS)[period],
        'periods': PERIODS,
        'range_start': start,
        'range_end': end,
        'generated_at': timezone.now().astimezone(WAT),

        'total_count': totals['total_count'],
        'total_amount': totals['total_amount'],
        'total_url': _admin_url(transaction_list, {**purchase_types_param, **date_params}),

        'success_count': totals['success_count'],
        'success_amount': totals['success_amount'],
        'success_url': _admin_url(transaction_list, {**purchase_types_param, 'status__iexact': 'success', **date_params}),

        'failed_count': totals['failed_count'],
        'failed_amount': totals['failed_amount'],
        'failed_url': _admin_url(transaction_list, {**purchase_types_param, 'status__in': 'Failed,Refunded', **date_params}),

        'pending_count': totals['pending_count'],
        'pending_amount': totals['pending_amount'],
        'pending_all_time': pending_all_time,
        'pending_url': _admin_url(transaction_list, {**purchase_types_param, 'status__iexact': 'pending'}),

        'sales_amount': totals['success_amount'],
        'sales_breakdown': sales_breakdown,

        'deposit_count': deposits['count'],
        'deposit_amount': deposits['amount'] or zero,
        'admin_credit_count': admin_credits['count'],
        'admin_credit_amount': admin_credits['amount'] or zero,
        'deposit_url': _admin_url('admin:api_depositrecord_changelist', {'status__iexact': 'successful', **date_params}),

        'new_users': new_users,
        'total_users': total_users,
        'users_url': _admin_url('admin:auth_user_changelist', _range_params('date_joined', start, end)),
        'emails_url': _admin_url('admin:customer-emails', {}),
        'transactions_url': _admin_url(transaction_list, {}),
        'networks_url': _admin_url('admin:api_networkstatus_changelist', {}),
        'plans_url': _admin_url('admin:api_data_changelist', {}),
        'network_switch_url': _admin_url('admin:network-switch', {}),

        'data_volume': format_volume(volume_mb),
        'data_volume_by_network': sorted(
            ((network, format_volume(mb)) for network, mb in volume_by_network.items()),
            key=lambda item: -volume_by_network[item[0]],
        ),
        'data_unparsed': unparsed,
        'data_url': _admin_url(transaction_list, {'type__exact': 'Data', 'status__iexact': 'success', **date_params}),
    }
