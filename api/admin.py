from django.contrib import admin
from django.utils.html import format_html
from django.conf import settings
from django.contrib import messages
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
)


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
    list_display = ['network', 'network_id', 'plan_type', 'bandwidth', 'amount', 'reseller_amount', 'price_desc']
    search_fields = ('bandwidth',)
    list_editable = ['bandwidth', 'amount', 'reseller_amount']


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
    list_display = ['id', 'user', 'phone', 'location', 'state', 'reseller', 'account_generation_failed']
    list_filter = ('reseller', 'state', 'account_generation_failed')
    list_editable = ['reseller']
    search_fields = ('user__username', 'user__email', 'phone')
    list_per_page = 25
    actions = [retry_virtual_accounts]


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['user', 'amount', 'type', 'status', 'date_and_time']
    list_filter = ('type', 'status', 'date_and_time')
    search_fields = ('user__username', 'user__email', 'detail', 'phone_number')
    ordering = ['-date_and_time']
    list_per_page = 25


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
