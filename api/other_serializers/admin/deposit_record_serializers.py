from rest_framework import serializers

from api.models import DepositRecord

class DepositRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = DepositRecord
        fields = '__all__'