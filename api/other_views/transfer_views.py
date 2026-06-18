from django.db import transaction as db_transaction
from django.contrib.auth.models import User
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from api.models import Wallet, Profile, Transaction, TransactionPin
from api.other_serializers.purchase_serializers import TransactionSerializer
from api.other_views.purchase_views import _send_push


class WalletToWalletTransferView(GenericAPIView):
    """
    POST /api/transfer/wallet-to-wallet/
    Body: { "recipient_username": "john", "amount": 500, "pin": "1234" }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        recipient_username = request.data.get('recipient_username', '').strip()
        pin = request.data.get('pin', '').strip()
        try:
            amount = float(request.data.get('amount', 0))
        except (TypeError, ValueError):
            return Response({'status': 'error', 'message': 'Invalid amount'}, status=400)

        if not recipient_username or not pin:
            return Response({'status': 'error', 'message': 'recipient_username and pin are required'}, status=400)
        if amount <= 0:
            return Response({'status': 'error', 'message': 'Amount must be greater than 0'}, status=400)
        if request.user.username == recipient_username:
            return Response({'status': 'error', 'message': 'Cannot transfer to yourself'}, status=400)

        # Verify sender PIN
        try:
            sender_profile = Profile.objects.get(user=request.user)
            sender_pin = TransactionPin.objects.get(profile=sender_profile)
        except (Profile.DoesNotExist, TransactionPin.DoesNotExist):
            return Response({'status': 'error', 'message': 'Your profile or PIN not found'}, status=400)

        if sender_pin.pin != pin:
            return Response({'status': 'error', 'message': 'Incorrect transaction PIN'}, status=400)

        # Verify recipient exists
        try:
            recipient_user = User.objects.get(username=recipient_username)
            recipient_profile = Profile.objects.get(user=recipient_user)
        except (User.DoesNotExist, Profile.DoesNotExist):
            return Response({'status': 'error', 'message': f'User "{recipient_username}" not found'}, status=404)

        with db_transaction.atomic():
            sender_wallet = Wallet.objects.select_for_update().get(user=sender_profile)
            recipient_wallet = Wallet.objects.select_for_update().get(user=recipient_profile)

            if sender_wallet.balance < amount:
                return Response({'status': 'error', 'message': 'Insufficient wallet balance'}, status=400)

            sender_old_balance = sender_wallet.balance
            recipient_old_balance = recipient_wallet.balance

            sender_wallet.balance -= amount
            sender_wallet.save(update_fields=['balance'])

            recipient_wallet.balance += amount
            recipient_wallet.save(update_fields=['balance'])

            # Debit record for sender
            sender_trans = Transaction.objects.create(
                user=request.user,
                detail=f'Transfer to {recipient_username}',
                old_balance=sender_old_balance,
                new_balance=sender_wallet.balance,
                amount=amount,
                status='Success',
                type='Transfer',
            )

            # Credit record for recipient
            Transaction.objects.create(
                user=recipient_user,
                detail=f'Transfer from {request.user.username}',
                old_balance=recipient_old_balance,
                new_balance=recipient_wallet.balance,
                amount=amount,
                status='Success',
                type='Transfer',
            )

        _send_push(request.user, 'Transfer Sent', f'₦{amount:,.0f} sent to {recipient_username}')
        _send_push(recipient_user, 'Transfer Received', f'₦{amount:,.0f} received from {request.user.username}')

        return Response({
            'status': 'success',
            'message': f'₦{amount:,.0f} transferred to {recipient_username}',
            'new_balance': sender_wallet.balance,
            'transaction': TransactionSerializer(sender_trans).data,
        }, status=200)
