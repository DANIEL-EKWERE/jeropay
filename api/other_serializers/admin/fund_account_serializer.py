from rest_framework import serializers
from api.models import Wallet

class FundUserAccountSerializer(serializers.ModelSerializer):
    username = serializers.CharField(max_length=300)
    amount = serializers.DecimalField(decimal_places=2, max_digits=11)
    
    class Meta:
        model = Wallet
        exclude = ['balance', 'id', 'user']