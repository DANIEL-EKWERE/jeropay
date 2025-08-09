import logging
from uuid import uuid4

from django.conf import settings

# rest framework Modules
from rest_framework.generics import GenericAPIView, ListAPIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

# requests
import requests, json, urllib3

# models
from api.models import Transaction, Data, Profile, CableSubscription, Wallet

# serializers
from api.other_serializers.purchase_serializers import (
    TransactionSerializer,
    AirtimeSerializer,
    DataSerializer,
    DeductAirtimeSerializer,
    DeductDataSerializer,
    PurchaseExamEpinSerializer,

    # electricity bills
    ValidateMeterNumberSerializer,
    ElectricBillPaymentSerializer,

    # cable tv
    ValidateCableNumber,
    CablePaymentSerializer,

    # price
    DataPriceSerializer,
    )

# wallet
from api.other_views.mixins.wallet_check_mixins import WalletCheckMixin

# constants
from api.constants import (
    EXAM_RESULT_CHECKER,
    NETWORK_ID, 
    ELECTRIC_DISCO_ID,
    CABLE_PROVIDER_ID,
    KVDATA_BASE_URL,
    KVDATA_PROVIDER_TOKEN,
    API_BASE_URL,
    API_PROVIDER_TOKEN,

    RequestWrapper
    )

logger = logging.getLogger(__name__)

"""
Section for purchasing Services i.e airtime, data, elect, etc
"""

'''
me testing here below
'''

class DeductTest(WalletCheckMixin, GenericAPIView):
    serializer_class = DeductAirtimeSerializer
    permission_classes = (IsAuthenticated,)
    def get(self, request, *args, **kwargs):
        return Response({'success':'deduct api received'},status=200)

    def post(self, request, *args, **kwargs):
        amount = 200
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            vd = serializer.validated_data
            phone_number = vd['phone_number']
            network = vd['network'].upper()
            amount = vd['amount']
            wallet = self.check_wallet_balance(amount=amount)

            
            message = f'You have purchased {amount} airtime from {network}'
            
            balances = self.deduct_amount_from_balance(amount=amount)

            trans = Transaction.objects.create(
                user=request.user,
                detail= message,
                old_balance=balances[0],
                new_balance= balances[1],
                phone_number=phone_number,
                status='Success',
                amount=amount,
                type= 'Airtime',
            )

            trans_serializer = TransactionSerializer(trans).data

            return Response(
                data={
                    'status': 'success',
                    'data': trans_serializer
                },
                status=200
            )
        return Response(
            data={
                'status': 'error',
                'message': response.json()
            },
        status=400
        )

            # return Response({"success":"purchase successfull, enoy!!!"})
        return Response({"try again later":"something went wrong pls try again later"})


class DeductData(WalletCheckMixin,GenericAPIView):
    serializer_class = DeductDataSerializer

    def get(self, request, *args, **kwargs):
        return Response({
            "success":"deduct data api callled successfully"
        })

    def post(self, request, data_plan_uuid, *args, **kwargs):
        try:
            data = Data.objects.get(id=data_plan_uuid)
        except:
            return Response({
                "error":"uuid does not exit"
            })

        data_network = data.network
        data_plan_id = data.network_id
        data_bandwidth = data.bandwidth

        # handle reseller pricing
        data_plan_price = data.amount

        profile = Profile.objects.get(user=request.user)
        if profile.reseller == True:
            # update the data plan price to the reseller price
            data_plan_price = data.reseller_amount

        # get the network ID dynamically 
        network_id = NETWORK_ID[data_network]

        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            # get serialized information
            vd = serializer.validated_data
            phone_number = vd['phone_number']

             # check wallet balance against the price of the data plan
            wallet = self.check_wallet_balance(amount=data_plan_price)
            balances = self.deduct_amount_from_balance(amount=data_plan_price)
            message = f'You have purchased {data_bandwidth} Data from {data_network}'
            trans = Transaction.objects.create(
                user=request.user,
                detail= message,
                old_balance=balances[0],
                new_balance= balances[1],
                phone_number=phone_number,
                status='Success',
                amount= data_plan_price,
                type= 'Data',
            )

            trans_serializer = TransactionSerializer(trans).data

            return Response(
                            data={
                                'status': 'success',
                                'message': trans_serializer
                            },
                            status=200
                        )
        else:
            return Response(
                data={
                    'status': 'error',
                    'message': response.json()
                },
                status=400
            )
        
