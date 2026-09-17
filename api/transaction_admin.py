"""
Transaction monitoring in Django admin: search, filters, summary bar, detail page
and safe actions for settling pending purchases.
"""
import re
import uuid
from datetime import datetime, time, timedelta
from decimal import Decimal, InvalidOperation

from django.contrib import admin, messages
from django.core.exceptions import PermissionDenied
from django.db import transaction as db_transaction
from django.db.models import Count, F, Q, Sum
from django.db.models.functions import Coalesce
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.html import format_html
from urllib.parse import urlencode

from api.dashboard import PURCHASE_TYPES, WAT, period_range
from api.models import Profile, Transaction, Wallet

SUCCESS_Q = Q(status__iexact='success')
FAILED_Q = Q(status__iexact='failed') | Q(status__iexact='refunded')
PENDING_Q = Q(status__iexact='pending')

NETWORK_QUERIES = {
    'MTN': Q(network__iexact='MTN'),
    'AIRTEL': Q(network__iexact='AIRTEL'),
    'GLO': Q(network__iexact='GLO'),
    '9MOBILE': Q(network__iexact='9MOBILE') | Q(network__iexact='9 MOBILE') | Q(network__iexact='ETISALAT'),
}

STATUS_CHOICES = ['Success', 'Pending', 'Failed', 'Refunded']


def canonical_status(value):
    """'success' -> 'Success' etc., so old lowercase rows compare correctly."""
    for choice in STATUS_CHOICES:
        if str(value or '').lower() == choice.lower():
            return choice
    return str(value or '')


def status_change_effect(trans, new_status):
    """What changing to new_status does to the wallet: ('credit'|'debit'|None, amount)."""
    if trans.type not in PURCHASE_TYPES:
        return None, Decimal('0')
    old = canonical_status(trans.status)
    if new_status == 'Refunded' and old != 'Refunded':
        return 'credit', trans.amount
    if old == 'Refunded' and new_status != 'Refunded':
        return 'debit', trans.amount
    return None, Decimal('0')


def apply_status_change(pk, new_status, reason, move_money, admin_user):
    """
    Change one transaction's status, keeping the wallet consistent.
    Returns (changed: bool, message: str, transaction or None).
    """
    with db_transaction.atomic():
        trans = Transaction.objects.select_for_update().select_related('user').filter(pk=pk).first()
        if trans is None:
            return False, 'Transaction not found.', None
        old = canonical_status(trans.status)
        if old == new_status:
            return False, f'{str(trans.pk)[:8]} is already {new_status}.', trans

        effect, amount = status_change_effect(trans, new_status)
        money_note = ''
        if effect and move_money:
            wallet = Wallet.objects.select_for_update().filter(user__user=trans.user).first()
            if wallet is None:
                return False, f'{str(trans.pk)[:8]}: customer has no wallet, status not changed.', trans
            if effect == 'debit' and wallet.balance < amount:
                return False, (f'{str(trans.pk)[:8]}: wallet balance ₦{wallet.balance:,.2f} is less than ₦{amount:,.2f}, '
                               'status not changed. Untick "take the money back" to change the status only.'), trans
            delta = amount if effect == 'credit' else -amount
            Wallet.objects.filter(pk=wallet.pk).update(balance=F('balance') + delta)
            money_note = f' ₦{amount:,.2f} {"refunded to" if effect == "credit" else "taken back from"} wallet.'

        if trans.type in PURCHASE_TYPES:
            if old == 'Success' and new_status != 'Success':
                Wallet.objects.filter(user__user=trans.user).update(
                    total_purchase=Coalesce(F('total_purchase'), Decimal('0')) - trans.amount)
            elif new_status == 'Success' and old != 'Success':
                Wallet.objects.filter(user__user=trans.user).update(
                    total_purchase=Coalesce(F('total_purchase'), Decimal('0')) + trans.amount)

        note = f'Status {old} -> {new_status} by {admin_user.username}: {reason}.{money_note}'
        trans.status = new_status
        trans.response = f'{note} | {trans.response or ""}'[:300]
        trans.save(update_fields=['status', 'response'])
        return True, note, trans


