from django.contrib import admin
from django.utils.html import format_html, format_html_join
from django.conf import settings
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from django.db.models import Count
from django.urls import reverse
from urllib.parse import urlencode
from api.utils.push import send_push, send_push_to_all, make_message

from .models import (
    Airtime,
    CableSubscription,
    Data,
    ElectricitySubscription,
    Wallet,
    Profile,
    Transaction,
    ConfirmPayment,
    DepositRecord,
    Deduct,
    ReservedAccount,
    Announcement,
    ExamPinPrice,
    VirtualAccount,
    TransactionPin,
    CommunityPost,
    CommunityPostLike,
    PushNotification,
    InAppNotification,
    Referral,
    EmailCampaign,
    EmailRecipient,
    EmailUnsubscribe,
    NetworkStatus,
)
from api.transaction_admin import TransactionMonitorAdmin


# ── Overview on the admin home page ──────────────────────────────────────────
admin.site.index_template = 'admin/jeropay_index.html'
_default_admin_index = admin.site.index


def _admin_index_with_overview(request, extra_context=None):
    from api.dashboard import build_dashboard_stats

    extra_context = dict(extra_context or {})
    extra_context['jeropay_stats'] = build_dashboard_stats(request.GET.get('period', 'today'))
    from api.network_control import network_statuses
    extra_context['network_statuses'] = network_statuses(create_missing=True)
    extra_context['can_switch_networks'] = request.user.has_perm('api.change_networkstatus')
    return _default_admin_index(request, extra_context)


admin.site.index = _admin_index_with_overview


# ── Customer emails page: /admin/database/customer-emails/ ───────────────────
from django.contrib.auth import get_user_model as _get_user_model
from django.urls import path as _path
from api.customer_emails import customer_emails_view, export_emails_action, SELECTION_SESSION_KEY
from api.email_views import compose_email_view

_default_admin_get_urls = admin.site.get_urls


def _admin_get_urls():
    extra = [
        _path(
            'customer-emails/',
            admin.site.admin_view(lambda request: customer_emails_view(request, admin.site)),
            name='customer-emails',
        ),
        _path('network-switch/', admin.site.admin_view(lambda request: network_switch_view(request)), name='network-switch'),
        _path(
            'send-email/',
            admin.site.admin_view(lambda request: compose_email_view(request, admin.site)),
            name='send-email',
        ),
    ]
    return extra + _default_admin_get_urls()


admin.site.get_urls = _admin_get_urls

# "Copy / download emails of selected customers" on the built-in Users list
def send_email_action(modeladmin, request, queryset):
    """Admin action on Users / Profiles: write an email to the ticked customers."""
    from django.http import HttpResponseRedirect as _Redirect
    from urllib.parse import urlencode as _urlencode

    User = _get_user_model()
    if queryset.model is User:
        users = queryset
    else:
        users = User.objects.filter(pk__in=queryset.values_list('user_id', flat=True))
    emails = [e for e in users.values_list('email', flat=True) if e]
    if not emails:
        modeladmin.message_user(request, 'None of the selected customers has an email address.', level=messages.WARNING)
        return None
    if len(emails) <= 50:
        return _Redirect(reverse('admin:send-email') + '?' + _urlencode({'to': ', '.join(emails)}))
    request.session[SELECTION_SESSION_KEY] = list(users.values_list('pk', flat=True))
    return _Redirect(reverse('admin:send-email') + '?mode=bulk&selection=1&include_staff=1&include_inactive=1')


send_email_action.short_description = 'Send email to selected customers'

_user_admin = admin.site._registry.get(_get_user_model())
if _user_admin is not None:
    _user_admin.actions = list(_user_admin.actions or []) + [send_email_action, export_emails_action]


@admin.register(Announcement)
class AdminAnnouncement(admin.ModelAdmin):
    list_display = ['body']


@admin.register(Airtime)
class AdminAirtime(admin.ModelAdmin):
    list_display = ['id', 'network', 'amount']
    search_fields = ('network',)


@admin.register(CableSubscription)
class AdminCableSubscription(admin.ModelAdmin):
    list_display = ['cable_service', 'provider', 'amount', 'plan_id']
    search_fields = ('decoder_number',)
    list_editable = ['provider', 'plan_id']