'''
me testing the api for purchase above
'''

class PurchaseAirtimeView(WalletCheckMixin, GenericAPIView):
    serializer_class = AirtimeSerializer
    # queryset = Airtime.
    permission_classes = [IsAuthenticated, ]
    
    
    def get(self, request, *args, **kwargs):
        return Response({
            'status': 'success',
        }, status=200)
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            vd = serializer.validated_data

            # Data from the serializers
            phone_number = vd['phone_number']
            network = vd['network'].upper()
            amount = vd['amount']
            
            
            # check wallet balance method
            wallet = self.check_wallet_balance(amount=amount)
            
            # Parameters and flow for the old process
            # request_params = {
            #     'username': settings.PG_USERNAME,
            #     'password': settings.PG_PASSWORD,
            #     'phone': phone_number,
            #     'network_id': network,
            #     'amount': amount,
            # }

# {
#  "network": 1,
#  "phone": "09065903769",
#  "bypass": false,
#  "request-id": "", 
# "plan_type": "VTU",
#  "amount": "100" 
#}
            # parameters ,url and request for the new 
            
            params = {
                "network": NETWORK_ID[network],
                "phone": phone_number,
                "bypass": False,
                "request-id": "", 
                "plan_type": "VTU",
                "amount": int(amount),
            }

            headers = {
                'Authorization': f'Token {API_PROVIDER_TOKEN}',
                'Content-Type': 'application/json'
            }


            # Process the request
            # url = settings.PG_URL
            # response = requests.get(url, params=request_params)
            url = API_BASE_URL + 'airtime/'
            response = requests.post(
                url,
                headers=headers,
                data=json.dumps(params),
            )
            
            if response.status_code == 200:
                print(response)
                response_data = response.json()
                status = response_data.get("status")
                print(f"status =========== {status}")
                print(response_data)
                data_response = response_data.get("response")
                request_id = response_data.get("request-id")
                message = f'You have purchased {amount} airtime from {network}'
                
                balances = self.deduct_amount_from_balance(amount=amount)

                trans = Transaction.objects.create(
                    user=request.user,
                    detail= message,
                    network=network,
                    response=data_response,
                    request_id=request_id,
                    old_balance=balances[0],
                    new_balance= balances[1],
                    phone_number=phone_number,
                    status='Success',
                    amount= amount,
                    type= 'Airtime',
                )
                profile = Profile.objects.get(user=request.user)
                wallet = Wallet.objects.get(user=profile)
                    
                totalpur = wallet.total_purchase + amount
                Wallet.objects.filter(user=profile).update(total_purchase=totalpur)

                trans_serializer = TransactionSerializer(trans).data

                trans_serializer = TransactionSerializer(trans).data

                return Response(
                    data={
                        'status': 'success',
                        'data': trans_serializer
                    },
                    status=200
                )
                # send push notification
                # devices = FCMDevice.objects.filter(user=user.id)
                # devices.send_message(
                #     message =Message(
                #         notification=Notification(
                #             title='Airtime Purchase Completed!!!',
                #             body=f'Success🎉, You have purchased {amount} airtime from {network}'
                #         ),
                #         token=FCMDevice.objects.get(user=user.id).device_id,
                #     ),

                #     app=settings.FCM_DJANGO_SETTINGS['DEFAULT_FIREBASE_APP']
                # )
            return Response(
                data={
                    'status': 'error',
                    'message': response.json()
                },
            status=400
            )
        return Response(
            data={
                'status': 'error',
                'details': serializer.errors,
            },
            status=400
        )
 #================================================================================

''' modified code for airtime purchase '''

