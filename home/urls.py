from django.urls import path

# views
from .views import HomeView, DownloadView

app_name='home'

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('download-app/', DownloadView.as_view(), name='download-app'),
]