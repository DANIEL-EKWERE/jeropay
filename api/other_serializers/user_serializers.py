from rest_framework import serializers
from api.models import ReservedAccount, Announcement
class FCMDeviceIDSerializer(serializers.Serializer):
    device_id = serializers.CharField()
    device_type = serializers.CharField()

class ReserveAcctountSerializer(serializers.Serializer):
    class Meta:
        model = ReservedAccount
        fields = '__all__'

class AnnouncementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Announcement
        fields = '__all__'