class PurchaseDataView1(WalletCheckMixin, GenericAPIView):
    serializer_class = DataSerializer
    # queryset = Airtime.
    permission_classes = [IsAuthenticated, ]
    
    
    def get(self, request, *args, **kwargs):
        return Response({
            'status': 'success',
        }, status=200)
    
    def post(self, request, data_plan_uuid, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        try:
            # Retrieve data plan information
            data = Data.objects.get(id=data_plan_uuid)
        except Data.DoesNotExist:
            return  JsonResponse({'status': 'error', 'message': 'This UUID does not exist'}, status=404)

        # Process data plan pricing
        data_plan_price = data.reseller_amount if Profile.objects.get(user=request.user).reseller else data.amount



        if serializer.is_valid():
            vd = serializer.validated_data

            # Data from the serializers
            phone_number = vd['phone_number']
            # network = vd['network'].upper()
            # amount = vd['amount']
            
            
            # check wallet balance method
            wallet = self.check_wallet_balance(amount=data_plan_price)
            
            # Parameters and flow for the old process
            # request_params = {
            #     'username': settings.PG_USERNAME,
            #     'password': settings.PG_PASSWORD,
            #     'phone': phone_number,
            #     'network_id': network,
            #     'amount': amount,
            # }


            # parameters ,url and request for the new 
            network_id = NETWORK_ID[data.network]

            params = {
                "network": network_id,
                "mobile_number": phone_number,
                "plan": data.data_plan_id,
                "Ported_number": True,
            }

            headers = {
                'Authorization': f'Token {KVDATA_PROVIDER_TOKEN}',
                'Content-Type': 'application/json'
            }

            try:
                # Process the request
                # url = settings.PG_URL
                # response = requests.get(url, params=request_params)
                url = KVDATA_BASE_URL + 'data/'
                response = requests.post(
                    url,
                    headers=headers,
                    data=json.dumps(params),
                )
            
                if response.status_code == 201:
                        # check if the API returns a failed status
                        if response.json()['Status'] == 'failed':
                            return Response(
                                data={
                                    'status': 'error',
                                    'message': 'There was an Issue with Processing this request',
                                },
                                status=400,
                            )
                        balances = self.deduct_amount_from_balance(amount=data_plan_price)
                    
                        trans = Transaction.objects.create(
                            user=request.user,
                            detail= message,
                            old_balance=balances[0],
                            new_balance= balances[1],
                            phone_number=phone_number,
                            status='Success',
                            amount= data_plan_price,
                            type= 'Data',
                        )

                        trans_serializer = TransactionSerializer(trans).data

                        return Response(
                                        data={
                                            'status': 'success',
                                            'message': trans_serializer
                                        },
                                        status=200
                                    )
                        
                        # devices = FCMDevice.objects.filter(user=user.id)
                        # devices.send_message(
                        #     message =Message(
                        #         notification=Notification(
                        #             title='Data Purchase Completed',
                        #             body=f'Success🎉, You\'ve purchased {data_bandwidth} for ₦{data_plan_price}'
                        #         ),
                        #         token=FCMDevice.objects.get(user=user.id).device_id,
                        #     ),

                        #     app=settings.FCM_DJANGO_SETTINGS['DEFAULT_FIREBASE_APP']
                        # )

                else:
                    return Response(
                        data={
                            'status': 'error',
                            'message': response.json()
                        },
                        status=400
                    )
            except requests.exceptions.Timeout:
                logger.error('Request to KVDATA API Timed out')

                balances = self.deduct_amount_from_balance(amount=data_plan_price)
                trans_params = {
                    'detail': message,
                    'old_balance':balances[0],
                    'new_balance': balances[1],
                    'phone_number':phone_number,
                    'amount': data_plan_price,
                    'type': 'Data',
                }
                trans_params['status'] = 'Pending'
                self.create_transaction_record(
                    **trans_params
                )
                
                return Response(
                    data ={
                        'status': 'error',
                        'message': 'Transaction Pending',
                    },
                    status=504
                )
            
            except requests.exceptions.RequestException as e:
                logger.error(f'Error in the request to KVDATA API: {str(e)}')
                # trans_params['status'] = 'Pending'
                # self.create_transaction_record(
                #     **trans_params
                # )
                return Response(
                    data ={
                        'status': 'error',
                        'message': f'Service Failure {str(e)}'
                    },
                    status=500
                )
        
        return Response(
            data={
                'status': 'error',
                'details': serializer.errors
            },
            status=400,
            )

        #====================================================



import requests
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

class PurchaseDataView2(WalletCheckMixin ,GenericAPIView):
    serializer_class = DataSerializer
    permission_classes = [IsAuthenticated,]

    def post(self, request, data_plan_uuid, *args, **kwargs):
        try:
            # Retrieve data plan information
            data = Data.objects.get(id=data_plan_uuid)
        except Data.DoesNotExist:
            return  JsonResponse({'status': 'error', 'message': 'This UUID does not exist'}, status=404)

        # Process data plan pricing
        data_plan_price = data.reseller_amount if Profile.objects.get(user=request.user).reseller else data.amount

        # Validate serializer
        # serializer = DataSerializer(data=request.POST)
        # if not serializer.is_valid():
        #     return JsonResponse({'status': 'error', 'details': serializer.errors}, status=400)
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
        # Get serialized information
            phone_number = serializer.validated_data['phone_number']
        print(serializer.errors)
        # Check wallet balance against the price of the data plan
        wallet_balance = self.check_wallet_balance(amount=data_plan_price)
        if not wallet_balance:
            return JsonResponse({'status': 'error', 'message': 'Insufficient funds'}, status=400)

        # Construct the request parameters
        network_id = NETWORK_ID[data.network]
        print(serializer.errors)
        print(network_id)
        print(phone_number)
        print(data.data_plan_id)
        params = {
            "network": network_id,
            "mobile_number": phone_number,
            "plan": data.data_plan_id,
            "Ported_number": True,
        }

        headers = {
            'Authorization': f'Token {KVDATA_PROVIDER_TOKEN}',
            'Content-Type': 'application/json'
        }

        # Make the request to KVDATA API
        try:
            response = requests.post(KVDATA_BASE_URL + 'data/', data=json.dumps(params), headers=headers, timeout=20)
            response.raise_for_status()
            print(response.text)
            print(response.body)
            print(response.status_code)
            if response.status_code == 201 and response.json().get('Status') == 'success':
                # Deduct amount from balance
                new_balances = deduct_amount_from_balance(amount=data_plan_price)

                # Create transaction record
                trans = Transaction.objects.create(
                    user=request.user,
                    detail=f'You have purchased {data.bandwidth} Data from {data.network}',
                    old_balance=new_balances[0],
                    new_balance=new_balances[1],
                    phone_number=phone_number,
                    status='Success',
                    amount=data_plan_price,
                    type='Data',
                )

                trans_serializer = TransactionSerializer(trans).data

                # Send success response
                return JsonResponse({'status': 'success', 'message': trans_serializer}, status=200)

            else:
                return JsonResponse({'status': 'error', 'message': response.json()}, status=400)

        except requests.exceptions.Timeout:
            logger.error('Request to KVDATA API Timed out')

            # Create pending transaction record
            trans_params = {
                'detail': f'You have purchased {data.bandwidth} Data from {data.network}',
                'old_balance': wallet_balance[0],
                'new_balance': wallet_balance[1],
                'phone_number': phone_number,
                'amount': data_plan_price,
                'type': 'Data',
            }
            trans_params['status'] = 'Pending'
            create_transaction_record(**trans_params)

            return JsonResponse({'status': 'error', 'message': 'Transaction Pending'}, status=504)

        except requests.exceptions.RequestException as e:
            logger.error(f'Error in the request to KVDATA API: {str(e)}')
            return JsonResponse({'status': 'error', 'message': 'Service Failure'}, status=500)




















    
class PurchaseDataView(WalletCheckMixin ,GenericAPIView):
    serializer_class = DataSerializer
    permission_classes = [IsAuthenticated,]

    def post(self, request, data_plan_uuid, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            data = Data.objects.get(id=data_plan_uuid)
        
        except:
            return Response(
                data={
                    'status': 'error',
                    'message': 'This uuid does not exist'
                }
            )
        
        # gather info about data i.e network, Plan price, plan type and network id
        data_network = data.network
        data_plan_id = data.data_plan_id
        data_bandwidth = data.bandwidth

        # handle reseller pricing
        data_plan_price = data.amount

        profile = Profile.objects.get(user=request.user)
        if profile.reseller == True:
            # update the data plan price to the reseller price
            data_plan_price = data.reseller_amount

        # get the network ID dynamically 
        network_id = NETWORK_ID[data_network]

        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            # get serialized information
            vd = serializer.validated_data
            phone_number = vd['phone_number']

            # check wallet balance against the price of the data plan
            wallet = self.check_wallet_balance(amount=data_plan_price)
#{
#  "network": 1,
#  "phone" : "09065903769",
#  "bypass" : false,
#  "request-id" : "",
#  "data_plan" : 1 
#}



            '''make the request'''
            params = {
                "network":  network_id,
                "phone": phone_number,
                "bypass" : False,
                "request-id" : "",
                "data_plan" : data_plan_id,
                "Ported_number": True,
                
            }

            headers = {
                'Authorization': f'Token {API_PROVIDER_TOKEN}',
                'Content-Type': 'application/json'
            }
            
            message = f'You have purchased {data_bandwidth} Data from {data_network}'
            

            try:

                response = requests.post(API_BASE_URL + 'data/',headers=headers, data=json.dumps(params),timeout=20)
                #response.raise_for_status()

                if response.status_code == 201 or response.status_code == 200:
                    response_data = response.json()
                    data_response = response_data.get("response")
                    request_id = response_data.get("request_id") 
                    # check if the API returns a failed status
                    if response.json()['Status'] == 'fail':
                        return Response(
                            data={
                                'status': 'error',
                                'message': 'There was an Issue with Processing this request',
                            },
                            status=400,
                        )
                    balances = self.deduct_amount_from_balance(amount=data_plan_price)
                
                    trans = Transaction.objects.create(
                        user=request.user,
                        detail= message,
                        response=data_response,
                        network=data_network,
                        request_id=request_id,
                        old_balance=balances[0],
                        new_balance= balances[1],
                        phone_number=phone_number,
                        status='Success',
                        amount= data_plan_price,
                        type= 'Data',
                    )
                    # user = User.objects.get(username=username)
                    # try:
                    #     profile = Profile.objects.get(user=user)

                    # except:
                    #     return Response(
                    #         data={
                    #         'status':'error',
                    #         'data': 'No Profile found'
                    #         },
                    #         status=404
                    #     )
                    wallet = Wallet.objects.get(user=profile)
                    
                    totalpur = wallet.total_purchase + data_plan_price
                    Wallet.objects.filter(user=profile).update(total_purchase=totalpur)

                    trans_serializer = TransactionSerializer(trans).data

                    return Response(
                                    data={
                                        'status': 'success',
                                        'message': trans_serializer
                                    },
                                    status=200
                                )
                    
                    # devices = FCMDevice.objects.filter(user=user.id)
                    # devices.send_message(
                    #     message =Message(
                    #         notification=Notification(
                    #             title='Data Purchase Completed',
                    #             body=f'Success🎉, You\'ve purchased {data_bandwidth} for ₦{data_plan_price}'
                    #         ),
                    #         token=FCMDevice.objects.get(user=user.id).device_id,
                    #     ),

                    #     app=settings.FCM_DJANGO_SETTINGS['DEFAULT_FIREBASE_APP']
                    # )

                else:
                    return Response(
                        data={
                            'status': 'error',
                            'message': response.json()
                        },
                        status=400
                    )
            except requests.exceptions.Timeout:
                logger.error('Request to KVDATA API Timed out')

                balances = self.deduct_amount_from_balance(amount=data_plan_price)
                trans_params = {
                    'detail': message,
                    'old_balance':balances[0],
                    'new_balance': balances[1],
                    'phone_number':phone_number,
                    'amount': data_plan_price,
                    'type': 'Data',
                }
                trans_params['status'] = 'Pending'
                self.create_transaction_record(
                    **trans_params
                )
                
                return Response(
                    data ={
                        'status': 'error',
                        'message': 'Transaction Pending',
                    },
                    status=504
                )
            
            except requests.exceptions.RequestException as e:
                logger.error(f'Error in the request to KVDATA API: {str(e)}')
                # trans_params['status'] = 'Pending'
                # self.create_transaction_record(
                #     **trans_params
                # )
                return Response(
                    data ={
                        'status': 'error',
                        'message': f'Service Failure {str(e)}'
                    },
                    status=500
                )
        
        return Response(
            data={
                'status': 'error',
                'details': serializer.errors
            },
            status=400,
            )


class BillPurchaseMixin(RequestWrapper, WalletCheckMixin):
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        
        if  serializer.is_valid():
            valid_data = serializer.validated_data
            print(valid_data)

            try:            
                amount = valid_data['amount']
            except:
                amount = 0
            

            # check balance, if successful, process the transaction
            self.check_wallet_balance(amount=amount)
            # commented out 'amount'
            data = self.request_data(valid_data, **kwargs)
            print(f'data === {data}')
            response = self.req_post(data=data)
            print(f"response ===== {response.json()}")
            json_resp = response.json()
            
            if "message" in json_resp and "balance is low" in json_resp["message"]:
                return Response(
                    json_resp,
                    status=400,
                )

            if json_resp['status'] == 'fail':
                return Response(
                    json_resp,
                    status=400,
                )
            
            
            
            if "message" in json_resp and "balance is low" in json_resp["message"]:
                return Response(
                    json_resp,
                    status=400,
                )
            
            # deduct from wallet
            old_bal, new_bal = self.deduct_amount_from_balance(amount=amount)

            # create the transaction
            kwargs['json_resp'] = json_resp
            trans_data = self.transaction_data(old_bal, new_bal, **kwargs)
            trans = self.create_transaction_record(
                **trans_data
            )
            trans_serializer = TransactionSerializer(trans).data
            
            return Response(
                {
                    'status': 'success',
                    'data': trans_serializer
                },
                status=200
            )

        return Response(
            serializer.errors,
            status=400
        )


class PurchaseElectricityView(BillPurchaseMixin, GenericAPIView):
    url = API_BASE_URL
    endpoint = 'bill'
    provider_token = API_PROVIDER_TOKEN
    serializer_class = ElectricBillPaymentSerializer
    queryset = Transaction.objects.all()
    permission_classes = [IsAuthenticated, ]

    def request_data(self, amount, valid_data, **kwargs):
        return {
                "disco": ELECTRIC_DISCO_ID[valid_data['disco']],
                "amount": int(amount),
                "meter_number": valid_data['meter_number'],
                "meter_type": valid_data["meter_type"],
                "bypass": True,
                "phone": valid_data["phone"],
                "request-id": f'{uuid4()}'
            }

    def transaction_data(amount, old_bal, new_bal, **kwargs):
        token = kwargs['json_resp']['token']
        trans_data = {
            'detail': f'You have purchased {amount}, {token}',
            'old_balance': old_bal,
            'new_balance': new_bal,
            'phone_number': '',
            'status': 'Success',
            'amount': amount,
            'type': 'Electricity'
        }
        return trans_data
  
    
class PurchaseCableSubscriptionView(BillPurchaseMixin, GenericAPIView):
    url = API_BASE_URL
    endpoint = 'cable'
    provider_token = API_PROVIDER_TOKEN
    serializer_class = CablePaymentSerializer
    permission_classes = [IsAuthenticated, ]
    queryset = CableSubscription.objects.all()
    def request_data(self, amount, valid_data, **kwargs):
        cable_id = kwargs['cable_uuid']
        cable_sub_instance = CableSubscription.objects.get(id=cable_id)

        return {
                "cable": CABLE_PROVIDER_ID[valid_data['cable_provider']],
                "cable_plan": str(cable_sub_instance.plan_id),
                "iuc": valid_data['iuc'],
                "bypass": True,
                "request-id": f'{uuid4()}'
            }

    def transaction_data(amount, old_bal, new_bal, **kwargs):
        token = kwargs['json_resp']['token']
        trans_data = {
            'detail': f'You have purchased {amount}, {token}',
            'old_balance': old_bal,
            'new_balance': new_bal,
            'phone_number': '',
            'status': 'Success',
            'amount': amount,
            'type': 'Cable Subscription'
        }
        return trans_data



class PurchaseExamEpin(BillPurchaseMixin, GenericAPIView):
    url = API_BASE_URL
    endpoint = 'exam'
    provider_token = API_PROVIDER_TOKEN
    serializer_class = PurchaseExamEpinSerializer
    queryset = Transaction.objects.all()
    # permission_classes = [IsAuthenticated, ]

    def request_data(self, valid_data, **kwargs):
        return {
                # "network": valid_data['network'].upper(),
                "exam": EXAM_RESULT_CHECKER[valid_data["exam_name"].upper()],
                "quantity": valid_data["quantity"],
            }

    def transaction_data(amount, old_bal, new_bal, **kwargs):
        # trans_data = kwargs['json_resp']
        token = kwargs['json_resp']['pin']
        exam = kwargs['json_resp']['exam']
        request_id = kwargs['json_resp']['request_id']
        print(kwargs['json_resp'])
        trans_data = {
            'detail': f'You have purchased {amount}, {token}',
            "request_id": request_id,
            'old_balance': old_bal,
            'new_balance': new_bal,
            'phone_number': token,
            'status': 'Success',
            'amount': amount,
            'type': f'{exam} - Exam Epin'
        }
        return trans_data
  





"""
Section for validating Services Mainly Electricity and Cable.
"""
class BillValidatorMixin(RequestWrapper):

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        
        if serializer.is_valid():
            valid_data = serializer.validated_data
            
            data = self.request_data(valid_data)
            print(data)

            response = self.req_get(params=data)
            
            json_data = response.json()
            print(json_data)
            
            if json_data['status'] == 'fail':
                return Response(
                    json_data,
                    status=400
                )

            if json_data['status'] == False:
                return Response(
                    json_data,
                    status=400
                )
            return Response(
                json_data
            )

        return Response(
            serializer.errors,
            status=400
        )

class ValidateMeterNumberAPI(BillValidatorMixin, GenericAPIView):
    serializer_class = ValidateMeterNumberSerializer
    permission_classes = [IsAuthenticated,]
    url = API_BASE_URL
    endpoint = 'bill/bill-validation'
    provider_token = API_PROVIDER_TOKEN

    def request_data(self, valid_data):
        return {
            'meter_number': str(valid_data['meter_number']),
            'meter_type': valid_data['meter_type'],
            'disco': ELECTRIC_DISCO_ID[valid_data['disco']]
        }
        
class ValidateCableNumberAPI(BillValidatorMixin, GenericAPIView):
    serializer_class = ValidateCableNumber
    permission_classes = [IsAuthenticated,]
    url = API_BASE_URL
    endpoint = 'cable/cable-validation'
    provider_token = API_PROVIDER_TOKEN
    
    def request_data(self, valid_data):
        return {
            'iuc': str(valid_data['iuc']),
            'cable': CABLE_PROVIDER_ID[valid_data['cable_provider']],
        }

'''
Collecting the pricing plans for data plans for a certain network
'''
class DataPriceListAPI(ListAPIView):
    serializer_class = DataPriceSerializer
    # permission_classes = [IsAuthenticated, ]
    lookup_field = 'network'
    queryset = Data.objects.all()

    def get_queryset(self):
        
        return Data.objects.filter(network=self.kwargs['network'])

        # return super().get_queryset()