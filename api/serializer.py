from rest_framework import serializers
from .models import Airtime, CableSubscription, Data ,ElectricitySubscription, Profile,Wallet



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