STATUS_COLOURS = {
    'success': ('#1e7e46', '#e3f5ea', 'Successful'),
    'pending': ('#8a5a00', '#fff3d6', 'Pending'),
    'failed': ('#b42318', '#fde8e7', 'Failed'),
    'refunded': ('#b42318', '#fde8e7', 'Refunded'),
}


# ── filters ──────────────────────────────────────────────────────────────────

class ResultFilter(admin.SimpleListFilter):
    title = 'result'
    parameter_name = 'result'

    def lookups(self, request, model_admin):
        return (('success', 'Successful'), ('failed', 'Failed / refunded'), ('pending', 'Pending'))

    def queryset(self, request, queryset):
        return {
            'success': lambda: queryset.filter(SUCCESS_Q),
            'failed': lambda: queryset.filter(FAILED_Q),
            'pending': lambda: queryset.filter(PENDING_Q),
        }.get(self.value(), lambda: queryset)()


class NetworkFilter(admin.SimpleListFilter):
    title = 'network'
    parameter_name = 'network_is'

    def lookups(self, request, model_admin):
        return (('MTN', 'MTN'), ('AIRTEL', 'Airtel'), ('GLO', 'Glo'), ('9MOBILE', '9mobile'))

    def queryset(self, request, queryset):
        query = NETWORK_QUERIES.get(self.value())
        return queryset.filter(query) if query is not None else queryset


class WhenFilter(admin.SimpleListFilter):
    title = 'date'
    parameter_name = 'when'

    def lookups(self, request, model_admin):
        return (('today', 'Today'), ('yesterday', 'Yesterday'), ('7d', 'Last 7 days'), ('30d', 'Last 30 days'))

    def queryset(self, request, queryset):
        if self.value() not in ('today', 'yesterday', '7d', '30d'):
            return queryset
        start, end = period_range(self.value())
        queryset = queryset.filter(date_and_time__gte=start)
        return queryset.filter(date_and_time__lt=end) if end else queryset


class InputRangeFilter(admin.ListFilter):
    """Sidebar filter with two text/date inputs (e.g. from/to) instead of links."""
    template = 'admin/filter_input_range.html'
    fields = ()  # (parameter, label, input type, placeholder)

    def __init__(self, request, params, model, model_admin):
        super().__init__(request, params, model, model_admin)
        self.request = request
        for name, *_rest in self.fields:
            if name in params:
                value = params.pop(name)
                # Django 5+ passes lists, Django 3.2 passes strings
                value = value[-1] if isinstance(value, (list, tuple)) else value
                if str(value).strip():
                    self.used_parameters[name] = str(value).strip()

    def has_output(self):
        return True

    def expected_parameters(self):
        return [name for name, *_rest in self.fields]

    def choices(self, changelist):
        own = set(self.expected_parameters())
        hidden = [(k, v) for k, values in self.request.GET.lists() if k not in own and k not in ('p', 'e') for v in values]
        clear = {k: v for k, v in hidden}
        yield {
            'inputs': [
                {'name': name, 'label': label, 'type': kind, 'placeholder': placeholder,
                 'value': self.used_parameters.get(name, '')}
                for name, label, kind, placeholder in self.fields
            ],
            'hidden': hidden,
            'active': bool(self.used_parameters),
            'clear_url': '?' + urlencode(clear) if clear else '?',
        }


class DateRangeFilter(InputRangeFilter):
    title = 'date range'
    fields = (('date_from', 'From', 'date', ''), ('date_to', 'To', 'date', ''))

    @staticmethod
    def _date(value):
        try:
            return datetime.strptime(value, '%Y-%m-%d').date()
        except (TypeError, ValueError):
            return None

    def queryset(self, request, queryset):
        start = self._date(self.used_parameters.get('date_from'))
        end = self._date(self.used_parameters.get('date_to'))
        if start:
            queryset = queryset.filter(date_and_time__gte=datetime.combine(start, time.min, tzinfo=WAT))
        if end:
            queryset = queryset.filter(date_and_time__lt=datetime.combine(end + timedelta(days=1), time.min, tzinfo=WAT))
        return queryset