@admin.register(Data)
class AdminData(admin.ModelAdmin):
    list_display = ['plan_switch', 'network', 'network_id', 'plan_type', 'bandwidth', 'amount', 'reseller_amount', 'price_desc', 'is_active']
    list_display_links = ['plan_switch']
    list_filter = ('network', 'plan_type', 'is_active')
    search_fields = ('bandwidth', 'network', 'plan_type')
    list_editable = ['bandwidth', 'amount', 'reseller_amount', 'is_active']
    ordering = ['network', 'amount']
    actions = ['turn_plans_on', 'turn_plans_off']

    @admin.display(description='Plan', ordering='network')
    def plan_switch(self, obj):
        network_off = not NetworkStatus.objects.filter(network=str(obj.network).upper(), is_enabled=False).exists()
        on = obj.is_active and network_off
        label = f'{obj.network} {obj.bandwidth} ({obj.plan_type})'
        state = 'ON' if on else ('OFF' if not obj.is_active else 'OFF (network off)')
        return format_html('{} {} &mdash; {}', '🟢' if on else '🔴', label, state)

    @admin.action(description='Turn selected plans ON')
    def turn_plans_on(self, request, queryset):
        count = queryset.update(is_active=True)
        self.message_user(request, f'{count} plan(s) turned ON.', messages.SUCCESS)

    @admin.action(description='Turn selected plans OFF')
    def turn_plans_off(self, request, queryset):
        count = queryset.update(is_active=False)
        self.message_user(request, f'{count} plan(s) turned OFF. They are hidden in the app and cannot be bought.', messages.WARNING)


@admin.register(ElectricitySubscription)
class AdminElectricitySubscription(admin.ModelAdmin):
    list_display = ['id', 'electric_service']
    search_fields = ('meter_number',)


@admin.register(Wallet)
class AdminWallet(admin.ModelAdmin):
    list_display = ['id', 'user', 'balance', 'total_deposit', 'total_purchase', 'gateway']
    search_fields = ('user__user__username', 'user__user__email')
    readonly_fields = ['total_deposit', 'total_purchase']
    list_per_page = 25

    def save_model(self, request, obj, form, change):
        if not change:
            super().save_model(request, obj, form, change)
            return

        old_balance = Wallet.objects.get(pk=obj.pk).balance
        new_balance = obj.balance
        diff = new_balance - old_balance

        if diff == 0:
            super().save_model(request, obj, form, change)
            return

        is_credit = diff > 0
        tx_type = 'AdminCredit' if is_credit else 'AdminDebit'
        amount = abs(diff)

        super().save_model(request, obj, form, change)

        # Keep total_deposit in sync when admin credits
        if is_credit:
            Wallet.objects.filter(pk=obj.pk).update(
                total_deposit=(obj.total_deposit or 0) + amount
            )

        user = obj.user.user
        Transaction.objects.create(
            user=user,
            detail=f'Admin {"Credit" if is_credit else "Debit"} by {request.user.username}',
            network='N/A',
            response='N/A',
            request_id='N/A',
            old_balance=old_balance,
            new_balance=new_balance,
            phone_number='N/A',
            status='Success',
            amount=amount,
            type=tx_type,
        )

        sign = '+' if is_credit else '-'
        send_push(user, 'Wallet Updated', f'Your wallet has been {sign}₦{amount:,.2f} by admin. New balance: ₦{new_balance:,.2f}')


@admin.register(ExamPinPrice)
class AdminExamPrice(admin.ModelAdmin):
    list_display = ['id', 'exam', 'price']


def retry_virtual_accounts(modeladmin, request, queryset):
    from api.signals import _create_virtual_account_for, BANK_CODES
    from .models import VirtualAccount

    created_count = 0
    fully_recovered = []

    for profile in queryset:
        existing = set(VirtualAccount.objects.filter(profile=profile).values_list('bank_code', flat=True))
        missing = [b for b in BANK_CODES if b not in existing]
        profile_failed = False
        for bank_code in missing:
            try:
                success = _create_virtual_account_for(profile, bank_code)
                if success:
                    created_count += 1
                else:
                    profile_failed = True
            except Exception:
                profile_failed = True

        if not profile_failed:
            fully_recovered.append(profile.pk)

    if fully_recovered:
        queryset.model.objects.filter(pk__in=fully_recovered).update(account_generation_failed=False)

    modeladmin.message_user(
        request,
        f'Created {created_count} virtual account(s). '
        f'{len(fully_recovered)} profile(s) fully recovered and flag cleared.',
    )

