# django
from uuid import uuid4
import random
from django.contrib.auth.models import User
from django.conf import settings
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction as db_transaction

# rest framework imports
from rest_framework.generics import GenericAPIView, ListAPIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, IsAuthenticated

# fcm_django
from fcm_django.models import FCMDevice
from firebase_admin.messaging import Message, Notification

# serializers
from api.other_serializers.admin.fund_account_serializer import FundUserAccountSerializer
from api.other_serializers.admin.deposit_record_serializers import DepositRecordSerializer

# models
from api.models import Profile, Wallet, DepositRecord, Transaction

import json
from django.http import JsonResponse


def create_id():
    return str(random.randint(10, 99)) + str(uuid4())


class FundCustomerAccount(GenericAPIView):
    serializer_class = FundUserAccountSerializer

    def put(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            vd = serializer.validated_data
            username = vd['username']
            amount = vd['amount']

            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                return Response({'status': 'error', 'data': 'User not found'}, status=404)

            try:
                profile = Profile.objects.get(user=user)
            except Profile.DoesNotExist:
                return Response({'status': 'error', 'data': 'No Profile found'}, status=404)

            with db_transaction.atomic():
                wallet = Wallet.objects.select_for_update().get(user=profile)
                old_balance = wallet.balance
                new_balance = old_balance + amount

                Wallet.objects.filter(user=profile).update(
                    balance=new_balance,
                    total_deposit=wallet.total_deposit + amount,
                )

                DepositRecord.objects.create(
                    wallet=wallet,
                    amount=amount,
                    gateway='Wallet Deposit from Admin',
                    status='successful',
                    reference=create_id(),
                )

                # Create a Transaction record so it shows in user history
                Transaction.objects.create(
                    user=user,
                    detail='Admin Credit',
                    network='N/A',
                    response='N/A',
                    request_id='N/A',
                    old_balance=old_balance,
                    new_balance=new_balance,
                    phone_number='N/A',
                    status='Success',
                    amount=amount,
                    type='AdminCredit',
                )

            _send_wallet_push(
                user,
                title='Wallet Funded',
                body=f'Your account has been credited with ₦{amount}. New balance: ₦{new_balance}',
            )

            return Response(
                data={'status': 'success', 'data': f'Updated {user} balance to {new_balance}'},
                status=200,
            )

        return Response(data={'status': 'error', 'data': serializer.errors}, status=400)


def _send_wallet_push(user, title, body):
    try:
        devices = FCMDevice.objects.filter(user=user, active=True)
        if devices.exists():
            devices.send_message(
                Message(notification=Notification(title=title, body=body)),
                app=settings.FCM_DJANGO_SETTINGS['DEFAULT_FIREBASE_APP'],
            )
    except Exception as e:
        print(f'FCM notification failed: {e}')


class DeductCustomerAccount(GenericAPIView):
    serializer_class = FundUserAccountSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]

    def put(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        if not serializer.is_valid():
            return Response({'status': 'error', 'data': serializer.errors}, status=400)

        username = serializer.validated_data['username']
        amount = serializer.validated_data['amount']

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({'status': 'error', 'data': 'User not found'}, status=404)

        try:
            profile = Profile.objects.get(user=user)
        except Profile.DoesNotExist:
            return Response({'status': 'error', 'data': 'No Profile found'}, status=404)

        with db_transaction.atomic():
            wallet = Wallet.objects.select_for_update().get(user=profile)
            old_balance = wallet.balance

            if old_balance < amount:
                return Response(
                    {'status': 'error', 'data': f'Insufficient balance. Current balance: ₦{old_balance}'},
                    status=400,
                )

            new_balance = old_balance - amount
            Wallet.objects.filter(user=profile).update(balance=new_balance)

            Transaction.objects.create(
                user=user,
                detail='Admin Debit',
                network='N/A',
                response='N/A',
                request_id='N/A',
                old_balance=old_balance,
                new_balance=new_balance,
                phone_number='N/A',
                status='Success',
                amount=amount,
                type='AdminDebit',
            )

        _send_wallet_push(
            user,
            title='Wallet Debited',
            body=f'₦{amount} has been deducted from your wallet. New balance: ₦{new_balance}',
        )

        return Response(
            {'status': 'success', 'data': f'Deducted ₦{amount} from {user}. New balance: ₦{new_balance}'},
            status=200,
        )


# @require_POST
# @csrf_exempt
# def payment_webhook(request):
#     try:
#         payload = request.body
#         data = json.loads(payload)

#         reference = data["data"]["reference"]
#         amount = float(data["data"]["amount"])
#         payer_info = data["data"]["payer"]
#         payer_email = payer_info.get("email", None)

#         if DepositRecord.objects.filter(reference=reference).exists():
#             return JsonResponse({"message": "Transaction already exists."}, status=200)

#         user = User.objects.get(email__iexact=payer_email)
#         profile = Profile.objects.get(user=user)

#         with db_transaction.atomic():
#             wallet = Wallet.objects.select_for_update().get(user=profile)
#             old_balance = wallet.balance
#             new_balance = old_balance + amount

#             Wallet.objects.filter(user=profile).update(balance=new_balance)

#             DepositRecord.objects.create(
#                 wallet=wallet,
#                 amount=amount,
#                 gateway='Wallet Transfer Deposit (Webhook)',
#                 status='successful',
#                 reference=reference,
#             )

#             Transaction.objects.create(
#                 user=user,
#                 detail='Wallet Funding via Transfer',
#                 network='N/A',
#                 response='N/A',
#                 request_id=reference,
#                 old_balance=old_balance,
#                 new_balance=new_balance,
#                 phone_number='N/A',
#                 status='Success',
#                 amount=amount,
#                 type='Deposit',
#             )

#         # Send FCM notification
#         try:
#             devices = FCMDevice.objects.filter(user=user)
#             if devices.exists():
#                 devices.send_message(
#                     Message(
#                         notification=Notification(
#                             title='Wallet Funded',
#                             body=f'Your wallet has been credited with ₦{amount}',
#                         )
#                     ),
#                     app=settings.FCM_DJANGO_SETTINGS['DEFAULT_FIREBASE_APP'],
#                 )
#         except Exception as e:
#             print(f'FCM notification failed: {e}')

#         return JsonResponse(
#             {"message": "success", "data": f"Updated {user.email}'s balance to {new_balance}"},
#             status=200,
#         )

#     except User.DoesNotExist:
#         return JsonResponse({"message": "User not found."}, status=404)
#     except Profile.DoesNotExist:
#         return JsonResponse({"message": "Profile not found."}, status=404)
#     except Wallet.DoesNotExist:
#         return JsonResponse({"message": "Wallet not found."}, status=404)
#     except Exception as e:
#         return JsonResponse({"message": f"An error occurred: {str(e)}"}, status=500)

import logging
import json
from decimal import Decimal
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

logger = logging.getLogger(__name__)

@require_POST
@csrf_exempt
def payment_webhook(request):
    try:
        # Log raw request data for debugging
        logger.info("=== BILLSTACK WEBHOOK DEBUG START ===")
        logger.info(f"Request method: {request.method}")
        logger.info(f"Content-Type: {request.content_type}")
        logger.info(f"Raw body: {request.body}")
        
        # Parse the request payload
        payload = request.body
        
        # Check if payload is empty
        if not payload:
            logger.error("Empty payload received")
            return JsonResponse({"message": "Empty payload"}, status=400)
        
        # Try to parse JSON
        try:
            data = json.loads(payload)
            logger.info(f"Parsed JSON: {json.dumps(data, indent=2)}")
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {str(e)}")
            return JsonResponse({"message": "Invalid JSON payload"}, status=400)
        
        # Verify this is a BillStack payment notification
        if data.get("event") != "PAYMENT_NOTIFICATION":
            logger.error(f"Unknown event type: {data.get('event')}")
            return JsonResponse({"message": "Unknown event type"}, status=400)
        
        # Check if required keys exist
        if "data" not in data:
            logger.error(f"Missing 'data' key in payload")
            return JsonResponse({"message": "Missing 'data' key in payload"}, status=400)
        
        webhook_data = data["data"]
        
        # Extract BillStack-specific data based on your actual response structure
        try:
            # Debug: Log the structure of webhook_data
            logger.info(f"webhook_data type: {type(webhook_data)}")
            logger.info(f"webhook_data keys: {list(webhook_data.keys()) if isinstance(webhook_data, dict) else 'Not a dict'}")
            
            reference = webhook_data["reference"]  # R-CFMYTEPGQJ
            merchant_reference = webhook_data["merchant_reference"]  # sna09036507421
            wiaxy_ref = webhook_data["wiaxy_ref"]  # 100004250611101004134551029602
            transaction_ref = webhook_data["transaction_ref"]  # Same as wiaxy_ref
            amount = float(webhook_data["amount"])  # 6750
            created_at = webhook_data["created_at"]  # 2025-06-11 10:10:11
            
            # Account information - Handle potential list
            account_info = webhook_data["account"]
            logger.info(f"account_info type: {type(account_info)}")
            
            if isinstance(account_info, list):
                logger.info("account_info is a list, taking first item")
                account_info = account_info[0] if len(account_info) > 0 else {}
            elif not isinstance(account_info, dict):
                logger.error(f"account_info is neither list nor dict: {type(account_info)}")
                account_info = {}
            
            account_number = account_info.get("account_number", "")
            account_name = account_info.get("account_name", "")
            bank_name = account_info.get("bank_name", "")
            
            # Payer information - Handle as list
            payer_info = webhook_data["payer"]
            logger.info(f"payer_info type: {type(payer_info)}")
            logger.info(f"payer_info content: {payer_info}")
            
            if isinstance(payer_info, list):
                logger.info("payer_info is a list, taking first item")
                payer_info = payer_info[0] if len(payer_info) > 0 else {}
            elif not isinstance(payer_info, dict):
                logger.error(f"payer_info is neither list nor dict: {type(payer_info)}")
                payer_info = {}
                
            payer_account_number = payer_info.get("account_number", "")
            payer_account_name = payer_info.get("account_name", "")
            
            # Customer information - Handle potential list
            customer_info = webhook_data["customer"]
            logger.info(f"customer_info type: {type(customer_info)}")
            
            if isinstance(customer_info, list):
                logger.info("customer_info is a list, taking first item")
                customer_info = customer_info[0] if len(customer_info) > 0 else {}
            elif not isinstance(customer_info, dict):
                logger.error(f"customer_info is neither list nor dict: {type(customer_info)}")
                customer_info = {}
                
            customer_first_name = customer_info.get("firstName", "").strip()
            customer_last_name = customer_info.get("lastName", "").strip()
            customer_email = customer_info.get("email", "").strip()
            
            logger.info(f"BillStack Transaction - Ref: {reference}, Amount: {amount}")
            logger.info(f"Account: {account_name} ({account_number})")
            logger.info(f"Customer: {customer_first_name} {customer_last_name} ({customer_email})")
            
        except KeyError as e:
            logger.error(f"Missing required field in BillStack payload: {e}")
            return JsonResponse({"message": f"Missing field: {e}"}, status=400)
        except (ValueError, TypeError) as e:
            logger.error(f"Data conversion error: {e}")
            logger.error(f"webhook_data: {webhook_data}")
            return JsonResponse({"message": f"Invalid data format: {e}"}, status=400)
        
        # Check if the transaction already exists
        if DepositRecord.objects.filter(reference=transaction_ref).exists():
            logger.info(f"Transaction {reference} already processed")
            return JsonResponse({"message": "Transaction already processed"}, status=200)
        
        # Find user - now we have email from customer info!
        user = None
        
        # Method 1: Try to find user by customer email (most reliable)
        try:
            user = User.objects.get(email__iexact=customer_email)
            logger.info(f"Found user by customer email: {user.email}")
        except User.DoesNotExist:
            logger.warning(f"User not found by email: {customer_email}")
        
        # Method 2: Try to find user by merchant_reference if email fails
        if not user:
            try:
                if "@" in merchant_reference:
                    user = User.objects.get(email__iexact=merchant_reference)
                else:
                    user = User.objects.get(username__iexact=merchant_reference)
                logger.info(f"Found user by merchant_reference: {user.email}")
            except User.DoesNotExist:
                pass
        
        # Method 3: Try to find user by customer name
        if not user:
            try:
                user = User.objects.filter(
                    first_name__iexact=customer_first_name,
                    last_name__iexact=customer_last_name
                ).first()
                if user:
                    logger.info(f"Found user by customer name: {user.email}")
            except Exception as e:
                logger.error(f"Error matching by customer name: {e}")
        
        if not user:
            logger.error(f"No user found for customer: {customer_email}, name: {customer_first_name} {customer_last_name}")
            return JsonResponse({
                "message": "User not found", 
                "customer_email": customer_email,
                "customer_name": f"{customer_first_name} {customer_last_name}",
                "merchant_reference": merchant_reference
            }, status=404)
        
        # Get user's profile and wallet
        try:
            profile = Profile.objects.get(user=user)
            wallet = Wallet.objects.get(user=profile)
        except Profile.DoesNotExist:
            logger.error(f"Profile not found for user: {user.email}")
            return JsonResponse({"message": "Profile not found"}, status=404)
        except Wallet.DoesNotExist:
            logger.error(f"Wallet not found for user: {user.email}")
            return JsonResponse({"message": "Wallet not found"}, status=404)
        
        # Handle Decimal and Float conversion properly
        # Convert both to Decimal for precision
        old_balance = Decimal(str(wallet.balance or 0))
        original_amount = Decimal(str(amount))
        
        # Calculate 1% fee
        fee_percentage = Decimal('0.01')  # 1%
        processing_fee = original_amount * fee_percentage
        amount_after_fee = original_amount - processing_fee
        
        new_balance = old_balance + amount_after_fee
        
        logger.info(f"Original amount: {float(original_amount)}")
        logger.info(f"Processing fee (1%): {float(processing_fee)}")
        logger.info(f"Amount after fee: {float(amount_after_fee)}")
        
        # Convert to float for logging/response
        old_balance_float = float(old_balance)
        new_balance_float = float(new_balance)
        amount_after_fee_float = float(amount_after_fee)
        processing_fee_float = float(processing_fee)
        
        logger.info(f"Updating balance from {old_balance_float} to {new_balance_float}")
        
        # Update wallet balance with amount after fee
        Wallet.objects.filter(user=profile).update(balance=new_balance)
        
        # Save the transaction in DepositRecord (with original amount and fee info)
        DepositRecord.objects.create(
            wallet=wallet,
            amount=amount_after_fee,  # Amount after fee
            gateway="BillStack Bank Transfer",
            status="successful",
            reference=reference,
        )
        
        # Create transaction record
        Transaction.objects.create(
            user=user,
            detail=f'Bank Transfer from {customer_first_name} {customer_last_name} via {bank_name} (Fee: {processing_fee_float})',
            network=bank_name,
            response='Successful',
            request_id=reference,
            old_balance=old_balance_float,
            new_balance=new_balance_float,
            phone_number='N/A',
            status='success',
            amount=amount_after_fee_float,  # Amount after fee
            type='Deposit',
        )

        # Send FCM notification
        try:
            devices = FCMDevice.objects.filter(user=user)
            if devices.exists():
                devices.send_message(
                    Message(
                        notification=Notification(
                            title='Wallet Funded',
                            body=f'Your wallet has been credited with ₦{amount}',
                        )
                    ),
                    app=settings.FCM_DJANGO_SETTINGS['DEFAULT_FIREBASE_APP'],
                )
        except Exception as e:
            print(f'FCM notification failed: {e}')

        return JsonResponse(
            {"message": "success", "data": f"Updated {user.email}'s balance to {new_balance}"},
            status=200,
        )
        
        logger.info(f"Successfully processed BillStack payment: {reference}")
        
        # Send a success response
        return JsonResponse({
            "message": "success",
            "data": f"Updated {user.email}'s wallet balance by {amount_after_fee_float} (Original: {float(original_amount)}, Fee: {processing_fee_float})",
            "reference": reference,
            "original_amount": float(original_amount),
            "processing_fee": processing_fee_float,
            "amount_credited": amount_after_fee_float,
            "new_balance": new_balance_float,
            "customer_email": customer_email
        }, status=200)
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {str(e)}")
        return JsonResponse({"message": "Invalid JSON payload"}, status=400)
    
    except Exception as e:
        logger.error(f"Unexpected BillStack webhook error: {str(e)}", exc_info=True)
        return JsonResponse({"message": f"An error occurred: {str(e)}"}, status=500)


class DisplayDepositRecordsView(ListAPIView):
    serializer_class = DepositRecordSerializer
    queryset = DepositRecord.objects.all()


class DisplayDepositRecordsPerUserView(ListAPIView):
    serializer_class = DepositRecordSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    queryset = DepositRecord.objects.all()
    lookup_field = 'id'

    def get_queryset(self):
        return DepositRecord.objects.filter(id=self.kwargs['id']).order_by('amount')
