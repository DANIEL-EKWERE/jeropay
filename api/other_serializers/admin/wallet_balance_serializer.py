from rest_framework import serializers

from api.models import Wallet

class CustomerWalletBalanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wallet
        fields = '__all__'

class UserWalletBalanceSerializer(serializers.Serializer):
    balance = serializers.CharField()