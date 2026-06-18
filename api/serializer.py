from rest_framework import serializers
from .models import Airtime, CableSubscription, Data ,ElectricitySubscription, Profile,Wallet
#from django_rest_passwordreset.views import ResetPasswordRequestToken
from django_rest_passwordreset.serializers import  EmailSerializer
from django_rest_passwordreset.models import ResetPasswordToken

class CableSubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CableSubscription
        ordering = ['amount']
        fields = ['id', 'cable_service', 'amount','provider','plan_id']
        

class DataSerializer(serializers.ModelSerializer):
    class Meta:
        model = Data
        fields = '__all__'
            
class ElectricitySubscriptionSerializer(serializers.Serializer):
    id = serializers.UUIDField(format='hex_verbose')
    electric_service = serializers.CharField(max_length=50)
    meter_number = serializers.CharField(max_length=20)
    meter_type = serializers.CharField(max_length=20)
    amount = serializers.CharField(max_length=30)
    
    class Meta:
        ordering = ['electric_service']

class ProfileSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Profile
        fields = ['id', 'user', 'location', 'phone', 'reseller', 'state'] 

class WalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wallet
        fields = ['id', 'user', 'balance']


# class CustomResetPasswordView(ResetPasswordRequestToken):
#     pass

class CustomPasswordResetSerializer(EmailSerializer):

    #token = serializers.EmailField()

    def save(self):
        #reset_password_token = super().save()
        request = self.context.get('request')
        email = self.validated_data['email']

        super().save()

        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            user = User.objects.get(email=email)
            token = ResetPasswordToken.objects.filter(user=user).first()

            if token:
                self.context['reset_token'] = token.key
        except User.DoesNotExist: 
            pass

       