retry_virtual_accounts.short_description = 'Retry virtual account generation'


@admin.register(Profile)
class AdminProfile(admin.ModelAdmin):
    list_display = ['id', 'user', 'phone', 'location', 'state', 'code', 'recommended_by', 'referrals_count', 'reseller', 'account_generation_failed']
    list_filter = ('reseller', 'state', 'account_generation_failed')
    list_editable = ['reseller']
    search_fields = ('user__username', 'user__email', 'phone', 'code', 'recommended_by__username')
    readonly_fields = ['referred_users', 'send_email_link']
    list_per_page = 25
    actions = [retry_virtual_accounts, send_email_action, export_emails_action]

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(_referrals_count=Count('user__ref_by', distinct=True))

    @admin.display(description='Referrals', ordering='_referrals_count')
    def referrals_count(self, obj):
        count = getattr(obj, '_referrals_count', 0)
        if not count:
            return 0
        url = reverse('admin:api_referral_changelist') + f'?recommended_by__id__exact={obj.user_id}'
        return format_html('<a href="{}">{}</a>', url, count)

    @admin.display(description='Email')
    def send_email_link(self, obj):
        email = obj.user.email if obj.user_id else ''
        if not email:
            return 'No email address'
        url = reverse('admin:send-email') + '?' + urlencode({'to': email})
        return format_html('{} &nbsp; <a class="button" href="{}">Send email</a>', email, url)

    @admin.display(description='People this user referred')
    def referred_users(self, obj):
        referred = Profile.objects.filter(recommended_by=obj.user).select_related('user').order_by('-user__date_joined')
        if not referred.exists():
            return '-'
        rows = format_html_join(
            '', '<li>{} ({}) - joined {}</li>',
            ((p.user.username, p.fullName, p.user.date_joined.strftime('%d %b %Y')) for p in referred),
        )
        return format_html('<ul style="margin:0;padding-left:1em">{}</ul>', rows)


@admin.register(Referral)
class ReferralAdmin(admin.ModelAdmin):
    """Everyone who signed up with a referral code, and who referred them."""
    list_display = ['referred_user', 'fullName', 'phone', 'referred_by', 'referrer_code', 'date_joined']
    list_filter = (('user__date_joined', admin.DateFieldListFilter),)
    search_fields = (
        'user__username', 'user__email', 'fullName', 'phone',
        'recommended_by__username', 'recommended_by__email', 'recommended_by__profile__code',
    )
    list_select_related = ('user', 'recommended_by', 'recommended_by__profile')
    ordering = ['-user__date_joined']
    list_per_page = 50

    def get_queryset(self, request):
        return super().get_queryset(request).filter(recommended_by__isnull=False)

    def lookup_allowed(self, lookup, value, request=None):
        # lets the "Referrals" count on Profiles link here filtered by referrer
        if lookup == 'recommended_by__id__exact':
            return True
        return super().lookup_allowed(lookup, value, request) if request is not None else super().lookup_allowed(lookup, value)

    @admin.display(description='User', ordering='user__username')
    def referred_user(self, obj):
        return obj.user.username

    @admin.display(description='Referred by', ordering='recommended_by__username')
    def referred_by(self, obj):
        return obj.recommended_by.username

    @admin.display(description='Referrer code')
    def referrer_code(self, obj):
        profile = getattr(obj.recommended_by, 'profile', None)
        return profile.code if profile else '-'

    @admin.display(description='Joined', ordering='user__date_joined')
    def date_joined(self, obj):
        return obj.user.date_joined

    # read-only list: referrals are created by signup, not by hand
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(Transaction, TransactionMonitorAdmin)


@admin.register(ConfirmPayment)
class ConfirmPaymentAdmin(admin.ModelAdmin):
    list_display = ['profile', 'image']


@admin.register(DepositRecord)
class DepositRecordAdmin(admin.ModelAdmin):
    list_display = ['wallet', 'amount', 'date_and_time', 'gateway', 'status']
    list_filter = ('gateway', 'status', 'date_and_time')
    list_per_page = 25


@admin.register(ReservedAccount)
class ReservedAccountAdmin(admin.ModelAdmin):
    list_display = ['user', 'reservedaccountNumber', 'reservedbankName', 'reservedaccountName', 'accounts']


