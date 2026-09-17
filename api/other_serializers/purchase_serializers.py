from decimal import Decimal

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
    amount = serializers.DecimalField(max_digits=11, decimal_places=2, min_value=Decimal('50'))
    phone_number = serializers.CharField(max_length=11)

    def validate_amount(self, value):
        # the provider only takes whole naira, so don't charge for kobo it won't deliver
        if value != value.to_integral_value():
            raise ValidationError("Amount must be a whole number.")
        return value

class DataSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=11)

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        exclude = ['user', ]

class PurchaseExamEpinSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=10,decimal_places=2)
    exam_name = serializers.CharField(max_length=10)
    quantity = serializers.CharField(max_length=10)

'''
    Validate and purchase Electricity bill serializer
'''
class ValidateMeterNumberSerializer(serializers.Serializer):
    # CharField so meter numbers starting with 0 keep their leading zero
    meter_number = serializers.RegexField(r'^\d{6,20}$', error_messages={'invalid': 'Meter number must contain only digits.'})
    meter_type = serializers.CharField()
    disco = serializers.CharField()

    def validate_meter_type(self, value):
        value = value.strip().lower()
        if value not in ('prepaid', 'postpaid'):
            raise ValidationError("Meter type must be prepaid or postpaid.")
        return value

class ElectricBillPaymentSerializer(ValidateMeterNumberSerializer):
    amount = serializers.IntegerField()
    phone = serializers.CharField()
    disco = serializers.CharField()
    bypass = serializers.BooleanField(required=False, default=True)
   
    def validate_amount(self, value):
        if value < 300:
            raise ValidationError("Amount must be at least 300.")
        return value


'''
    Validate and purchase Cable subscription serializer
'''
class ValidateCableNumber(serializers.Serializer):
    # CharField so smartcard numbers starting with 0 (e.g. StarTimes) keep their leading zero
    iuc = serializers.RegexField(r'^\d{6,20}$', error_messages={'invalid': 'IUC / smartcard number must contain only digits.'})
    cable_provider = serializers.CharField()

class CablePaymentSerializer(ValidateCableNumber):
    # cable = serializers.IntegerField()
    # iuc = serializers.CharField()
    # bypass = serializers.BooleanField()
    # request_id = serializers.CharField()
    # cable_plan = serializers.CharField()
    pass


'''
Serializer for handling Data Pricing
'''
class DataPriceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Data
        fields = '__all__'