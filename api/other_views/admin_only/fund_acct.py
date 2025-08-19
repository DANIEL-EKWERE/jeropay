# django
from django.contrib.auth.models import User
from django.conf import settings
from django.views.decorators.http import require_POST
import random
from django.views.decorators.csrf import csrf_exempt

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

class FundCustomerAccount(GenericAPIView):
    serializer_class = FundUserAccountSerializer
    # permission_classes = [IsAuthenticated, IsAdminUser,]

    def put(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            vd = serializer.validated_data
            username = vd['username']
            amount = vd['amount']

            user = User.objects.get(username=username)
            try:
                profile = Profile.objects.get(user=user)

            except:
                return Response(
                    data={
                    'status':'error',
                    'data': 'No Profile found'
                    },
                    status=404
                )
            wallet = Wallet.objects.get(user=profile)
            
            new_balance = wallet.balance + amount
            Wallet.objects.filter(user=profile).update(balance=new_balance)

            deposit = wallet.total_deposit + amount
            Wallet.objects.filter(user=profile).update(total_deposit=deposit)

            

            # # create the new Deposit Record
            # def create_id():
            #     num = random.randint(1, 10)
            #     num_2 = random.randint(1, 10)
            #     num_3 = random.randint(1, 10)
            #     return str(num_2)+str(num_3)+str(uuid.uuid4())


            DepositRecord.objects.create(
                wallet = wallet,
                amount=amount,
                gateway='Wallet Deposit from Admin',
                status='successfull',
                reference= create_id(),
            )

            # Send a notification
            devices = FCMDevice.objects.filter(user=user.id)
            devices.send_message(
                message =Message(
                    notification=Notification(
                        title='Wallet Deposit from Admin',
                        body=f'Success🎉 Your account has been funded with ₦{amount}'
                    ),
                    token=FCMDevice.objects.get(user=user.id).device_id,
                ),

                app=settings.FCM_DJANGO_SETTINGS['DEFAULT_FIREBASE_APP']
            )

            return Response(data={
                'status': 'success', 
                'data': f'updated {user} Balance to {new_balance}'
                },
                status=200)
        else:
            return Response(
                data={
                'status': 'error', 
                'data': serializer.errors
                },
                status=400
            )

# def create_id():
#                 num = random.randint(1, 10)
#                 num_2 = random.randint(1, 10)
#                 num_3 = random.randint(1, 10)
#                 return str(num_2)+str(num_3)+str(uuid.uuid4())

'''  PYTHON DJANGO SAMPLE WEBHOOK  '''

# @require_POST
# @csrf_exempt
# def payvessel_payment_done(request):
#         payload = request.body
#         payvessel_signature = request.META.get('HTTP_PAYVESSEL_HTTP_SIGNATURE')
#         #this line maybe be differ depends on your server
#         #ip_address = u'{}'.format(request.META.get('HTTP_X_FORWARDED_FOR'))
#         #ip_address = u'{}'.format(request.META.get('REMOTE_ADDR'))
#         secret = bytes("PVSECRET-", 'utf-8')
#         hashkey = hmac.new(secret,request.body, hashlib.sha512).hexdigest()
#         if payvessel_signature == hashkey:
#                 data = json.loads(payload)
#                 print(data)
#                 amount = float(data['order']["amount"])
#                 settlementAmount = float(data['order']["settlement_amount"])
#                 fee = float(data['order']["fee"])
#                 reference = data['transaction']["reference"]
#                 description = data['order']["description"]
#                 settlementAmount = settlementAmount 
#                 paynow = (round(amount - fee))
                
#                 ###check if reference already exist in your payment transaction table   
#                 if not DepositRecord.objects.filter(reference=reference).exists():
                   
#                     #fund user wallet here
#                     email = data["eventData"]["customer"]["email"]
#                     user = User.objects.get(email__iexact=email)
#                     try:
#                         profile = Profile.objects.get(user=user)

#                     except:
#                         return Response(
#                             data={
#                             'status':'error',
#                             'data': 'No Profile found'
#                             },
#                             status=404
#                         )
#                     wallet = Wallet.objects.get(user=profile)
                    
#                     new_balance = wallet.balance + paynow
#                     # deposit = wallet.total_deposit + paynow
#                     Wallet.objects.filter(user=profile).update(balance=new_balance)
#                     #Wallet.objects.filter(user=profile).update(total_deposit=deposit)
#                     DepositRecord.objects.create(
#                     wallet = wallet,
#                     amount=amount,
#                     gateway='Wallet Transfer Deposit (payvessel)',
#                     status='successfull',
#                     reference=reference,
#                     )



#                     # Send a notification
#                     # devices = FCMDevice.objects.filter(user=user.id)
#                     # devices.send_message(
#                     #     message =Message(
#                     #         notification=Notification(
#                     #             title='Wallet Transfer Deposit',
#                     #             body=f'Success🎉 Your account has been funded with ₦{paynow}'
#                     #         ),
#                     #         token=FCMDevice.objects.get(user=user.id).device_id,
#                     #     ),

#                     #     app=settings.FCM_DJANGO_SETTINGS['DEFAULT_FIREBASE_APP']
#                     # )


#                     return JsonResponse({"message": "success",'data': f'updated {user} Balance to {paynow}'},status=200) 
                        
#                 else:
#                     return JsonResponse({"message": "transaction already exist",},status=200) 
        
#         else:
#             return JsonResponse({"message": "Permission denied, invalid hash or ip address.",},status=400)




@require_POST
@csrf_exempt
def payment_webhook(request):
    try:
        # Parse the request payload
        payload = request.body
        data = json.loads(payload)

        # Extract data from the payload
        reference = data["data"]["reference"]
        amount = float(data["data"]["amount"])  # Payment amount
        payer_info = data["data"]["payer"]
        payer_email = payer_info.get("email", None)  # Assuming email is in the payload

        # Check if the reference already exists in `DepositRecord`
        if DepositRecord.objects.filter(reference=reference).exists():
            return JsonResponse({"message": "Transaction already exists."}, status=200)

        # Get the user and their wallet
        user = User.objects.get(email__iexact=payer_email)
        profile = Profile.objects.get(user=user)
        wallet = Wallet.objects.get(user=profile)

        # Update wallet balance
        new_balance = wallet.balance + amount
        balance = Wallet.objects.filter(user=profile).balance
        Wallet.objects.filter(user=profile).update(balance=new_balance)

        # Save the transaction in `DepositRecord`
        DepositRecord.objects.create(
            wallet=wallet,
            amount=amount,
            gateway="Wallet Transfer Deposit (Webhook)",
            status="successful",
            reference=reference,
        )

        Transaction.objects.create(
                    user=request.user,
                    detail= 'Not Applicable',
                    network='Not Applicable',
                    response='Not Applicable',
                    request_id='Not Applicable',
                    old_balance=balance,
                    new_balance= balance + amount,
                    phone_number='Not Applicable',
                    status='succes',
                    amount= amount,
                    type= 'Deposit',
                )

        # Send a success response
        return JsonResponse(
            {
                "message": "success",
                "data": f"Updated {user.email}'s wallet balance by {amount}",
            },
            status=200,
        )

    except User.DoesNotExist:
        return JsonResponse({"message": "User not found."}, status=404)

    except Profile.DoesNotExist:
        return JsonResponse({"message": "Profile not found."}, status=404)

    except Wallet.DoesNotExist:
        return JsonResponse({"message": "Wallet not found."}, status=404)

    except Exception as e:
        return JsonResponse({"message": f"An error occurred: {str(e)}"}, status=500)

        
class DisplayDepositRecordsView(ListAPIView):
    serializer_class = DepositRecordSerializer
    # permission_classes = [IsAuthenticated, IsAdminUser]
    queryset = DepositRecord.objects.all()

class DisplayDepositRecordsPerUserView(ListAPIView):
    serializer_class = DepositRecordSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    queryset = DepositRecord.objects.all()
    lookup_field = 'id'

    def get_queryset(self):
        return DepositRecord.objects.filter(id=self.kwargs['id']).order_by('amount')

    # def get(request, username, *args, **kwargs):
    #     user = get_user_model
    #     user.username
        # Wallet = DepositRecord.objects.filter(wallet=)