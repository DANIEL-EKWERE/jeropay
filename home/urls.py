from django.urls import path
from django.views.generic import RedirectView

# views
from .views import AboutView, HomeView, DownloadView, PrivacyPolicyView, TermsAndConditionView

app_name='home'

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('about/', AboutView.as_view(), name='about'),
    path('privacy-policy/', PrivacyPolicyView.as_view(), name='privacy-policy'),
    path('terms-and-condition/', TermsAndConditionView.as_view(), name='terms-and-condition'),
    path('download-app/', DownloadView.as_view(), name='download-app'),
    path('download-app.html', RedirectView.as_view(pattern_name='home:download-app', permanent=True)),
]