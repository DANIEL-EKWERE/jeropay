from rest_framework.serializers import ModelSerializer
from api.models import Wallet, Transaction, ConfirmPayment,VirtualAccount

class WalletSerializer(ModelSerializer):
    class Meta:
        model = Wallet
        fields = '__all__'

class VirtualAccountsSerializer(ModelSerializer):
    class Meta:
        model = VirtualAccount
        fields = '__all__'


class TransactionSerializer(ModelSerializer):
    class Meta:
        model = Transaction
        exclude = ['user',]

class ConfirmPaymentSerializer(ModelSerializer):
    class Meta:
        model = ConfirmPayment
        fields = ['image']

class PhoneNumbersSerializer(ModelSerializer):
    class Meta:
        model = Transaction
        fields = ['phone_number']