from django.contrib import admin
from .models import AppDownload , ContactUs

@admin.register(AppDownload)
class AppDownloadAdmin(admin.ModelAdmin):
    list_display = ['upload_date',]

@admin.register(ContactUs)
class AppDownloadAdmin(admin.ModelAdmin):
    list_display = ['fullName',
                    'emailAddress',
                    'phoneNumber',        
                    ]
