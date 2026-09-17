from decimal import Decimal, InvalidOperation

from django import template

register = template.Library()


@register.filter
def naira(value):
    """12345.5 -> ₦12,345.50"""
    try:
        return f'₦{Decimal(value or 0):,.2f}'
    except (InvalidOperation, TypeError, ValueError):
        return value


@register.filter
def intcomma_plain(value):
    """12345 -> 12,345 (django.contrib.humanize isn't installed)"""
    try:
        return f'{int(value or 0):,}'
    except (TypeError, ValueError):
        return value
