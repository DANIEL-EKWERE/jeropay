"""
Admin ON/OFF switches for whole networks (NetworkStatus) and single data plans (Data.is_active).

Checked by the airtime and data purchase views before any money moves, and used
to hide unavailable plans from the app.
"""
from api.models import NetworkStatus

NETWORK_ORDER = [code for code, _label in NetworkStatus.NETWORK_CHOICES]

# how networks are spelled around the codebase / old records
_ALIASES = {
    '9 MOBILE': '9MOBILE',
    '9-MOBILE': '9MOBILE',
    'ETISALAT': '9MOBILE',
}


def normalize_network(name):
    code = str(name or '').strip().upper()
    return _ALIASES.get(code, code)


def disabled_networks():
    """{network_code: customer message} for every network switched off."""
    return {
        status.network: status.customer_message
        for status in NetworkStatus.objects.filter(is_enabled=False)
    }


def network_block_message(network):
    """None if purchases on this network are allowed, else the message for the customer."""
    status = NetworkStatus.objects.filter(network=normalize_network(network)).first()
    if status is None or status.is_enabled:
        return None
    return status.customer_message


def available_plans(queryset):
    """Only plans that are switched on and whose network is switched on."""
    off = list(disabled_networks().keys())
    queryset = queryset.filter(is_active=True)
    if off:
        queryset = queryset.exclude(network__in=off)
    return queryset


def ensure_network_rows():
    """Create any missing network switch rows (ON). Needed when the migration that seeds them wasn't used."""
    existing = set(NetworkStatus.objects.values_list('network', flat=True))
    for code in NETWORK_ORDER:
        if code not in existing:
            NetworkStatus.objects.get_or_create(network=code, defaults={'is_enabled': True})


def network_statuses(create_missing=False):
    """Every network in display order, including ones without a row yet (treated as ON)."""
    if create_missing:
        ensure_network_rows()
    rows = {s.network: s for s in NetworkStatus.objects.all()}
    result = []
    for code, label in NetworkStatus.NETWORK_CHOICES:
        status = rows.get(code)
        result.append({
            'network': code,
            'label': label,
            'is_enabled': status.is_enabled if status else True,
            'message': status.customer_message if status and not status.is_enabled else '',
        })
    return result
