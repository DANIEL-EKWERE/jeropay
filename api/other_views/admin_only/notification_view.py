from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from api.utils.push import send_push_to_all
from api.other_serializers.admin.notification_serializer import AnnouncementSerializer


class AnnouncementNotificationView(GenericAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = AnnouncementSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            count = send_push_to_all(
                title=serializer.validated_data['title'],
                body=serializer.validated_data['body'],
            )
            return Response({'announcement': 'sent successfully', 'devices': count}, status=200)
        return Response(data=serializer.errors, status=400)