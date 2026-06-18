from rest_framework import serializers

class AnnouncementSerializer(serializers.Serializer):
    title = serializers.CharField()
    body = serializers.CharField()