class AmountRangeFilter(InputRangeFilter):
    title = 'amount (₦)'
    fields = (('amount_min', 'Min', 'number', '0'), ('amount_max', 'Max', 'number', 'any'))

    @staticmethod
    def _amount(value):
        try:
            return Decimal(value) if value not in (None, '') else None
        except (InvalidOperation, TypeError):
            return None

    def queryset(self, request, queryset):
        low = self._amount(self.used_parameters.get('amount_min'))
        high = self._amount(self.used_parameters.get('amount_max'))
        if low is not None:
            queryset = queryset.filter(amount__gte=low)
        if high is not None:
            queryset = queryset.filter(amount__lte=high)
        return queryset


# ── admin ────────────────────────────────────────────────────────────────────

class TransactionMonitorAdmin(admin.ModelAdmin):
    list_display = ['short_id', 'when', 'customer', 'type', 'network_label', 'phone_number', 'amount_naira', 'status_badge', 'response_short']
    list_display_links = ['short_id', 'when']
    list_filter = (ResultFilter, 'type', NetworkFilter, WhenFilter, DateRangeFilter, AmountRangeFilter)
    search_fields = ('phone_number',)  # real search is in get_search_results
    search_help_text = 'Search by phone number, transaction ID, provider reference, customer username/email, or response text.'
    list_select_related = ('user',)
    ordering = ['-date_and_time']
    list_per_page = 50
    change_list_template = 'admin/api/transaction/change_list.html'
    actions = ['change_status_action', 'mark_successful_action', 'refund_pending_action']
    change_form_template = 'admin/api/transaction/change_form.html'

    fieldsets = (
        ('Transaction', {'fields': ('id', 'type', 'status_badge', 'amount_naira', 'date_and_time', 'detail')}),
        ('Customer', {'fields': ('customer_link', 'phone_links', 'network')}),
        ('Wallet', {'fields': ('old_balance', 'new_balance')}),
        ('Provider / API', {'fields': ('request_id', 'provider_response')}),
        ('Investigate', {'fields': ('related_links',)}),
    )

    # transactions are money records: view-only, changed only through the actions below
    def get_readonly_fields(self, request, obj=None):
        return [
            'id', 'type', 'status_badge', 'amount_naira', 'date_and_time', 'detail', 'customer_link',
            'phone_links', 'network', 'old_balance', 'new_balance', 'request_id', 'provider_response', 'related_links',
        ]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    # ── search ──
    def get_search_results(self, request, queryset, search_term):
        term = (search_term or '').strip()
        if not term:
            return queryset, False

        query = (
            Q(phone_number__icontains=term) | Q(request_id__icontains=term) | Q(detail__icontains=term)
            | Q(response__icontains=term) | Q(user__username__icontains=term) | Q(user__email__icontains=term)
        )

        digits = re.sub(r'\D', '', term)
        if len(digits) >= 6:
            query |= Q(phone_number__icontains=digits)
            if digits.startswith('234') and len(digits) > 10:
                query |= Q(phone_number__icontains='0' + digits[3:])   # +234803... -> 0803...
            if len(digits) == 10 and not digits.startswith('0'):
                query |= Q(phone_number__icontains='0' + digits)      # 803... -> 0803...

        hex_term = term.replace('-', '').lower()
        if re.fullmatch(r'[0-9a-f]{32}', hex_term):
            query |= Q(id=uuid.UUID(hex_term))
        elif re.fullmatch(r'[0-9a-f]{6,31}', hex_term):
            query |= Q(id__startswith=term.lower())
        return queryset.filter(query), False

    # ── list columns ──
    @admin.display(description='ID', ordering='id')
    def short_id(self, obj):
        return str(obj.id)[:8]

    @admin.display(description='Date (WAT)', ordering='date_and_time')
    def when(self, obj):
        return obj.date_and_time.astimezone(WAT).strftime('%d %b %Y, %H:%M')

    @admin.display(description='Customer', ordering='user__username')
    def customer(self, obj):
        return obj.user.username

    @admin.display(description='Network', ordering='network')
    def network_label(self, obj):
        return obj.network if obj.network not in (None, '', 'N/A') else '-'

    @admin.display(description='Amount', ordering='amount')
    def amount_naira(self, obj):
        return f'₦{obj.amount:,.2f}'

    @admin.display(description='Status', ordering='status')
    def status_badge(self, obj):
        fg, bg, label = STATUS_COLOURS.get(str(obj.status).lower(), ('#444', '#eee', obj.status))
        return format_html(
            '<span style="display:inline-block;padding:2px 8px;border-radius:10px;font-weight:600;font-size:11px;color:{};background:{}">{}</span>',
            fg, bg, label,
        )

    @admin.display(description='Provider response')
    def response_short(self, obj):
        text = obj.response or ''
        return text if len(text) <= 60 else text[:57] + '...'

    # ── detail fields ──
    @admin.display(description='Customer')
    def customer_link(self, obj):
        user = obj.user
        profile = Profile.objects.filter(user=user).first()
        wallet = Wallet.objects.filter(user=profile).first() if profile else None
        user_url = reverse('admin:auth_user_change', args=[user.pk])
        extra = f' · wallet ₦{wallet.balance:,.2f}' if wallet else ''
        return format_html('<a href="{}">{}</a> ({}){}', user_url, user.username, user.email or 'no email', extra)

    @admin.display(description='Phone number')
    def phone_links(self, obj):
        phone = obj.phone_number or ''
        if not phone or phone in ('0', 'N/A'):
            return phone or '-'
        url = reverse('admin:api_transaction_changelist') + '?' + urlencode({'q': phone})
        return format_html('{} &nbsp; <a href="{}">All transactions to this number</a>', phone, url)

    @admin.display(description='Provider response')
    def provider_response(self, obj):
        return format_html('<pre style="white-space:pre-wrap;margin:0;font-size:12px">{}</pre>', obj.response or '-')

    @admin.display(description='Related')
    def related_links(self, obj):
        base = reverse('admin:api_transaction_changelist')
        same_user = base + '?' + urlencode({'q': obj.user.username})
        same_day = base + '?' + urlencode({'date_from': obj.date_and_time.astimezone(WAT).strftime('%Y-%m-%d'),
                                           'date_to': obj.date_and_time.astimezone(WAT).strftime('%Y-%m-%d')})
        return format_html('<a href="{}">This customer\'s transactions</a> &nbsp;·&nbsp; <a href="{}">All transactions that day</a>',
                           same_user, same_day)

    # ── change status (single transaction page + bulk action) ──
    def get_urls(self):
        from django.urls import path
        custom = [
            path('<path:object_id>/change-status/', self.admin_site.admin_view(self.change_status_view),
                 name='api_transaction_change_status'),
        ]
        return custom + super().get_urls()

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = dict(extra_context or {})
        extra_context['can_change_status'] = request.user.has_perm('api.change_transaction')
        return super().change_view(request, object_id, form_url, extra_context)

    def change_status_view(self, request, object_id):
        self._check(request)
        return self._status_form(request, Transaction.objects.filter(pk=object_id), single=True)

    @admin.action(description='Change status of selected transactions')
    def change_status_action(self, request, queryset):
        self._check(request)
        return self._status_form(request, queryset, single=False)

    def _status_form(self, request, queryset, single):
        from api.utils.push import send_push

        transactions = list(queryset.select_related('user').order_by('-date_and_time'))
        if single and not transactions:
            self.message_user(request, 'Transaction not found.', messages.ERROR)
            from django.http import HttpResponseRedirect
            return HttpResponseRedirect(reverse('admin:api_transaction_changelist'))

        errors = []
        new_status = request.POST.get('new_status', '')
        reason = request.POST.get('reason', '').strip()
        submitted = request.method == 'POST' and request.POST.get('apply_status') == 'yes'

        if submitted:
            if new_status not in STATUS_CHOICES:
                errors.append('Choose the new status.')
            if len(reason) < 3:
                errors.append('Write a short reason (it is saved on the transaction and in its History).')
            if not errors:
                move_money = request.POST.get('move_money') == 'yes'
                notify = request.POST.get('notify') == 'yes'
                changed, skipped = 0, []
                for trans in transactions:
                    ok, note, updated = apply_status_change(trans.pk, new_status, reason, move_money, request.user)
                    if not ok:
                        skipped.append(note)
                        continue
                    changed += 1
                    self._log(request, updated, note)
                    if notify and updated.type in PURCHASE_TYPES:
                        if new_status == 'Refunded':
                            body = f'₦{updated.amount:,.2f} has been refunded to your wallet.' if move_money else 'Your purchase was marked as refunded.'
                        elif new_status == 'Success':
                            body = f'Your ₦{updated.amount:,.2f} {updated.type.lower()} purchase was successful.'
                        elif new_status == 'Failed':
                            body = f'Your ₦{updated.amount:,.2f} {updated.type.lower()} purchase failed.'
                        else:
                            body = f'Your ₦{updated.amount:,.2f} {updated.type.lower()} purchase is being processed.'
                        send_push(updated.user, f'{updated.type} Purchase Update', body)
                if changed:
                    self.message_user(request, f'Changed {changed} transaction(s) to {new_status}.', messages.SUCCESS)
                for note in skipped:
                    self.message_user(request, note, messages.WARNING)
                from django.http import HttpResponseRedirect
                if single:
                    return HttpResponseRedirect(reverse('admin:api_transaction_change', args=[transactions[0].pk]))
                return None  # back to the list

        rows = [{
            'trans': t,
            'current': canonical_status(t.status),
            'is_purchase': t.type in PURCHASE_TYPES,
        } for t in transactions]
        return TemplateResponse(request, 'admin/transaction_change_status.html', {
            **self.admin_site.each_context(request),
            'title': 'Change transaction status',
            'rows': rows,
            'single': single,
            'statuses': STATUS_CHOICES,
            'new_status': new_status,
            'reason': reason,
            'errors': errors,
            'selected_ids': [str(t.pk) for t in transactions],
            'opts': self.model._meta,
            # ticked by default; after a failed submit, keep what the admin chose
            'move_money_checked': (request.POST.get('move_money') == 'yes') if submitted else True,
            'notify_checked': (request.POST.get('notify') == 'yes') if submitted else True,
        })

    # ── summary bar for whatever is currently filtered ──
    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(request, extra_context)
        context = getattr(response, 'context_data', None)
        if not context or 'cl' not in context:
            return response
        qs = context['cl'].queryset
        summary = qs.aggregate(
            count=Count('id'), total_amount=Sum('amount'),
            success=Count('id', filter=SUCCESS_Q), success_amount=Sum('amount', filter=SUCCESS_Q),
            failed=Count('id', filter=FAILED_Q), failed_amount=Sum('amount', filter=FAILED_Q),
            pending=Count('id', filter=PENDING_Q), pending_amount=Sum('amount', filter=PENDING_Q),
        )
        for key in ('total_amount', 'success_amount', 'failed_amount', 'pending_amount'):
            summary[key] = summary[key] or Decimal('0')
        base = reverse('admin:api_transaction_changelist')
        params = request.GET.copy()
        for key in ('result', 'p', 'e'):
            params.pop(key, None)
        def with_result(value):
            p = params.copy()
            p['result'] = value
            return f'{base}?{p.urlencode()}'
        summary['urls'] = {'success': with_result('success'), 'failed': with_result('failed'), 'pending': with_result('pending')}
        summary['pending_all_time'] = Transaction.objects.filter(type__in=PURCHASE_TYPES).filter(PENDING_Q).count()
        summary['pending_all_url'] = f'{base}?result=pending'
        context['transaction_summary'] = summary
        return response

    # ── actions for pending purchases ──
    def _confirm(self, request, queryset, action, title, explanation, button):
        pending = queryset.filter(PENDING_Q, type__in=PURCHASE_TYPES)
        skipped = queryset.count() - pending.count()
        total = pending.aggregate(total=Sum('amount'))['total'] or Decimal('0')
        return TemplateResponse(request, 'admin/transaction_action_confirm.html', {
            **self.admin_site.each_context(request),
            'title': title,
            'explanation': explanation,
            'button': button,
            'action': action,
            'transactions': pending.select_related('user'),
            'selected_ids': [str(pk) for pk in queryset.values_list('pk', flat=True)],
            'skipped': skipped,
            'total': total,
            'opts': self.model._meta,
        })

    def _check(self, request):
        if not request.user.has_perm('api.change_transaction'):
            raise PermissionDenied

    def _log(self, request, obj, message):
        # shows in the transaction's History in admin
        self.log_change(request, obj, message)

    @admin.action(description='Mark pending purchases as successful')
    def mark_successful_action(self, request, queryset):
        self._check(request)
        if request.POST.get('confirm') != 'yes':
            return self._confirm(
                request, queryset, 'mark_successful_action', 'Mark as successful',
                'Only do this after confirming on the 247API dashboard that the customer received the value. '
                'The money already taken from their wallet stays taken.',
                'Yes, mark as successful',
            )
        done = 0
        for pk in queryset.filter(PENDING_Q, type__in=PURCHASE_TYPES).values_list('pk', flat=True):
            with db_transaction.atomic():
                trans = Transaction.objects.select_for_update().filter(pk=pk).filter(PENDING_Q).first()
                if trans is None:
                    continue
                trans.status = 'Success'
                trans.response = (f'Marked successful by {request.user.username}. {trans.response or ""}')[:300]
                trans.save(update_fields=['status', 'response'])
                Wallet.objects.filter(user__user=trans.user).update(
                    total_purchase=Coalesce(F('total_purchase'), Decimal('0')) + trans.amount
                )
                self._log(request, trans, 'Marked pending purchase as successful')
            done += 1
        self.message_user(request, f'{done} pending purchase(s) marked as successful.', messages.SUCCESS)
        return None

    @admin.action(description='Refund pending purchases to wallet')
    def refund_pending_action(self, request, queryset):
        self._check(request)
        if request.POST.get('confirm') != 'yes':
            return self._confirm(
                request, queryset, 'refund_pending_action', 'Refund to wallet',
                'Only do this after confirming on the 247API dashboard that the purchase failed. '
                'The amount goes back into each customer\'s wallet and the transaction is marked Refunded.',
                'Yes, refund',
            )
        from api.utils.push import send_push

        done, refunded = 0, Decimal('0')
        for pk in queryset.filter(PENDING_Q, type__in=PURCHASE_TYPES).values_list('pk', flat=True):
            with db_transaction.atomic():
                trans = Transaction.objects.select_for_update().filter(pk=pk).filter(PENDING_Q).first()
                if trans is None:
                    continue  # already settled by someone else or by the webhook
                wallet = Wallet.objects.select_for_update().filter(user__user=trans.user).first()
                if wallet is None:
                    continue
                Wallet.objects.filter(pk=wallet.pk).update(balance=F('balance') + trans.amount)
                trans.status = 'Refunded'
                trans.response = (f'Refunded by {request.user.username}. {trans.response or ""}')[:300]
                trans.save(update_fields=['status', 'response'])
                self._log(request, trans, f'Refunded ₦{trans.amount} to wallet')
            send_push(trans.user, f'{trans.type} Purchase Refunded', f'₦{trans.amount} has been refunded to your wallet.')
            done += 1
            refunded += trans.amount
        self.message_user(request, f'Refunded {done} purchase(s), ₦{refunded:,.2f} in total.', messages.SUCCESS)
        return None