@admin.register(VirtualAccount)
class VirtualAccountAdmin(admin.ModelAdmin):
    list_display = ['profile', 'bank_name', 'account_number', 'account_name', 'bank_code', 'created_at']
    search_fields = ('profile__user__username', 'account_number', 'bank_name')
    list_filter = ('bank_code',)
    list_per_page = 25


@admin.register(TransactionPin)
class TransactionPinAdmin(admin.ModelAdmin):
    list_display = ['profile', 'pin', 'created_at']
    search_fields = ('profile__user__username',)


@admin.register(CommunityPost)
class CommunityPostAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'is_approved', 'likes', 'created_at']
    list_filter = ('is_approved',)
    list_editable = ['is_approved']
    search_fields = ('title', 'author__username')
    ordering = ['-created_at']
    list_per_page = 25


@admin.register(CommunityPostLike)
class CommunityPostLikeAdmin(admin.ModelAdmin):
    list_display = ['post', 'user']
    search_fields = ('user__username',)


@admin.register(PushNotification)
class PushNotificationAdmin(admin.ModelAdmin):
    list_display = ['title', 'recipient_type', 'recipient_user', 'sent_count', 'sent_by', 'sent_at']
    list_filter = ('recipient_type', 'sent_at')
    search_fields = ('title', 'body', 'sent_by__username')
    readonly_fields = ['sent_at', 'sent_by', 'sent_count']
    ordering = ['-sent_at']
    list_per_page = 25

    fieldsets = (
        ('Notification Content', {
            'fields': ('title', 'body'),
        }),
        ('Recipients', {
            'fields': ('recipient_type', 'recipient_user'),
            'description': 'Choose "All Users" to broadcast, "Resellers Only" to target resellers, or "Specific User" and pick a user.',
        }),
        ('Send Info (auto-filled)', {
            'fields': ('sent_by', 'sent_count', 'sent_at'),
            'classes': ('collapse',),
        }),
    )

    def save_model(self, request, obj, form, change):
        if change:
            # Editing an already-sent notification — do not re-send
            self.message_user(request, 'Saved. Note: editing a sent notification does not re-send it.', level=messages.WARNING)
            super().save_model(request, obj, form, change)
            return

        from fcm_django.models import FCMDevice
        from firebase_admin.messaging import Message, Notification as FCMNotification

        # Build device queryset based on recipient type
        if obj.recipient_type == 'all':
            devices = FCMDevice.objects.filter(active=True)
        elif obj.recipient_type == 'resellers':
            reseller_user_ids = Profile.objects.filter(reseller=True).values_list('user_id', flat=True)
            devices = FCMDevice.objects.filter(user_id__in=reseller_user_ids, active=True)
        elif obj.recipient_type == 'specific':
            if not obj.recipient_user:
                self.message_user(request, 'Please select a specific user before sending.', level=messages.ERROR)
                return
            devices = FCMDevice.objects.filter(user=obj.recipient_user, active=True)
        else:
            devices = FCMDevice.objects.none()

        count = devices.count()
        obj.sent_by = request.user

        if count == 0:
            self.message_user(request, 'No active devices found for the selected recipients. Notification saved but not delivered.', level=messages.WARNING)
            obj.sent_count = 0
            super().save_model(request, obj, form, change)
            return

        # Persist in-app notification for every targeted user before sending FCM
        user_ids = list(devices.values_list('user_id', flat=True).distinct())
        InAppNotification.objects.bulk_create([
            InAppNotification(user_id=uid, title=obj.title, body=obj.body)
            for uid in user_ids
        ])

        try:
            response = devices.send_message(
                make_message(obj.title, obj.body),
                app=settings.FCM_DJANGO_SETTINGS.get('DEFAULT_FIREBASE_APP'),
            )
            success = getattr(response, 'success_count', None)
            failure = getattr(response, 'failure_count', None)

            if success is not None and failure is not None:
                obj.sent_count = success
                super().save_model(request, obj, form, change)
                if failure > 0:
                    errors = [
                        str(r.exception) for r in response.responses if not r.success and r.exception
                    ]
                    self.message_user(
                        request,
                        f'Sent to {success}/{count} device(s). {failure} failed: {"; ".join(errors)}',
                        level=messages.WARNING,
                    )
                else:
                    self.message_user(request, f'Push notification sent to {success} device(s) successfully.', level=messages.SUCCESS)
            else:
                obj.sent_count = count
                super().save_model(request, obj, form, change)
                self.message_user(request, f'Push notification sent to {count} device(s) successfully.', level=messages.SUCCESS)
        except Exception as e:
            obj.sent_count = 0
            super().save_model(request, obj, form, change)
            self.message_user(request, f'Notification saved but delivery failed: {e}', level=messages.ERROR)


