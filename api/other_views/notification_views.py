from decimal import Decimal
from django.db.models import F
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import serializers

from api.models import InAppNotification, Profile, Wallet


class InAppNotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = InAppNotification
        fields = ['id', 'title', 'body', 'is_read', 'created_at']


class InAppNotificationListView(GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        notifications = InAppNotification.objects.filter(user=request.user)
        data = InAppNotificationSerializer(notifications, many=True).data
        unread_count = notifications.filter(is_read=False).count()
        return Response({'status': 'success', 'unread_count': unread_count, 'data': data})


class InAppNotificationMarkReadView(GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        updated = InAppNotification.objects.filter(pk=pk, user=request.user).update(is_read=True)
        if not updated:
            return Response({'status': 'error', 'message': 'Notification not found'}, status=404)
        return Response({'status': 'success'})


class InAppNotificationMarkAllReadView(GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        InAppNotification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return Response({'status': 'success'})


class CompleteGoogleProfileView(GenericAPIView):
    """
    Called after Google sign-up (201) to collect phone, username, address, referral code.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        phone = request.data.get('phone', '').strip()
        username = request.data.get('username', '').strip()
        address = request.data.get('address', '').strip()
        referred_by = request.data.get('referred_by', '').strip()

        if not phone:
            return Response({'status': 'error', 'message': 'Phone number is required'}, status=400)

        from django.contrib.auth import get_user_model
        User = get_user_model()

        user = request.user

        # Update username if provided and not taken
        if username and username != user.username:
            if User.objects.filter(username=username).exclude(pk=user.pk).exists():
                return Response({'status': 'error', 'message': 'Username already taken'}, status=400)
            user.username = username
            user.save(update_fields=['username'])

        # Update profile
        try:
            profile = Profile.objects.get(user=user)
        except Profile.DoesNotExist:
            return Response({'status': 'error', 'message': 'Profile not found'}, status=404)

        profile.phone = phone
        if address:
            profile.location = address
        profile.save(update_fields=['phone', 'location'])

        # Apply referral bonus
        if referred_by:
            try:
                ref_profile = Profile.objects.get(code=referred_by)
                if ref_profile.user != user:
                    Wallet.objects.filter(user=ref_profile).update(
                        commission_balance=F('commission_balance') + Decimal('3.00')
                    )
                    profile.recommended_by = ref_profile.user
                    profile.save(update_fields=['recommended_by'])
            except Profile.DoesNotExist:
                pass

        return Response({'status': 'success', 'message': 'Profile updated'})
