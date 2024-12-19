from django.conf import settings
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from fcm_django.models import FCMDevice
from firebase_admin.messaging import Message, Notification


# serializers
from api.other_serializers.admin.notification_serializer import AnnouncementSerializer

class AnnouncementNotificationView(GenericAPIView):
    permission_classes = [IsAdminUser, ]
    queryset = FCMDevice.objects.all()
    serializer_class = AnnouncementSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        
        if serializer.is_valid():
            valid_data = serializer.validated_data

            FCMDevice.objects.send_message(
                message=Message(
                    notification=Notification(
                        title=valid_data['title'],
                        body=valid_data['body']
                    )
                ),
                app=settings.FCM_DJANGO_SETTINGS['DEFAULT_FIREBASE_APP']
            )
            return Response(
                {"announcement":"sent successfully"},
                status=200
            )
        return Response(
            data=serializer.errors,
            status=400
        )