@admin.register(InAppNotification)
class InAppNotificationAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'is_read', 'created_at']
    list_filter = ['is_read', 'created_at']
    search_fields = ['user__username', 'title']
    readonly_fields = ['created_at']


# ── Emails sent from admin ───────────────────────────────────────────────────
@admin.register(EmailCampaign)
class EmailCampaignAdmin(admin.ModelAdmin):
    list_display = ['subject', 'kind', 'audience_short', 'status', 'progress', 'created_by', 'created_at']
    list_filter = ('status', 'is_bulk', 'created_at')
    search_fields = ('subject', 'body', 'audience', 'recipients__email')
    readonly_fields = [
        'subject', 'message', 'kind', 'audience', 'status', 'progress', 'recipients_link', 'failures',
        'created_by', 'created_at', 'started_at', 'finished_at',
    ]
    fields = readonly_fields
    actions = ['retry_failed_action', 'resume_action', 'cancel_action']
    change_form_template = 'admin/email_campaign_change_form.html'
    list_per_page = 25

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('created_by')

    # compose page instead of the default add form
    def add_view(self, request, form_url='', extra_context=None):
        from django.http import HttpResponseRedirect as _Redirect
        return _Redirect(reverse('admin:send-email'))

    def has_change_permission(self, request, obj=None):
        # view-only record; actions check the add permission instead
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    @admin.display(description='Type', ordering='is_bulk')
    def kind(self, obj):
        return 'Bulk' if obj.is_bulk else 'Individual'

    @admin.display(description='To')
    def audience_short(self, obj):
        return obj.audience if len(obj.audience) <= 60 else obj.audience[:57] + '...'

    @admin.display(description='Progress')
    def progress(self, obj):
        done = obj.sent_count + obj.failed_count + obj.skipped_count
        parts = [f'{obj.sent_count} sent']
        if obj.failed_count:
            parts.append(format_html('<span style="color:#d64545">{} failed</span>', obj.failed_count))
        if obj.skipped_count:
            parts.append(f'{obj.skipped_count} unsubscribed')
        summary = format_html_join(', ', '{}', ((p,) for p in parts))
        return format_html('{} <span style="color:var(--body-quiet-color,#888)">({} of {})</span>', summary, done, obj.total_recipients)

    @admin.display(description='Message')
    def message(self, obj):
        return format_html('<div style="white-space:pre-wrap;max-width:700px">{}</div>', obj.body)

    @admin.display(description='Recipients')
    def recipients_link(self, obj):
        url = reverse('admin:api_emailrecipient_changelist') + f'?campaign__id__exact={obj.pk}'
        return format_html('<a href="{}">See all {} recipients and their status</a>', url, obj.total_recipients)

    @admin.display(description='Recent errors')
    def failures(self, obj):
        failed = obj.recipients.filter(status='failed').order_by('-id')[:5]
        if not failed:
            return '-'
        return format_html('<ul style="margin:0;padding-left:1em">{}</ul>', format_html_join(
            '', '<li>{}: {}</li>', ((r.email, r.error) for r in failed)))

    def _can_send(self, request):
        return request.user.has_perm('api.add_emailcampaign')

    @admin.action(description='Retry failed recipients')
    def retry_failed_action(self, request, queryset):
        from api import mailer
        if not self._can_send(request):
            raise PermissionDenied
        total = 0
        for campaign in queryset:
            count = mailer.retry_failed(campaign)
            if count:
                total += count
                mailer.start_campaign(campaign.pk)
        self.message_user(request, f'Retrying {total} failed recipient(s).' if total else 'No failed recipients to retry.')

    @admin.action(description='Resume a paused or stopped send')
    def resume_action(self, request, queryset):
        from api import mailer
        if not self._can_send(request):
            raise PermissionDenied
        resumed = 0
        for campaign in queryset:
            if mailer.can_resume(campaign) and campaign.recipients.filter(status='pending').exists():
                mailer.start_campaign(campaign.pk)
                resumed += 1
        self.message_user(request, f'Resumed {resumed} email(s).' if resumed else
                          'Nothing to resume. Emails still actively sending can be resumed 10 minutes after they stop making progress.')

    @admin.action(description='Cancel sending')
    def cancel_action(self, request, queryset):
        if not self._can_send(request):
            raise PermissionDenied
        count = queryset.filter(status__in=['queued', 'sending']).update(status='cancelled', finished_at=timezone.now())
        self.message_user(request, f'Cancelled {count} email(s). Anyone already emailed has received it.')


