"""DATABANK URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path,include
from rest_framework_simplejwt import views as jwt_views

# static
from django.conf import settings
from django.conf.urls.static import static

# admin decorator
from DATABANK.decorators import admin_whitelist_required

admin.autodiscover()

# admin.site.login = admin_whitelist_required(admin.site.login)

urlpatterns = [
    path('', include('home.urls', namespace='home')),

    # jwt authentication
    path('api/token/', jwt_views.TokenObtainPairView.as_view(), name ='token_obtain_pair'),
    path('api/token/refresh/', jwt_views.TokenRefreshView.as_view(), name ='token_refresh'),

    # api
    path('api/', include('api.urls', namespace='api')),

    path('admin/database/', admin.site.urls),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

urlpatterns += static(settings.MEDIA_URL, document_root= settings.MEDIA_ROOT)