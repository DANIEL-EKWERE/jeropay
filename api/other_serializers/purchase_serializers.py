from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from api.models import Data, Transaction

class DeductAirtimeSerializer(serializers.Serializer):
    network = serializers.CharField(max_length=10)
    amount = serializers.DecimalField(max_digits=11, decimal_places=2)
    phone_number = serializers.CharField(max_length=11)

class DeductDataSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=100)

class AirtimeSerializer(serializers.Serializer):
    network = serializers.CharField(max_length=10)
    amount = serializers.DecimalField(max_digits=11, decimal_places=2)
    phone_number = serializers.CharField(max_length=11)

class DataSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=11)

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        exclude = ['user', ]

class PurchaseExamEpinSerializer(serializers.Serializer):
    network = serializers.CharField(max_length=10)
    exam_name = serializers.CharField(max_length=10)
    quantity = serializers.CharField(max_length=10)

'''
    Validate and purchase Electricity bill serializer
'''
class ValidateMeterNumberSerializer(serializers.Serializer):
    number = serializers.IntegerField()
    type = serializers.CharField()
    disco = serializers.CharField()

class ElectricBillPaymentSerializer(ValidateMeterNumberSerializer):
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
   
    def validate_amount(self, value):
        if value < 300:
            raise ValidationError("Amount must be at least 300.")
        return value


'''
    Validate and purchase Cable subscription serializer
'''
class ValidateCableNumber(serializers.Serializer):
    iuc = serializers.IntegerField()
    cable_provider = serializers.CharField()

class CablePaymentSerializer(ValidateCableNumber):
    pass


'''
Serializer for handling Data Pricing
'''
class DataPriceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Data
        fields = '__all__'