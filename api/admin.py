from django.contrib import admin

# Register your models here.
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
     )


@admin.register(Announcement)
class AdminAnnouncement(admin.ModelAdmin):
     list_display = [
          'body'
     ]

@admin.register(Airtime)
class AdminAirtime(admin.ModelAdmin):
     list_display = [ 
                    'id',
                    'network',
                    'amount',
                    ]
     
     search_fields = ('network',)


@admin.register(CableSubscription)
class AdminCableSubscription(admin.ModelAdmin):
     list_display = [ 
                    'cable_service',
                    'provider',
                    'amount',
                    'plan_id'
                    ]
     
     search_fields = ('decoder_number',)
     list_editable = [
          'provider', 
          'plan_id']

@admin.register(Data)
class AdminData(admin.ModelAdmin):
     list_display = [ 
                    'network',
                    'network_id',
                    'plan_type',
                    'bandwidth',
                    'amount',
                    'reseller_amount',
                    'price_desc',
                    ]
     
     search_fields = ('bandwidth',)
     list_editable = ['bandwidth', 'amount', 'reseller_amount']


@admin.register(ElectricitySubscription)
class AdminElectricitySubscription(admin.ModelAdmin):
     list_display = [ 
                    'id',
                    'electric_service',
                    ]
     search_fields = ('meter_number',)
     

@admin.register(Wallet)
class AdminWallet(admin.ModelAdmin):
     list_display = [ 
                    'id',
                    'user',
                    'balance',
                    'gateway',
                    ]


@admin.register(Profile)
class AdminProfile(admin.ModelAdmin):
    list_display = [ 
                    'id',
                    'user',
                    'location',
                    'phone',
                    'reseller',
                    'state',
                    ]
    list_filter = ('user',)
    
@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
     list_display = [
          'user',
          'status',
          'type',
          'date_and_time'
     ]

     search_fields = [
          'type',
     ]

     ordering = ['-date_and_time']
     

@admin.register(ConfirmPayment)
class ConfirmPaymentAdmin(admin.ModelAdmin):
     list_display = [
          'profile',
          'image',
     ]

@admin.register(DepositRecord)
class DepositRecordAdmin(admin.ModelAdmin):
     list_display = [
          'wallet', 
          'amount', 
          'date_and_time',
          'gateway',
          'status',
          
     ]


@admin.register(ReservedAccount)
class ReservedAccountAdmin(admin.ModelAdmin):
     list_display=[
          'user',
          'reservedaccountNumber',
          'reservedbankName',
          'reservedaccountName',
          'accounts',
     ]

# @admin.register(Deduct)
# class DeductdAdmin(admin.ModelAdmin):
#      list_display = [
#           'amount',
          
#      ]

