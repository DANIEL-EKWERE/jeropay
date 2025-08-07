from uuid import uuid4
from django.db import models
from django.contrib.auth import get_user_model
# from django_countries.serializer_fields import CountryField
from django_countries.fields import CountryField
from .states import states_in_ng
from .networks import networks_in_ng, data_plans, plan_types
from .electricity_dist import electricity_dist_ng

User = get_user_model()


class SharedInfo(models.Model):
    amount = models.DecimalField(decimal_places=2, max_digits=11)
    
    class Meta:
        abstract = True   

    
class Airtime(SharedInfo):
    id = models.UUIDField(default=uuid4, primary_key=True)
    network = models.CharField(max_length=30,choices=networks_in_ng)
 
    verbose_name = 'Airtime'
    
    def __str__(self):
        return f'{self.network} {self.amount}'


class CableSubscription(models.Model):
    CABLE_PROVIDERS = (
        ('DSTV', 'DSTV'),
        ('GOTV', 'GOTV'),
        ('STARTIMES', 'STARTIMES'),
    )
    CABLE_SERVICES = (
        ('DStv Yanga + ExtraView','DStv Yanga + ExtraView'),
        ('DStv Premium French','DStv Premium French'),
        ('GOtv Max','GOtv Max'),
        ('Classic - 1200 Naira - 1 Week','Classic - 1200 Naira - 1 Week'),
        ('Nova - 900 Naira - 1 Month','Nova - 900 Naira - 1 Month'),
        ('Nova - 90 Naira - 1 Day','Nova - 90 Naira - 1 Day'),
        ('Gotv supa','Gotv supa'),
        ('Smart - 700 Naira - 1 Week','Smart - 700 Naira - 1 Week'),
        ('DStv Compact + Extra View','DStv Compact + Extra View'),
        ('GOtv Smallie - Yearly','GOtv Smallie - Yearly'),
        ('Classic - 320 Naira - 1 Day','Classic - 320 Naira - 1 Day'),
        ('DStv Padi + ExtraView','DStv Padi + ExtraView'),
        ('DStv Compact Plus','DStv Compact Plus'),
        ('ExtraView Access','ExtraView Access'),
        ('Smart - 2,200 Naira - 1 Month','Smart - 2,200 Naira - 1 Month'),
        ('DStv Confam + ExtraView','DStv Confam + ExtraView'),
        ('Nova - 90 Naira - 1 Day','Nova - 90 Naira - 1 Day'),
        ('Basic - 1,700 Naira - 1 Month','Basic - 1,700 Naira - 1 Month'),
        ('DStv Compact','DStv Compact'),
        ('Super - 1,500 Naira - 1 Week','Super - 1,500 Naira - 1 Week'),
        ('DStv Premium Asia','DStv Premium Asia'),
        ('DStv Asia','DStv Asia'),
        ('GOtv Jinja','GOtv Jinja'),
        ('Super - 400 Naira - 1 Day','Super - 400 Naira - 1 Day'),
        ('DStv Confam','DStv Confam'),
        ('DStv Premium + Extra View','DStv Premium + Extra View'),
        ('Super - 4,200 Naira - 1 Month','Super - 4,200 Naira - 1 Month'),
        ('Smart - 200 Naira - 1 Day','Smart - 200 Naira - 1 Day'),
        ('DStv Premium','DStv Premium'),
        ('DStv Compact Plus - Extra View','DStv Compact Plus - Extra View'),
        ('GOtv Smallie - Quarterly','GOtv Smallie - Quarterly'),
        ('Nova - 300 Naira - 1 Week','Nova - 300 Naira - 1 Week'),
        ('Basic - 160 Naira - 1 Day','Basic - 160 Naira - 1 Day'),
        ('Classic - 2,500 Naira - 1 Mont','Classic - 2,500 Naira - 1 Mont'),
        ('GOtv Smallie - Monthly','GOtv Smallie - Monthly'),
        ('Basic - 600 Naira - 1 Week','Basic - 600 Naira - 1 Week'),
        ('GOtv Jolli','GOtv Jolli'),
        ('DStv Padi','DStv Padi'),
        ('DStv HDPVR Access Service','DStv HDPVR Access Service'),
        ('DStv Yanga','DStv Yanga'),
    )

    AMOUNT = (
        (5850,5850),
        (29300,29300),
        (4150,4150),
        (1200,1200),
        (900,900),
        (90,90),
        (5500,5500),
        (700,700),
        (11900,11900),
        (7000,7000),
        (320,320),
        (5050,5050),
        (14250,14250),
        (2950,2950),
        (2600,2600),
        (8200,8200),
        (90,90),
        (1850,1850),
        (9000,9000),
        (1500,1500),
        (23500,23500),
        (7100,7100),
        (1900,1900),
        (400,400),
        (5300,5300),
        (23900,23900),
        (4900,4900),
        (200,200),
        (21000,21000),
        (17150,17150),
        (2400,2400),
        (300,300),
        (160,160),
        (2750,2750),
        (900,900),
        (600,600),
        (2800,2800),
        (2150,2150),
        (2950,2950),
        (4150,4150),
    )
    id = models.UUIDField(default=uuid4, primary_key=True)
    cable_service = models.CharField(max_length=50, choices=CABLE_SERVICES,default='')
    provider = models.CharField(max_length=50, choices=CABLE_PROVIDERS, default='')
    amount = models.DecimalField(max_digits=15, decimal_places=2,choices=AMOUNT, default='')
    plan_id = models.IntegerField(default=0)

    verbose_name = 'Cable Subscription'

    # def __str__(self):
    #     return f'{self.decoder_number}'






