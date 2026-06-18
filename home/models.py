from django.db import models

class AppDownload(models.Model):
    upload_date = models.DateTimeField(auto_now_add=True)
    file = models.FileField(upload_to='app/')


class ContactUs(models.Model):
    fullName = models.CharField(max_length=100,null=False,blank=False)
    emailAddress = models.CharField(max_length=40,null=False,blank=False)
    phoneNumber = models.CharField(max_length=100,null=False,blank=False)
    message = models.TextField(max_length=200,null=False,blank=False)

    def __str__(self):
        return self.fullName