@admin.register(EmailRecipient)
class EmailRecipientAdmin(admin.ModelAdmin):
    list_display = ['email', 'name', 'status', 'error', 'sent_at', 'campaign']
    list_filter = ('status', 'campaign')
    search_fields = ('email', 'name', 'username')
    list_select_related = ('campaign',)
    list_per_page = 100

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(EmailUnsubscribe)
class EmailUnsubscribeAdmin(admin.ModelAdmin):
    list_display = ['email', 'created_at']
    search_fields = ('email',)


# ── Network ON/OFF switches ──────────────────────────────────────────────────
@admin.register(NetworkStatus)
class NetworkStatusAdmin(admin.ModelAdmin):
    list_display = ['switch', 'is_enabled', 'message', 'plans', 'updated_at', 'updated_by']
    list_display_links = ['switch']
    list_editable = ['is_enabled', 'message']
    fields = ['network', 'is_enabled', 'message', 'updated_at', 'updated_by']
    readonly_fields = ['network', 'updated_at', 'updated_by']
    actions = ['turn_on', 'turn_off']

    @admin.display(description='Network')
    def switch(self, obj):
        return format_html('{} {} &mdash; {}', '🟢' if obj.is_enabled else '🔴', obj.get_network_display(), 'ON' if obj.is_enabled else 'OFF')

    @admin.display(description='Data plans')
    def plans(self, obj):
        total = Data.objects.filter(network=obj.network).count()
        off = Data.objects.filter(network=obj.network, is_active=False).count()
        url = reverse('admin:api_data_changelist') + '?' + urlencode({'network__exact': obj.network})
        return format_html('<a href="{}">{} plan{}{}</a>', url, total, '' if total == 1 else 's', f', {off} off' if off else '')

    def has_add_permission(self, request):
        return False  # the four networks are created automatically

    def changelist_view(self, request, extra_context=None):
        from api.network_control import ensure_network_rows
        ensure_network_rows()
        return super().changelist_view(request, extra_context)

    def has_delete_permission(self, request, obj=None):
        return False

    def save_model(self, request, obj, form, change):
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)

    def _set(self, request, queryset, enabled):
        for status in queryset:
            status.is_enabled = enabled
            status.updated_by = request.user
            status.save(update_fields=['is_enabled', 'updated_by', 'updated_at'])
        names = ', '.join(s.get_network_display() for s in queryset)
        self.message_user(request, f'{names} turned {"ON" if enabled else "OFF"}.', messages.SUCCESS if enabled else messages.WARNING)

    @admin.action(description='Turn selected networks ON')
    def turn_on(self, request, queryset):
        self._set(request, queryset, True)

    @admin.action(description='Turn selected networks OFF')
    def turn_off(self, request, queryset):
        self._set(request, queryset, False)


def network_switch_view(request):
    """POST from the admin home overview: flip one network ON or OFF."""
    from django.http import HttpResponseNotAllowed, HttpResponseRedirect as _Redirect
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    if not request.user.has_perm('api.change_networkstatus'):
        raise PermissionDenied
    from api.network_control import ensure_network_rows
    ensure_network_rows()
    network = request.POST.get('network', '')
    enabled = request.POST.get('enabled') == '1'
    status = NetworkStatus.objects.filter(network=network).first()
    if status is None:
        messages.error(request, 'Unknown network.')
    else:
        status.is_enabled = enabled
        status.updated_by = request.user
        status.save(update_fields=['is_enabled', 'updated_by', 'updated_at'])
        messages.success(request, f'{status.get_network_display()} is now {"ON" if enabled else "OFF"}.')
    from django.utils.http import url_has_allowed_host_and_scheme
    next_url = request.POST.get('next', '')
    if not url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
        next_url = reverse('admin:index')
    return _Redirect(next_url)