# class Referrer(models.Model):
#     user = models.OneToOneField(User, on_delete=models.CASCADE)
#     id = models.UUIDField(default=uuid4, primary_key=True,)
#     date_and_time = models.DateTimeField(auto_now_add=True)


class Profile(models.Model):
    id = models.UUIDField(default=uuid4, primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    location = models.CharField(max_length=100)
    phone = models.CharField(max_length=11)
    fullName = models.CharField(max_length=31, default="N/A")
    reseller = models.BooleanField()
    state = models.CharField(max_length=20, choices=states_in_ng)
    profile_picture = models.ImageField(upload_to='profile-pic/', blank=True)
    
    # New fields for bank details
    bank_name = models.CharField(max_length=100, blank=True)
    account_number = models.CharField(max_length=20, blank=True)
    account_name = models.CharField(max_length=100, blank=True)

    # new fields for referral
    code = models.CharField(max_length=10,default='',blank=True)
    recommended_by = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True, related_name='ref_by')

    #referral = models.ForeignKey(Referrer,on_delete=models.CASCADE,null=True,blank=True,default='')
   # referral_id = models.UUIDField(default=uuid4,)
    verbose_name_ = 'Profile'

    def __str__(self):
        return f'{self.user}'


    def get_recommened_profiles(self):
        qs = Profile.objects.all()
        my_recs = []
        for profile in qs:
            if profile.recommended_by == self.user:
                my_recs.append(profile)
        return my_recs


    def save(self, *args, **kwargs):
        if self.code == '':
            code = self.user.username
            self.code = code
        super().save(*args,**kwargs)

# class Invitee(models.Model):
#     referrer = models.ForeignKey(Referrer, on_delete=models.CASCADE)
#     date_and_time = models.DateTimeField(auto_now_add=True)

class Data(SharedInfo):
    id = models.UUIDField(default=uuid4, primary_key=True)
    # user = models.ForeignKey(Profile, on_delete=models.CASCADE, blank=True,null=True)
    network = models.CharField(max_length=30,choices=networks_in_ng)
    plan_type = models.CharField(max_length=20, choices=plan_types)
    bandwidth = models.CharField(max_length=15, choices=data_plans)
    network_id = models.CharField(max_length=3, default='')
    price_desc = models.CharField(max_length=100, default='')
    data_plan_id = models.CharField(max_length=3, default='')
    reseller_amount = models.DecimalField(decimal_places=2, max_digits=11, default=0.0)
    verbose_name = 'Internet Data'
    
    def __str__(self):
        return f'{self.network}'

    class Meta:
        ordering = ['amount']

