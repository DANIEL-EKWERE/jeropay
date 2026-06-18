from rest_framework import serializers
from api.models import ReservedAccount, Announcement
class FCMDeviceIDSerializer(serializers.Serializer):
    registration_id = serializers.CharField()           # FCM token
    device_id = serializers.CharField(default='')       # hardware device ID
    device_type = serializers.CharField(default='android')

class ReserveAcctountSerializer(serializers.Serializer):
    class Meta:
        model = ReservedAccount
        fields = '__all__'

class AnnouncementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Announcement
        fields = '__all__'
