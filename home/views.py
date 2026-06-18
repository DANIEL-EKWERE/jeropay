from django.views.generic import TemplateView, ListView
from django.shortcuts import render,redirect, get_object_or_404
# import models
from .models import AppDownload

class HomeView(TemplateView):
    template_name = 'base.html'

class AboutView(TemplateView):
    template_name = 'about.html'

class PrivacyPolicyView(TemplateView):
    template_name = 'privacy-policy.html'

class TermsAndConditionView(TemplateView):
    template_name = 'terms-and-condition.html'

class DownloadView(ListView):
    template_name = 'download-app.html'
    queryset = AppDownload.objects.all().order_by('-upload_date')


def FeedBack(request):
    if request.method == 'POST':
        fullName = request.POST.get('full_name')
        email = request.POST.get('email')
        phoneNumber = request.POST.get('phone')
        message = request.POST.get('message')
        contact_us = ContactUs(fullName=fullName,emailAddress=email,phoneNumber=phoneNumber,message=message)
        contact_us.save()
        return redirect('home')