class ElectricitySubscription(models.Model):
    id = models.UUIDField(default=uuid4, primary_key=True)
    electric_service = models.CharField(max_length=200, choices=electricity_dist_ng)
    # amount = models.CharField(max_length=10)
    
    verbose_name = 'Electricity Subscription'
    
    def __str__(self):
        return f'{self.meter_number}'

  
    
class Transaction(models.Model):
    status_types = (
        ('Pending', 'Pending'),
        ('Success', 'Success')
    )
    
    transaction_types = (
        ('Data', 'Data'),
        ('Airtime', 'Airtime'),
        ('Cable', 'Cable'),
        ('Electricity', 'Electricity'),
    )
    
    user = models.ForeignKey(User, on_delete= models.CASCADE)
    id = models.UUIDField(default=uuid4, primary_key=True)
    response = models.CharField(max_length=300,default='N/A',blank=True,null=True)
    detail = models.CharField(max_length=300,default='N/A')
    network = models.CharField(max_length=300,default='N/A',blank=True,null=True)
    request_id = models.CharField(max_length=300,default='N/A',blank=True,null=True)
    date_and_time = models.DateTimeField(auto_now_add=True)
    old_balance = models.DecimalField(decimal_places=2, max_digits=11)
    new_balance = models.DecimalField(decimal_places=2, max_digits=11)
    phone_number = models.CharField(max_length=11)
    status = models.CharField(max_length=20, choices=status_types)
    amount = models.DecimalField(decimal_places=2, max_digits=11)
    type = models.CharField(max_length=20, choices=transaction_types)
    
    verbose_name = 'Transaction'
    
    def __str__(self):
        return f'{self.detail}'
    
class Wallet(models.Model):
    id = models.UUIDField(default=uuid4, primary_key=True)
    user = models.OneToOneField(Profile, on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=11, decimal_places=2,default=0.0)
    gateway = models.CharField(max_length=100,default='')
    commission_balance = models.CharField(max_length=100,default='',null=True,blank=True)
    total_deposit = models.DecimalField(max_digits=10,default=0.0,decimal_places=2,null=True,blank=True)
    total_purchase = models.DecimalField(max_digits=10,default=0.0,decimal_places=2,null=True,blank=True)
    
    verbose_name = 'Wallet'
    
    def __str__(self):
        return f'{self.user}'


class DepositRecord(models.Model):
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE)
    id = models.UUIDField(default=uuid4, primary_key=True)
    amount = models.DecimalField(max_digits=11, decimal_places=2)
    date_and_time = models.DateTimeField(auto_now_add=True)
    gateway = models.CharField(max_length=100,default='')
    status = models.CharField(max_length=100,default='')
    reference = models.CharField(max_length=100,default='')
    # user = models.OneToOneField(Profile, on_delete=models.CASCADE, default='',blank=True)
    
class ConfirmPayment(models.Model):
    profile = models.ForeignKey(User, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='confirmation-picture/')

class Deduct(models.Model):
    amount = models.CharField(max_length=100)

class ReservedAccount(models.Model):
    user = models.OneToOneField(User,on_delete=models.CASCADE)
    reservedaccountNumber = models.CharField(max_length=100,blank=True,null=True)
    reservedbankName = models.CharField(max_length=100,blank=True,null=True)
    reservedaccountName = models.CharField(max_length=100,blank=True,null=True)
    accounts = models.BooleanField(default=False)


class Announcement(models.Model):
    body = models.TextField()



class VirtualAccount(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='virtual_accounts')
    bank_name = models.CharField(max_length=100)
    account_number = models.CharField(max_length=20)
    account_name = models.CharField(max_length=100)
    bank_code = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.bank_name} - {self.account_number} ({self.profile.user.username})"
    

class TransactionPin(models.Model):
    profile = models.OneToOneField(Profile, on_delete=models.CASCADE, related_name='transaction_pin')    
    pin = models.CharField(max_length=5)
    created_at = models.DateTimeField(auto_now_add=True)
